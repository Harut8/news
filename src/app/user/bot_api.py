from dependency_injector.wiring import Provide, inject
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.app.user.service import UserService
from src.core.di import DependencyContainer

user_router = Router(name="user_router")


@user_router.message(Command("start"))
@inject
async def start(
    message: Message,
    user_service: UserService = Provide[DependencyContainer.user_service],
):
    await message.answer(f"Hello {message.from_user.first_name}")
