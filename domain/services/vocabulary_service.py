import random
from collections.abc import Sequence

from domain.entities.vocabulary_word import VocabularyWord


class VocabularyService:
    def __init__(
        self,
        words: Sequence[VocabularyWord],
        randomizer: random.Random | None = None,
    ) -> None:
        self._words = tuple(words)
        self._randomizer = randomizer or random

    def get_random_word(self, *, level: str | None = None) -> VocabularyWord:
        words = self._filter_words(level=level)
        if not words:
            raise ValueError("No vocabulary words available")

        return self._randomizer.choice(words)

    @property
    def words(self) -> tuple[VocabularyWord, ...]:
        return self._words

    def get_random_words(
        self,
        count: int,
        *,
        level: str | None = None,
    ) -> list[VocabularyWord]:
        if count <= 0:
            raise ValueError("Word count must be greater than zero")

        words = self._filter_words(level=level)
        if not words:
            raise ValueError("No vocabulary words available")

        return self._randomizer.sample(words, k=min(count, len(words)))

    def _filter_words(self, *, level: str | None) -> tuple[VocabularyWord, ...]:
        if level is None:
            return self._words

        normalized_level = level.upper()
        return tuple(
            word for word in self._words if word.level.upper() == normalized_level
        )
