"""
Base types and utilities for models
"""
from typing import Any


class PyObjectId(str):
    """Custom ObjectId type for Pydantic models"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        from bson import ObjectId
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return str(v)
