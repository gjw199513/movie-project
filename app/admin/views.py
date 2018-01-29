# -*- coding:utf-8 -*-
__author__ = 'gjw'
__date__ = '2018/1/26 15:48'
from . import admin


# 调用蓝图
@admin.route('/')
def index():
    return "<h1 style='color:red'>this is admin</h1>"
