from datetime import date, timedelta

import pytest

from domain.services.streak_service import StreakService


class TestStreakService:
    """Test cases for the StreakService domain service."""

    def test_first_activity_ever(self):
        """Test that first activity sets streak to 1."""
        service = StreakService()
        today = date(2026, 7, 13)

        new_streak, streak_updated = service.calculate_new_streak(
            last_activity_date=None,
            current_streak=0,
            today=today,
        )

        assert new_streak == 1
        assert streak_updated is True

    def test_same_day_activity(self):
        """Test that multiple activities on the same day don't increment streak."""
        service = StreakService()
        today = date(2026, 7, 13)

        new_streak, streak_updated = service.calculate_new_streak(
            last_activity_date=today,
            current_streak=5,
            today=today,
        )

        assert new_streak == 5
        assert streak_updated is False

    def test_consecutive_day_activity(self):
        """Test that activity on consecutive days increments the streak."""
        service = StreakService()
        today = date(2026, 7, 13)
        yesterday = today - timedelta(days=1)

        new_streak, streak_updated = service.calculate_new_streak(
            last_activity_date=yesterday,
            current_streak=5,
            today=today,
        )

        assert new_streak == 6
        assert streak_updated is True

    def test_missed_one_day_resets_streak(self):
        """Test that missing a day resets the streak to 1."""
        service = StreakService()
        today = date(2026, 7, 13)
        two_days_ago = today - timedelta(days=2)

        new_streak, streak_updated = service.calculate_new_streak(
            last_activity_date=two_days_ago,
            current_streak=10,
            today=today,
        )

        assert new_streak == 1
        assert streak_updated is True

    def test_missed_many_days_resets_streak(self):
        """Test that missing multiple days resets the streak to 1."""
        service = StreakService()
        today = date(2026, 7, 13)
        last_activity = today - timedelta(days=30)

        new_streak, streak_updated = service.calculate_new_streak(
            last_activity_date=last_activity,
            current_streak=20,
            today=today,
        )

        assert new_streak == 1
        assert streak_updated is True

    def test_should_update_best_streak_when_current_higher(self):
        """Test that best streak is updated when current exceeds it."""
        service = StreakService()

        should_update = service.should_update_best_streak(
            current_streak=15,
            best_streak=10,
        )

        assert should_update is True

    def test_should_not_update_best_streak_when_current_lower(self):
        """Test that best streak is not updated when current is lower."""
        service = StreakService()

        should_update = service.should_update_best_streak(
            current_streak=8,
            best_streak=10,
        )

        assert should_update is False

    def test_should_not_update_best_streak_when_equal(self):
        """Test that best streak is not updated when current equals it."""
        service = StreakService()

        should_update = service.should_update_best_streak(
            current_streak=10,
            best_streak=10,
        )

        assert should_update is False
