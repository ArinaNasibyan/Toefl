import pytest
from unittest.mock import AsyncMock, MagicMock
from domain.entities.user_statistics import UserStatistics
from application.use_cases.get_user_statistics import GetUserStatisticsUseCase
from infrastructure.database.models import User, Attempt
from infrastructure.database.repositories import UserRepository, AttemptRepository


def test_user_statistics_from_user_data_calculation() -> None:
    # Test accuracy calculations
    stats = UserStatistics.from_user_data(
        completed_tasks=5,
        correct_answers=10,
        total_attempts=20,
        current_streak=3,
        best_streak=5,
        words_learned=12,
    )
    
    assert stats.completed_tasks == 5
    assert stats.correct_answers == 10
    assert stats.accuracy_percentage == 50  # 10 / 20 * 100
    assert stats.current_streak == 3
    assert stats.best_streak == 5
    assert stats.words_learned == 12


def test_user_statistics_zero_attempts() -> None:
    # Test accuracy when total_attempts is 0 (should be 0, not division by zero)
    stats = UserStatistics.from_user_data(
        completed_tasks=0,
        correct_answers=0,
        total_attempts=0,
        current_streak=0,
        best_streak=0,
        words_learned=0,
    )
    assert stats.accuracy_percentage == 0


@pytest.mark.asyncio
async def test_get_user_statistics_use_case_success() -> None:
    # Mock UserRepository and AttemptRepository
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_attempt_repo = MagicMock(spec=AttemptRepository)
    
    test_user = User(
        id=42,
        telegram_id=12345678,
        username="test_user",
        first_name="Test",
        completed_tasks=10,
        correct_answers=8,
        streak_days=3,
        best_streak=5,
        words_learned=15,
    )
    
    mock_user_repo.get_by_telegram_id = AsyncMock(return_value=test_user)
    mock_attempt_repo.count_by_user_id = AsyncMock(return_value=12)
    
    use_case = GetUserStatisticsUseCase(
        user_repository=mock_user_repo,
        attempt_repository=mock_attempt_repo,
    )
    
    stats = await use_case.execute(12345678)
    
    mock_user_repo.get_by_telegram_id.assert_called_once_with(12345678)
    mock_attempt_repo.count_by_user_id.assert_called_once_with(42)
    
    assert stats.completed_tasks == 10
    assert stats.correct_answers == 8
    assert stats.accuracy_percentage == 67  # round(8 / 12 * 100) = 67
    assert stats.current_streak == 3
    assert stats.best_streak == 5
    assert stats.words_learned == 15


@pytest.mark.asyncio
async def test_get_user_statistics_use_case_user_not_found() -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_attempt_repo = MagicMock(spec=AttemptRepository)
    
    mock_user_repo.get_by_telegram_id = AsyncMock(return_value=None)
    
    use_case = GetUserStatisticsUseCase(
        user_repository=mock_user_repo,
        attempt_repository=mock_attempt_repo,
    )
    
    with pytest.raises(ValueError, match="User not found"):
        await use_case.execute(999)
