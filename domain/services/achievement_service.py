from domain.entities.achievement import Achievement
from domain.entities.user_statistics import UserStatistics


class AchievementService:
    """Service for checking achievement unlock conditions."""

    def __init__(self, achievements: list[Achievement]) -> None:
        self.achievements = achievements

    def check_unlockable_achievements(
        self,
        statistics: UserStatistics,
        unlocked_achievement_ids: set[str],
        test_completed: bool = False,
        test_score: int | None = None,
        test_total: int | None = None,
        test_type: str | None = None,
    ) -> list[Achievement]:
        """
        Check which achievements can be unlocked based on current statistics.

        Args:
            statistics: User's current statistics
            unlocked_achievement_ids: Set of already unlocked achievement IDs
            test_completed: Whether a test was just completed
            test_score: Score from the just-completed test (if any)
            test_total: Total questions in the just-completed test (if any)
            test_type: Type of test completed ("vocabulary_mini_test" or "reading_passage")

        Returns:
            List of achievements that should be unlocked
        """
        unlockable = []

        for achievement in self.achievements:
            if achievement.id in unlocked_achievement_ids:
                continue

            if self._check_requirement(
                achievement,
                statistics,
                test_completed,
                test_score,
                test_total,
                test_type,
            ):
                unlockable.append(achievement)

        return unlockable

    def _check_requirement(
        self,
        achievement: Achievement,
        statistics: UserStatistics,
        test_completed: bool,
        test_score: int | None,
        test_total: int | None,
        test_type: str | None,
    ) -> bool:
        """Check if a single achievement requirement is met."""
        req_type = achievement.requirement_type
        req_value = achievement.requirement_value

        if req_type == "completed_tasks":
            return statistics.completed_tasks >= req_value

        if req_type == "words_learned":
            return statistics.words_learned >= req_value

        if req_type == "streak_days":
            return statistics.current_streak >= req_value

        if req_type == "correct_answers":
            return statistics.correct_answers >= req_value

        if req_type == "accuracy_percentage":
            return statistics.accuracy_percentage >= req_value

        if req_type == "perfect_test":
            if test_completed and test_score is not None and test_total is not None:
                is_perfect = test_score == test_total and test_total > 0
                if is_perfect:
                    return True
            return False

        if req_type == "vocabulary_tests_completed":
            return statistics.vocabulary_tests_completed >= req_value

        if req_type == "reading_tests_completed":
            return statistics.reading_tests_completed >= req_value

        if req_type == "listening_tests_completed":
            return statistics.listening_tests_completed >= req_value

        return False
