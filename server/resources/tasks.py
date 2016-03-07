from flask_restful import Resource
from server.models.tasks import Tasks


class TasksResource(Resource):
	@Tasks.method(transform_response=True, user_required=True)
	def post(self, task):
		task.put()
		return task

	@Tasks.query_method(transform_response=True)
	def get(self, tasks):
		return tasks
