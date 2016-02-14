from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.api.datastore_errors import BadArgumentError, BadValueError
from flask import request
from flask_restful import abort

from datetime import datetime

DATE_TIME_FORMAT = '%Y-%m-%d %H:%m:%d'
TIME_FORMAT = '%H:%m:%d'
DEFAULT_FETCH_LIMIT = 10


class ModelBase(ndb.Model):
    @classmethod
    def get_entity_data(cls, model, return_fields):
        output = {}
        for field in return_fields:
            if field == 'id':
                output[field] = model.key.id()
            else:
                value = getattr(model, field)
                if isinstance(value, datetime):
                    output[field] = cls.serialize_date(value)
                else:
                    output[field] = value
        return output

    @classmethod
    def get_entity_fields(cls):
        entity_fields = []
        for field, value in cls.__dict__.iteritems():
            cond1 = not field.startswith('_')
            cond2 = not hasattr(value, '__call__')
            cond3 = not hasattr(value, '__func__')
            if cond1 and cond2 and cond3:
                entity_fields.append(field)
        return entity_fields

    @staticmethod
    def serialize_date(date_time):
        try:
            date = datetime.strftime(date_time, DATE_TIME_FORMAT)
        except ValueError:
            try:
                date = datetime.strftime(date_time, TIME_FORMAT)
            except ValueError:
                raise
        return date

    @staticmethod
    def deserialize_date(date_time):
        try:
            date = datetime.strptime(date_time, DATE_TIME_FORMAT)
        except ValueError:
            try:
                date = datetime.strptime(date_time, TIME_FORMAT)
            except ValueError:
                raise
        return date

    @classmethod
    def query_method(cls, collection_fields=()):
        def decorator(handler):
            def wrapper(self, **kwargs):
                model_fields = ['id']
                model_fields += cls.get_entity_fields()
                unknown_fields = set(collection_fields) - set(model_fields)
                if unknown_fields:
                    raise AttributeError('Unknown attributes {} passed for collection fields of model {}'.format(
                        ','.join(unknown_fields), cls.__name__))

                model_query = cls.query()
                # apply filter(s)
                if kwargs:
                    for field, value in kwargs.iteritems():
                        if field in model_fields:
                            model_property = getattr(cls, field)
                            model_query = model_query.filter(model_property == value)

                handler_output = handler(self, model_query)

                # check for query strings
                default_fetch_limit = DEFAULT_FETCH_LIMIT
                curs = None
                if request.query_string:
                    query_strings = request.query_string.split('&')
                    for query_string in query_strings:
                        key, value = tuple(query_string.split('=', 1))
                        if key == 'limit':
                            default_fetch_limit = int(value)
                            if default_fetch_limit < 1:
                                abort(400, message='query limit cannot be less than 1')
                        elif key == 'cursor':
                            curs = Cursor(urlsafe=value)

                entities, next_curs, more = handler_output.fetch_page(page_size=default_fetch_limit, start_cursor=curs)
                if not entities:
                    abort(404, message='No entities found')

                return_fields = collection_fields or model_fields

                # handle output format
                if curs or (next_curs and more) or len(entities) > 1:
                    output = {'data': [cls.get_entity_data(entity, return_fields) for entity in entities]}
                    if more and next_curs:
                        output.update({'next_curs': next_curs.urlsafe(), 'more': more})
                    else:
                        output['more'] = False
                else:
                    output = cls.get_entity_data(entities[0], return_fields)

                return output
            return wrapper
        return decorator

    @classmethod
    def method(cls, parser=None, response_fields=()):
        def decorator(handler):
            def wrapper(self, **kwargs):
                """
                :param self:
                :param args:
                :param kwargs:
                :return:
                """
                model_fields = ['id']
                model_fields += cls.get_entity_fields()

                # check if response fields are attributes of current model
                unknown_fields = set(response_fields) - set(model_fields)
                if unknown_fields:
                    raise AttributeError('Fields {} does not exist'.format(','.join(unknown_fields)))

                # handle arbitrary field filters passed to server
                entity = None
                if kwargs:
                    for field, value in kwargs.iteritems():
                        if field in model_fields:
                            if field == 'id':
                                entity = cls.get_by_id(value)
                            else:
                                model_property = getattr(cls, field)
                                entity = cls.query(model_property == value).fetch()

                if not entity:
                    entity = cls()
                    entity.from_datastore = False
                else:
                    if type(entity) == list:
                        entity = entity[0]
                    entity.from_datastore = True

                # set new values into entity fields
                args = parser.parse_args() if parser else request.get_json()
                if args:
                    for field, value in args.iteritems():
                        if field in model_fields:
                            field_value_inst = getattr(cls, field)
                            if isinstance(field_value_inst, (ndb.DateTimeProperty, ndb.DateProperty)):
                                value = cls.deserialize_date(args[field])
                            else:
                                value = args[field]
                            # catch ndb errors
                            try:
                                setattr(entity, field, value)
                            except (BadArgumentError, BadValueError), e:
                                abort(400, message=e.message)

                model = handler(self, entity)

                # determine fields to return
                return_fields = response_fields or model_fields
                return cls.get_entity_data(model, return_fields)
            return wrapper
        return decorator