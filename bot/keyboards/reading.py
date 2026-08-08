from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.reading import ReadingCallback


def build_reading_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ Start Test",
                    callback_data=ReadingCallback(action="start_test").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Another Passage",
                    callback_data=ReadingCallback(action="next_passage").pack(),
                ),
                InlineKeyboardButton(
                    text="🔙 Back to Menu",
                    callback_data=ReadingCallback(action="back").pack(),
                ),
            ],
        ],
    )


def build_reading_question_keyboard(options: tuple[str, ...]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=option,
                    callback_data=ReadingCallback(
                        action="answer",
                        option_index=index,
                    ).pack(),
                ),
            ]
            for index, option in enumerate(options)
        ],
    )


def build_reading_finished_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 Try Another Passage",
                    callback_data=ReadingCallback(action="next_passage").pack(),
                ),
                InlineKeyboardButton(
                    text="🔙 Main Menu",
                    callback_data=ReadingCallback(action="back").pack(),
                ),
            ],
        ],
    )
