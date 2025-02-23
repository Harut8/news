from datetime import datetime

from pydantic import BaseModel, field_validator

from src.core.utils.base_value_objects import BaseIntEnum, UrlString


class SchedulerStatusType(BaseIntEnum):
    PENDING = 1
    COMPLETED = 2
    FAILED = 3
    PROCESSING = 4



class TaskDataDto(BaseModel):
    queue: str
    exchange: str
    routing_key: str


class SchedulerDto(BaseModel):
    task_data: TaskDataDto
    status: SchedulerStatusType = SchedulerStatusType.PENDING
    url: UrlString
    scheduled_time: datetime

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        data["status"] = SchedulerStatusType(data["status"]).str_value
        return data

    @field_validator("scheduled_time", mode="before")
    @classmethod
    def validate_scheduled_time(cls, v: str | datetime) -> datetime:
        if isinstance(v, str):
            _utc = datetime.fromisoformat(v)
        else:
            _utc = v
        return _utc.replace(tzinfo=None)
