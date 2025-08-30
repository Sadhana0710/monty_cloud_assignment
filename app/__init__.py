import os
from pyramid.config import Configurator


def main(global_config=None, **settings):
	"""Pyramid WSGI app factory."""
	settings = settings or {}
	# Allow environment variables to override settings
	settings.setdefault("aws_region", os.getenv("AWS_REGION", "us-east-1"))
	settings.setdefault("aws_endpoint_url", os.getenv("AWS_ENDPOINT_URL"))
	settings.setdefault("s3_bucket", os.getenv("S3_BUCKET", "images-bucket"))
	settings.setdefault("dynamodb_table", os.getenv("DYNAMODB_TABLE", "images"))

	config = Configurator(settings=settings)
	config.include(".routes")
	config.scan("app.views")
	return config.make_wsgi_app()