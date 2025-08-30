import json
import base64
from typing import Any, Dict, List, Optional

from pyramid.response import Response
from pyramid.view import view_config

from .schemas import ImageMetadata, ListImagesResponse, UploadImageRequest
from .storage import (
	delete_image,
	get_image_bytes,
	get_image_metadata,
	list_images,
	upload_image_with_metadata,
)


def _json_response(data: Dict[str, Any], status: int = 200) -> Response:
	return Response(
		body=json.dumps(data).encode("utf-8"),
		status=status,
		content_type="application/json",
	)


@view_config(route_name="health", request_method="GET")
def health(_):
	return _json_response({"status": "ok"})


@view_config(route_name="upload_image", request_method="POST")
def upload_image_view(request):
	ct = request.content_type or ""
	if ct.startswith("multipart/form-data"):
		post = request.POST
		file_field = post.get("file")
		# Avoid truthiness on FieldStorage which raises TypeError
		if file_field is None or getattr(file_field, "file", None) is None:
			return _json_response({"error": "file is required"}, status=400)
		content = file_field.file.read()
		content_type = getattr(file_field, "type", None) or getattr(file_field, "content_type", None)
		user_id = post.get("user_id")
		title = post.get("title")
		description = post.get("description")
		tags_field = post.get("tags")
		tags = [t.strip() for t in tags_field.split(",")] if isinstance(tags_field, str) and tags_field else None
	else:
		try:
			payload = request.json_body
		except Exception:
			return _json_response({"error": "Invalid JSON body"}, status=400)
		file_b64 = payload.get("file_base64")
		if not file_b64:
			return _json_response({"error": "file_base64 is required"}, status=400)
		content = base64.b64decode(file_b64)
		content_type = payload.get("content_type")
		user_id = payload.get("user_id")
		title = payload.get("title")
		description = payload.get("description")
		tags = payload.get("tags")

	if not user_id:
		return _json_response({"error": "user_id is required"}, status=400)

	meta = upload_image_with_metadata(
		request.registry.settings,
		user_id=user_id,
		content=content,
		content_type=content_type,
		title=title,
		description=description,
		tags=tags,
	)
	return _json_response(ImageMetadata(**meta).model_dump())


@view_config(route_name="list_images", request_method="GET")
def list_images_view(request):
	user_id = request.params.get("user_id")
	tag = request.params.get("tag")
	limit_str = request.params.get("limit")
	next_token = request.params.get("next_token")
	try:
		limit = int(limit_str) if limit_str else 50
	except ValueError:
		return _json_response({"error": "limit must be an integer"}, status=400)
	items, token = list_images(request.registry.settings, user_id=user_id, tag=tag, limit=limit, next_token=next_token)
	resp = ListImagesResponse(items=[ImageMetadata(**i) for i in items], next_token=token)
	return _json_response(resp.model_dump())


@view_config(route_name="get_image_metadata", request_method="GET")
def get_image_metadata_view(request):
	image_id = request.matchdict.get("image_id")
	item = get_image_metadata(request.registry.settings, image_id)
	if not item:
		return _json_response({"error": "not found"}, status=404)
	return _json_response(ImageMetadata(**item).model_dump())


@view_config(route_name="download_image", request_method="GET")
def download_image_view(request):
	image_id = request.matchdict.get("image_id")
	res = get_image_bytes(request.registry.settings, image_id)
	if not res:
		return _json_response({"error": "not found"}, status=404)
	data, meta = res
	r = Response(body=data, content_type=meta.get("content_type") or "application/octet-stream")
	r.content_disposition = f"attachment; filename=\"{meta.get('title') or image_id}\""
	return r


@view_config(route_name="delete_image", request_method="DELETE")
def delete_image_view(request):
	image_id = request.matchdict.get("image_id")
	ok = delete_image(request.registry.settings, image_id)
	if not ok:
		return _json_response({"error": "not found"}, status=404)
	return _json_response({"deleted": True})