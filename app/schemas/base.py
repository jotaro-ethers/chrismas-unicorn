from typing import Any, Optional
from pydantic import BaseModel


class BaseResponse(BaseModel):
    """Base response schema for all API responses."""
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error response schema for all error responses."""
    success: bool = False
    error: str
    detail: Optional[Any] = None
