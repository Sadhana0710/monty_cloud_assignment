from typing import List, Optional
from pydantic import BaseModel, Field


class UploadImageRequest(BaseModel):
	user_id: str = Field(..., description="ID of the user uploading the image")
	title: Optional[str] = None
	description: Optional[str] = None
	tags: Optional[List[str]] = None


class ImageMetadata(BaseModel):
	image_id: str
	user_id: str
	title: Optional[str] = None
	description: Optional[str] = None
	tags: List[str] = []
	created_at: str
	s3_bucket: str
	s3_key: str
	content_type: Optional[str] = None
	size: Optional[int] = None
	checksum_md5: Optional[str] = None


class ListImagesResponse(BaseModel):
	items: List[ImageMetadata]
	next_token: Optional[str] = None