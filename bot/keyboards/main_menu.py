from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def build_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📚 Vocabulary"),
                KeyboardButton(text="📖 Reading"),
            ],
            [
                KeyboardButton(text="🎯 Daily Challenge"),
                KeyboardButton(text="📊 Statistics"),
            ],
            [
                KeyboardButton(text="🏆 Achievements"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose a practice mode",
    )
