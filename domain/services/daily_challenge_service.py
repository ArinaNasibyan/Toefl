"""Daily challenge service for generating and managing daily challenges."""

from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.reading_passage import ReadingPassage
    from domain.entities.vocabulary_word import VocabularyWord


class DailyChallengeService:
    """Service for generating daily challenges based on date."""

    def __init__(
        self,
        vocabulary_words: list["VocabularyWord"],
        reading_passages: list["ReadingPassage"],
    ) -> None:
        self.vocabulary_words = vocabulary_words
        self.reading_passages = reading_passages

    def get_challenge_for_date(
        self, challenge_date: date
    ) -> tuple[str, str]:  # (challenge_type, content_id)
        """
        Generate a deterministic daily challenge based on the date.

        Returns:
            Tuple of (challenge_type, content_id) where challenge_type is
            "vocabulary_quiz" or "reading_passage"
        """
        # Use date to determine challenge type (alternates between vocab and reading)
        days_since_epoch = (challenge_date - date(2024, 1, 1)).days

        if days_since_epoch % 2 == 0:
            # Vocabulary challenge
            vocab_index = days_since_epoch % len(self.vocabulary_words)
            return ("vocabulary_quiz", self.vocabulary_words[vocab_index].id)
        else:
            # Reading challenge
            reading_index = days_since_epoch % len(self.reading_passages)
            return ("reading_passage", self.reading_passages[reading_index].id)

    def get_challenge_title(self, challenge_type: str) -> str:
        """Get human-readable title for challenge type."""
        if challenge_type == "vocabulary_quiz":
            return "📚 Vocabulary Challenge"
        elif challenge_type == "reading_passage":
            return "📖 Reading Challenge"
        return "🎯 Daily Challenge"

    def get_challenge_description(self, challenge_type: str) -> str:
        """Get description for challenge type."""
        if challenge_type == "vocabulary_quiz":
            return "Complete a 5-question vocabulary quiz"
        elif challenge_type == "reading_passage":
            return "Read a passage and answer 5 comprehension questions"
        return "Complete today's challenge"

    def get_reward_points(self, challenge_type: str) -> int:
        """Get reward points for completing challenge."""
        if challenge_type == "vocabulary_quiz":
            return 10
        elif challenge_type == "reading_passage":
            return 15
        return 5

    def calculate_time_until_next_challenge(self, current_date: date) -> timedelta:
        """Calculate time remaining until next challenge (midnight)."""
        next_day = current_date + timedelta(days=1)
        return timedelta(days=1)  # Simplified: always returns 1 day
