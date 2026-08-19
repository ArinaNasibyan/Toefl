"""Get or create today's daily challenge for a user."""

from datetime import date

from domain.entities.daily_challenge import UserDailyChallenge
from domain.entities.reading_passage import ReadingPassage
from domain.entities.vocabulary_word import VocabularyWord
from domain.services.daily_challenge_service import DailyChallengeService
from infrastructure.database.repositories import DailyChallengeRepository, UserRepository


class GetTodaysChallengeUseCase:
    """Get or create today's daily challenge for a user."""

    def __init__(
        self,
        daily_challenge_repo: DailyChallengeRepository,
        user_repo: UserRepository,
        vocabulary_words: list[VocabularyWord],
        reading_passages: list[ReadingPassage],
    ) -> None:
        self.daily_challenge_repo = daily_challenge_repo
        self.user_repo = user_repo
        self.challenge_service = DailyChallengeService(vocabulary_words, reading_passages)

    async def execute(self, telegram_id: int) -> UserDailyChallenge:
        """
        Get or create today's challenge for a user.

        Args:
            telegram_id: Telegram user ID

        Returns:
            UserDailyChallenge entity with today's challenge info

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            raise ValueError(f"User not found: {telegram_id}")

        today = date.today()

        # Check if challenge already exists for today
        existing_challenge = await self.daily_challenge_repo.get_challenge_for_date(
            user.id, today
        )

        if existing_challenge:
            return UserDailyChallenge(
                challenge_date=existing_challenge.challenge_date,
                challenge_type=existing_challenge.challenge_type,
                content_id=existing_challenge.content_id,
                completed=existing_challenge.completed,
                score=existing_challenge.score,
                total_questions=existing_challenge.total_questions,
            )

        # Generate new challenge for today
        challenge_type, content_id = self.challenge_service.get_challenge_for_date(today)

        # Create challenge record
        challenge = await self.daily_challenge_repo.create_challenge(
            user_id=user.id,
            challenge_date=today,
            challenge_type=challenge_type,
            content_id=content_id,
        )

        return UserDailyChallenge(
            challenge_date=challenge.challenge_date,
            challenge_type=challenge.challenge_type,
            content_id=challenge.content_id,
            completed=challenge.completed,
        )
