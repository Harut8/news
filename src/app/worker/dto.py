from src.core.utils.base_dtos import BaseDto, CamelBaseModel
from src.core.utils.base_value_objects import UrlString


class FetchUrlDto(BaseDto, CamelBaseModel):
    url: UrlString
