from flask_restful import Resource
from flask_restful import abort
from server.models.users import Users


class UsersResource(Resource):
	@Users.method()
	def post(self, user):
		user.put()
		return user

	@Users.method()
	def put(self, user):
		if not user.from_datastore:
			abort(400, message='User does not exist')
		user.put()
		return user

	@Users.method()
	def delete(self, user):
		if not user.from_datastore:
			abort(400, message='User does not exist')
		user.key.delete()
		return user

	@Users.query_method()
	def get(self, user):
		return user
