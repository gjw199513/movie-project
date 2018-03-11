# -*- coding:utf-8 -*-
__author__ = 'gjw'
__date__ = '2018/1/26 15:46'
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask.ext.redis import FlaskRedis
import pymysql
import os

# 创建一个新的应用
app = Flask(__name__)
# 连接数据库
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:gjw605134015@localhost:3306/movie"
# 如果设置成 True (默认情况)，Flask-SQLAlchemy 将会追踪对象的修改并且发送信号。
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
# 安全码
app.config["SECRET_KEY"] = "0993703df6ef45aba560f493b14fc49e"
# redis连接
app.config["REDIS_URL"] = "redis://127.0.0.1:6379/0"

# 上传文件配置
app.config["UP_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/")
app.config["FC_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/users/")

app.debug = True
db = SQLAlchemy(app)
rd = FlaskRedis(app)

# 注册蓝图
from app.home import home as home_blueprint
from app.admin import admin as admin_blueprint

app.register_blueprint(home_blueprint)
app.register_blueprint(admin_blueprint, url_prefix='/admin')


# 404页面
# 404页面配置需要在app入口中配置，在蓝图中配置无效
@app.errorhandler(404)
def page_not_found(error):
    return render_template('home/404.html'), 404
