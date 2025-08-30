from aws_lambda_wsgi import response
from app import main


_app = main({})


def handler(event, context):
	return response(_app, event, context)