from aiogram.filters.callback_data import CallbackData


class ReadingCallback(CallbackData, prefix="reading"):
    action: str
    option_index: int = -1
