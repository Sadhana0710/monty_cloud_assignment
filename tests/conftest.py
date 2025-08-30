import os
import sys

# Ensure both project root and its parent are on sys.path
_here = os.path.dirname(__file__)
_project_root = os.path.abspath(os.path.join(_here, ".."))
_outer_root = os.path.abspath(os.path.join(_project_root, ".."))
for _p in (_project_root, _outer_root):
	if _p not in sys.path:
		sys.path.insert(0, _p)

# Ensure tests don't inherit LocalStack endpoint env which breaks moto
for _var in ("AWS_ENDPOINT_URL", "AWS_S3_ENDPOINT", "AWS_S3_ENDPOINT_URL"):
	_val = os.environ.pop(_var, None)
	# If present with CRLF, ensure it's gone
	if _val and _var in os.environ:
		os.environ.pop(_var, None)