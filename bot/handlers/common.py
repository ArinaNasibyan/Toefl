from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
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
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await state.clear()
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

        # Get user to display streak
        user = await user_repository.get_by_telegram_id(telegram_user.id)
        current_streak = user.streak_days if user else 0

        await session.commit()

    first_name = telegram_user.first_name or "there"

    streak_text = ""
    if current_streak > 0:
        streak_text = f"\n\n🔥 Your current streak: <b>{current_streak} days</b> in a row!"

    await message.answer(
        text=(
            f"Welcome, {first_name}!\n\n"
            "Your TOEFL practice profile is ready. Choose a section to begin."
            f"{streak_text}"
        ),
        reply_markup=build_main_menu_keyboard(),
    )
