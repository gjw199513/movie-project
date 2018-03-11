# -*- coding:utf-8 -*-
__author__ = 'gjw'
__date__ = '2018/1/26 15:48'
from . import admin
from flask import render_template, redirect, url_for, flash, session, request, abort
from app.admin.forms import LoginForm, TagForm, MovieForm, PreviewForm, PwdForm, AuthForm, RoleForm, AdminForm
from app.models import Admin, Tag, Movie, Preview, User, Comment, Moviecol, Oplog, Adminlog, Userlog, Auth, Role
from functools import wraps
from app import db, app
from werkzeug.utils import secure_filename
import os
import uuid
import datetime


# 上下文应用处理器
# 封装全局变量，将全局变量展现到模板之中
@admin.context_processor
def tpl_extra():
    date = dict(
        # 该变量为全局变量，在父模板直接引用即可在全部页面实现全局时间
        online_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        # aaa="aaaaaaaa"
    )
    return date


# 登录控制函数
def admin_login_req(f):
    # wraps装饰器可以有效的解决被装饰函数在help命令无法显示函数名和解释文档的问题
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 判断登录时存入的session数据是否存在
        if "admin" not in session:
            # 在url后加入next参数
            return redirect(url_for('admin.login', next=request.url))

        return f(*args, **kwargs)

    return decorated_function


# 权限控制装饰器
def admin_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 将admin表和role表连接
        # 条件是：1.admin中的role_id和role中的id相同
        #        2.admin中的id和session中设置的admin_id值相同
        admin = Admin.query.join(
            Role
        ).filter(
            Role.id == Admin.role_id,
            Admin.id == session["admin_id"]
        ).first()
        # 遗留bug，当auth为空，出现异常
        # 解决办法：为auths不为空的值，在进行限制，
        #         由于auths值为空只有在最初设置超级管理员存在，可以使用超级管理员的is_supper来进行判断
        if admin.is_super != 0:
            # 查找该管理员拥有的权限
            auths = admin.role.auths
            # 将字符串以逗号分隔为列表
            auths = list(map(lambda v: int(v), auths.split(",")))
            # 查询出表中所有的权限
            auth_list = Auth.query.all()
            # 保存匹配的权限
            urls = [v.url for v in auth_list for val in auths if val == v.id]
            # 保存权限的url
            rule = request.url_rule
            # 判断是否具有该权限，没有返回404页面
            if str(rule) not in urls:
                abort(404)

        return f(*args, **kwargs)

    return decorated_function


# 修改文件名称
def change_filename(filename):
    # 将文件名分割
    # splitext:返回路径名和文件扩展名的元组
    fileinfo = os.path.splitext(filename)
    # 将文件重名：上传时间+uuid+扩展名
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + fileinfo[-1]
    return filename


# 调用蓝图
# 控制面板页
@admin.route('/')
@admin_login_req
@admin_auth
def index():
    return render_template('admin/index.html')


# 登录
@admin.route('/login/', methods=["GET", "POST"])
def login():
    form = LoginForm()
    # 提交的数据验证
    # validate_on_submit 会便捷地检查该请求是否是一个 POST 请求以及是否有效
    if form.validate_on_submit():
        # 表单中的数据
        data = form.data
        # 查询name与表单中的account字段匹配的数据
        admin = Admin.query.filter_by(name=data["account"]).first()
        # 判断查询到的用户和表单中的pwd数据是否匹配
        if not admin.check_pwd(data["pwd"]):
            # 闪现错误消息
            flash("密码错误！", 'err')
            # 重定向到登录
            return redirect(url_for('admin.login'))
        # 密码匹配成功
        # 将表单的account数据存入session的admin字段中
        session['admin'] = data['account']
        # 将admin的id保存到session的admin_id字段中
        session['admin_id'] = admin.id
        # 管理员登录日志保存
        adminlog = Adminlog(
            admin_id=admin.id,
            ip=request.remote_addr,
        )
        db.session.add(adminlog)
        db.session.commit()
        return redirect(request.args.get("next") or url_for("admin.index"))
    return render_template('admin/login.html', form=form)


# 退出
@admin.route('/logout/')
@admin_login_req
def logout():
    # 将登录保存的admin和admin_id出栈
    session.pop('admin', None)
    session.pop('admin_id', None)
    return redirect(url_for('admin.login'))


# 修改密码
@admin.route('/pwd/', methods=["GET", "POST"])
@admin_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session['admin']).first()
        from werkzeug.security import generate_password_hash
        # 将新密码进行hash加密
        admin.pwd = generate_password_hash(data['new_pwd'])
        db.session.add(admin)
        db.session.commit()
        flash("修改密码成功,请重新登录!", "ok")
        redirect(url_for("admin.logout"))
    return render_template('admin/pwd.html', form=form)


# 标签管理
# 添加标签
@admin.route('/tag/add/', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tag = Tag.query.filter_by(name=data["name"]).count()
        if tag == 1:
            flash("名称已存在", "err")
            return redirect(url_for("admin.tag_add"))
        # 将表单的name字段存入tag的name中
        tag = Tag(
            name=data["name"]
        )
        db.session.add(tag)
        db.session.commit()
        flash("添加标签成功", "ok")
        # 将登录用户信息、ip地址、原因存入oplog中
        oplog = Oplog(
            admin_id=session['admin_id'],
            ip=request.remote_addr,
            reason="添加标签%s" % data['name']
        )
        db.session.add(oplog)
        db.session.commit()
        redirect(url_for("admin.tag_add"))
    return render_template('admin/tag_add.html', form=form)


# 编辑标签
@admin.route('/tag/edit/<int:id>/', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def tag_edit(id=None):
    form = TagForm()
    # 查找id，不存在返回404
    tag = Tag.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        tag_count = Tag.query.filter_by(name=data["name"]).count()
        # 表单name值和该tag的name不同并且该tag的name存在
        if tag.name != data['name'] and tag_count == 1:
            flash("名称已存在", "err")
            return redirect(url_for("admin.tag_edit", id=id))
        tag.name = data['name']
        db.session.add(tag)
        db.session.commit()
        flash("修改标签成功", "ok")
        redirect(url_for("admin.tag_edit", id=id))
    return render_template('admin/tag_edit.html', form=form, tag=tag)


# 标签列表
# 传入整型页码
@admin.route('/tag/list/<int:page>/', methods=["GET"])
@admin_login_req
@admin_auth
def tag_list(page=None):
    if page is None:
        page = 1
    # sqlalchemy中的分页功能Pagination
    page_data = Tag.query.order_by(
        Tag.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/tag_list.html', page_data=page_data)


# 标签删除
@admin.route('/tag/del/<int:id>/', methods=["GET"])
@admin_login_req
@admin_auth
def tag_del(id=None):
    # first_or_404当未找到返回404
    tag = Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash("删除标签成功", "ok")
    return redirect(url_for("admin.tag_list", page=1))


# 添加电影
@admin.route('/movie/add/', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        # 创建安全的文件名
        file_url = secure_filename(form.url.data.filename)
        file_logo = secure_filename(form.logo.data.filename)
        # 在未存在文件路径时，创建文件
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            # 将文件将文件夹权限改为读写
            os.chmod(app.config["UP_DIR"], "rw")
        # 文件改名
        url = change_filename(file_url)
        logo = change_filename(file_logo)
        # 保存文件
        form.url.data.save(app.config["UP_DIR"] + url)
        form.logo.data.save(app.config["UP_DIR"] + logo)
        # 将输入的信息保存到movie中
        movie = Movie(
            title=data['title'],
            url=url,
            info=data['info'],
            logo=logo,
            star=int(data['star']),
            playnum=0,
            commentnum=0,
            tag_id=int(data['tag_id']),
            area=data['area'],
            release_time=data['release_time'],
            length=data['length']
        )
        db.session.add(movie)
        db.session.commit()
        flash("添加电影成功!", "ok")
        return redirect(url_for("admin.movie_add"))
    return render_template('admin/movie_add.html', form=form)


# 编辑电影
@admin.route('/movie/edit/<int:id>', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def movie_edit(id=None):
    form = MovieForm()
    # url和logo可以不传入数据
    form.url.validators = []
    form.logo.validators = []
    movie = Movie.query.get_or_404(int(id))
    # 对于get请求的数据设置初始值
    if request.method == "GET":
        form.info.data = movie.info
        form.tag_id.data = movie.tag_id
        form.star.data = movie.star
    if form.validate_on_submit():
        data = form.data
        movie_count = Movie.query.filter_by(title=data["title"]).count()
        if movie_count == 1 and movie.title != data["title"]:
            flash("片名已经存在!", "err")
            return redirect(url_for("admin.movie_edit", id=id))

        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config["UP_DIR"], "rw")

        if form.url.data.filename != "":
            # 电影文件
            file_url = secure_filename(form.url.data.filename)
            movie.url = change_filename(file_url)
            form.url.data.save(app.config["UP_DIR"] + movie.url)

        if form.logo.data.filename != "":
            # logo文件
            file_logo = secure_filename(form.logo.data.filename)
            movie.logo = change_filename(file_logo)
            form.logo.data.save(app.config["UP_DIR"] + movie.logo)

        movie.star = data["star"]
        movie.tag_id = data["tag_id"]
        movie.info = data["info"]
        movie.title = data["title"]
        movie.area = data["area"]
        movie.length = data["length"]
        movie.release_time = data["release_time"]
        db.session.add(movie)
        db.session.commit()

        flash("修改电影成功!", "ok")
        return redirect(url_for("admin.movie_edit", id=id))
    return render_template('admin/movie_edit.html', form=form, movie=movie)


# 电影列表
@admin.route('/movie/list/<int:page>', methods=["GET"])
@admin_login_req
@admin_auth
def movie_list(page=None):
    if page is None:
        page = 1
    # sqlalchemy中的分页功能Pagination
    # filter用于多表关联，filter_by用于单表查询
    # 将tag的id和movie的tag_id相等作为关联条件
    page_data = Movie.query.join(Tag).filter(
        Tag.id == Movie.tag_id
    ).order_by(
        Movie.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/movie_list.html', page_data=page_data)


# 删除电影
@admin.route('/movie/del/<int:id>', methods=["GET"])
@admin_login_req
@admin_auth
def movie_del(id=None):
    movie = Movie.query.get_or_404(int(id))
    db.session.delete(movie)
    db.session.commit()
    flash("删除电影成功!", "ok")
    return redirect(url_for("admin.movie_list", page=1))


# 预告管理
# 添加上映预告
@admin.route('/preview/add/', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        # 创建安全的文件名
        file_logo = secure_filename(form.logo.data.filename)
        # 在未存在文件路径时，创建文件
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config["UP_DIR"], "rw")
        # 文件改名
        logo = change_filename(file_logo)
        # 保存文件
        form.logo.data.save(app.config["UP_DIR"] + logo)
        preview = Preview(
            title=data['title'],
            logo=logo
        )
        db.session.add(preview)
        db.session.commit()
        flash("添加预告成功!", "ok")
        return redirect(url_for("admin.preview_add"))
    return render_template('admin/preview_add.html', form=form)


# 上映预告列表
@admin.route('/preview/list/<int:page>', methods=["GET"])
@admin_login_req
@admin_auth
def preview_list(page=None):
    if page is None:
        page = 1
    page_data = Preview.query.order_by(
        Preview.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/preview_list.html', page_data=page_data)


# 删除上映预告
@admin.route('/preview/del/<int:id>', methods=["GET"])
@admin_login_req
@admin_auth
def preview_del(id=None):
    preview = Preview.query.get_or_404(int(id))
    db.session.delete(preview)
    db.session.commit()
    flash("删除预告成功!", "ok")
    return redirect(url_for("admin.preview_list", page=1))


# 编辑上映预告
@admin.route('/preview/edit/<int:id>/', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def preview_edit(id=None):
    form = PreviewForm()
    form.logo.validators = []
    preview = Preview.query.get_or_404(int(id))
    if request.method == "GET":
        form.title.data = preview.title

    if form.validate_on_submit():
        data = form.data

        if form.logo.data.filename != "":
            # logo文件
            file_logo = secure_filename(form.logo.data.filename)
            preview.logo = change_filename(file_logo)
            form.logo.data.save(app.config["UP_DIR"] + preview.logo)

        preview.title = data['title']
        db.session.add(preview)
        db.session.commit()
        flash("修改预告成功!", "ok")
        return redirect(url_for("admin.preview_edit", id=id))
    return render_template('admin/preview_edit.html', form=form, preview=preview)


# 会员管理
# 会员列表
@admin.route('/user/list/<int:page>/')
@admin_login_req
@admin_auth
def user_list(page=None):
    if page is None:
        page = 1
    page_data = User.query.order_by(
        User.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/user_list.html', page_data=page_data)


# 查看会员
@admin.route('/user/view/<int:id>/', methods=["GET"])
@admin_login_req
@admin_auth
def user_view(id=None):
    user = User.query.get_or_404(int(id))
    return render_template('admin/user_view.html', user=user)


# 删除用户
@admin.route('/user/del/<int:id>', methods=["GET"])
@admin_login_req
@admin_auth
def user_del(id=None):
    user = User.query.get_or_404(int(id))
    db.session.delete(user)
    db.session.commit()
    flash("删除会员成功!", "ok")
    return redirect(url_for("admin.user_list", page=1))


# 评论管理
# 评论列表
@admin.route('/comment/list/<int:page>/', methods=["GET"])
@admin_login_req
@admin_auth
def comment_list(page=None):
    if page is None:
        page = 1
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Comment.movie_id,
        User.id == Comment.user_id,
    ).order_by(
        Comment.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/comment_list.html', page_data=page_data)


# 删除评论
@admin.route('/comment/del/<int:id>', methods=["GET"])
@admin_login_req
@admin_auth
def comment_del(id=None):
    comment = Comment.query.get_or_404(int(id))
    db.session.delete(comment)
    db.session.commit()
    flash("删除评论成功!", "ok")
    return redirect(url_for("admin.comment_list", page=1))


# 收藏管理
# 收藏列表
@admin.route('/moviecol/list/<int:page>/', methods=["GET"])
@admin_login_req
@admin_auth
def moviecol_list(page=None):
    if page is None:
        page = 1
    page_data = Moviecol.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Moviecol.movie_id,
        User.id == Moviecol.user_id,
    ).order_by(
        Moviecol.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/moviecol_list.html', page_data=page_data)


# 删除电影收藏
@admin.route('/moviecol/del/<int:id>', methods=["GET"])
@admin_login_req
@admin_auth
def moviecol_del(id=None):
    moviecol = Moviecol.query.get_or_404(int(id))
    db.session.delete(moviecol)
    db.session.commit()
    flash("删除收藏成功!", "ok")
    return redirect(url_for("admin.moviecol_list", page=1))


# 日志管理
# 操作日志列表
@admin.route('/oplog/list/<int:page>', methods=["GET"])
@admin_login_req
@admin_auth
def oplog_list(page=None):
    if page is None:
        page = 1
    page_data = Oplog.query.join(
        Admin
    ).filter(
        Admin.id == Oplog.admin_id,
    ).order_by(
        Oplog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/oplog_list.html', page_data=page_data)


# 管理员日志列表
@admin.route('/adminloginlog/list/<int:page>', methods=["GET"])
@admin_login_req
@admin_auth
def adminloginlog_list(page=None):
    if page is None:
        page = 1
    page_data = Adminlog.query.join(
        Admin
    ).filter(
        Admin.id == Adminlog.admin_id,
    ).order_by(
        Adminlog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/adminloginlog_list.html', page_data=page_data)


# 会员日志列表
@admin.route('/userloginlog/list/<int:page>', methods=["GET"])
@admin_login_req
@admin_auth
def userloginlog_list(page=None):
    if page is None:
        page = 1
    page_data = Userlog.query.join(
        User
    ).filter(
        User.id == Userlog.user_id,
    ).order_by(
        Userlog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/userloginlog_list.html', page_data=page_data)


# 权限管理
# 添加权限
@admin.route('/auth/add/', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def auth_add():
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth = Auth(
            name=data['name'],
            url=data['url']
        )
        db.session.add(auth)
        db.session.commit()
        flash("添加权限成功", "ok")
    return render_template('admin/auth_add.html', form=form)


# 编辑权限
@admin.route('/auth/edit/<int:id>', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def auth_edit(id=None):
    form = AuthForm()
    auth = Auth.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        auth.url = data['url']
        auth.name = data['name']
        db.session.add(auth)
        db.session.commit()
        flash("修改权限成功!", "ok")
        redirect(url_for("admin.auth_edit", id=id))
    return render_template('admin/auth_edit.html', form=form, auth=auth)


# 权限列表
# 传入整型页码
@admin.route('/auth/list/<int:page>', methods=["GET"])
@admin_login_req
@admin_auth
def auth_list(page=None):
    if page is None:
        page = 1
    # sqlalchemy中的分页功能Pagination
    page_data = Auth.query.order_by(
        Auth.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/auth_list.html', page_data=page_data)


# 权限删除
@admin.route('/auth/del/<int:id>', methods=["GET"])
@admin_login_req
@admin_auth
def auth_del(id=None):
    # first_or_404当未找到返回404
    auth = Auth.query.filter_by(id=id).first_or_404()
    db.session.delete(auth)
    db.session.commit()
    flash("删除权限成功", "ok")
    return redirect(url_for("admin.auth_list", page=1))


# 角色管理
# 添加角色
@admin.route('/role/add/', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def role_add():
    form = RoleForm()
    if form.validate_on_submit():
        data = form.data
        role = Role(
            name=data['name'],
            # 将列表转换成以逗号连接的字符串
            # 多选框中的内容连接成字符串存入
            auths=",".join(map(lambda v: str(v), data['auths']))
        )
        db.session.add(role)
        db.session.commit()
        flash("添加角色成功", "ok")
    return render_template('admin/role_add.html', form=form)


# 角色列表
@admin.route('/role/list/<int:page>', methods=["GET"])
@admin_login_req
@admin_auth
def role_list(page=None):
    if page is None:
        page = 1
    # sqlalchemy中的分页功能Pagination
    page_data = Role.query.order_by(
        Role.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/role_list.html', page_data=page_data)


# 删除角色
@admin.route('/role/del/<int:id>', methods=["GET"])
@admin_login_req
@admin_auth
def role_del(id=None):
    # first_or_404当未找到返回404
    role = Role.query.filter_by(id=id).first_or_404()
    db.session.delete(role)
    db.session.commit()
    flash("删除角色成功", "ok")
    return redirect(url_for("admin.role_list", page=1))


# 编辑角色
@admin.route('/role/edit/<int:id>', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def role_edit(id=None):
    form = RoleForm()
    role = Role.query.get_or_404(id)
    if request.method == "GET":
        # 该角色的权限
        auths = role.auths
        # 将字符串转换为列表
        # 将存入的id字符串分隔为列表，并且将其传入form中，RoleForm中的多选框选项与id匹配，进行显示
        form.auths.data = list(map(lambda v: int(v), auths.split(',')))
    if form.validate_on_submit():
        data = form.data
        role.name = data["name"]
        # 将分隔的列表转换为字符串（存入数据库需以字符串的格式进行传递）
        role.auths = ",".join(map(lambda v: str(v), data['auths']))
        db.session.add(role)
        db.session.commit()
        flash("修改角色成功!", "ok")
        redirect(url_for("admin.role_edit", id=id))
    return render_template('admin/role_edit.html', form=form, role=role)


# 管理员管理
# 添加管理员
@admin.route('/admin/add/', methods=["GET", "POST"])
@admin_login_req
@admin_auth
def admin_add():
    form = AdminForm()
    from werkzeug.security import generate_password_hash
    if form.validate_on_submit():
        data = form.data
        admin = Admin(
            name=data['name'],
            # 对密码进行hash加密
            pwd=generate_password_hash(data['pwd']),
            role_id=data['role_id'],
            # 只有初始加入的管理员是超级管理员，以后无法将用户设为超级管理员
            is_super=1
        )
        db.session.add(admin)
        db.session.commit()
        flash("添加权限成功", "ok")
    return render_template('admin/admin_add.html', form=form)


# 管理员列表
@admin.route('/admin/list/<int:page>', methods=["GET"])
@admin_login_req
@admin_auth
def admin_list(page=None):
    if page is None:
        page = 1
    page_data = Admin.query.join(
        Role
    ).filter(
        Role.id == Admin.role_id
    ).order_by(
        Admin.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/admin_list.html', page_data=page_data)
