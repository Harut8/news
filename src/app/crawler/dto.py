import datetime

from src.core.utils.base_dtos import BaseDto, CamelBaseModel


class ContentDto(BaseDto, CamelBaseModel):
    title: str
    content: str


class MetaDto(BaseDto, CamelBaseModel):
    content_type: str
    http_status: int
    author_id: int
    published_at: datetime.datetime


class AuthorDto(BaseDto, CamelBaseModel):
    web_site: str
    name: str


class IndexDto(BaseDto, CamelBaseModel):
    keyword: str
    frequency: int
