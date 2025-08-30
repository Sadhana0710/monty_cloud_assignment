import base64
import hashlib
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import boto3
from .aws import get_s3_client, get_dynamodb_resource


ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _utc_now_iso() -> str:
	return datetime.now(timezone.utc).strftime(ISO_FORMAT)


def _compute_md5(data: bytes) -> str:
	return hashlib.md5(data).hexdigest()


def _normalize_tags(tags: Optional[List[str]]) -> List[str]:
	if not tags:
		return []
	return [t.strip() for t in tags if t and t.strip()]


def upload_image_with_metadata(settings: dict, *, user_id: str, content: bytes, content_type: Optional[str], title: Optional[str], description: Optional[str], tags: Optional[List[str]]) -> Dict:
	s3 = get_s3_client(settings)
	db = get_dynamodb_resource(settings)
	bucket = settings.get("s3_bucket")
	table_name = settings.get("dynamodb_table")
	table = db.Table(table_name)

	image_id = str(uuid.uuid4())
	s3_key = f"{user_id}/{image_id}"

	# Upload to S3
	put_kwargs = {
		"Bucket": bucket,
		"Key": s3_key,
		"Body": content,
	}
	if content_type:
		put_kwargs["ContentType"] = content_type
	put_resp = s3.put_object(**put_kwargs)
	etag = put_resp.get("ETag", "").strip('"')

	metadata = {
		"image_id": image_id,
		"user_id": user_id,
		"title": title,
		"description": description,
		"tags": _normalize_tags(tags),
		"created_at": _utc_now_iso(),
		"s3_bucket": bucket,
		"s3_key": s3_key,
		"content_type": content_type,
		"size": len(content),
		"checksum_md5": etag or _compute_md5(content),
	}

	# Persist metadata
	table.put_item(Item={k: v for k, v in metadata.items() if v is not None})
	return metadata


def get_image_metadata(settings: dict, image_id: str) -> Optional[Dict]:
	db = get_dynamodb_resource(settings)
	table = db.Table(settings.get("dynamodb_table"))
	resp = table.get_item(Key={"image_id": image_id})
	return resp.get("Item")


def get_image_bytes(settings: dict, image_id: str) -> Optional[Tuple[bytes, Dict]]:
	meta = get_image_metadata(settings, image_id)
	if not meta:
		return None
	s3 = get_s3_client(settings)
	obj = s3.get_object(Bucket=meta["s3_bucket"], Key=meta["s3_key"])
	return obj["Body"].read(), meta


def list_images(settings: dict, *, user_id: Optional[str] = None, tag: Optional[str] = None, limit: int = 50, next_token: Optional[str] = None) -> Tuple[List[Dict], Optional[str]]:
	db = get_dynamodb_resource(settings)
	table = db.Table(settings.get("dynamodb_table"))
	items: List[Dict] = []
	exclusive_start_key = None
	if next_token:
		try:
			exclusive_start_key = json.loads(base64.b64decode(next_token).decode("utf-8"))
		except Exception:
			exclusive_start_key = None

	# Try using GSI if user_id provided
	if user_id:
		try:
			from boto3.dynamodb.conditions import Key
			resp = table.query(
				IndexName="user_id-created_at-index",
				KeyConditionExpression=Key("user_id").eq(user_id),
				Limit=limit,
				ExclusiveStartKey=exclusive_start_key if exclusive_start_key else None,
				ScanIndexForward=False,
			)
			items = resp.get("Items", [])
			if tag:
				items = [i for i in items if tag in i.get("tags", [])]
			next_key = resp.get("LastEvaluatedKey")
			next_token_out = base64.b64encode(json.dumps(next_key).encode("utf-8")).decode("utf-8") if next_key else None
			return items, next_token_out
		except Exception:
			pass

	# Fallback: scan and filter in memory
	scan_kwargs = {
		"Limit": limit,
	}
	if exclusive_start_key:
		scan_kwargs["ExclusiveStartKey"] = exclusive_start_key
	resp = table.scan(**scan_kwargs)
	items = resp.get("Items", [])
	# Filter
	if user_id:
		items = [i for i in items if i.get("user_id") == user_id]
	if tag:
		items = [i for i in items if tag in i.get("tags", [])]
	# Sort newest first by created_at (best-effort)
	items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
	next_key = resp.get("LastEvaluatedKey")
	next_token_out = base64.b64encode(json.dumps(next_key).encode("utf-8")).decode("utf-8") if next_key else None
	return items[:limit], next_token_out


def delete_image(settings: dict, image_id: str) -> bool:
	meta = get_image_metadata(settings, image_id)
	if not meta:
		return False
	s3 = get_s3_client(settings)
	db = get_dynamodb_resource(settings)
	table = db.Table(settings.get("dynamodb_table"))
	s3.delete_object(Bucket=meta["s3_bucket"], Key=meta["s3_key"])
	table.delete_item(Key={"image_id": image_id})
	return True