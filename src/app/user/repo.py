from sqlalchemy import select
from src.app.user.model import User
from src.core.db.pg_base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    async def create_user(self, user: User):
        return await self.insert_one_without_commit(user)

    async def get_user_by_telegram_id(self, telegram_id: int):
        _stmt = select(User).where(User.telegram_id == telegram_id)
        return await self.run_select_stmt_for_one(_stmt)

    async def get_user_by_user_name(self, user_name: str):
        _stmt = select(User).where(User.user_name == user_name)
        return await self.run_select_stmt_for_one(_stmt)

    async def get_all_users(self):
        _stmt = select(User)
        return await self.run_select_stmt_for_all(_stmt)
