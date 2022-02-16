"""BBS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from app01 import views
from django.views.static import serve
from BBS import settings

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # 查询搜索
    url(r'^searchfor/', views.searchfor, name='searchfor'),
    #     注册
    url(r'^register/', views.register, name='reg'),
    # 登录
    url(r'^login/', views.login, name='log'),
    url(r'^get_code/', views.get_code, name='getcode'),
    url(r'^home/', views.home, name='home'),
    # 改密
    url(r'^set_password/', views.set_password, name='set_pwd'),
    url(r'^logout/', views.logout, name='logout'),
    # 点赞点菜
    url(r'^up_or_down/', views.up_or_down),
    # 评论
    url(r'^comment/', views.comment),
    # 后台管理
    url(r'^backend/', views.backend),
    url(r'^book/edit/(?P<edit_id>\d+)/', views.book_edit,name='book_edit'),
    url(r'^book/delete/', views.book_delete,name='book_delete'),
    # 添加文章
    url(r'^add/article/', views.add_article),
    url(r'^set/avatar/', views.set_avatar),
    #     暴露后端指定文件夹资源
    url(r'^media/(?P<path>.*)', serve, {'document_root': settings.MEDIA_ROOT}),
    #     个人站点页面搭建
    url(r'^(?P<username>\w+)/$', views.site, name='site'),
    url(r'^(?P<username>\w+)/(?P<condition>category|tag|archive)/(?P<param>.*)/', views.site),
    #     文章详情页面
    url(r'^(?P<username>\w+)/article/(?P<article_id>\d+)/', views.article_detail)

]
