import datetime
import re
import uuid
from enum import StrEnum
from typing import TypeVar

from pydantic.alias_generators import to_camel
from sqlalchemy import UUID, DateTime, String, func
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from typing_extensions import Annotated

_FACTORY_CLS = TypeVar("_FACTORY_CLS", bound="PgBaseModel")


def to_snake_case(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("__([A-Z])", r"_\1", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


int_col = mapped_column(BIGINT)
uuid_col = mapped_column(UUID(as_uuid=True))

int_pk_col = mapped_column(BIGINT, primary_key=True, autoincrement=True)
uuid_pk_col = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

# Annotated types for IDs (without auto-increment or default)
int_annotated = Annotated[int, int_col]
uuid_annotated = Annotated[uuid.UUID, uuid_col]

# Annotated types for primary key IDs (with auto-increment or default)
int_pk_annotated = Annotated[int, int_pk_col]
uuid_pk_annotated = Annotated[uuid.UUID, uuid_pk_col]

created_at = Annotated[
    datetime.datetime,
    mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now()),
]
updated_at = Annotated[
    datetime.datetime,
    mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    ),
]

str_500 = Annotated[
    str,
    mapped_column(
        String(500),
        nullable=False,
    ),
]


class IdType(StrEnum):
    UUID_PK = "uuid_pk"
    INT_PK = "int_pk"


class IntPkIdMixin:
    id: Mapped[int_pk_annotated]


class UUIDPkIdMixin:
    id: Mapped[uuid_pk_annotated]


class PgBaseModel(DeclarativeBase):
    __abstract__ = True
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    @declared_attr.directive
    def __tablename__(cls):
        return to_snake_case(cls.__name__)

    @classmethod
    def factory(cls: type, **kwargs) -> _FACTORY_CLS:
        return cls(**kwargs)

    def to_dict(self, camel_case: bool = False, **kwargs):
        if camel_case:
            return {
                to_camel(c.name): getattr(self, c.name) for c in self.__table__.columns
            } | kwargs  # type: ignore
        return {c.name: getattr(self, c.name) for c in self.__table__.columns} | kwargs  # type: ignore

    def merge_tables_output(self, output):
        for c in output.__table__.columns:
            setattr(self, c.name, getattr(output, c.name))
        return self

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        return self

    @classmethod
    def from_dict(cls, data):
        _filtered_data = {
            k: v for k, v in data.items() if v is not None and hasattr(cls, k)
        }
        return cls(**_filtered_data)

