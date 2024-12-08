from typing import Optional

from src.app.user.exception import UserNotFoundError
from src.app.user.model import User
from src.app.user.repo import UserRepository
from src.core.db.pg_uow import PgSQLAlchemyUnitOfWork


class UserService:
    def __init__(self, uow: PgSQLAlchemyUnitOfWork):
        self._uow = uow

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        async with self._uow.atomic() as _session:
            return await self._uow.get_repository(
                UserRepository, _session
            ).get_user_by_telegram_id(telegram_id)

    async def get_user_by_telegram_id_with_error(self, telegram_id: int) -> User:
        _user = await self.get_user_by_telegram_id(telegram_id)
        if not _user:
            raise UserNotFoundError(
                message=f"User with telegram_id: {telegram_id} not found"
            )
        return _user

    async def create_user_if_not_exist(self, telegram_id: int) -> User:
        _user = await self.get_user_by_telegram_id(telegram_id)
        if _user:
            return _user
        _user_dto = User.create(...)
        async with self._uow.atomic() as _session:
            _user = await self._uow.get_repository(
                UserRepository, _session
            ).create_user(_user_dto)
        return _user
