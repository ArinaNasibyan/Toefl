import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.database.repositories import UserRepository
from infrastructure.database.models import User


@pytest.mark.asyncio
async def test_user_repository_crud(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    
    # 1. Get by non-existing telegram id
    user = await repo.get_by_telegram_id(99999)
    assert user is None
    
    # 2. Create user
    new_user = await repo.create(
        telegram_id=12345,
        username="john_doe",
        first_name="John",
    )
    await db_session.commit()
    
    assert new_user.id is not None
    assert new_user.telegram_id == 12345
    assert new_user.username == "john_doe"
    assert new_user.first_name == "John"
    
    # 3. Get by existing telegram id
    fetched_user = await repo.get_by_telegram_id(12345)
    assert fetched_user is not None
    assert fetched_user.id == new_user.id
    
    # 4. Update last activity
    old_activity = fetched_user.last_activity
    await repo.update_last_activity(fetched_user)
    await db_session.commit()
    
    # Refresh to see change
    await db_session.refresh(fetched_user)
    assert fetched_user.last_activity >= old_activity
    
    # 5. Increment correct answers
    assert fetched_user.correct_answers == 0
    await repo.increment_correct_answers(fetched_user.id)
    await db_session.commit()
    
    await db_session.refresh(fetched_user)
    assert fetched_user.correct_answers == 1
    
    # 6. Increment completed tasks
    assert fetched_user.completed_tasks == 0
    await repo.increment_completed_tasks(fetched_user.id)
    await db_session.commit()
    
    await db_session.refresh(fetched_user)
    assert fetched_user.completed_tasks == 1
