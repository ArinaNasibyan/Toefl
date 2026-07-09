from infrastructure.database.repositories import AttemptRepository, UserRepository

VOCABULARY_MINI_TEST_CONTENT_TYPE = "vocabulary_mini_test"


class SubmitVocabularyAnswerUseCase:
    def __init__(
        self,
        attempt_repository: AttemptRepository,
        user_repository: UserRepository,
    ) -> None:
        self._attempt_repository = attempt_repository
        self._user_repository = user_repository

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

        return is_correct
