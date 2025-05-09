from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.crawler.mixins import UrlForeignKeyMixin, UrlRelationshipMixin
from src.core.db.pg_base_model import IntPkIdMixin, PgBaseModel, created_at
from src.core.db.pg_mixin import StatusMixin
from src.core.utils.base_value_objects import BaseIntEnum


class CrawlingStatus(BaseIntEnum):
    IDLE = 0  # Not active, ready to start
    RUNNING = 1  # Actively crawling
    PAUSED = 2  # Temporarily halted
    COMPLETED = 3  # Finished successfully
    FAILED = 4  # Stopped due to an error
    QUEUED = 5  # Waiting to start
    BLOCKED = 6  # Restricted by the website
    STOPPING = 7  # In the process of shutting down
    STOPPED = 8  # Stopped by user


class Url(PgBaseModel, IntPkIdMixin, StatusMixin):
    _status_from = CrawlingStatus
    _status_name = "crawling_status"

    url: Mapped[str]
    crawled_at: Mapped[Optional[created_at]]

    index: Mapped[Optional[list["Index"]]] = relationship("Index", back_populates="url", cascade="all, delete-orphan")
    content: Mapped["Content"] = relationship("Content", back_populates="url", cascade="all, delete-orphan")
    meta: Mapped["Meta"] = relationship("Meta", back_populates="url", cascade="all, delete-orphan")
    author: Mapped["Author"] = relationship("Author", back_populates="url", cascade="all, delete-orphan")


class Content(PgBaseModel, IntPkIdMixin, UrlForeignKeyMixin, UrlRelationshipMixin):
    title: Mapped[str]
    content: Mapped[str]


class Index(PgBaseModel, IntPkIdMixin, UrlForeignKeyMixin, UrlRelationshipMixin):
    keyword: Mapped[str]
    frequency: Mapped[int]


class Author(PgBaseModel, IntPkIdMixin, UrlForeignKeyMixin, UrlRelationshipMixin):
    name: Mapped[str]
    web_site: Mapped[str]


class Meta(PgBaseModel, IntPkIdMixin, UrlForeignKeyMixin, UrlRelationshipMixin):
    content_type: Mapped[str]
    http_status: Mapped[int]
    author_id = mapped_column(ForeignKey("author.id"), nullable=True)
    published_at: Mapped[created_at]
