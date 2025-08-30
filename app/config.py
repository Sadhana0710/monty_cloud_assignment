import os
from typing import Optional


def get_setting(settings: dict, key: str, default: Optional[str] = None) -> Optional[str]:
	if key in settings and settings[key] is not None:
		return settings[key]
	return os.getenv(key.upper(), default)