from flask_wtf import Form
from wtforms.ext.appengine.ndb import model_form
from wtforms import StringField, PasswordField, validators

from models.users import Users


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