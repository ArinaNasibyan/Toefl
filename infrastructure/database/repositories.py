from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import (
    Achievement,
    Attempt,
    DailyChallenge,
    User,
    VocabularyProgress,
)


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

    async def increment_words_learned(self, user_id: int) -> None:
        user = await self._get_user_by_id(user_id)
        user.words_learned += 1
        await self._session.flush()

    async def update_streak(
        self,
        user_id: int,
        new_streak: int,
        activity_date: date,
    ) -> None:
        """Update user's streak and last activity date."""
        user = await self._get_user_by_id(user_id)
        user.streak_days = new_streak
        user.last_activity_date = activity_date
        await self._session.flush()

    async def update_best_streak(self, user_id: int, best_streak: int) -> None:
        """Update user's best streak if current is higher."""
        user = await self._get_user_by_id(user_id)
        user.best_streak = best_streak
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

    async def count_by_user_id(self, user_id: int) -> int:
        statement = (
            select(func.count())
            .select_from(Attempt)
            .where(Attempt.user_id == user_id)
        )
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def count_by_user_and_content_type(
        self, user_id: int, content_type: str
    ) -> int:
        """Count attempts for a specific content type (e.g., 'vocabulary_mini_test')."""
        statement = (
            select(func.count())
            .select_from(Attempt)
            .where(Attempt.user_id == user_id)
            .where(Attempt.content_type == content_type)
        )
        result = await self._session.execute(statement)
        return int(result.scalar_one())


class VocabularyProgressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_and_word(
        self,
        user_id: int,
        word_id: str,
    ) -> VocabularyProgress | None:
        statement = (
            select(VocabularyProgress)
            .where(VocabularyProgress.user_id == user_id)
            .where(VocabularyProgress.word_id == word_id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        user_id: int,
        word_id: str,
        repetitions: int = 0,
        mastered: bool = False,
        last_review_date: datetime | None = None,
    ) -> VocabularyProgress:
        progress = VocabularyProgress(
            user_id=user_id,
            word_id=word_id,
            repetitions=repetitions,
            mastered=mastered,
            last_review_date=last_review_date,
        )
        self._session.add(progress)
        await self._session.flush()
        return progress


class AchievementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_unlocked_by_user_id(self, user_id: int) -> list[Achievement]:
        """Get all achievements unlocked by a user."""
        statement = (
            select(Achievement)
            .where(Achievement.user_id == user_id)
            .order_by(Achievement.unlocked_at.desc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def get_unlocked_achievement_ids(self, user_id: int) -> set[str]:
        """Get set of achievement_type IDs that user has unlocked."""
        statement = select(Achievement.achievement_type).where(
            Achievement.user_id == user_id
        )
        result = await self._session.execute(statement)
        return set(result.scalars().all())

    async def unlock_achievement(
        self,
        *,
        user_id: int,
        achievement_type: str,
    ) -> Achievement:
        """Unlock an achievement for a user."""
        achievement = Achievement(
            user_id=user_id,
            achievement_type=achievement_type,
        )
        self._session.add(achievement)
        await self._session.flush()
        return achievement

    async def is_unlocked(self, user_id: int, achievement_type: str) -> bool:
        """Check if a user has unlocked a specific achievement."""
        statement = (
            select(func.count())
            .select_from(Achievement)
            .where(Achievement.user_id == user_id)
            .where(Achievement.achievement_type == achievement_type)
        )
        result = await self._session.execute(statement)
        count = result.scalar_one()
        return count > 0


class DailyChallengeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_challenge_for_date(
        self,
        user_id: int,
        challenge_date: date,
    ) -> DailyChallenge | None:
        """Get user's daily challenge for a specific date."""
        statement = (
            select(DailyChallenge)
            .where(DailyChallenge.user_id == user_id)
            .where(DailyChallenge.challenge_date == challenge_date)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def create_challenge(
        self,
        *,
        user_id: int,
        challenge_date: date,
        challenge_type: str,
        content_id: str,
    ) -> DailyChallenge:
        """Create a new daily challenge for a user."""
        challenge = DailyChallenge(
            user_id=user_id,
            challenge_date=challenge_date,
            challenge_type=challenge_type,
            content_id=content_id,
            completed=False,
        )
        self._session.add(challenge)
        await self._session.flush()
        return challenge

    async def mark_completed(
        self,
        challenge_id: int,
        score: int,
        total_questions: int,
    ) -> None:
        """Mark a challenge as completed with score."""
        statement = select(DailyChallenge).where(DailyChallenge.id == challenge_id)
        result = await self._session.execute(statement)
        challenge = result.scalar_one_or_none()

        if challenge is None:
            raise ValueError(f"Challenge not found: {challenge_id}")

        challenge.completed = True
        challenge.score = score
        challenge.total_questions = total_questions
        challenge.completed_at = datetime.now(UTC)
        await self._session.flush()

    async def count_completed_challenges(self, user_id: int) -> int:
        """Count total completed challenges for a user."""
        statement = (
            select(func.count())
            .select_from(DailyChallenge)
            .where(DailyChallenge.user_id == user_id)
            .where(DailyChallenge.completed == True)
        )
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def get_current_streak(self, user_id: int) -> int:
        """Calculate current streak of consecutive completed challenges."""
        statement = (
            select(DailyChallenge)
            .where(DailyChallenge.user_id == user_id)
            .where(DailyChallenge.completed == True)
            .order_by(DailyChallenge.challenge_date.desc())
        )
        result = await self._session.execute(statement)
        challenges = list(result.scalars().all())

        if not challenges:
            return 0

        streak = 0
        today = date.today()
        expected_date = today

        for challenge in challenges:
            if challenge.challenge_date == expected_date:
                streak += 1
                expected_date = expected_date - timedelta(days=1)
            elif challenge.challenge_date == expected_date - timedelta(days=1):
                expected_date = challenge.challenge_date
            else:
                break

        return streak

