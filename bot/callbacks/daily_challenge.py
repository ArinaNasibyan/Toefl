from aiogram.filters.callback_data import CallbackData


class DailyChallengeCallback(CallbackData, prefix="daily_challenge"):
    action: str  # "start", "answer", "back"
    data: str = ""  # Additional data (answer index, etc.)
