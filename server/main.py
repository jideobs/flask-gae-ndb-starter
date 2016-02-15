from time import sleep
from flask import Flask, request, render_template, url_for, redirect
from flask_restful import Api
from flask_login import LoginManager, login_user, login_required, current_user, logout_user

from models.users import Users
from config import APP_CONFIG
from webapp2_extras import security
from resources.users import UsersResource
from forms import LoginForm
from forms import RegisterFormExt

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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        form.user.is_authenticated = True
        form.user.put()
        login_user(form.user, remember=form.remember_me.data)
        sleep(1)
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    register_error = None
    form = RegisterFormExt(csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        password = security.generate_password_hash(form.password.data, length=32)
        user = Users(username=form.username.data, password=password)
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
