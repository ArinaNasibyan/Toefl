from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True, slots=True)
class DailyChallengeDefinition:
    """Represents a daily challenge template/definition."""

    id: str
    title: str
    description: str
    type: str  # "vocabulary_quiz" or "reading_passage"
    difficulty: str  # "easy", "medium", "hard"
    reward_points: int

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "DailyChallengeDefinition":
        required_fields = ("id", "title", "description", "type", "difficulty", "reward_points")

        missing_fields = [
            field for field in required_fields if field not in data or data[field] is None
        ]
        if missing_fields:
            fields = ", ".join(missing_fields)
            raise ValueError(f"Daily challenge is missing required fields: {fields}")

        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            description=str(data["description"]),
            type=str(data["type"]),
            difficulty=str(data["difficulty"]),
            reward_points=int(data["reward_points"]),
        )


@dataclass(frozen=True, slots=True)
class UserDailyChallenge:
    """Represents a user's daily challenge status."""

    challenge_date: date
    challenge_type: str
    content_id: str
    completed: bool
    score: int | None = None
    total_questions: int | None = None
