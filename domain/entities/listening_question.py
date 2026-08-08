from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ListeningQuestion:
    id: str
    question: str
    options: tuple[str, str, str, str]
    correct_index: int
    explanation: str

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "options": list(self.options),
            "correct_index": self.correct_index,
            "explanation": self.explanation,
        }

    @classmethod
    def from_state_dict(cls, data: dict[str, Any]) -> "ListeningQuestion":
        options = tuple(str(opt) for opt in data["options"])
        if len(options) != 4:
            raise ValueError("Listening question must have exactly four options")

        return cls(
            id=str(data["id"]),
            question=str(data["question"]),
            options=options,  # type: ignore[arg-type]
            correct_index=int(data["correct_index"]),
            explanation=str(data["explanation"]),
        )
