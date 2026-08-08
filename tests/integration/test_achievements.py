import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.use_cases.check_achievements import CheckAchievementsUseCase
from domain.entities.achievement import Achievement
from domain.entities.user_statistics import UserStatistics
from domain.services.achievement_service import AchievementService
from infrastructure.database.repositories import AchievementRepository, UserRepository


@pytest.mark.asyncio
async def test_achievement_unlock_integration(db_session: AsyncSession):
    """Test full achievement unlock flow with database."""
    # Create a test user
    user_repo = UserRepository(db_session)
    user = await user_repo.create(
        telegram_id=999999,
        username="test_achiever",
        first_name="Test",
    )
    await db_session.commit()

    # Create achievement definitions
    achievements = [
        Achievement(
            id="first_test",
            title="First Steps",
            description="Complete your first test",
            emoji="🎯",
            category="milestone",
            requirement_type="completed_tasks",
            requirement_value=1,
        ),
        Achievement(
            id="perfect_score",
            title="Perfectionist",
            description="Score 100% on any test",
            emoji="💯",
            category="skill",
            requirement_type="perfect_test",
            requirement_value=1,
        ),
    ]

    # Create services and use case
    achievement_service = AchievementService(achievements)
    achievement_repo = AchievementRepository(db_session)
    check_achievements = CheckAchievementsUseCase(
        achievement_service, achievement_repo
    )

    # User completes first test with perfect score
    statistics = UserStatistics(
        completed_tasks=1,
        correct_answers=5,
        accuracy_percentage=100,
        current_streak=0,
        best_streak=0,
        words_learned=0,
    )

    # Check and unlock achievements
    newly_unlocked = await check_achievements.execute(
        user_id=user.id,
        statistics=statistics,
        test_completed=True,
        test_score=5,
        test_total=5,
    )
    await db_session.commit()

    # Verify both achievements were unlocked
    assert len(newly_unlocked) == 2
    achievement_ids = {ach.id for ach in newly_unlocked}
    assert "first_test" in achievement_ids
    assert "perfect_score" in achievement_ids

    # Verify achievements are in database
    unlocked_ids = await achievement_repo.get_unlocked_achievement_ids(user.id)
    assert "first_test" in unlocked_ids
    assert "perfect_score" in unlocked_ids

    # Run check again - should return empty (already unlocked)
    newly_unlocked_again = await check_achievements.execute(
        user_id=user.id,
        statistics=statistics,
        test_completed=True,
        test_score=5,
        test_total=5,
    )
    assert len(newly_unlocked_again) == 0
