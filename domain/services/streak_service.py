from datetime import date, timedelta


class StreakService:
    """Domain service for calculating and managing user learning streaks."""

    @staticmethod
    def calculate_new_streak(
        last_activity_date: date | None,
        current_streak: int,
        today: date,
    ) -> tuple[int, bool]:
        """
        Calculate the new streak based on last activity date.

        Args:
            last_activity_date: The date of the user's last activity (None if first time)
            current_streak: The user's current streak count
            today: Today's date

        Returns:
            Tuple of (new_streak, streak_updated)
            - new_streak: The updated streak count
            - streak_updated: True if the streak was incremented (consecutive day)
        """
        # First activity ever
        if last_activity_date is None:
            return (1, True)

        # Same day - maintain current streak
        if last_activity_date == today:
            return (current_streak, False)

        # Consecutive day - increment streak
        yesterday = today - timedelta(days=1)
        if last_activity_date == yesterday:
            return (current_streak + 1, True)

        # Streak broken - reset to 1
        return (1, True)

    @staticmethod
    def should_update_best_streak(current_streak: int, best_streak: int) -> bool:
        """
        Check if the best streak should be updated.

        Args:
            current_streak: The current streak value
            best_streak: The best (longest) streak value

        Returns:
            True if best_streak should be updated to current_streak
        """
        return current_streak > best_streak
