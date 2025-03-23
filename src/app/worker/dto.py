from src.core.utils.base_dtos import BaseDto, CamelBaseModel
from src.core.utils.base_value_objects import UrlString


class FetchUrlDto(BaseDto, CamelBaseModel):
    url: UrlString


class ByDateFetchUrlDto(BaseDto, CamelBaseModel):
    url: UrlString
    year: str
    month: str
    day: str


class FetchedUrlDto(BaseDto, CamelBaseModel):
    url_id: int
