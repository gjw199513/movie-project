# -*- coding:utf-8 -*-
__author__ = 'gjw'
__date__ = '2018/1/26 15:48'

from flask_wtf import FlaskForm
from wtforms.fields import StringField, PasswordField, SubmitField, FileField, TextAreaField, SelectField, \
    SelectMultipleField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Email, Regexp
from app.models import User


# 注册表单
class RegistForm(FlaskForm):
    name = StringField(
        label='昵称',
        validators=[
            DataRequired('请输入昵称！')
        ],
        # 描述
        description='昵称',
        # 附加选项
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入昵称！",
        }
    )
    email = StringField(
        label='邮箱',
        validators=[
            DataRequired('请输入邮箱！'),
            # 邮箱格式验证
            Email("邮箱格式不正确")
        ],
        # 描述
        description='邮箱',
        # 附加选项
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入邮箱！",
        }
    )
    phone = StringField(
        label='手机',
        validators=[
            DataRequired('请输入手机！'),
            # 使用正则验证手机号码
            Regexp('1[3458]\d{9}', message="手机号码不正确!")
        ],
        # 描述
        description='手机',
        # 附加选项
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入手机！",
        }
    )
    pwd = PasswordField(
        label="密码",
        validators=[
            DataRequired('请输入密码！')
        ],
        description="密码",
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入密码！",
        }
    )
    repwd = PasswordField(
        label="确认密码",
        validators=[
            DataRequired('请输入确认密码！'),
            EqualTo('pwd', message="两次密码不一致！")
        ],
        description="确认密码",
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入确认密码！",
        }
    )
    submit = SubmitField(
        "注册",
        render_kw={
            "class": "btn btn-lg btn-success btn-block",
        }
    )

    # 验证昵称是否存在
    def validate_name(self, filed):
        name = filed.data
        # 查找是否存在该昵称
        user = User.query.filter_by(name=name).count()
        if user == 1:
            raise ValidationError("昵称已经存在")

    # 验证邮箱是否存在
    def validate_email(self, filed):
        email = filed.data
        user = User.query.filter_by(email=email).count()
        if user == 1:
            raise ValidationError("邮箱已经存在")

    # 验证电话号码是否存在
    def validate_phone(self, filed):
        phone = filed.data
        user = User.query.filter_by(phone=phone).count()
        if user == 1:
            raise ValidationError("手机号码已经存在")


class LoginForm(FlaskForm):
    name = StringField(
        label='账号',
        validators=[
            DataRequired('请输入账号！')
        ],
        # 描述
        description='账号',
        # 附加选项
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入账号！",
        }
    )
    pwd = PasswordField(
        label="密码",
        validators=[
            DataRequired('请输入密码！')
        ],
        description="密码",
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入密码！",
        }
    )
    submit = SubmitField(
        "登录",
        render_kw={
            "class": "btn btn-lg btn-primary btn-block",
        }
    )


# 会员资料表单
class UserdetailForm(FlaskForm):
    name = StringField(
        label='账号',
        validators=[
            DataRequired('请输入账号！')
        ],
        # 描述
        description='账号',
        # 附加选项
        render_kw={
            "class": "form-control",
            "placeholder": "请输入账号！",
        }
    )
    email = StringField(
        label='邮箱',
        validators=[
            DataRequired('请输入邮箱！'),
            Email("邮箱格式不正确")
        ],
        # 描述
        description='邮箱',
        # 附加选项
        render_kw={
            "class": "form-control",
            "placeholder": "请输入邮箱！",
        }
    )
    phone = StringField(
        label='手机',
        validators=[
            DataRequired('请输入手机！'),
            Regexp('1[3458]\d{9}', message="手机号码不正确!")
        ],
        # 描述
        description='手机',
        # 附加选项
        render_kw={
            "class": "form-control",
            "placeholder": "请输入手机！",
        }
    )
    face = FileField(
        label="头像",
        validators=[
            DataRequired("请上传头像！")
        ],
        description="头像",
    )
    info = TextAreaField(
        label="简介",
        validators=[
            DataRequired("请输入简介！")
        ],
        description="简介",
        render_kw={
            "class": "form-control",
            "rows": 10,
        }
    )
    submit = SubmitField(
        '保存修改',
        render_kw={
            "class": "btn btn-success",
        }
    )


# 密码表单
class PwdForm(FlaskForm):
    old_pwd = PasswordField(
        label="旧密码",
        validators=[
            DataRequired('请输入旧密码！')
        ],
        description="旧密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入旧密码！",
        }
    )
    new_pwd = PasswordField(
        label="新密码",
        validators=[
            DataRequired('请输入新密码！')
        ],
        description="新密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入密码！",
        }
    )
    submit = SubmitField(
        "修改密码",
        render_kw={
            "class": "btn btn-success",
        }
    )


# 评论表单
class CommentForm(FlaskForm):
    content = TextAreaField(
        label="内容",
        validators=[
            DataRequired('请输入内容！')
        ],
        description="内容",
        render_kw={
            "id": "input_content",
        }
    )
    submit = SubmitField(
        "添加评论",
        render_kw={
            "class": "btn btn-success",
            "id": "btn-sub"
        }
    )
