import enum

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import  mapped_column
from sqlalchemy.dialects.postgresql import ENUM


class StatusMixin:
    _status_nullable = False
    _status_index = True
    _status_from = None
    _status_name = None

    @declared_attr
    def status(self):
        if not issubclass(self._status_from, enum.Enum):
            raise TypeError(f"{self.__name__}._status_from must be an Enum subclass")

        _status = mapped_column(
            ENUM(*[str(x.value) for x in self._status_from], name=self._status_name),
            nullable=self._status_nullable,
            index=self._status_index,
        )
        return _status