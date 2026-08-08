from datetime import date, timedelta

import pytest

from application.use_cases.update_streak import UpdateStreakUseCase
from infrastructure.database.repositories import UserRepository


@pytest.mark.asyncio
async def test_update_streak_first_time(db_session):
    """Test updating streak for the first time."""
    user_repo = UserRepository(db_session)

    # Create a user
    user = await user_repo.create(
        telegram_id=123456,
        username="testuser",
        first_name="Test",
    )
    await db_session.commit()

    # Update streak for the first time
    update_streak = UpdateStreakUseCase(user_repo)
    new_streak, streak_increased = await update_streak.execute(user_id=user.id)

    assert new_streak == 1
    assert streak_increased is True

    # Verify user was updated
    await db_session.refresh(user)
    assert user.streak_days == 1
    assert user.best_streak == 1
    assert user.last_activity_date == date.today()


@pytest.mark.asyncio
async def test_update_streak_consecutive_days(db_session):
    """Test updating streak on consecutive days."""
    user_repo = UserRepository(db_session)

    # Create a user with existing streak
    user = await user_repo.create(
        telegram_id=223456,
        username="testuser2",
        first_name="Test",
    )
    yesterday = date.today() - timedelta(days=1)
    user.streak_days = 5
    user.best_streak = 5
    user.last_activity_date = yesterday
    await db_session.commit()

    # Update streak (simulating today's activity)
    update_streak = UpdateStreakUseCase(user_repo)
    new_streak, streak_increased = await update_streak.execute(user_id=user.id)

    assert new_streak == 6
    assert streak_increased is True

    # Verify user was updated
    await db_session.refresh(user)
    assert user.streak_days == 6
    assert user.best_streak == 6
    assert user.last_activity_date == date.today()


@pytest.mark.asyncio
async def test_update_streak_same_day(db_session):
    """Test that updating streak multiple times on the same day doesn't increment."""
    user_repo = UserRepository(db_session)

    # Create a user with activity today
    user = await user_repo.create(
        telegram_id=323456,
        username="testuser3",
        first_name="Test",
    )
    user.streak_days = 5
    user.best_streak = 10
    user.last_activity_date = date.today()
    await db_session.commit()

    # Update streak again (same day)
    update_streak = UpdateStreakUseCase(user_repo)
    new_streak, streak_increased = await update_streak.execute(user_id=user.id)

    assert new_streak == 5
    assert streak_increased is False

    # Verify user streak didn't change
    await db_session.refresh(user)
    assert user.streak_days == 5
    assert user.best_streak == 10  # Should not be updated


@pytest.mark.asyncio
async def test_update_streak_missed_day(db_session):
    """Test that missing a day resets the streak."""
    user_repo = UserRepository(db_session)

    # Create a user with last activity 2 days ago
    user = await user_repo.create(
        telegram_id=423456,
        username="testuser4",
        first_name="Test",
    )
    two_days_ago = date.today() - timedelta(days=2)
    user.streak_days = 10
    user.best_streak = 15
    user.last_activity_date = two_days_ago
    await db_session.commit()

    # Update streak (missed a day, should reset)
    update_streak = UpdateStreakUseCase(user_repo)
    new_streak, streak_increased = await update_streak.execute(user_id=user.id)

    assert new_streak == 1
    assert streak_increased is True

    # Verify streak was reset but best_streak preserved
    await db_session.refresh(user)
    assert user.streak_days == 1
    assert user.best_streak == 15  # Best streak should remain
    assert user.last_activity_date == date.today()


@pytest.mark.asyncio
async def test_update_streak_new_record(db_session):
    """Test that best_streak is updated when current streak exceeds it."""
    user_repo = UserRepository(db_session)

    # Create a user approaching their best streak
    user = await user_repo.create(
        telegram_id=523456,
        username="testuser5",
        first_name="Test",
    )
    yesterday = date.today() - timedelta(days=1)
    user.streak_days = 9
    user.best_streak = 9
    user.last_activity_date = yesterday
    await db_session.commit()

    # Update streak (should set new record)
    update_streak = UpdateStreakUseCase(user_repo)
    new_streak, streak_increased = await update_streak.execute(user_id=user.id)

    assert new_streak == 10
    assert streak_increased is True

    # Verify both current and best were updated
    await db_session.refresh(user)
    assert user.streak_days == 10
    assert user.best_streak == 10  # New record!
    assert user.last_activity_date == date.today()
