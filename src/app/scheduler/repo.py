from sqlalchemy import update, select, text, func

from src.app.scheduler.dto import SchedulerStatusType
from src.app.scheduler.model import Scheduler
from src.core.db.pg_base_repo import BaseRepository


class SchedulerRepository(BaseRepository[Scheduler]):

    async def is_url_exists(self, url: str)-> bool:
        _stmt = select(Scheduler).filter(Scheduler.url.ilike(url))
        return True if await self.run_select_stmt_for_one(_stmt) else False

    async def add_schedule(self, schedule: Scheduler) -> Scheduler:
        return await self.insert_one_without_commit(schedule)

    async def fetch_10_pending_schedules_mark_as_processing(self) -> list[dict]:
        # WORKS
        # Step 1: Subquery for Pending Schedules
        _subquery = (
            select(Scheduler.id.label("id"))
            .where(
                Scheduler.scheduled_time <= text("CURRENT_TIMESTAMP AT TIME ZONE 'UTC'"),
                Scheduler.status == SchedulerStatusType.PENDING.str_value,
            )
            .order_by(Scheduler.scheduled_time.asc())
            .limit(10)
            .with_for_update(skip_locked=True)
            .cte("subquery")
        )

        # Step 2: Lock and update schedules to PROCESSING
        _locks = select(_subquery.c.id)
        _stmt = (
            update(Scheduler)
            .where(Scheduler.id.in_(_locks))
            .values(status=SchedulerStatusType.PROCESSING.str_value)
            .returning(
                Scheduler.id,
                Scheduler.task_data,
                Scheduler.retry_count,
                Scheduler.url,
                Scheduler.scheduled_time,
                Scheduler.created_at,
            )
        ).cte("updated_schedules")

        # Step 3: Define a CTE with row numbers partitioned by id
        _numbered_schedules = (
            select(
                _stmt.c.id,
                _stmt.c.task_data,
                _stmt.c.retry_count,
                _stmt.c.url,
                _stmt.c.scheduled_time,
                _stmt.c.created_at,
                func.row_number()
                .over(partition_by=_stmt.c.id, order_by=_stmt.c.created_at.desc())
                .label("row_num"),
            )
        ).cte("numbered_schedules")

        # Step 4: Select only the most recent schedules (where row_num == 1) from the updated records
        _latest_schedules = select(
            _numbered_schedules.c.id,
            _numbered_schedules.c.task_data,
            _numbered_schedules.c.row_num,
            _numbered_schedules.c.retry_count,
            _numbered_schedules.c.url,
        ).filter(_numbered_schedules.c.row_num == 1) # type: ignore

        _schedules = await self.update_stmt_with_commit_returning(_latest_schedules)
        return _schedules

    async def update_scheduler_status_by_id(self, schedule_id, kwargs: dict):
        _stmt = update(Scheduler).where(Scheduler.id == schedule_id).values(**kwargs)
        await self.update_stmt_without_commit(_stmt)

