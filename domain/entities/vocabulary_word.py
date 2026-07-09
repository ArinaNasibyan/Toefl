from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class VocabularyWord:
    id: str
    word: str
    translation: str
    transcription: str
    example: str
    level: str

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "VocabularyWord":
        required_fields = (
            "id",
            "word",
            "translation",
            "transcription",
            "example",
            "level",
        )

        missing_fields = [
            field for field in required_fields if field not in data or not data[field]
        ]
        if missing_fields:
            fields = ", ".join(missing_fields)
            raise ValueError(f"Vocabulary word is missing required fields: {fields}")

        return cls(
            id=str(data["id"]),
            word=str(data["word"]),
            translation=str(data["translation"]),
            transcription=str(data["transcription"]),
            example=str(data["example"]),
            level=str(data["level"]),
        )
