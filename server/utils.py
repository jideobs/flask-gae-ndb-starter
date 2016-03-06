import datetime as main_datetime
from google.appengine.ext import ndb

DATE_FORMAT = '%Y-%m-%d'
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TIME_FORMAT = '%H:%M:%S'


def date_to_str(date_time):
	if type(date_time) is main_datetime.date:
		return main_datetime.date.strftime(date_time, DATE_FORMAT)
	elif type(date_time) is main_datetime.time:
		return main_datetime.time.strftime(date_time, TIME_FORMAT)
	else:
		return main_datetime.datetime.strftime(date_time, DATE_TIME_FORMAT)


def date_from_str(prop_type, str_date):
	if isinstance(prop_type, ndb.DateProperty):
		return main_datetime.datetime.strptime(str_date, DATE_FORMAT)
	elif isinstance(prop_type, ndb.DateTimeProperty):
		return main_datetime.datetime.strptime(str_date, DATE_TIME_FORMAT)
	else:
		return main_datetime.datetime.strptime(str_date, TIME_FORMAT)
