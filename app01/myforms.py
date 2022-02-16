'''Kou'''
# 针对用户表的forms组件代码
from django import forms
from app01 import models


class MyRegForm(forms.Form):
    username = forms.CharField(label='用户名', min_length=3, max_length=8,
                               error_messages={
                                   'required': '朋友，用户名不能为空',
                                   'min_length': '兄弟，用户名最少3位',
                                   'max_length': '姐妹，用户名最多8位'
                               },
                               widget=forms.widgets.TextInput(attrs={'class': 'form-control'})
                               )
    password = forms.CharField(label='密码', min_length=3, max_length=8,
                               error_messages={
                                   'required': '朋友，密码不能为空',
                                   'min_length': '兄弟，密码最少3位',
                                   'max_length': '姐妹，密码最多8位'
                               },
                               widget=forms.widgets.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(label='确认密码', min_length=3, max_length=8,
                                       error_messages={
                                           'required': '朋友，确认密码不能为空',
                                           'min_length': '兄弟，确认密码最少3位',
                                           'max_length': '姐妹，确认密码最多8位'
                                       },
                                       widget=forms.widgets.PasswordInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='邮箱',
                             error_messages={
                                 'required': '邮箱空着确实不太好',
                                 'invalid': '亲，这邮箱好像不对劲'
                             },
                             widget=forms.widgets.EmailInput(attrs={'class': 'form-control'}))

    #     钩子函数，校验用户名是否已经存在
    def clean_username(self):
        username = self.cleaned_data.get('username')
        is_exist = models.UserInfo.objects.filter(username=username)
        if is_exist:
            self.add_error('username', '用户名已经有人占用了')
        return username

    def clean(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if not password == confirm_password:
            self.add_error('confirm_password', '两次密码不一致- -')
        return self.cleaned_data
