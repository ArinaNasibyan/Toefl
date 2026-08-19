from dataclasses import dataclass
from typing import Any

from domain.entities.listening_question import ListeningQuestion


@dataclass(frozen=True, slots=True)
class ListeningPassage:
    id: str
    title: str
    type: str  # "lecture" or "conversation"
    audio_file: str  # Relative path to generated MP3 file
    transcript: str
    questions: tuple[ListeningQuestion, ...]

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "audio_file": self.audio_file,
            "transcript": self.transcript,
            "questions": [q.to_state_dict() for q in self.questions],  # List serialization for FSM compatibility
        }

    @classmethod
    def from_state_dict(cls, data: dict[str, Any]) -> "ListeningPassage":
        questions = tuple(
            ListeningQuestion.from_state_dict(q) for q in data["questions"]
        )
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            type=str(data["type"]),
            audio_file=str(data["audio_file"]),
            transcript=str(data["transcript"]),
            questions=questions,
        )
