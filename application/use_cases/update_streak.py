from datetime import date, datetime, timezone

from domain.services.streak_service import StreakService
from infrastructure.database.repositories import UserRepository


class UpdateStreakUseCase:
    """Use case for updating user's learning streak after completing an activity."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository
        self._streak_service = StreakService()

    async def execute(self, user_id: int) -> tuple[int, bool]:
        """
        Update user's streak based on today's activity.

        Args:
            user_id: The user's database ID

        Returns:
            Tuple of (new_streak, streak_increased)
            - new_streak: The updated streak count
            - streak_increased: True if streak was incremented (consecutive day)
        """
        # Get user data
        user = await self._user_repository._get_user_by_id(user_id)

        # Calculate today's date in UTC
        today = datetime.now(timezone.utc).date()

        # Calculate new streak
        new_streak, streak_updated = self._streak_service.calculate_new_streak(
            last_activity_date=user.last_activity_date,
            current_streak=user.streak_days,
            today=today,
        )

        # Update streak and last activity date
        await self._user_repository.update_streak(
            user_id=user_id,
            new_streak=new_streak,
            activity_date=today,
        )

        # Update best streak if necessary
        if self._streak_service.should_update_best_streak(new_streak, user.best_streak):
            await self._user_repository.update_best_streak(
                user_id=user_id,
                best_streak=new_streak,
            )

        return (new_streak, streak_updated)
