import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.use_cases.register_user import RegisterUserUseCase, TelegramUserData
from application.use_cases.get_user_statistics import GetUserStatisticsUseCase
from application.use_cases.start_vocabulary_mini_test import StartVocabularyMiniTestUseCase
from application.use_cases.submit_vocabulary_answer import SubmitVocabularyAnswerUseCase
from domain.entities.vocabulary_word import VocabularyWord
from infrastructure.database.repositories import UserRepository, AttemptRepository, VocabularyProgressRepository


@pytest.mark.asyncio
async def test_end_to_end_use_cases(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    attempt_repo = AttemptRepository(db_session)
    progress_repo = VocabularyProgressRepository(db_session)
    
    # 1. Register User
    register_use_case = RegisterUserUseCase(user_repo)
    user_data = TelegramUserData(
        telegram_id=55555,
        username="test_e2e",
        first_name="E2E Test",
    )
    user = await register_use_case.execute(user_data)
    await db_session.commit()
    
    assert user.id is not None
    assert user.telegram_id == 55555
    assert user.completed_tasks == 0
    assert user.correct_answers == 0
    
    # 2. Start Mini Test
    words = [
        VocabularyWord(id="v1", word="abundant", translation="plentiful", transcription="/t/", example="ex", level="B2"),
        VocabularyWord(id="v2", word="acquire", translation="obtain", transcription="/t/", example="ex", level="B1"),
        VocabularyWord(id="v3", word="adapt", translation="adjust", transcription="/t/", example="ex", level="B1"),
        VocabularyWord(id="v4", word="adequate", translation="sufficient", transcription="/t/", example="ex", level="B2"),
        VocabularyWord(id="v5", word="advocate", translation="support", transcription="/t/", example="ex", level="C1"),
    ]
    
    start_test_use_case = StartVocabularyMiniTestUseCase(words, question_count=3)
    questions = start_test_use_case.execute()
    
    assert len(questions) == 3
    for q in questions:
        assert len(q.options) == 4
        assert q.correct_index in (0, 1, 2, 3)
        assert q.options[q.correct_index] == q.word.translation
        
    # 3. Submit Answers
    submit_use_case = SubmitVocabularyAnswerUseCase(attempt_repo, user_repo, progress_repo)
    
    # Submit first answer (correct)
    ans1 = await submit_use_case.execute(
        user_id=user.id,
        word_id=questions[0].word.id,
        is_correct=True,
        finish_quiz=False,
    )
    assert ans1 is True
    
    # Verify repetitions = 1 for questions[0].word.id
    progress1 = await progress_repo.get_by_user_and_word(user.id, questions[0].word.id)
    assert progress1 is not None
    assert progress1.repetitions == 1
    assert progress1.mastered is False
    
    # Submit second answer (incorrect)
    ans2 = await submit_use_case.execute(
        user_id=user.id,
        word_id=questions[1].word.id,
        is_correct=False,
        finish_quiz=False,
    )
    assert ans2 is False
    
    # Verify repetitions = 0 for questions[1].word.id
    progress2 = await progress_repo.get_by_user_and_word(user.id, questions[1].word.id)
    assert progress2 is not None
    assert progress2.repetitions == 0
    assert progress2.mastered is False
    
    # Submit third answer (correct and finishes quiz)
    ans3 = await submit_use_case.execute(
        user_id=user.id,
        word_id=questions[2].word.id,
        is_correct=True,
        finish_quiz=True,
    )
    assert ans3 is True
    
    # Verify repetitions = 1 for questions[2].word.id
    progress3 = await progress_repo.get_by_user_and_word(user.id, questions[2].word.id)
    assert progress3 is not None
    assert progress3.repetitions == 1
    
    # Let's perform 2 more correct answers for questions[2].word.id to reach 3 repetitions and master it
    await submit_use_case.execute(
        user_id=user.id,
        word_id=questions[2].word.id,
        is_correct=True,
        finish_quiz=False,
    )
    await submit_use_case.execute(
        user_id=user.id,
        word_id=questions[2].word.id,
        is_correct=True,
        finish_quiz=False,
    )
    
    # Verify it is now mastered!
    await db_session.refresh(progress3)
    assert progress3.repetitions == 3
    assert progress3.mastered is True
    
    await db_session.commit()
    
    # Refresh user to verify updates
    await db_session.refresh(user)
    assert user.completed_tasks == 1  # Incremented because finish_quiz=True
    assert user.correct_answers == 4  # ans1 + ans3 + 2 extra correct reviews = 4
    assert user.words_learned == 1  # mastered 1 word!
    
    # 4. Get Statistics
    get_stats_use_case = GetUserStatisticsUseCase(user_repo, attempt_repo)
    stats = await get_stats_use_case.execute(telegram_id=55555)
    
    assert stats.completed_tasks == 1
    assert stats.correct_answers == 4
    assert stats.words_learned == 1

