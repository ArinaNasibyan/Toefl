from aiogram.filters.callback_data import CallbackData


class ListeningCallback(CallbackData, prefix="listening"):
    action: str
    option_index: int = -1
