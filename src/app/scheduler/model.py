from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.app.scheduler.dto import SchedulerStatusType
from src.core.db.pg_base_model import IntPkIdMixin, PgBaseModel
from src.core.db.pg_mixin import StatusMixin


class ScheduledUrl(
    PgBaseModel,
    IntPkIdMixin,
    StatusMixin,
):
    _status_name = "scheduled_url_status"
    _status_from = SchedulerStatusType

    task_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scheduled_time: Mapped[datetime] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(nullable=False)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    exception_info: Mapped[str] = mapped_column(nullable=True)


class PredefinedUrl(PgBaseModel, IntPkIdMixin, StatusMixin):
    _status_name = "predefined_url_status"
    _status_from = SchedulerStatusType

    url: Mapped[str] = mapped_column(nullable=False)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    exception_info: Mapped[str] = mapped_column(nullable=True)
    task_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
