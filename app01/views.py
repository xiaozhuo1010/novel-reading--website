from django.shortcuts import render, HttpResponse, redirect
from app01.myforms import MyRegForm
from app01 import models
from django.http import JsonResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from utils.mypage import Pagination
from django.db.models import Count
from django.db.models.functions import TruncMonth
import json


# Create your views here.

def register(request):
    form_obj = MyRegForm()
    back_dic = {
        'code': 1000,
        'msg': ''
    }
    if request.method == 'POST':
        form_obj = MyRegForm(request.POST)
        if form_obj.is_valid():
            clean_data = form_obj.cleaned_data
            clean_data.pop('confirm_password')
            file_obj = request.FILES.get('avatar')
            if form_obj:
                clean_data['avatar'] = file_obj
            models.UserInfo.objects.create_user(**clean_data)
            back_dic['url'] = '/login/'
        else:
            back_dic['code'] = 2000
            back_dic['msg'] = form_obj.errors
        return JsonResponse(back_dic)
    return render(request, 'register.html', locals())


def login(request):
    if request.method == 'POST':
        back_dic = {
            'code': 1000,
            'msg': ''
        }
        username = request.POST.get('username')
        password = request.POST.get('password')
        code = request.POST.get('code')
        if request.session.get('code').upper() == code.upper():
            #         校验密码
            user_obj = auth.authenticate(username=username, password=password)
            if user_obj:
                #             保存用户状态
                auth.login(request, user_obj)
                back_dic['url'] = '/home/'
            else:
                back_dic['code'] = 2000
                back_dic['msg'] = '用户名或密码错误了，铁汁'
        else:
            back_dic['code'] = 3000
            back_dic['msg'] = '不是吧不是吧，验证码这么明显，不会都填不对吧'
        return JsonResponse(back_dic)

    return render(request, 'login.html')


from PIL import Image, ImageDraw, ImageFont
# 内存管理器模块
from io import BytesIO, StringIO
import random


def get_random():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def get_code(request):
    img_obj = Image.new('RGB', (480, 35), get_random())
    img_draw = ImageDraw.Draw(img_obj)  # 产生一个画笔对象
    img_font = ImageFont.truetype('static/font/111.ttf', 30)  # 字体样式
    #     5位随机验证码
    code = ''
    for i in range(5):
        random_upper = chr(random.randint(65, 90))
        random_lower = chr(random.randint(97, 122))
        random_int = str(random.randint(0, 9))
        tmp = random.choice([random_upper, random_lower, random_int])
        img_draw.text((i * 60 + 60, 5), tmp, get_random(), img_font)
        code += tmp
    # print(code)
    request.session['code'] = code
    io_obj = BytesIO()
    img_obj.save(io_obj, 'png')
    return HttpResponse(io_obj.getvalue())


def home(request):
    article_queryset = models.Article.objects.all()
    current_page = request.GET.get('page', 1)
    all_count = article_queryset.count()
    page_obj = Pagination(current_page=current_page, all_count=all_count)
    page_queryset = article_queryset[page_obj.start: page_obj.end]
    return render(request, 'home.html', locals())


@login_required
def set_password(request):
    if request.is_ajax():
        back_dic = {'code': 1000, 'msg': ''}
        if request.method == 'POST':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            is_right = request.user.check_password(old_password)
            if is_right:
                if new_password == confirm_password:
                    request.user.set_password(new_password)
                    request.user.save()
                    back_dic['msg'] = '修改成功'
                else:
                    back_dic['code'] = 1001
                    back_dic['msg'] = '两次密码不一致'
            else:
                back_dic['code'] = 1002
                back_dic['msg'] = '原密码错误'
        return JsonResponse(back_dic)


@login_required
def logout(request):
    auth.logout(request)
    return redirect('/home/')

@login_required
def site(request, username, **kwargs):
    user_obj = models.UserInfo.objects.filter(username=username).first()
    if not user_obj:
        return render(request, 'errors.html')
    blog = user_obj.blog
    article_list = models.Article.objects.filter(blog=blog)

    if kwargs:
        # print(kwargs)
        condition = kwargs.get('condition')
        param = kwargs.get('param')
        # print(article_list)
        if condition == 'category':
            article_list = article_list.filter(category_id=param)
            # print(article_list)
        elif condition == 'tag':
            article_list = article_list.filter(tag__id=param)
        else:
            year, month = param.split('-')
            article_list = article_list.filter(create_time__year=year, create_time__month=month)

    current_page = request.GET.get('page', 1)
    all_count = article_list.count()
    page_obj = Pagination(current_page=current_page, all_count=all_count)
    page_queryset = article_list[page_obj.start: page_obj.end]
    # 分类
    # print(date_list)

    return render(request, 'site.html', locals())

@login_required
def article_detail(request, username, article_id):
    article_obj = models.Article.objects.filter(pk=article_id, blog__userinfo__username=username).first()
    # print(username, article_id)
    if not article_obj:
        return render(request, 'errors.html')
    comment_list = models.Comment.objects.filter(article=article_obj)
    return render(request, 'article_detail.html', locals())


from django.db.models import F


def up_or_down(request):
    """
    1.校验用户是否登陆
    2.判断当前文章是否是当前用户自己写的(自己不能点自己的文章)
    3.当前用户是否已经给当前文章点过了
    4.操作数据库了
    :param request:
    :return:
    """
    if request.is_ajax():
        back_dic = {'code': 1000, 'msg': ''}
        # 1 先判断当前用户是否登陆
        if request.user.is_authenticated():
            article_id = request.POST.get('article_id')
            is_up = request.POST.get('is_up')
            # print(is_up,type(is_up))  # true <class 'str'>
            is_up = json.loads(is_up)  # 记得转换
            # print(is_up, type(is_up))  # True <class 'bool'>
            # 2 判断当前文章是否是当前用户自己写的  根据文章id查询文章对象 根据文章对象查作者 根request.user比对
            article_obj = models.Article.objects.filter(pk=article_id).first()
            print(111)
            # print(article_obj.username)
            print(is_up)
            if not article_obj.blog.userinfo == request.user:
                # 3 校验当前用户是否已经点了      哪个地方记录了用户到底点没点
                is_click = models.UpAndDown.objects.filter(user=request.user, article=article_obj)
                if not is_click:
                    # 4 操作数据库 记录数据      要同步操作普通字段
                    # 判断当前用户点了赞还是踩 从而决定给哪个字段加一
                    if is_up:
                        # 给点赞数加一
                        models.Article.objects.filter(pk=article_id).update(up_num=F('up_num') + 1)
                        back_dic['msg'] = '点赞成功'
                    else:
                        # 给点踩数加一
                        models.Article.objects.filter(pk=article_id).update(down_num=F('down_num') + 1)
                        back_dic['msg'] = '点踩成功'
                    # 操作点赞点踩表
                    models.UpAndDown.objects.create(user=request.user, article=article_obj, is_up=is_up)
                else:
                    back_dic['code'] = 1001
                    back_dic['msg'] = '你已经点过了,不能再点了'  # 这里你可以做的更加的详细 提示用户到底点了赞还是点了踩
            else:
                back_dic['code'] = 1002
                back_dic['msg'] = '你个臭不要脸的!'
        else:
            back_dic['code'] = 1003
            back_dic['msg'] = '请先<a href="/login/">登陆</a>'
        return JsonResponse(back_dic)
from django.db import transaction
def comment(request):
    # 自己也可以给自己的文章评论内容
    if request.is_ajax():
        back_dic = {'code': 1000, 'msg': ""}
        if request.method == 'POST':
            if request.user.is_authenticated():
                article_id = request.POST.get('article_id')
                content = request.POST.get("content")
                parent_id = request.POST.get('parent_id')
                # 直接操作评论表 存储数据      两张表
                with transaction.atomic():
                    models.Article.objects.filter(pk=article_id).update(comment_num = F('comment_num') + 1)
                    models.Comment.objects.create(user=request.user,article_id=article_id,content=content,parent_id=parent_id)
                back_dic['msg'] = '评论成功'
            else:
                back_dic['code'] = 1001
                back_dic['msg'] = '用户未登陆'
            return JsonResponse(back_dic)
@login_required
def backend(request):
    article_list = models.Article.objects.filter(blog=request.user.blog)
    page_obj = Pagination(current_page=request.GET.get('page',1),all_count=article_list.count(),per_page_num=5)
    page_queryset = article_list[page_obj.start:page_obj.end]
    return render(request,'backend/backend.html',locals())




from bs4 import BeautifulSoup


@login_required
def add_article(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get("category")
        tag_id_list = request.POST.getlist('tag')
        # 模块使用
        soup = BeautifulSoup(content, 'html.parser')

        tags = soup.find_all()
        # 获取所有的标签
        for tag in tags:
            # print(tag.name)  # 获取页面所有的标签
            # 针对script标签 直接删除
            if tag.name == 'script':
                # 删除标签
                tag.decompose()
        # 文章简介
        # 1 先简单暴力的直接切去content 150个字符
        # desc = content[0:150]
        # 2 截取文本150个
        desc = soup.text[0:150]
        article_obj = models.Article.objects.create(
            title=title,
            content=str(soup),
            desc=desc,
            category_id=category_id,
            blog=request.user.blog
        )
        # 文章和标签的关系表 是我们自己创建的 没法使用add set remove clear方法
        # 自己去操作关系表   一次性可能需要创建多条数据      批量插入bulk_create()
        article_obj_list = []
        for i in tag_id_list:
            tag_article_obj = models.Article2Tag(article=article_obj, tag_id=i)
            article_obj_list.append(tag_article_obj)
        # 批量插入数据
        models.Article2Tag.objects.bulk_create(article_obj_list)
        # 跳转到后台管理文章展示页
        return redirect('/backend/')
    category_list = models.Category.objects.filter(blog=request.user.blog)
    tag_list = models.Tag.objects.filter(blog=request.user.blog)
    return render(request, 'backend/add_article.html', locals())
def book_edit(request,edit_id):
    # user_obj = models.UserInfo.objects.filter(username=request.user.username).first()
    edit_obj = models.Article.objects.filter(id=edit_id).first()
    category_list = models.Category.objects.filter(blog=request.user.blog)
    tag_list = models.Tag.objects.filter(blog=request.user.blog)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        models.Article.objects.filter(pk=edit_id).update(title=title,content=content)
        return redirect('/backend/')
    return render(request,'backend/book_edit.html',locals())
def book_delete(request):
    dele_id = request.GET.get('dele_id')
    models.Article.objects.filter(id=dele_id).delete()
    return redirect('/backend/')
import os
from BBS import settings


def upload_image(request):
    """
         //成功时
        {
                "error" : 0,
                "url" : "http://www.example.com/path/to/file.ext"
        }
        //失败时
        {
                "error" : 1,
                "message" : "错误信息"
        }
    :param request:
    :return:
    """
    back_dic = {'error': 0, }  # 先提前定义返回给编辑器的数据格式

    # 用户写文章上传的图片 也算静态资源 也应该防盗media文件夹下

    if request.method == "POST":
        # 获取用户上传的图片对象
        # print(request.FILES)  # 打印看到了健固定叫imgFile
        file_obj = request.FILES.get('imgFile')
        # 手动拼接存储文件的路径
        file_dir = os.path.join(settings.BASE_DIR, 'media', 'article_img')
        # 优化操作 先判断当前文件夹是否存在 不存在 自动创建
        if not os.path.isdir(file_dir):
            os.mkdir(file_dir)  # 创建一层目录结构  article_img
        # 拼接图片的完整路径
        file_path = os.path.join(file_dir, file_obj.name)
        with open(file_path, 'wb') as f:
            for line in file_obj:
                f.write(line)
        back_dic['url'] = '/media/article_img/%s' % file_obj.name

    return JsonResponse(back_dic)


@login_required
def set_avatar(request):
    user_obj = models.UserInfo.objects.filter(username=request.user.username).first()
    if request.method == 'POST':
        file_obj = request.FILES.get('avatar')
        # models.UserInfo.objects.filter(pk=request.user.pk).update(avatar=file_obj)  # 不会再自动加avatar前缀
        # 1.自己手动加前缀
        # 2.换一种更新方式
        user_obj = request.user
        user_obj.avatar = file_obj
        user_obj.save()
        return redirect('/home/')
    blog = request.user.blog
    username = request.user.username
    return render(request, 'set_avatar.html', locals())
from django.db.models import Q
# def searchfor(request):
#         if request.method == 'POST':
#             content = request.POST.get('content')
#             article_list=models.Article.objects.filter(title__contains=content)
#             current_page = request.GET.get('page', 1)
#             all_count = article_list.count()
#             page_obj = Pagination(current_page=current_page, all_count=all_count)
#             page_queryset = article_list[page_obj.start: page_obj.end]
@login_required
def searchfor(request):
    current_page = request.GET.get('page', 1)
    if request.method == 'POST':
        content = request.POST.get('content')
        article_list = models.Article.objects.filter(title__icontains=content)
        all_count = article_list.count()
        page_obj = Pagination(current_page=current_page, all_count=all_count)
        page_queryset = article_list[page_obj.start: page_obj.end]
        blog = article_list.first().blog
        username = blog.site_name
        return render(request, 'search.html', locals())