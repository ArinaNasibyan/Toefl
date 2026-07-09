from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import Attempt, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        statement = select(User).where(User.telegram_id == telegram_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def update_last_activity(self, user: User) -> None:
        user.last_activity = datetime.now(UTC)
        await self._session.flush()

    async def increment_correct_answers(self, user_id: int) -> None:
        user = await self._get_user_by_id(user_id)
        user.correct_answers += 1
        await self._session.flush()

    async def increment_completed_tasks(self, user_id: int) -> None:
        user = await self._get_user_by_id(user_id)
        user.completed_tasks += 1
        await self._session.flush()

    async def _get_user_by_id(self, user_id: int) -> User:
        statement = select(User).where(User.id == user_id)
        result = await self._session.execute(statement)
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User not found: {user_id}")
        return user


class AttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: int,
        content_type: str,
        content_id: str,
        is_correct: bool,
    ) -> Attempt:
        attempt = Attempt(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id,
            is_correct=is_correct,
        )
        self._session.add(attempt)
        await self._session.flush()
        return attempt
