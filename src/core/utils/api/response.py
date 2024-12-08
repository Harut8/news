from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseDto(BaseModel, Generic[T]):
    data: T = Field(description="Response data", default_factory=str)
    message: Optional[str] = Field(description="Response message", examples=["Success"])
    status: str = "ok"
