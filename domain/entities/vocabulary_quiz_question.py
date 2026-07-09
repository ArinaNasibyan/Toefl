from dataclasses import dataclass
from typing import Any

from domain.entities.vocabulary_word import VocabularyWord


@dataclass(frozen=True, slots=True)
class VocabularyQuizQuestion:
    word: VocabularyWord
    options: tuple[str, str, str, str]
    correct_index: int

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "word_id": self.word.id,
            "word": self.word.word,
            "transcription": self.word.transcription,
            "translation": self.word.translation,
            "options": list(self.options),
            "correct_index": self.correct_index,
        }

    @classmethod
    def from_state_dict(cls, data: dict[str, Any]) -> "VocabularyQuizQuestion":
        word = VocabularyWord(
            id=str(data["word_id"]),
            word=str(data["word"]),
            translation=str(data["translation"]),
            transcription=str(data["transcription"]),
            example="",
            level="",
        )
        options = tuple(str(option) for option in data["options"])
        if len(options) != 4:
            raise ValueError("Quiz question must have exactly four options")

        return cls(
            word=word,
            options=options,  # type: ignore[arg-type]
            correct_index=int(data["correct_index"]),
        )
