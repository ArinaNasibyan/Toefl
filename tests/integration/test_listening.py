import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.use_cases.register_user import RegisterUserUseCase, TelegramUserData
from application.use_cases.get_user_statistics import GetUserStatisticsUseCase
from application.use_cases.listening_practice import (
    StartListeningPracticeUseCase,
    SubmitListeningAnswerUseCase,
)
from domain.entities.listening_passage import ListeningPassage
from domain.entities.listening_question import ListeningQuestion
from infrastructure.database.repositories import UserRepository, AttemptRepository, AchievementRepository
from infrastructure.content.json_content_loader import JsonContentLoader
from domain.services.achievement_service import AchievementService
from application.use_cases.check_achievements import CheckAchievementsUseCase


@pytest.mark.asyncio
async def test_listening_flow_and_stats(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    attempt_repo = AttemptRepository(db_session)
    achievement_repo = AchievementRepository(db_session)

    # 1. Register User
    register_use_case = RegisterUserUseCase(user_repo)
    user_data = TelegramUserData(
        telegram_id=98765,
        username="listening_user",
        first_name="Listening Learner",
    )
    user = await register_use_case.execute(user_data)
    await db_session.commit()

    # 2. Test Content Loader
    passages = await JsonContentLoader().load_listening_passages()
    assert len(passages) >= 2
    for p in passages:
        assert isinstance(p, ListeningPassage)
        assert len(p.questions) == 4
        for q in p.questions:
            assert isinstance(q, ListeningQuestion)
            assert len(q.options) == 4
            assert q.correct_index in (0, 1, 2, 3)
            assert q.explanation != ""

    # 3. Start Listening Practice Use Case
    start_use_case = StartListeningPracticeUseCase(passages)
    selected_passage = start_use_case.execute()
    assert selected_passage in passages

    # 4. Submit Listening Answers Use Case
    submit_use_case = SubmitListeningAnswerUseCase(attempt_repo, user_repo)
    
    # Submit 3 correct answers, 1 incorrect
    q1 = selected_passage.questions[0]
    res1 = await submit_use_case.execute(
        user_id=user.id,
        question_id=q1.id,
        is_correct=True,
        finish_test=False,
    )
    assert res1 is True

    q2 = selected_passage.questions[1]
    res2 = await submit_use_case.execute(
        user_id=user.id,
        question_id=q2.id,
        is_correct=False,
        finish_test=False,
    )
    assert res2 is False

    q3 = selected_passage.questions[2]
    res3 = await submit_use_case.execute(
        user_id=user.id,
        question_id=q3.id,
        is_correct=True,
        finish_test=False,
    )
    assert res3 is True

    # Last question completes the test
    q4 = selected_passage.questions[3]
    res4 = await submit_use_case.execute(
        user_id=user.id,
        question_id=q4.id,
        is_correct=True,
        finish_test=True,
    )
    assert res4 is True

    await db_session.commit()
    await db_session.refresh(user)

    assert user.completed_tasks == 1
    assert user.correct_answers == 3

    # 5. Get User Statistics and verify listening tests completed
    stats_use_case = GetUserStatisticsUseCase(user_repo, attempt_repo)
    stats = await stats_use_case.execute(telegram_id=98765)
    
    assert stats.completed_tasks == 1
    assert stats.correct_answers == 3
    assert stats.listening_tests_completed == 4
    assert stats.reading_tests_completed == 0

    # 6. Verify Achievements Checking works
    achfile = await JsonContentLoader().load_achievements()
    achievement_service = AchievementService(achfile)
    check_achievements = CheckAchievementsUseCase(
        achievement_service,
        achievement_repo,
    )
    
    newly_unlocked = await check_achievements.execute(
        user_id=user.id,
        statistics=stats,
        test_completed=True,
        test_score=3,
        test_total=4,
        test_type="listening_passage",
    )
    
    # User completed their first test, so the first_test achievement should unlock!
    assert len(newly_unlocked) > 0
    assert any(a.id == "first_test" for a in newly_unlocked)
