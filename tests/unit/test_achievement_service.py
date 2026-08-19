import pytest

from domain.entities.achievement import Achievement
from domain.entities.user_statistics import UserStatistics
from domain.services.achievement_service import AchievementService


@pytest.fixture
def sample_achievements() -> list[Achievement]:
    return [
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
            id="vocabulary_rookie",
            title="Vocabulary Rookie",
            description="Complete 5 vocabulary mini tests",
            emoji="📚",
            category="vocabulary",
            requirement_type="vocabulary_tests_completed",
            requirement_value=5,
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
        Achievement(
            id="accurate_shooter",
            title="Sharp Shooter",
            description="Achieve 80% accuracy overall",
            emoji="🎯",
            category="skill",
            requirement_type="accuracy_percentage",
            requirement_value=80,
        ),
    ]


@pytest.fixture
def achievement_service(sample_achievements: list[Achievement]) -> AchievementService:
    return AchievementService(sample_achievements)


def test_check_completed_tasks_achievement(achievement_service: AchievementService):
    statistics = UserStatistics(
        completed_tasks=1,
        correct_answers=5,
        accuracy_percentage=80,
        current_streak=0,
        best_streak=0,
        words_learned=0,
    )

    unlockable = achievement_service.check_unlockable_achievements(
        statistics=statistics,
        unlocked_achievement_ids=set(),
    )

    assert len(unlockable) == 2  # first_test and accurate_shooter
    achievement_ids = {ach.id for ach in unlockable}
    assert "first_test" in achievement_ids
    assert "accurate_shooter" in achievement_ids


def test_check_vocabulary_tests_achievement(achievement_service: AchievementService):
    statistics = UserStatistics(
        completed_tasks=5,
        correct_answers=20,
        accuracy_percentage=80,
        current_streak=0,
        best_streak=0,
        words_learned=0,
        vocabulary_tests_completed=5,
    )

    unlockable = achievement_service.check_unlockable_achievements(
        statistics=statistics,
        unlocked_achievement_ids=set(),
    )

    achievement_ids = {ach.id for ach in unlockable}
    assert "vocabulary_rookie" in achievement_ids


def test_check_perfect_test_achievement(achievement_service: AchievementService):
    statistics = UserStatistics(
        completed_tasks=1,
        correct_answers=5,
        accuracy_percentage=100,
        current_streak=0,
        best_streak=0,
        words_learned=0,
    )

    unlockable = achievement_service.check_unlockable_achievements(
        statistics=statistics,
        unlocked_achievement_ids=set(),
        test_completed=True,
        test_score=5,
        test_total=5,
    )

    achievement_ids = {ach.id for ach in unlockable}
    assert "perfect_score" in achievement_ids


def test_perfect_test_not_achieved_when_not_perfect(
    achievement_service: AchievementService,
):
    statistics = UserStatistics(
        completed_tasks=1,
        correct_answers=4,
        accuracy_percentage=80,
        current_streak=0,
        best_streak=0,
        words_learned=0,
    )

    unlockable = achievement_service.check_unlockable_achievements(
        statistics=statistics,
        unlocked_achievement_ids=set(),
        test_completed=True,
        test_score=4,
        test_total=5,
    )

    achievement_ids = {ach.id for ach in unlockable}
    assert "perfect_score" not in achievement_ids


def test_already_unlocked_achievements_not_returned(
    achievement_service: AchievementService,
):
    statistics = UserStatistics(
        completed_tasks=1,
        correct_answers=5,
        accuracy_percentage=80,
        current_streak=0,
        best_streak=0,
        words_learned=0,
    )

    unlockable = achievement_service.check_unlockable_achievements(
        statistics=statistics,
        unlocked_achievement_ids={"first_test"},
    )

    achievement_ids = {ach.id for ach in unlockable}
    assert "first_test" not in achievement_ids
    assert "accurate_shooter" in achievement_ids


def test_no_achievements_when_requirements_not_met(
    achievement_service: AchievementService,
):
    statistics = UserStatistics(
        completed_tasks=0,
        correct_answers=0,
        accuracy_percentage=0,
        current_streak=0,
        best_streak=0,
        words_learned=0,
    )

    unlockable = achievement_service.check_unlockable_achievements(
        statistics=statistics,
        unlocked_achievement_ids=set(),
    )

    assert len(unlockable) == 0
