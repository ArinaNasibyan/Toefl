import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.database.repositories import UserRepository, AttemptRepository


@pytest.mark.asyncio
async def test_attempt_repository_count(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    attempt_repo = AttemptRepository(db_session)
    
    # Create user first
    user = await user_repo.create(
        telegram_id=98765,
        username="jane_doe",
        first_name="Jane",
    )
    await db_session.commit()
    
    # Count should be 0 initially
    count = await attempt_repo.count_by_user_id(user.id)
    assert count == 0
    
    # Record attempt 1
    await attempt_repo.create(
        user_id=user.id,
        content_type="vocabulary_mini_test",
        content_id="vocab_001",
        is_correct=True,
    )
    
    # Record attempt 2
    await attempt_repo.create(
        user_id=user.id,
        content_type="vocabulary_mini_test",
        content_id="vocab_002",
        is_correct=False,
    )
    
    await db_session.commit()
    
    # Count should be 2 now
    count = await attempt_repo.count_by_user_id(user.id)
    assert count == 2
