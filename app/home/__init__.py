# -*- coding:utf-8 -*-
__author__ = 'gjw'
__date__ = '2018/1/26 15:48'
# 定义蓝图
from flask import Blueprint

home = Blueprint('home', __name__)

import app.home.views
