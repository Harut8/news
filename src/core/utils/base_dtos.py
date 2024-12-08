from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class CamelBaseModel(BaseModel):
    class Config:  # type: ignore
        alias_generator = to_camel


class BaseDto(BaseModel):
    class Config:  # type: ignore
        from_attributes = True
        populate_by_name = True


class IdBaseDto(BaseDto):
    id: int


class LabelDto(BaseDto, CamelBaseModel):
    label: str


class ByChunkDto(CamelBaseModel, BaseDto):
    current_page: int
    total_pages: int
    total_results: int
