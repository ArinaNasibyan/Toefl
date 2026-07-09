from dataclasses import dataclass

from infrastructure.database.models import User
from infrastructure.database.repositories import UserRepository


@dataclass(frozen=True, slots=True)
class TelegramUserData:
    telegram_id: int
    username: str | None
    first_name: str | None


class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, user_data: TelegramUserData) -> User:
        user = await self._user_repository.get_by_telegram_id(
            user_data.telegram_id,
        )

        if user is None:
            return await self._user_repository.create(
                telegram_id=user_data.telegram_id,
                username=user_data.username,
                first_name=user_data.first_name,
            )

        await self._user_repository.update_last_activity(user)
        return user
