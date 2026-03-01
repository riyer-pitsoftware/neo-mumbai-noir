"""
Utility functions for the database layer.
"""
import json
import re


def slugify(name: str) -> str:
    """Turn a name into a filename-safe slug."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def to_json(obj) -> str:
    """Serialize a Python object to a JSON string for storage."""
    if obj is None:
        return "[]"
    if isinstance(obj, str):
        return obj
    return json.dumps(obj)


def from_json(text) -> list:
    """Deserialize a JSON string from storage."""
    if text is None:
        return []
    if isinstance(text, list):
        return text
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return []
