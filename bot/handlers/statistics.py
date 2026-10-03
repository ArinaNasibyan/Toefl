from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.use_cases.get_user_statistics import GetUserStatisticsUseCase
from bot.keyboards.main_menu import build_main_menu_keyboard
from domain.entities.user_statistics import UserStatistics
from infrastructure.database.repositories import AttemptRepository, UserRepository


router = Router(name="statistics")


@router.message(Command("statistics"))
@router.message(F.text == "📊 Statistics")
async def show_statistics(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await state.clear()
    telegram_user = message.from_user
    if telegram_user is None:
        return

    async with session_factory() as session:
        get_statistics = GetUserStatisticsUseCase(
            UserRepository(session),
            AttemptRepository(session),
        )

        try:
            statistics = await get_statistics.execute(telegram_user.id)
        except ValueError:
            await message.answer(
                text="Please send /start to create your profile first.",
                reply_markup=build_main_menu_keyboard(),
            )
            return

    await message.answer(
        text=_format_statistics(statistics),
        reply_markup=build_main_menu_keyboard(),
    )


def _format_statistics(statistics: UserStatistics) -> str:
    return (
        "📊 <b>Your TOEFL Statistics</b>\n\n"
        f"📚 <b>Words learned:</b> {statistics.words_learned}\n"
        f"📝 <b>Completed tasks:</b> {statistics.completed_tasks}\n"
        f"✅ <b>Correct answers:</b> {statistics.correct_answers}\n"
        f"🔥 <b>Current streak:</b> {statistics.current_streak} days\n"
        f"🏆 <b>Best streak:</b> {statistics.best_streak} days\n"
        f"🎯 <b>Accuracy:</b> {statistics.accuracy_percentage}%"
    )

