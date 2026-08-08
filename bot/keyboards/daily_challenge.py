from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.daily_challenge import DailyChallengeCallback


def build_daily_challenge_menu_keyboard(completed: bool) -> InlineKeyboardMarkup:
    """Build keyboard for daily challenge menu."""
    buttons = []

    if not completed:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🎯 Start Challenge",
                    callback_data=DailyChallengeCallback(action="start").pack(),
                )
            ]
        )
    else:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="✅ Completed Today",
                    callback_data=DailyChallengeCallback(action="completed").pack(),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=DailyChallengeCallback(action="back").pack(),
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_challenge_answer_keyboard(options: list[str]) -> InlineKeyboardMarkup:
    """Build keyboard with answer options."""
    buttons = []

    for index, option in enumerate(options):
        buttons.append(
            [
                InlineKeyboardButton(
                    text=option,
                    callback_data=DailyChallengeCallback(
                        action="answer", data=str(index)
                    ).pack(),
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_challenge_finished_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for finished challenge."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏆 Achievements",
                    callback_data=DailyChallengeCallback(action="achievements").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back to Menu",
                    callback_data=DailyChallengeCallback(action="back").pack(),
                )
            ],
        ]
    )
