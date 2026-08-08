from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.callbacks.achievements import AchievementsCallback
from bot.keyboards.achievements import build_achievements_keyboard
from bot.keyboards.main_menu import build_main_menu_keyboard
from domain.entities.achievement import Achievement
from infrastructure.content.json_content_loader import JsonContentLoader
from infrastructure.database.repositories import AchievementRepository, UserRepository


router = Router(name="achievements")


@router.message(Command("achievements"))
@router.message(F.text == "🏆 Achievements")
async def show_achievements(
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
        user = await user_repository.get_by_telegram_id(telegram_user.id)

        if user is None:
            await message.answer(
                text="Please send /start to create your profile first.",
                reply_markup=build_main_menu_keyboard(),
            )
            return

        achievement_repository = AchievementRepository(session)
        unlocked_achievement_records = await achievement_repository.get_unlocked_by_user_id(
            user.id
        )
        await session.commit()

    # Load all achievement definitions
    all_achievements = await JsonContentLoader().load_achievements()
    achievements_by_id = {ach.id: ach for ach in all_achievements}

    # Create unlocked achievements list with full details
    unlocked_ids = {record.achievement_type for record in unlocked_achievement_records}
    unlocked_achievements = [
        achievements_by_id[ach_id]
        for ach_id in unlocked_ids
        if ach_id in achievements_by_id
    ]

    # Sort by category
    unlocked_achievements.sort(key=lambda a: (a.category, a.title))

    await message.answer(
        text=_format_achievements_list(unlocked_achievements, all_achievements),
        reply_markup=build_achievements_keyboard(),
    )


@router.callback_query(AchievementsCallback.filter(F.action == "back"))
async def back_to_main_menu(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.answer(
            text="Back to the main menu.",
            reply_markup=build_main_menu_keyboard(),
        )
        await callback.message.delete()

    await callback.answer()


def _format_achievements_list(
    unlocked: list[Achievement],
    all_achievements: list[Achievement],
) -> str:
    total = len(all_achievements)
    unlocked_count = len(unlocked)

    text = (
        f"🏆 <b>Your Achievements</b>\n\n"
        f"Unlocked: <b>{unlocked_count}/{total}</b>\n\n"
    )

    if not unlocked:
        text += "You haven't unlocked any achievements yet.\nComplete tests and practice to earn achievements!"
        return text

    # Group by category
    by_category: dict[str, list[Achievement]] = {}
    for ach in unlocked:
        if ach.category not in by_category:
            by_category[ach.category] = []
        by_category[ach.category].append(ach)

    category_names = {
        "milestone": "📊 Milestones",
        "vocabulary": "📚 Vocabulary",
        "reading": "📖 Reading",
        "skill": "🎯 Skills",
        "streak": "🔥 Streaks",
    }

    for category, achievements in sorted(by_category.items()):
        category_title = category_names.get(category, category.title())
        text += f"<b>{category_title}</b>\n"

        for ach in achievements:
            text += f"{ach.emoji} <b>{ach.title}</b>\n"
            text += f"   <i>{ach.description}</i>\n"

        text += "\n"

    return text.strip()
