def includeme(config):
	config.add_route("health", "/health", request_method="GET")
	config.add_route("upload_image", "/images", request_method="POST")
	config.add_route("list_images", "/images", request_method="GET")
	config.add_route("get_image_metadata", "/images/{image_id}", request_method="GET")
	config.add_route("download_image", "/images/{image_id}/download", request_method="GET")
	config.add_route("delete_image", "/images/{image_id}", request_method="DELETE")