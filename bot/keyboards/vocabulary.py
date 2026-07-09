from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.vocabulary import VocabularyCallback


def build_vocabulary_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Next word",
                    callback_data=VocabularyCallback(action="next").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📝 Mini Test",
                    callback_data=VocabularyCallback(action="mini_test").pack(),
                ),
                InlineKeyboardButton(
                    text="🔙 Back to Menu",
                    callback_data=VocabularyCallback(action="back").pack(),
                ),
            ],
        ],
    )


def build_quiz_answer_keyboard(options: tuple[str, ...]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=option,
                    callback_data=VocabularyCallback(
                        action="answer",
                        option_index=index,
                    ).pack(),
                ),
            ]
            for index, option in enumerate(options)
        ],
    )


def build_quiz_finished_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📚 Back to Vocabulary",
                    callback_data=VocabularyCallback(action="back_to_vocab").pack(),
                ),
                InlineKeyboardButton(
                    text="🔙 Main Menu",
                    callback_data=VocabularyCallback(action="back").pack(),
                ),
            ],
        ],
    )
