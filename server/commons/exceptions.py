class RequiredInputError(Exception):
	def __init__(self, message):
		self.message = message or 'Required inputs not found'
		self.error_code = 400


class AuthenticationError(Exception):
	def __init__(self):
		self.message = 'Invalid user'
		self.error_code = 401
