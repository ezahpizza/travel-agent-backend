import enum
from typing import Any
from bson import ObjectId
import logging
import traceback

# Utility to convert Enum to str
def enum_to_str(val: Any) -> Any:
    if isinstance(val, enum.Enum):
        return val.value
    return val

# Utility to convert Pydantic model to dict
def pydantic_to_dict(val: Any) -> Any:
    if hasattr(val, 'dict'):
        return val.dict()
    return val

# Utility to convert ObjectId to str
def objectid_to_str(val: Any) -> Any:
    if isinstance(val, ObjectId):
        return str(val)
    return val

# Recursively serialize dicts for MongoDB
def serialize_for_mongo(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: serialize_for_mongo(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_for_mongo(i) for i in data]
    elif isinstance(data, enum.Enum):
        return data.value
    elif hasattr(data, 'dict'):
        return serialize_for_mongo(data.dict())
    elif isinstance(data, ObjectId):
        return str(data)
    return data

# Enhanced error logging
def log_exception(logger, msg: str, exc: Exception):
    logger.error(f"{msg}: {str(exc)}\n{traceback.format_exc()}")
