from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.app.scheduler.dto import SchedulerStatusType
from src.core.db.pg_base_model import PgBaseModel, IntPkIdMixin
from src.core.db.pg_mixin import StatusMixin


class Scheduler(
    PgBaseModel,
    IntPkIdMixin,
    StatusMixin,
):
    _status_name = "schedule_status"
    _status_from = SchedulerStatusType

    task_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scheduled_time: Mapped[datetime] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(nullable=False)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    exception_info: Mapped[str] = mapped_column(nullable=True)
