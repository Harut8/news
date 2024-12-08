from typing import Generic, Iterable, Sequence, TypeVar, cast

from sqlalchemy import Row, Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.pg_base_model import PgBaseModel

T = TypeVar("T", bound=PgBaseModel)


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession):
        self._session: AsyncSession = session

    @property
    def name(self):
        return self.__class__.__name__

    @classmethod
    def factory(cls: type, **kwargs):
        return cls(**kwargs)

    @property
    def session(self) -> AsyncSession:
        return self._session

    @session.setter
    def session(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def as_dict(row: Row):
        return row._asdict() if row else {}

    @staticmethod
    async def _insert_instance(instance: T, db: AsyncSession) -> T:
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        return instance

    async def run_select_stmt_for_one(self, stmt) -> T:
        result = await self.session.execute(stmt)
        return result.scalar()

    async def run_select_stmt_for_all(self, stmt) -> list[T]:
        result = await self.session.execute(stmt)
        return cast(list[T], result.scalars().all())

    async def run_select_stmt_for_all_with_unique_dict(self, stmt) -> list[dict]:
        _result = await self.session.execute(stmt)
        _rows = _result.unique().all()
        _result_dict = [BaseRepository.as_dict(_row) for _row in _rows]
        return _result_dict

    async def run_select_stmt_for_all_with_dict(self, stmt) -> list[dict]:
        _result = await self.session.execute(stmt)
        _rows = _result.all()
        _result_dict = [BaseRepository.as_dict(_row) for _row in _rows]
        return _result_dict

    async def run_select_stmt_for_all_with_row(self, stmt) -> list[Row]:
        _result = await self.session.execute(stmt)
        _rows = _result.all()
        return cast(list[Row], _rows)

    async def run_select_stmt_for_all_with_unique_entity(self, stmt) -> list[T]:
        _result = await self.session.execute(stmt)
        _rows = _result.unique().all()
        return [_row[0] for _row in _rows]

    async def run_select_stmt_for_one_with_unique_entity(self, stmt) -> T:
        _result = await self.session.execute(stmt)
        _rows = _result.unique().first()
        return _rows[0] if _rows else None

    async def run_select_stmt_for_one_with_dict(self, stmt) -> dict:
        _result = await self.session.execute(stmt)
        _rows = _result.first()
        return BaseRepository.as_dict(_rows)

    async def paginated_select_entity(
        self, stmt: Select, page_size: int, page_number: int
    ) -> Sequence[T]:
        _offset = (page_number - 1) * page_size
        _limit = page_size
        _stmt = stmt.limit(_limit).offset(_offset)
        return await self.run_select_stmt_for_all(_stmt)

    async def paginated_select_with_unique_entity(
        self, stmt: Select, page_size: int, page_number: int
    ) -> list[T]:
        _offset = (page_number - 1) * page_size
        _limit = page_size
        _stmt = stmt.limit(_limit).offset(_offset)
        _res = await self.run_select_stmt_for_all_with_unique_entity(_stmt)
        return cast(list[T], _res)

    async def insert_one_with_commit(self, instance: T) -> T:
        return await BaseRepository._insert_instance(instance, self._session)

    async def insert_one_without_commit(self, instance: T) -> T:
        self.session.add(instance)
        return instance

    async def insert_one_updated_with_commit(self, instance: T) -> T:
        self.session.add(instance)
        await self.session.commit()
        return instance

    async def insert_many_orm_with_commit(
        self, instances: Iterable[T] | Sequence[T]
    ) -> list[T]:
        self.session.add_all(instances)
        await self.session.commit()
        await self.session.flush(instances)
        return cast(list, instances)

    async def bulk_insert_orm_without_commit(self, instances: Iterable[T]) -> list[T]:
        await self.session.run_sync(lambda ses: ses.bulk_save_objects(instances))
        return cast(list, instances)

    async def bulk_insert_core_without_commit(
        self, instances: Iterable[dict], mapping
    ) -> list[T]:
        await self.session.run_sync(
            lambda ses: ses.bulk_insert_mappings(mapping, instances)
        )
        return cast(list, instances)

    async def del_exist_instance_without_commit(self, instance: T):
        await self.session.delete(instance)

    async def del_exist_instances(self, instances: Iterable[T]):
        for instance in instances:
            await self.session.delete(instance)

    async def run_delete_stmt_without_commit(self, stmt):
        await self.session.execute(stmt)

    async def update_stmt_without_commit(self, stmt):
        await self.session.execute(stmt)

    async def update_stmt_with_commit_returning(self, stmt) -> list[dict]:
        _result = await self.session.execute(stmt)
        await self.session.commit()
        return [BaseRepository.as_dict(_row) for _row in _result.all()]

    async def update_instances_without_commit(self, instances: list[T], payload: dict):
        for instance in instances:
            self.session.add(instance.update(**payload))
