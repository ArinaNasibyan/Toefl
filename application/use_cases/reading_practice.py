import random
from collections.abc import Sequence

from domain.entities.reading_passage import ReadingPassage


class StartReadingPracticeUseCase:
    def __init__(
        self,
        passages: Sequence[ReadingPassage],
        randomizer: random.Random | None = None,
    ) -> None:
        self._passages = passages
        self._randomizer = randomizer or random

    def execute(self) -> ReadingPassage:
        if not self._passages:
            raise ValueError("No reading passages available")

        return self._randomizer.choice(self._passages)


class SubmitReadingAnswerUseCase:
    def __init__(
        self,
        attempt_repository,
        user_repository,
    ) -> None:
        self._attempt_repository = attempt_repository
        self._user_repository = user_repository

    async def execute(
        self,
        *,
        user_id: int,
        question_id: str,
        is_correct: bool,
        finish_test: bool = False,
    ) -> bool:
        await self._attempt_repository.create(
            user_id=user_id,
            content_type="reading_passage",
            content_id=question_id,
            is_correct=is_correct,
        )

        if is_correct:
            await self._user_repository.increment_correct_answers(user_id)

        if finish_test:
            await self._user_repository.increment_completed_tasks(user_id)

        return is_correct
