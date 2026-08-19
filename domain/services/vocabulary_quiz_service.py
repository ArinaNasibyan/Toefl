import random

from domain.entities.vocabulary_quiz_question import VocabularyQuizQuestion
from domain.services.vocabulary_service import VocabularyService


class VocabularyQuizService:
    OPTIONS_PER_QUESTION = 4
    DISTRACTOR_COUNT = OPTIONS_PER_QUESTION - 1

    def __init__(
        self,
        vocabulary_service: VocabularyService,
        randomizer: random.Random | None = None,
    ) -> None:
        self._vocabulary_service = vocabulary_service
        self._randomizer = randomizer or random

    def generate_quiz(self, question_count: int = 5) -> list[VocabularyQuizQuestion]:
        if question_count <= 0:
            raise ValueError("Question count must be greater than zero")

        words = self._vocabulary_service.get_random_words(question_count)
        return [self._build_question(word) for word in words]

    def _build_question(self, word) -> VocabularyQuizQuestion:
        correct_translation = word.translation
        distractor_pool = self._get_distractor_pool(
            word_id=word.id,
            correct_translation=correct_translation,
        )

        if len(distractor_pool) < self.DISTRACTOR_COUNT:
            raise ValueError("Not enough vocabulary words to build quiz options")

        distractors = self._randomizer.sample(
            distractor_pool,
            k=self.DISTRACTOR_COUNT,
        )
        options = [correct_translation, *distractors]
        self._randomizer.shuffle(options)
        correct_index = options.index(correct_translation)

        return VocabularyQuizQuestion(
            word=word,
            options=tuple(options),  # type: ignore[arg-type]
            correct_index=correct_index,
        )

    def _get_distractor_pool(
        self,
        *,
        word_id: str,
        correct_translation: str,
    ) -> list[str]:
        seen_translations: set[str] = set()
        distractor_pool: list[str] = []

        for candidate in self._vocabulary_service.words:
            if candidate.id == word_id:
                continue

            normalized_translation = candidate.translation.strip().lower()
            if (
                candidate.translation == correct_translation
                or normalized_translation in seen_translations
            ):
                continue

            seen_translations.add(normalized_translation)
            distractor_pool.append(candidate.translation)

        return distractor_pool
