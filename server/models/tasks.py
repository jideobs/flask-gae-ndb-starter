from google.appengine.ext import ndb
from model_base import ModelBase
from users import Users


class Tasks(ModelBase):
	owner = ndb.KeyProperty(kind=Users, required=True)
	title = ndb.StringProperty(required=True)
	date_completed = ndb.DateTimeProperty(auto_now_add=True)
