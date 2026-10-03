from datetime import date
from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.use_cases.check_achievements import CheckAchievementsUseCase
from application.use_cases.complete_daily_challenge import CompleteDailyChallengeUseCase
from application.use_cases.get_todays_challenge import GetTodaysChallengeUseCase
from application.use_cases.get_user_statistics import GetUserStatisticsUseCase
from application.use_cases.update_streak import UpdateStreakUseCase
from bot.callbacks.daily_challenge import DailyChallengeCallback
from bot.keyboards.daily_challenge import (
    build_challenge_answer_keyboard,
    build_challenge_finished_keyboard,
    build_daily_challenge_menu_keyboard,
)
from bot.keyboards.main_menu import build_main_menu_keyboard
from bot.states.daily_challenge import DailyChallengeStates
from domain.entities.vocabulary_quiz_question import VocabularyQuizQuestion
from domain.services.achievement_service import AchievementService
from domain.services.vocabulary_service import VocabularyService
from domain.services.vocabulary_quiz_service import VocabularyQuizService
from infrastructure.content.json_content_loader import JsonContentLoader
from infrastructure.database.repositories import (
    AchievementRepository,
    AttemptRepository,
    DailyChallengeRepository,
    UserRepository,
)


router = Router(name="daily_challenge")


@router.message(Command("daily"))
@router.message(F.text == "🎯 Daily Challenge")
async def show_daily_challenge(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await state.clear()
    telegram_user = message.from_user
    if telegram_user is None:
        return

    async with session_factory() as session:
        user_repository = UserRepository(session)
        user = await user_repository.get_by_telegram_id(telegram_user.id)

        if user is None:
            await message.answer(
                text="Please send /start to create your profile first.",
                reply_markup=build_main_menu_keyboard(),
            )
            return

        # Load content
        vocabulary_words = await JsonContentLoader().load_vocabulary()
        reading_passages = await JsonContentLoader().load_reading_passages()

        # Get or create today's challenge
        get_challenge_use_case = GetTodaysChallengeUseCase(
            DailyChallengeRepository(session),
            user_repository,
            vocabulary_words,
            reading_passages,
        )

        try:
            challenge = await get_challenge_use_case.execute(telegram_user.id)
            await session.commit()
        except ValueError as error:
            await message.answer(text=str(error))
            return

    # Format and display challenge
    challenge_text = _format_daily_challenge(challenge)

    await message.answer(
        text=challenge_text,
        reply_markup=build_daily_challenge_menu_keyboard(challenge.completed),
    )


@router.callback_query(DailyChallengeCallback.filter(F.action == "start"))
async def start_daily_challenge(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    try:
        await callback.answer()
    except Exception:
        pass

    telegram_user = callback.from_user
    if telegram_user is None or callback.message is None:
        return

    async with session_factory() as session:
        user_repository = UserRepository(session)
        user = await user_repository.get_by_telegram_id(telegram_user.id)

        if user is None:
            await callback.answer(text="Please send /start first.", show_alert=True)
            return

        # Get today's challenge
        challenge_repo = DailyChallengeRepository(session)
        today = date.today()
        challenge = await challenge_repo.get_challenge_for_date(user.id, today)

        if challenge is None:
            await callback.answer(text="No challenge found for today.", show_alert=True)
            return

        if challenge.completed:
            await callback.answer(
                text="You've already completed today's challenge!",
                show_alert=True,
            )
            return

        # Load content based on challenge type
        if challenge.challenge_type == "vocabulary_quiz":
            words = await JsonContentLoader().load_vocabulary()
            await _start_vocabulary_challenge(
                callback, state, session_factory, user.id, words, challenge.content_id
            )
        elif challenge.challenge_type == "reading_passage":
            passages = await JsonContentLoader().load_reading_passages()
            await _start_reading_challenge(
                callback, state, session_factory, user.id, passages, challenge.content_id
            )

        await session.commit()


async def _start_vocabulary_challenge(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    user_id: int,
    words: list,
    content_id: str,
) -> None:
    """Start a vocabulary challenge (5 questions)."""
    # Generate 5 deterministic questions from vocabulary based on today's date
    import random
    today = date.today()
    days_since_epoch = (today - date(2024, 1, 1)).days
    randomizer = random.Random(days_since_epoch)

    vocabulary_service = VocabularyService(words)
    quiz_service = VocabularyQuizService(vocabulary_service, randomizer=randomizer)
    questions = quiz_service.generate_quiz(5)

    await state.clear()
    await state.set_state(DailyChallengeStates.in_quiz)
    await state.update_data(
        user_id=user_id,
        challenge_type="vocabulary_quiz",
        questions=[q.to_state_dict() for q in questions],
        current_index=0,
        score=0,
    )

    first_question = questions[0]
    if callback.message is not None:
        await callback.message.edit_text(
            text=_format_quiz_question(first_question, question_number=1, total_questions=5),
            reply_markup=build_challenge_answer_keyboard(first_question.options),
        )


async def _start_reading_challenge(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    user_id: int,
    passages: list,
    content_id: str,
) -> None:
    """Start a reading challenge."""
    # Find the passage by ID
    passage = next((p for p in passages if p.id == content_id), None)

    if passage is None:
        await callback.answer(text="Reading passage not found.", show_alert=True)
        return

    await state.clear()
    await state.set_state(DailyChallengeStates.in_quiz)
    await state.update_data(
        user_id=user_id,
        challenge_type="reading_passage",
        passage=passage.to_state_dict(),
        current_index=0,
        score=0,
    )

    if callback.message is not None:
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="▶️ Start Test",
                        callback_data=DailyChallengeCallback(
                            action="start_reading_quiz"
                        ).pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Back",
                        callback_data=DailyChallengeCallback(action="back").pack(),
                    )
                ],
            ]
        )
        await callback.message.edit_text(
            text=_format_reading_passage(passage),
            reply_markup=keyboard,
        )


@router.callback_query(
    DailyChallengeCallback.filter(F.action == "start_reading_quiz"),
    DailyChallengeStates.in_quiz,
)
async def start_reading_quiz_questions(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.message is None:
        return

    state_data = await state.get_data()
    passage_data = state_data.get("passage")
    if not passage_data:
        await callback.answer("Session expired. Please restart the challenge.", show_alert=True)
        return

    from domain.entities.reading_passage import ReadingPassage
    passage = ReadingPassage.from_state_dict(passage_data)
    first_question = passage.questions[0]
    total_questions = len(passage.questions)

    await callback.message.edit_text(
        text=_format_reading_question(
            first_question,
            question_number=1,
            total_questions=total_questions,
        ),
        reply_markup=build_challenge_answer_keyboard(first_question.options),
    )
    await callback.answer()


@router.callback_query(
    DailyChallengeCallback.filter(F.action == "answer"),
    DailyChallengeStates.in_quiz,
)
async def handle_challenge_answer(
    callback: CallbackQuery,
    callback_data: DailyChallengeCallback,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    telegram_user = callback.from_user
    if telegram_user is None or callback.message is None:
        return

    state_data = await state.get_data()
    challenge_type = state_data.get("challenge_type")
    current_index = state_data.get("current_index", 0)
    score = state_data.get("score", 0)
    user_id = state_data.get("user_id")

    selected_index = int(callback_data.data)

    if challenge_type == "vocabulary_quiz":
        await _handle_vocabulary_answer(
            callback, state, session_factory, selected_index, state_data
        )
    elif challenge_type == "reading_passage":
        await _handle_reading_answer(
            callback, state, session_factory, selected_index, state_data
        )


async def _handle_vocabulary_answer(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    selected_index: int,
    state_data: dict,
) -> None:
    """Handle vocabulary quiz answer."""
    telegram_user = callback.from_user
    if telegram_user is None or callback.message is None:
        return

    questions_data = state_data.get("questions", [])
    current_index = state_data.get("current_index", 0)
    score = state_data.get("score", 0)
    user_id = state_data.get("user_id")

    question = VocabularyQuizQuestion.from_state_dict(questions_data[current_index])
    is_correct = selected_index == question.correct_index

    if is_correct:
        score += 1

    # Record attempt
    async with session_factory() as session:
        attempt_repo = AttemptRepository(session)
        await attempt_repo.create(
            user_id=user_id,
            content_type="daily_challenge_vocab",
            content_id=question.word.id,
            is_correct=is_correct,
        )
        await session.commit()

    feedback = "✅ Correct!" if is_correct else f"❌ Wrong. Correct: {question.options[question.correct_index]}"
    await callback.answer(text=feedback, show_alert=True)

    total_questions = len(questions_data)
    is_last_question = current_index + 1 >= total_questions

    if is_last_question:
        await _finish_challenge(callback, state, session_factory, score, total_questions)
        return

    # Next question
    next_index = current_index + 1
    next_question = VocabularyQuizQuestion.from_state_dict(questions_data[next_index])

    await state.update_data(current_index=next_index, score=score)
    await callback.message.edit_text(
        text=_format_quiz_question(
            next_question,
            question_number=next_index + 1,
            total_questions=total_questions,
        ),
        reply_markup=build_challenge_answer_keyboard(next_question.options),
    )


async def _handle_reading_answer(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    selected_index: int,
    state_data: dict,
) -> None:
    """Handle reading quiz answer."""
    telegram_user = callback.from_user
    if telegram_user is None or callback.message is None:
        return

    from domain.entities.reading_passage import ReadingPassage

    passage_data = state_data.get("passage", {})
    current_index = state_data.get("current_index", 0)
    score = state_data.get("score", 0)
    user_id = state_data.get("user_id")

    passage = ReadingPassage.from_state_dict(passage_data)
    question = passage.questions[current_index]

    is_correct = selected_index == question.correct_index

    if is_correct:
        score += 1

    # Record attempt
    async with session_factory() as session:
        attempt_repo = AttemptRepository(session)
        await attempt_repo.create(
            user_id=user_id,
            content_type="daily_challenge_reading",
            content_id=question.id,
            is_correct=is_correct,
        )
        await session.commit()

    feedback = "✅ Correct!" if is_correct else f"❌ Wrong. Correct: {question.options[question.correct_index]}"
    await callback.answer(text=feedback, show_alert=True)

    total_questions = len(passage.questions)
    is_last_question = current_index + 1 >= total_questions

    if is_last_question:
        await _finish_challenge(callback, state, session_factory, score, total_questions)
        return

    # Next question
    next_index = current_index + 1
    next_question = passage.questions[next_index]

    await state.update_data(current_index=next_index, score=score)
    await callback.message.edit_text(
        text=_format_reading_question(
            next_question,
            question_number=next_index + 1,
            total_questions=total_questions,
        ),
        reply_markup=build_challenge_answer_keyboard(next_question.options),
    )


async def _finish_challenge(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    score: int,
    total_questions: int,
) -> None:
    """Finish the daily challenge and show results."""
    telegram_user = callback.from_user
    if telegram_user is None or callback.message is None:
        return

    # Complete the challenge
    newly_unlocked = []
    streak_increased = False
    new_streak = 0
    reward_points = 0

    async with session_factory() as session:
        # Complete challenge
        complete_use_case = CompleteDailyChallengeUseCase(
            DailyChallengeRepository(session),
            UserRepository(session),
        )

        try:
            reward_points = await complete_use_case.execute(
                telegram_user.id, score, total_questions
            )
        except ValueError as error:
            await callback.answer(text=str(error), show_alert=True)
            return

        # Update streak
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_user.id)
        if user:
            update_streak = UpdateStreakUseCase(user_repo)
            new_streak, streak_increased = await update_streak.execute(user.id)

            # Check achievements
            get_statistics = GetUserStatisticsUseCase(user_repo, AttemptRepository(session))
            statistics = await get_statistics.execute(telegram_user.id)

            achievements = await JsonContentLoader().load_achievements()
            achievement_service = AchievementService(achievements)
            check_achievements = CheckAchievementsUseCase(
                achievement_service,
                AchievementRepository(session),
            )

            newly_unlocked = await check_achievements.execute(
                user_id=user.id,
                statistics=statistics,
                test_completed=True,
                test_score=score,
                test_total=total_questions,
                test_type="daily_challenge",
            )

        await session.commit()

    await state.set_state(DailyChallengeStates.quiz_finished)
    result_text = _format_challenge_results(score, total_questions, reward_points)

    if streak_increased:
        result_text += f"\n\n🔥 <b>Streak increased!</b> {new_streak} days in a row!"
    else:
        result_text += f"\n\n🔥 Your current streak: {new_streak} days"

    if newly_unlocked:
        result_text += "\n\n" + _format_achievements_unlocked(newly_unlocked)

    await callback.message.edit_text(
        text=result_text,
        reply_markup=build_challenge_finished_keyboard(),
    )


@router.callback_query(DailyChallengeCallback.filter(F.action == "back"))
async def back_to_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()

    if callback.message is not None:
        await callback.message.answer(
            text="Back to the main menu.",
            reply_markup=build_main_menu_keyboard(),
        )
        await callback.message.delete()

    await callback.answer()


@router.callback_query(DailyChallengeCallback.filter(F.action == "completed"))
async def already_completed(callback: CallbackQuery) -> None:
    await callback.answer(
        text="You've already completed today's challenge! Come back tomorrow for a new one.",
        show_alert=True,
    )


def _format_daily_challenge(challenge) -> str:
    """Format daily challenge information."""
    status_emoji = "✅" if challenge.completed else "🎯"
    challenge_type_text = (
        "📚 Vocabulary Quiz"
        if challenge.challenge_type == "vocabulary_quiz"
        else "📖 Reading Comprehension"
    )

    text = f"{status_emoji} <b>Daily Challenge</b>\n\n"
    text += f"<b>Today's Challenge:</b> {challenge_type_text}\n"
    text += f"<b>Date:</b> {challenge.challenge_date.strftime('%B %d, %Y')}\n\n"

    if challenge.completed:
        text += f"<b>Status:</b> ✅ Completed\n"
        text += f"<b>Score:</b> {challenge.score}/{challenge.total_questions}\n"
        percentage = round((challenge.score / challenge.total_questions) * 100) if challenge.total_questions else 0
        text += f"<b>Accuracy:</b> {percentage}%\n\n"
        text += "Come back tomorrow for a new challenge!"
    else:
        text += "<b>Status:</b> ⏳ Not started\n\n"
        if challenge.challenge_type == "vocabulary_quiz":
            text += "Complete 5 vocabulary questions to earn <b>10 points</b>!\n"
            text += "+5 bonus points for perfect score! 💯"
        else:
            text += "Read a passage and answer 5 questions to earn <b>15 points</b>!\n"
            text += "+5 bonus points for perfect score! 💯"

    return text


def _format_quiz_question(
    question: VocabularyQuizQuestion,
    *,
    question_number: int,
    total_questions: int,
) -> str:
    """Format vocabulary quiz question."""
    return (
        f"🎯 <b>Daily Challenge</b>\n"
        f"Question {question_number}/{total_questions}\n\n"
        f"<b>What does \"{escape(question.word.word)}\" mean?</b>"
    )


def _format_reading_question(
    question,
    *,
    question_number: int,
    total_questions: int,
) -> str:
    """Format reading quiz question."""
    return (
        f"🎯 <b>Daily Challenge - Reading</b>\n"
        f"Question {question_number}/{total_questions}\n\n"
        f"<b>{escape(question.question)}</b>"
    )


def _format_reading_passage(passage) -> str:
    """Format reading passage."""
    return (
        f"📖 <b>Daily Challenge - Reading</b>\n\n"
        f"<b>{escape(passage.title)}</b>\n\n"
        f"{escape(passage.text)}\n\n"
        f"<i>Read the passage and click <b>Start Test</b> to answer the {len(passage.questions)} questions.</i>"
    )


def _format_challenge_results(score: int, total_questions: int, reward_points: int) -> str:
    """Format challenge completion results."""
    percentage = round((score / total_questions) * 100) if total_questions else 0
    return (
        "🎉 <b>Daily Challenge Complete!</b>\n\n"
        f"Your score: <b>{score}/{total_questions}</b> ({percentage}%)\n"
        f"Points earned: <b>+{reward_points}</b> 🏆\n\n"
        "Great job! Come back tomorrow for a new challenge."
    )


def _format_achievements_unlocked(achievements: list) -> str:
    """Format newly unlocked achievements."""
    if not achievements:
        return ""

    achievement_lines = []
    for achievement in achievements:
        achievement_lines.append(
            f"{achievement.emoji} <b>{achievement.title}</b>\n"
            f"   {achievement.description}"
        )

    return "🎉 <b>New Achievements Unlocked!</b>\n\n" + "\n\n".join(achievement_lines)
