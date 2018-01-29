# -*- coding:utf-8 -*-
__author__ = 'gjw'
__date__ = '2018/1/26 15:48'
from . import home


# 调用蓝图
@home.route('/')
def index():
    return "<h1 style='color:green'>this is home</h1>"
