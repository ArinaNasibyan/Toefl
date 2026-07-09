from aiogram.filters.callback_data import CallbackData


class VocabularyCallback(CallbackData, prefix="vocabulary"):
    action: str
    option_index: int = -1
