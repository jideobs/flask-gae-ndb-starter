from time import sleep

from flask import Flask, request, render_template, url_for, redirect, jsonify
from flask_restful import Api
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from flask_wtf import Form
from wtforms.ext.appengine.ndb import model_form
from wtforms import StringField, PasswordField, validators
from models.users import Users
from config import APP_CONFIG
from webapp2_extras import security

from resources.users import UsersResource

app = Flask(__name__)
app.config.update(APP_CONFIG)
api = Api(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'


@login_manager.user_loader
def user_loader(username):
    return Users.get_by_username(username)


@app.route('/', methods=['GET'])
def default():
    return render_template('index.html')


class LoginForm(Form):
    username = StringField('Username', [validators.DataRequired(message='Please enter your username')])
    password = PasswordField('Password', [validators.DataRequired(message='Please enter your password')])

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        user = Users.get_by_username(self.username.data)
        if not user:
            self.username.errors.append('User does not exist')
            return False

        if not user.verify_password(self.password.data):
            self.password.errors.append('Password incorrect')
            return False
        self.user = user
        return True


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        form.user.is_authenticated = True
        form.user.put()
        login_user(form.user)
        sleep(1)
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', form=form)


@app.route('/api/token', methods=['GET'])
@login_required
def get_auth_token():
    return jsonify(auth_token=current_user.generate_auth_token())

RegisterForm = model_form(Users, Form)


class RegisterFormExt(RegisterForm):
    password = PasswordField('Password', [validators.DataRequired(),
                                          validators.EqualTo('confirm_password', message='Password does not match')])
    confirm_password = PasswordField('Confirm Password', [validators.DataRequired()])

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        user = Users.get_by_username(self.username.data)
        if user:
            self.username.errors.append('Username has already been registered')
            return False
        return True


@app.route('/register', methods=['GET', 'POST'])
def register():
    register_error = None
    form = RegisterFormExt(csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        password = security.generate_password_hash(form.password.data, length=32)
        user = Users(username=form.username.data, password=password, school=form.school.data,
                     graduating_class_name=form.graduating_class_name.data)
        user.put()
        return redirect(url_for('login'), code=302)
    return render_template('register.html', form=form, register_error=register_error)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    current_user.is_authenticated = False
    current_user.put()
    logout_user()
    return redirect(url_for('login'))


api.add_resource(UsersResource, '/users', '/users/<string:username>', '/users/<int:id>')

if __name__ == '__main__':
    app.run(debug=True)
