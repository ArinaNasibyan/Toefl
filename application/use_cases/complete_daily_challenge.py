"""Complete a daily challenge and update user statistics."""

from datetime import date

from infrastructure.database.repositories import (
    DailyChallengeRepository,
    UserRepository,
)


class CompleteDailyChallengeUseCase:
    """Complete a daily challenge and update user statistics."""

    def __init__(
        self,
        daily_challenge_repo: DailyChallengeRepository,
        user_repo: UserRepository,
    ) -> None:
        self.daily_challenge_repo = daily_challenge_repo
        self.user_repo = user_repo

    async def execute(
        self,
        telegram_id: int,
        score: int,
        total_questions: int,
    ) -> int:
        """
        Mark today's challenge as completed and update stats.

        Args:
            telegram_id: Telegram user ID
            score: Number of correct answers
            total_questions: Total number of questions

        Returns:
            Number of reward points earned

        Raises:
            ValueError: If user not found or challenge not found
        """
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            raise ValueError(f"User not found: {telegram_id}")

        today = date.today()

        # Get today's challenge
        challenge = await self.daily_challenge_repo.get_challenge_for_date(
            user.id, today
        )

        if challenge is None:
            raise ValueError("No challenge found for today")

        if challenge.completed:
            raise ValueError("Challenge already completed")

        # Mark challenge as completed
        await self.daily_challenge_repo.mark_completed(
            challenge_id=challenge.id,
            score=score,
            total_questions=total_questions,
        )

        # Update user stats
        await self.user_repo.increment_completed_tasks(user.id)
        for _ in range(score):
            await self.user_repo.increment_correct_answers(user.id)

        # Calculate reward points based on challenge type
        if challenge.challenge_type == "vocabulary_quiz":
            reward_points = 10
        elif challenge.challenge_type == "reading_passage":
            reward_points = 15
        else:
            reward_points = 5

        # Bonus points for perfect score
        if score == total_questions:
            reward_points += 5

        return reward_points
