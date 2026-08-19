from aiogram.filters.callback_data import CallbackData


class AchievementsCallback(CallbackData, prefix="achievements"):
    action: str
