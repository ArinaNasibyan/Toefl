from domain.entities.achievement import Achievement
from domain.entities.user_statistics import UserStatistics
from domain.services.achievement_service import AchievementService
from infrastructure.database.repositories import AchievementRepository


class CheckAchievementsUseCase:
    """Check and unlock newly achieved achievements for a user."""

    def __init__(
        self,
        achievement_service: AchievementService,
        achievement_repository: AchievementRepository,
    ) -> None:
        self._achievement_service = achievement_service
        self._achievement_repository = achievement_repository

    async def execute(
        self,
        user_id: int,
        statistics: UserStatistics,
        test_completed: bool = False,
        test_score: int | None = None,
        test_total: int | None = None,
        test_type: str | None = None,
    ) -> list[Achievement]:
        """
        Check for unlockable achievements and unlock them.

        Args:
            user_id: The user's database ID
            statistics: Current user statistics
            test_completed: Whether a test was just completed
            test_score: Score from the completed test
            test_total: Total questions in the test
            test_type: Type of test ("vocabulary_mini_test" or "reading_passage")

        Returns:
            List of newly unlocked achievements
        """
        unlocked_ids = await self._achievement_repository.get_unlocked_achievement_ids(
            user_id
        )

        unlockable = self._achievement_service.check_unlockable_achievements(
            statistics=statistics,
            unlocked_achievement_ids=unlocked_ids,
            test_completed=test_completed,
            test_score=test_score,
            test_total=test_total,
            test_type=test_type,
        )

        newly_unlocked = []
        for achievement in unlockable:
            await self._achievement_repository.unlock_achievement(
                user_id=user_id,
                achievement_type=achievement.id,
            )
            newly_unlocked.append(achievement)

        return newly_unlocked
