from datetime import UTC, datetime
from infrastructure.database.repositories import (
    AttemptRepository,
    UserRepository,
    VocabularyProgressRepository,
)

VOCABULARY_MINI_TEST_CONTENT_TYPE = "vocabulary_mini_test"


class SubmitVocabularyAnswerUseCase:
    def __init__(
        self,
        attempt_repository: AttemptRepository,
        user_repository: UserRepository,
        vocabulary_progress_repository: VocabularyProgressRepository,
    ) -> None:
        self._attempt_repository = attempt_repository
        self._user_repository = user_repository
        self._vocabulary_progress_repository = vocabulary_progress_repository

    async def execute(
        self,
        *,
        user_id: int,
        word_id: str,
        is_correct: bool,
        finish_quiz: bool = False,
    ) -> bool:
        await self._attempt_repository.create(
            user_id=user_id,
            content_type=VOCABULARY_MINI_TEST_CONTENT_TYPE,
            content_id=word_id,
            is_correct=is_correct,
        )

        if is_correct:
            await self._user_repository.increment_correct_answers(user_id)

        if finish_quiz:
            await self._user_repository.increment_completed_tasks(user_id)

        # Manage Spaced Repetition / Vocabulary Progress
        progress = await self._vocabulary_progress_repository.get_by_user_and_word(
            user_id=user_id,
            word_id=word_id,
        )
        now_utc = datetime.now(UTC)

        if progress is None:
            # Create a new progress entry. Note that it's only marked as 1 repetition if correct.
            await self._vocabulary_progress_repository.create(
                user_id=user_id,
                word_id=word_id,
                repetitions=1 if is_correct else 0,
                mastered=False,
                last_review_date=now_utc,
            )
        else:
            if is_correct:
                progress.repetitions += 1
                if progress.repetitions >= 3 and not progress.mastered:
                    progress.mastered = True
                    await self._user_repository.increment_words_learned(user_id)
            else:
                progress.repetitions = 0  # reset on incorrect answer
            progress.last_review_date = now_utc

        return is_correct

