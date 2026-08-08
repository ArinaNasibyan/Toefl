from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.listening import ListeningCallback


def build_listening_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ Start Questions",
                    callback_data=ListeningCallback(action="start_test").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Another Audio",
                    callback_data=ListeningCallback(action="next_passage").pack(),
                ),
                InlineKeyboardButton(
                    text="🔙 Back to Menu",
                    callback_data=ListeningCallback(action="back").pack(),
                ),
            ],
        ],
    )


def build_listening_question_keyboard(options: tuple[str, ...]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=option,
                    callback_data=ListeningCallback(
                        action="answer",
                        option_index=index,
                    ).pack(),
                ),
            ]
            for index, option in enumerate(options)
        ],
    )


def build_listening_finished_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎧 Another Practice",
                    callback_data=ListeningCallback(action="next_passage").pack(),
                ),
                InlineKeyboardButton(
                    text="🔙 Main Menu",
                    callback_data=ListeningCallback(action="back").pack(),
                ),
            ],
        ],
    )


def build_listening_feedback_keyboard(is_last: bool) -> InlineKeyboardMarkup:
    button_text = "🏁 View Results" if is_last else "➡️ Next Question"
    action_name = "show_results" if is_last else "next_question"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=ListeningCallback(action=action_name).pack(),
                )
            ]
        ]
    )
