from domain.entities.user_statistics import UserStatistics
from infrastructure.database.repositories import AttemptRepository, UserRepository


class GetUserStatisticsUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        attempt_repository: AttemptRepository,
    ) -> None:
        self._user_repository = user_repository
        self._attempt_repository = attempt_repository

    async def execute(self, telegram_id: int) -> UserStatistics:
        user = await self._user_repository.get_by_telegram_id(telegram_id)
        if user is None:
            raise ValueError("User not found")

        total_attempts = await self._attempt_repository.count_by_user_id(user.id)
        vocab_tests = await self._attempt_repository.count_by_user_and_content_type(
            user.id, "vocabulary_mini_test"
        )
        reading_tests = await self._attempt_repository.count_by_user_and_content_type(
            user.id, "reading_passage"
        )
        listening_tests = await self._attempt_repository.count_by_user_and_content_type(
            user.id, "listening_passage"
        )

        return UserStatistics.from_user_data(
            completed_tasks=user.completed_tasks,
            correct_answers=user.correct_answers,
            total_attempts=total_attempts,
            current_streak=user.streak_days,
            best_streak=user.best_streak,
            words_learned=user.words_learned,
            vocabulary_tests_completed=vocab_tests,
            reading_tests_completed=reading_tests,
            listening_tests_completed=listening_tests,
        )
