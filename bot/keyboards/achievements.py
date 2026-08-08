from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.achievements import AchievementsCallback


def build_achievements_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Back to Menu",
                    callback_data=AchievementsCallback(action="back").pack(),
                ),
            ],
        ],
    )
