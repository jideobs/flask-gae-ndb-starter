from model_base import ModelBase
from google.appengine.ext import ndb
from webapp2_extras import security


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
