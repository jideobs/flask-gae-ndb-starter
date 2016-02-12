from model_base import ModelBase
from google.appengine.ext import ndb
from webapp2_extras import security
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from server.config import APP_CONFIG


SECRET = APP_CONFIG['SECRET_KEY']


class Users(ModelBase):
    username = ndb.StringProperty(required=True)
    password = ndb.StringProperty(required=True)
    is_authenticated = ndb.BooleanProperty(default=False)
    date_registered = ndb.DateTimeProperty(auto_now_add=True)
    date_last_updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

    @classmethod
    def get_by_username(cls, username):
        users = cls.query(cls.username == username).fetch()
        return users[0] if users else None

    def hash_password(self):
        self.password = security.generate_password_hash(self.password, length=32)

    def verify_password(self, password):
        return security.check_password_hash(password, self.password)

    def generate_auth_token(self, expiration_date=600):
        serializer = Serializer(SECRET, expires_in=expiration_date)
        return serializer.dumps({'id': self.key.id()})

    @staticmethod
    def verify_auth_token(token):
        serializer = Serializer(SECRET)
        try:
            data = serializer.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        user = Users.get_by_id(data['id'])
        return user
