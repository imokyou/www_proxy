# coding=utf8
from flask import Flask, request, render_template, redirect, g, session
from flask_sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from passlib.hash import pbkdf2_sha256
from datetime import datetime, timedelta
from settings import *
from db import RedisClient
from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length
from utils.validators import Unique, UnExists


app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] =  'mysql://{}:{}@{}/{}?charset=utf8'.format(DB['user'], DB['pwd'], DB['host'], DB['db'])
app.secret_key = 'aljkdfj0921347@#@5d031'
app.permanent_session_lifetime = timedelta(minutes=5)

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'signin'
login_manager.remember_cookie_duration=timedelta(days=1)
login_manager.init_app(app)

_redisdb = RedisClient()
_db = SQLAlchemy(app)   


class User(_db.Model):
    id = _db.Column(_db.Integer, primary_key=True, autoincrement=True)
    email = _db.Column(_db.String(128))
    password = _db.Column(_db.String(128))
    contact = _db.Column(_db.String(128))
    created_at = _db.Column(_db.DateTime, default=datetime.utcnow)

    def hash_password(self, password):
        self.password = pbkdf2_sha256.hash(password)

    def verify_password(self, password):
        return pbkdf2_sha256.verify(password, self.password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.email)

class SignupForm(Form):
    email = StringField(u'邮箱', 
                        validators=[DataRequired(message=u"邮箱不能为空"), Email(message=u"不合法的邮箱"), Unique(User, User.email, message=u'该邮箱已被用于注册')],
                        render_kw={'class': 'form-control'})
    password = PasswordField(u'密码', validators=[DataRequired(message=u"密码不能为空"), Length(6, 24, message=u"密码长度为6-24个字符")], render_kw={'class': 'form-control'})
    contact = StringField(u'联系QQ', render_kw={'class': 'form-control'})


class SigninForm(Form):
    email = StringField(u'邮箱', 
                        validators=[DataRequired(message=u"邮箱不能为空"), Email(message=u"不合法的邮箱"), UnExists(User, User.email, message=u'该邮箱不存在')],
                        render_kw={'class': 'form-control'})
    password = PasswordField(u'密码', validators=[DataRequired(message=u"密码不能为空"), Length(6, 24, message=u"密码长度为6-24个字符")], render_kw={'class': 'form-control'})


@login_manager.user_loader
def load_user(user_id):
    user = _db.session.query(User).filter(User.id == user_id).first()
    return user

@app.before_request
def before_request():
    g.user = current_user

@app.route("/proxy/", methods=["GET"])
def get_proxy():
    key = request.args.get('key', '')
    if key != SIGNKEY:
        return ''
    proxy = _redisdb.rand_proxy()
    return proxy

@app.route("/proxy/count/", methods=["GET"])
def count_proxy():
    proxy_len = _redisdb.proxy_len
    return str(proxy_len)

@app.route("/", methods=["GET"])
def home():
    user = g.user
    proxies_source = _redisdb.get_proxies_cache()
    if not proxies_source:
        proxies_s = _redisdb.get_proxies_source(20)
        proxies_ava = _redisdb.get_proxies(10)
        proxies_source = proxies_s + proxies_ava
        _redisdb.set_proxies_cache(proxies_source)
    if not user.get_id():
        proxies_source = proxies_source[0:15]

    proxies = []
    for p in proxies_source:
        proto = p.split('://')[0]
        ip, port = p.split('://')[1].split(':')
        proxies.append({
            'ip': ip,
            'port': port,
            'proto': proto.upper()
        })
    return render_template('index.html', proxies=proxies, user=user)


@app.route("/signup/", methods=["GET", "POST"])
def signup():
    if g.user.get_id():
        return redirect('/')
    form = SignupForm()
    if form.validate_on_submit():
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        contact = request.form.get('password', '')
        user = User(
            email=email,
            password=password,
            contact=contact
        )
        user.hash_password(password)
        _db.session.add(user)
        _db.session.commit()
        return redirect('/signin/')
    return render_template('signup.html', form=form)

@app.route("/signin/", methods=["GET", "POST"])
def signin():
    if g.user.get_id():
        return redirect('/')
    form = SigninForm()
    if form.validate_on_submit():
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        user = _db.session.query(User).filter(User.email == email).first()
        if user.verify_password(password):
            session.permanent = True
            login_user(user)
            return redirect('/')
    return render_template('signin.html', form=form)

@app.route('/signout/')
@login_required
def signout():
    logout_user()
    return redirect('/')



def main():
    app.run(debug=True)

if __name__ == '__main__':
    main()