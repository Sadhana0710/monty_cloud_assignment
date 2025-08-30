import boto3
from typing import Optional


def _client(service_name: str, region_name: Optional[str], endpoint_url: Optional[str]):
	params = {}
	if region_name:
		params["region_name"] = region_name
	if endpoint_url:
		params["endpoint_url"] = endpoint_url
	return boto3.client(service_name, **params)


def _resource(service_name: str, region_name: Optional[str], endpoint_url: Optional[str]):
	params = {}
	if region_name:
		params["region_name"] = region_name
	if endpoint_url:
		params["endpoint_url"] = endpoint_url
	return boto3.resource(service_name, **params)


def get_s3_client(settings: dict):
	return _client(
		"s3",
		settings.get("aws_region"),
		settings.get("aws_endpoint_url"),
	)


def get_dynamodb_client(settings: dict):
	return _client(
		"dynamodb",
		settings.get("aws_region"),
		settings.get("aws_endpoint_url"),
	)


def get_dynamodb_resource(settings: dict):
	return _resource(
		"dynamodb",
		settings.get("aws_region"),
		settings.get("aws_endpoint_url"),
	)