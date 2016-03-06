from flask_restful import Resource
from server.models.tasks import Tasks


class TaskResource(Resource):
    @Tasks.method(filter_fields=('owner',))
    def post(self):
        pass

    @Tasks.query_method()
    def get(self):
        pass
