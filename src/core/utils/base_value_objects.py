import re
from enum import IntEnum
from typing import Annotated

from pydantic import GetJsonSchemaHandler, WrapValidator
from pydantic_core import CoreSchema

from src.core.utils.api.http_exceptions import ValidationError


class BaseIntEnum(IntEnum):
    @classmethod
    def to_label_value(cls) -> list[dict]:
        return [
            {"label": cls.from_enum_mapping(_model.name), "value": _model.value}
            for _model in cls
        ]

    @property
    def str_value(self) -> str:
        return str(self._value_)

    @classmethod
    def from_enum_mapping(cls, _key: str) -> str:
        _key = _key.lower().strip()
        _attr = None
        if isinstance(_key, str):
            _attr = getattr(cls, _key, None)
        if _attr is None:
            return cls._mapping[_key]  # type: ignore
        else:
            return _attr

    @classmethod
    def str_values(cls) -> list[str]:
        return [x.str_value for x in cls]

    @classmethod
    def int_values(cls):
        return [x.value for x in cls]

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: CoreSchema, handler: GetJsonSchemaHandler
    ):
        json_schema = handler(schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema.update(
            {
                "enum": [x.value for x in cls],
                "type": "integer",
            }
        )
        return json_schema


def add_mapping_to_enum(_mapping: dict):
    def _wrapper(_enum):
        def __wrapper():
            _enum._mapping = _mapping
            return _enum

        return __wrapper()

    return _wrapper


url_regex_str = (
    r"^(?:http|ftp)s?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or IP
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$"  # path
)

url_regex = re.compile(url_regex_str, re.IGNORECASE)

def url_regexp_check(value):
    if not url_regex.match(value):
        raise ValidationError("Invalid url format")
    return value


def validate_url_format():
    def wrapper(value, handler):
        return url_regexp_check(value)

    return wrapper


UrlString = Annotated[
    str,
    WrapValidator(validate_url_format()),
]