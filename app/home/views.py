# -*- coding:utf-8 -*-
__author__ = 'gjw'
__date__ = '2018/1/26 15:48'
from . import home
from flask import render_template, redirect, url_for, flash, session, request, Response
from app.home.forms import RegistForm, LoginForm, UserdetailForm, PwdForm, CommentForm
from app.models import User, Userlog, Preview, Tag, Movie, Comment, Moviecol
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from app import db, app, rd
from functools import wraps
import uuid
import os
import datetime


# 登录控制函数
def user_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for('home.login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# 修改文件名称
def change_filename(filename):
    # 将文件名分割
    fileinfo = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + fileinfo[-1]
    return filename


# 调用蓝图
# 登录
@home.route('/login/', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=data['name']).first()
        if not user.check_pwd(data['pwd']):
            flash("密码错误！", "err")
            return redirect(url_for('home.login'))
        session["user"] = user.name
        session["user_id"] = user.id
        userlog = Userlog(
            user_id=user.id,
            ip=request.remote_addr,
        )
        db.session.add(userlog)
        db.session.commit()
        return redirect(url_for('home.index', page=1))
    return render_template('home/login.html', form=form)


# 退出
@home.route('/logout/')
def logout():
    # 重定向，退出后返回登录视图
    session.pop("user", None)
    session.pop("user_id", None)
    return redirect(url_for('home.login'))


# 会员注册
@home.route('/regist/', methods=["GET", "POST"])
def regist():
    form = RegistForm()
    if form.validate_on_submit():
        data = form.data
        user = User(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            pwd=generate_password_hash(data["pwd"]),
            # 生产随机的uuid
            uuid=uuid.uuid4().hex
        )
        db.session.add(user)
        db.session.commit()
        flash("注册成功", "ok")
    return render_template('home/regist.html', form=form)


# 会员修改资料
@home.route('/user/', methods=["GET", "POST"])
@user_login_req
def user():
    form = UserdetailForm()
    user = User.query.get(int(session['user_id']))
    # 允许头像初始为空
    form.face.validators = []
    if request.method == "GET":
        # 为表单设置默认值可以直接在form.属性.data中进行赋值
        # 也可以在HTML字段中在value属性中设置默认值
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info
    if form.validate_on_submit():
        data = form.data
        file_face = secure_filename(form.face.data.filename)
        # 在未存在文件路径时，创建文件
        if not os.path.exists(app.config['FC_DIR']):
            os.makedirs(app.config['FC_DIR'])
            os.chmod(app.config["FC_DIR"], "rw")
        # 文件改名
        user.face = change_filename(file_face)
        # 保存文件
        form.face.data.save(app.config["FC_DIR"] + user.face)

        name_count = User.query.filter_by(name=data["name"]).count()
        # 判断信息是否存在
        if data["name"] != user.name and name_count == 1:
            flash("昵称已经存在！", "err")
            return redirect(url_for("home.user"))

        email_count = User.query.filter_by(email=data["email"]).count()
        if data["email"] != user.email and email_count == 1:
            flash("邮箱已经存在！", "err")
            return redirect(url_for("home.user"))

        phone_count = User.query.filter_by(phone=data["phone"]).count()
        # 判断是否重复
        if data["phone"] != user.phone and phone_count == 1:
            flash("手机号码已经存在！", "err")
            return redirect(url_for("home.user"))
        user.name = data["name"]
        user.email = data["email"]
        user.phone = data["phone"]
        user.info = data["info"]
        db.session.add(user)
        db.session.commit()
        flash("修改成功", "ok")
        return redirect(url_for("home.user"))
    return render_template('home/user.html', form=form, user=user)


# 修改密码
@home.route('/pwd/', methods=["GET", "POST"])
@user_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=session['user']).first()
        if not user.check_pwd(data["old_pwd"]):
            flash("旧密码错误", "err")
            return redirect(url_for("home.pwd"))
        user.pwd = generate_password_hash(data['new_pwd'])
        db.session.add(user)
        db.session.commit()
        flash("修改密码成功,请重新登录!", "ok")
        return redirect(url_for("home.logout"))
    return render_template('home/pwd.html', form=form)


# 评论记录
@home.route('/comments/<int:page>/')
@user_login_req
def comments(page=None):
    if page is None:
        page = 1
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Comment.movie_id,
        User.id == session["user_id"],
    ).order_by(
        Comment.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('home/comments.html', page_data=page_data)


# 会员登录日志
@home.route('/loginlog/<int:page>', methods=["GET"])
@user_login_req
def loginlog(page=None):
    if page is None:
        page = 1
    page_data = Userlog.query.filter_by(
        user_id=int(session["user_id"]),
    ).order_by(
        Userlog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('home/loginlog.html', page_data=page_data)


# 添加电影收藏
# 在play/video下面的js中
@home.route('/moviecol/add/', methods=["GET"])
@user_login_req
def moviecol_add():
    # 获取url中的uid和mid参数
    uid = request.args.get("uid", "")
    mid = request.args.get("mid", "")
    # 用查询数量来查找该用户是否收藏过该电影
    moviecol = Moviecol.query.filter_by(
        user_id=int(uid),
        movie_id=int(mid),
    ).count()
    if moviecol == 1:
        data = dict(ok=0)

    # 未收藏则收藏，并存入数据库
    if moviecol == 0:
        moviecol = Moviecol(
            user_id=int(uid),
            movie_id=int(mid)
        )
        db.session.add(moviecol)
        db.session.commit()
        data = dict(ok=1)
    import json
    return json.dumps(data)


# 电影收藏
@home.route('/moviecol/<int:page>/')
@user_login_req
def moviecol(page=None):
    if page is None:
        page = 1
    page_data = Moviecol.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Moviecol.movie_id,
        User.id == session["user_id"]
    ).order_by(
        Moviecol.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('home/moviecol.html', page_data=page_data)


# 电影列表
@home.route('/<int:page>/', methods=["GET"])
def index(page=None):
    tags = Tag.query.all()
    page_data = Movie.query
    # 使用简便方法：加入url参数可以得到值
    # 根据标签筛选
    # 得到参数值并且设置默认值
    tid = request.args.get('tid', 0)
    if int(tid) != 0:
        page_data = page_data.filter_by(tag_id=int(tid))

    # 根据星级筛选
    star = request.args.get("star", 0)
    if int(star) != 0:
        page_data = page_data.filter_by(star=int(star))

    # 根据时间先后筛选
    time = request.args.get("time", 0)
    if int(time) != 0:
        if int(time) == 1:
            page_data = page_data.order_by(
                Movie.addtime.desc()
            )
        else:
            page_data = page_data.order_by(
                Movie.addtime.asc()
            )

    # 根据播放量筛选
    pm = request.args.get("pm", 0)
    if int(pm) != 0:
        if int(pm) == 1:
            page_data = page_data.order_by(
                Movie.playnum.desc()
            )
        else:
            page_data = page_data.order_by(
                Movie.playnum.asc()
            )

    # 根据评论数筛选
    cm = request.args.get("cm", 0)
    if int(cm) != 0:
        if int(cm) == 1:
            page_data = page_data.order_by(
                Movie.commentnum.desc()
            )
        else:
            page_data = page_data.order_by(
                Movie.commentnum.asc()
            )
    # 获取页码
    if page is None:
        page = 1
    page_data = page_data.paginate(page=page, per_page=10)
    # 传入参数字典
    p = dict(
        tid=tid,
        star=star,
        time=time,
        pm=pm,
        cm=cm,
    )
    return render_template('home/index.html', tags=tags, p=p, page_data=page_data)


# 上映预告
@home.route('/animation/')
def animation():
    data = Preview.query.all()
    return render_template('home/animation.html', data=data)


# 搜索
@home.route('/search/<int:page>/')
def search(page=None):
    if page is None:
        page = 1
    key = request.args.get("key", "")
    # 统计搜索后的电影数
    movie_count = Movie.query.filter(
        Movie.title.like('%' + key + '%')
    ).count()
    # 搜索后电影分页显示
    page_data = Movie.query.filter(
        Movie.title.like('%' + key + '%')
    ).order_by(
        Movie.addtime.desc()
    ).paginate(page=page, per_page=10)
    page_data.key = key
    return render_template('home/search.html', key=key, movie_count=movie_count, page_data=page_data)


# 使用下面的弹幕播放器进行替换
"""
# 电影播放
@home.route('/play/<int:id>/<int:page>/', methods=["GET", "POST"])
def play(id=None, page=None):
    movie = Movie.query.join(Tag).filter(
        Tag.id == Movie.tag_id,
        Movie.id == int(id)
    ).first_or_404()
    if page is None:
        page = 1
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == movie.id,
        User.id == Comment.user_id,
    ).order_by(
        Comment.addtime.desc()
    ).paginate(page=page, per_page=10)
    movie.playnum += 1
    form = CommentForm()
    if "user" in session and form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data["content"],
            movie_id=movie.id,
            user_id=session["user_id"]
        )
        db.session.add(comment)
        db.session.commit()
        movie.commentnum += 1
        db.session.add(movie)
        db.session.commit()
        flash("添加评论成功", "ok")
        return redirect(url_for("home.play", id=movie.id, page=1))
    db.session.add(movie)
    db.session.commit()
    return render_template('home/play.html', movie=movie, form=form, page_data=page_data)
"""


# 弹幕播放器
@home.route('/video/<int:id>/<int:page>/', methods=["GET", "POST"])
def video(id=None, page=None):
    movie = Movie.query.join(Tag).filter(
        Tag.id == Movie.tag_id,
        Movie.id == int(id)
    ).first_or_404()
    if page is None:
        page = 1
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == movie.id,
        User.id == Comment.user_id,
    ).order_by(
        Comment.addtime.desc()
    ).paginate(page=page, per_page=10)
    movie.playnum += 1

    # 评论相关
    form = CommentForm()
    # 用户登录并且点击提交
    if "user" in session and form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data["content"],
            movie_id=movie.id,
            user_id=session["user_id"]
        )
        db.session.add(comment)
        db.session.commit()
        movie.commentnum += 1
        db.session.add(movie)
        db.session.commit()
        flash("添加评论成功", "ok")
        return redirect(url_for("home.video", id=movie.id, page=1))
    db.session.add(movie)
    db.session.commit()
    return render_template('home/video.html', movie=movie, form=form, page_data=page_data)


@home.route("/tm/", methods=["GET", "POST"])
def tm():
    """
    弹幕消息处理
    """
    import json
    if request.method == "GET":
        # 获取弹幕消息队列
        id = request.args.get('id')
        # 存放在redis队列中的键值
        key = "movie" + str(id)
        if rd.llen(key):
            msgs = rd.lrange(key, 0, 2999)
            res = {
                "code": 1,
                "danmaku": [json.loads(v) for v in msgs]
            }
        else:
            res = {
                "code": 1,
                "danmaku": []
            }
        resp = json.dumps(res)
    if request.method == "POST":
        # 添加弹幕
        data = json.loads(request.get_data())
        msg = {
            "__v": 0,
            "author": data["author"],
            "time": data["time"],
            "text": data["text"],
            "color": data["color"],
            "type": data['type'],
            "ip": request.remote_addr,
            "_id": datetime.datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex,
            "player": [
                data["player"]
            ]
        }
        res = {
            "code": 1,
            "data": msg
        }
        resp = json.dumps(res)
        # 将添加的弹幕推入redis的队列中
        rd.lpush("movie" + str(data["player"]), json.dumps(msg))
    return Response(resp, mimetype='application/json')
