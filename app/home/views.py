# -*- coding:utf-8 -*-
__author__ = 'gjw'
__date__ = '2018/1/26 15:48'
from . import home
from flask import render_template, redirect, url_for


# 调用蓝图
# 登录
@home.route('/login/')
def login():
    return render_template('home/login.html')


# 退出
@home.route('/logout/')
def logout():
    # 重定向，退出后返回登录视图
    return redirect(url_for('home.login'))


# 注册
@home.route('/regist/')
def regist():
    return render_template('home/regist.html')


# 会员中心
@home.route('/user/')
def user():
    return render_template('home/user.html')


# 修改密码
@home.route('/pwd/')
def pwd():
    return render_template('home/pwd.html')


# 评论记录
@home.route('/comments/')
def comments():
    return render_template('home/comments.html')


# 登录日志
@home.route('/loginlog/')
def loginlog():
    return render_template('home/loginlog.html')


# 收藏电影
@home.route('/moviecol/')
def moviecol():
    return render_template('home/moviecol.html')


# 电影列表
@home.route('/')
def index():
    return render_template('home/index.html')


# 动画
@home.route('/animation/')
def animation():
    return render_template('home/animation.html')


# 搜索
@home.route('/search/')
def search():
    return render_template('home/search.html')


# 电影详情
@home.route('/play/')
def play():
    return render_template('home/play.html')


