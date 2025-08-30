import base64
import io
import json

import boto3
import pytest
from moto import mock_aws
from webtest import TestApp

from app import main


@pytest.fixture()
def app_settings():
	return {
		"aws_region": "us-east-1",
		"s3_bucket": "images-bucket",
		"dynamodb_table": "images",
	}


def _bootstrap_moto_resources(settings):
	s3 = boto3.client("s3", region_name=settings["aws_region"])
	s3.create_bucket(Bucket=settings["s3_bucket"])
	db = boto3.client("dynamodb", region_name=settings["aws_region"])
	db.create_table(
		TableName=settings["dynamodb_table"],
		AttributeDefinitions=[
			{"AttributeName": "image_id", "AttributeType": "S"},
			{"AttributeName": "user_id", "AttributeType": "S"},
			{"AttributeName": "created_at", "AttributeType": "S"},
		],
		KeySchema=[{"AttributeName": "image_id", "KeyType": "HASH"}],
		BillingMode="PAY_PER_REQUEST",
		GlobalSecondaryIndexes=[
			{
				"IndexName": "user_id-created_at-index",
				"KeySchema": [
					{"AttributeName": "user_id", "KeyType": "HASH"},
					{"AttributeName": "created_at", "KeyType": "RANGE"},
				],
				"Projection": {"ProjectionType": "ALL"},
			}
		],
	)


@mock_aws
def test_upload_and_get_metadata_json(app_settings):
	_bootstrap_moto_resources(app_settings)
	wsgi = main(**app_settings)
	client = TestApp(wsgi)
	content = b"hello world"
	payload = {
		"file_base64": base64.b64encode(content).decode("utf-8"),
		"content_type": "text/plain",
		"user_id": "user-1",
		"title": "greet",
		"tags": ["note"],
	}
	res = client.post_json("/images", payload)
	assert res.status_int == 200
	image_id = res.json["image_id"]

	# Get metadata
	res2 = client.get(f"/images/{image_id}")
	assert res2.status_int == 200
	assert res2.json["user_id"] == "user-1"
	assert res2.json["title"] == "greet"


@mock_aws
def test_upload_multipart_and_download(app_settings):
	_bootstrap_moto_resources(app_settings)
	wsgi = main(**app_settings)
	client = TestApp(wsgi)
	content = b"\xff\xd8\xff\xe0"  # pretend jpeg magic
	res = client.post(
		"/images",
		upload_files=[("file", "test.jpg", content)],
		params={"user_id": "u2", "title": "t"},
	)
	assert res.status_int == 200
	image_id = res.json["image_id"]

	res2 = client.get(f"/images/{image_id}/download")
	assert res2.status_int == 200
	assert res2.body == content
	assert res2.content_type.startswith("application/") or res2.content_type.startswith("image/")


@mock_aws
def test_list_filters_and_pagination(app_settings):
	_bootstrap_moto_resources(app_settings)
	wsgi = main(**app_settings)
	client = TestApp(wsgi)
	# seed 3 images
	for i in range(3):
		payload = {
			"file_base64": base64.b64encode(f"{i}".encode()).decode(),
			"user_id": "user-x" if i < 2 else "user-y",
			"tags": ["cat"] if i != 1 else ["dog"],
		}
		client.post_json("/images", payload)

	res = client.get("/images", params={"user_id": "user-x", "tag": "cat", "limit": "1"})
	assert res.status_int == 200
	assert len(res.json["items"]) == 1
	next_token = res.json.get("next_token")
	res2 = client.get("/images", params={"user_id": "user-x", "tag": "cat", "limit": "2", "next_token": next_token})
	assert res2.status_int == 200
	# Remaining items could be 0 or 1 depending on order; ensure all are cat and user-x
	for item in res2.json["items"]:
		assert item["user_id"] == "user-x"
		assert "cat" in item.get("tags", [])


@mock_aws
def test_delete_image(app_settings):
	_bootstrap_moto_resources(app_settings)
	wsgi = main(**app_settings)
	client = TestApp(wsgi)
	payload = {
		"file_base64": base64.b64encode(b"bye").decode(),
		"user_id": "user-del",
	}
	res = client.post_json("/images", payload)
	image_id = res.json["image_id"]

	res2 = client.delete(f"/images/{image_id}")
	assert res2.status_int == 200

	res3 = client.get(f"/images/{image_id}", expect_errors=True)
	assert res3.status_int == 404