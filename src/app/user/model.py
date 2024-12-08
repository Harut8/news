from typing import Optional

from sqlalchemy.orm import Mapped
from src.core.db.pg_base_model import PgBaseModel, IntPkIdMixin, int_pk_annotated


class User(PgBaseModel, IntPkIdMixin):
    telegram_id: Mapped[int_pk_annotated]
    user_name: Mapped[Optional[str]]
    first_name: Mapped[Optional[str]]
    last_name: Mapped[Optional[str]]

    @classmethod
    def create(
        cls,
        telegram_id: int,
        user_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ):
        return cls(
            telegram_id=telegram_id,
            user_name=user_name,
            first_name=first_name,
            last_name=last_name,
        )
