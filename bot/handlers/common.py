from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.use_cases.register_user import (
    RegisterUserUseCase,
    TelegramUserData,
)
from bot.keyboards.main_menu import build_main_menu_keyboard
from infrastructure.database.repositories import UserRepository


router = Router(name="common")


@router.message(CommandStart())
async def start_command(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
        return

    async with session_factory() as session:
        user_repository = UserRepository(session)
        register_user = RegisterUserUseCase(user_repository)

        await register_user.execute(
            TelegramUserData(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
            ),
        )
        await session.commit()

    first_name = telegram_user.first_name or "there"
    await message.answer(
        text=(
            f"Welcome, {first_name}!\n\n"
            "Your TOEFL practice profile is ready. Choose a section to begin."
        ),
        reply_markup=build_main_menu_keyboard(),
    )
