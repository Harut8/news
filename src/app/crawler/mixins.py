from typing import TYPE_CHECKING

from sqlalchemy import INTEGER, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from src.app.crawler.model import Url

class UrlForeignKeyMixin:
    _url_id_nullable = False
    _url_id_unique = False
    _url_ondelete = None
    _set_on_url_id_index = False

    @declared_attr
    def url_id(self):
        return mapped_column(
            INTEGER,
            ForeignKey("url.id", ondelete=self._url_ondelete),
            nullable=self._url_id_nullable,
            unique=self._url_id_unique,
            index=self._set_on_url_id_index,
        )


class UrlRelationshipMixin:
    _url_back_populates: str = None
    _url_lazy_load = None

    @declared_attr
    def url(self) -> Mapped["Url"]:
        return relationship(
            "Url",
            back_populates=self._url_back_populates,
            lazy=self._url_lazy_load,
        )
