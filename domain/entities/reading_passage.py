from dataclasses import dataclass
from typing import Any

from domain.entities.question import ReadingQuestion


@dataclass(frozen=True, slots=True)
class ReadingPassage:
    id: str
    title: str
    text: str
    questions: tuple[ReadingQuestion, ...]

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "questions": [q.to_state_dict() for q in self.questions],
        }

    @classmethod
    def from_state_dict(cls, data: dict[str, Any]) -> "ReadingPassage":
        questions = tuple(
            ReadingQuestion.from_state_dict(q) for q in data["questions"]
        )
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            text=str(data["text"]),
            questions=questions,
        )
