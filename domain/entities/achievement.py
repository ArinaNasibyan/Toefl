from dataclasses import dataclass


@dataclass(frozen=True)
class Achievement:
    """Domain entity representing an achievement definition."""

    id: str
    title: str
    description: str
    emoji: str
    category: str
    requirement_type: str
    requirement_value: int

    @classmethod
    def from_dict(cls, data: dict) -> "Achievement":
        """Create Achievement from JSON data."""
        requirement = data.get("requirement", {})
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            emoji=data["emoji"],
            category=data["category"],
            requirement_type=requirement.get("type", ""),
            requirement_value=requirement.get("value", 0),
        )


@dataclass(frozen=True)
class UserAchievement:
    """Domain entity representing a user's unlocked achievement."""

    achievement_id: str
    title: str
    description: str
    emoji: str
    category: str
    unlocked_at: str
