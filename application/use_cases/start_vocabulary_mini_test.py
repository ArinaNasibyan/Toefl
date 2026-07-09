from collections.abc import Sequence

from domain.entities.vocabulary_quiz_question import VocabularyQuizQuestion
from domain.entities.vocabulary_word import VocabularyWord
from domain.services.vocabulary_quiz_service import VocabularyQuizService
from domain.services.vocabulary_service import VocabularyService


DEFAULT_MINI_TEST_QUESTION_COUNT = 5


class StartVocabularyMiniTestUseCase:
    def __init__(
        self,
        words: Sequence[VocabularyWord],
        *,
        question_count: int = DEFAULT_MINI_TEST_QUESTION_COUNT,
    ) -> None:
        self._words = words
        self._question_count = question_count

    def execute(self) -> list[VocabularyQuizQuestion]:
        vocabulary_service = VocabularyService(self._words)
        quiz_service = VocabularyQuizService(vocabulary_service)
        return quiz_service.generate_quiz(self._question_count)
