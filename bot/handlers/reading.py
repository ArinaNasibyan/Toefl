from html import escape

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.use_cases.check_achievements import CheckAchievementsUseCase
from application.use_cases.get_user_statistics import GetUserStatisticsUseCase
from application.use_cases.reading_practice import (
    StartReadingPracticeUseCase,
    SubmitReadingAnswerUseCase,
)
from application.use_cases.update_streak import UpdateStreakUseCase
from bot.callbacks.reading import ReadingCallback
from bot.keyboards.main_menu import build_main_menu_keyboard
from bot.keyboards.reading import (
    build_reading_finished_keyboard,
    build_reading_question_keyboard,
    build_reading_start_keyboard,
)
from bot.states.reading import ReadingStates
from domain.entities.question import ReadingQuestion
from domain.entities.reading_passage import ReadingPassage
from domain.services.achievement_service import AchievementService
from infrastructure.content.json_content_loader import JsonContentLoader
from infrastructure.database.repositories import AttemptRepository, UserRepository, AchievementRepository


router = Router(name="reading")


@router.message(Command("reading"))
@router.message(F.text == "📖 Reading")
async def show_reading_passage(message: Message, state: FSMContext) -> None:
    await state.clear()
    passages = await JsonContentLoader().load_reading_passages()

    if not passages:
        await message.answer(
            text="No reading passages available at the moment.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    try:
        use_case = StartReadingPracticeUseCase(passages)
        passage = use_case.execute()
    except ValueError as error:
        await message.answer(
            text=str(error),
            reply_markup=build_main_menu_keyboard(),
        )
        return

    await state.set_state(ReadingStates.reading_text)
    await state.update_data(passage=passage.to_state_dict())

    await message.answer(
        text=_format_reading_passage(passage),
        reply_markup=build_reading_start_keyboard(),
    )


@router.callback_query(ReadingCallback.filter(F.action == "next_passage"))
async def show_next_passage(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    passages = await JsonContentLoader().load_reading_passages()

    if not passages:
        await callback.answer(
            text="No reading passages available.",
            show_alert=True,
        )
        return

    try:
        use_case = StartReadingPracticeUseCase(passages)
        passage = use_case.execute()
    except ValueError as error:
        await callback.answer(text=str(error), show_alert=True)
        return

    await state.set_state(ReadingStates.reading_text)
    await state.update_data(passage=passage.to_state_dict())

    if callback.message is not None:
        await callback.message.edit_text(
            text=_format_reading_passage(passage),
            reply_markup=build_reading_start_keyboard(),
        )

    await callback.answer()


@router.callback_query(
    ReadingCallback.filter(F.action == "start_test"),
    StateFilter(ReadingStates.reading_text),
)
async def start_reading_test(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    telegram_user = callback.from_user
    if telegram_user is None or callback.message is None:
        return

    data = await state.get_data()
    passage_data = data.get("passage")

    if not passage_data:
        await callback.answer(
            text="Session expired. Please select a reading passage again.",
            show_alert=True,
        )
        await state.clear()
        return

    async with session_factory() as session:
        user_repository = UserRepository(session)
        user = await user_repository.get_by_telegram_id(telegram_user.id)

        if user is None:
            await callback.answer(
                text="Please send /start before taking the test.",
                show_alert=True,
            )
            return

        user_id = user.id
        await session.commit()

    passage = ReadingPassage.from_state_dict(passage_data)
    total_questions = len(passage.questions)

    await state.set_state(ReadingStates.answering_questions)
    await state.update_data(
        current_index=0,
        score=0,
        user_id=user_id,
        total_questions=total_questions,
    )

    first_question = passage.questions[0]
    await callback.message.edit_text(
        text=_format_reading_question(
            first_question,
            question_number=1,
            total_questions=total_questions,
        ),
        reply_markup=build_reading_question_keyboard(first_question.options),
    )
    await callback.answer()


@router.callback_query(
    ReadingCallback.filter(F.action == "answer"),
    StateFilter(ReadingStates.answering_questions),
)
async def submit_reading_answer(
    callback: CallbackQuery,
    callback_data: ReadingCallback,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        return

    data = await state.get_data()
    passage_data = data.get("passage")
    current_index = int(data.get("current_index", 0))
    score = int(data.get("score", 0))
    user_id = data.get("user_id")
    total_questions = int(data.get("total_questions", 0))

    if not passage_data or user_id is None:
        await state.clear()
        await callback.answer(
            text="This test session has expired. Start a new reading test.",
            show_alert=True,
        )
        return

    passage = ReadingPassage.from_state_dict(passage_data)

    if current_index >= len(passage.questions):
        await callback.answer(
            text="Invalid question index.",
            show_alert=True,
        )
        return

    question = passage.questions[current_index]
    selected_index = callback_data.option_index

    if selected_index < 0 or selected_index >= len(question.options):
        await callback.answer(text="Invalid answer.", show_alert=True)
        return

    is_correct = selected_index == question.correct_index
    if is_correct:
        score += 1

    is_last_question = current_index + 1 >= total_questions

    async with session_factory() as session:
        submit_answer = SubmitReadingAnswerUseCase(
            AttemptRepository(session),
            UserRepository(session),
        )
        await submit_answer.execute(
            user_id=user_id,
            question_id=question.id,
            is_correct=is_correct,
            finish_test=is_last_question,
        )
        await session.commit()

    feedback = _format_answer_feedback(question, is_correct)
    await callback.answer(text=feedback, show_alert=True)

    if is_last_question:
        # Update streak and check for newly unlocked achievements
        newly_unlocked = []
        streak_increased = False
        new_streak = 0

        async with session_factory() as session:
            # Update user's streak
            update_streak = UpdateStreakUseCase(UserRepository(session))
            new_streak, streak_increased = await update_streak.execute(user_id=user_id)

            get_statistics = GetUserStatisticsUseCase(
                UserRepository(session),
                AttemptRepository(session),
            )
            statistics = await get_statistics.execute(telegram_user.id)

            achievements = await JsonContentLoader().load_achievements()
            achievement_service = AchievementService(achievements)
            check_achievements = CheckAchievementsUseCase(
                achievement_service,
                AchievementRepository(session),
            )

            newly_unlocked = await check_achievements.execute(
                user_id=user_id,
                statistics=statistics,
                test_completed=True,
                test_score=score,
                test_total=total_questions,
                test_type="reading_passage",
            )
            await session.commit()

        await state.set_state(ReadingStates.quiz_finished)
        result_text = _format_test_results(score, total_questions)

        # Add streak notification
        if streak_increased:
            result_text += f"\n\n🔥 <b>Streak increased!</b> {new_streak} days in a row!"
        else:
            result_text += f"\n\n🔥 Your current streak: {new_streak} days"

        if newly_unlocked:
            result_text += "\n\n" + _format_achievements_unlocked(newly_unlocked)

        await callback.message.edit_text(
            text=result_text,
            reply_markup=build_reading_finished_keyboard(),
        )
        return

    next_index = current_index + 1
    next_question = passage.questions[next_index]

    await state.update_data(current_index=next_index, score=score)
    await callback.message.edit_text(
        text=_format_reading_question(
            next_question,
            question_number=next_index + 1,
            total_questions=total_questions,
        ),
        reply_markup=build_reading_question_keyboard(next_question.options),
    )


@router.callback_query(ReadingCallback.filter(F.action == "back"))
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


def _format_reading_passage(passage: ReadingPassage) -> str:
    return (
        f"📖 <b>{escape(passage.title)}</b>\n\n"
        f"{escape(passage.text)}\n\n"
        f"<b>Questions:</b> {len(passage.questions)}\n\n"
        "Read the passage carefully, then click <b>Start Test</b> to answer the questions."
    )


def _format_reading_question(
    question: ReadingQuestion,
    *,
    question_number: int,
    total_questions: int,
) -> str:
    return (
        "📝 <b>Reading Comprehension Test</b>\n\n"
        f"<b>Question {question_number} of {total_questions}</b>\n\n"
        f"{escape(question.question)}"
    )


def _format_answer_feedback(question: ReadingQuestion, is_correct: bool) -> str:
    if is_correct:
        return f"✅ Correct!\n\n{question.explanation}"

    correct_answer = question.options[question.correct_index]
    return f"❌ Wrong.\n\nCorrect answer: {correct_answer}\n\n{question.explanation}"


def _format_test_results(score: int, total_questions: int) -> str:
    percentage = round((score / total_questions) * 100) if total_questions else 0

    if percentage >= 80:
        emoji = "🎉"
        message = "Excellent work!"
    elif percentage >= 60:
        emoji = "👍"
        message = "Good job!"
    else:
        emoji = "📚"
        message = "Keep practicing!"

    return (
        f"{emoji} <b>Reading Test Complete</b>\n\n"
        f"Your score: <b>{score}/{total_questions}</b> ({percentage}%)\n\n"
        f"{message}"
    )


def _format_achievements_unlocked(achievements: list) -> str:
    """Format newly unlocked achievements for display."""
    if not achievements:
        return ""

    achievement_lines = []
    for achievement in achievements:
        achievement_lines.append(
            f"{achievement.emoji} <b>{achievement.title}</b>\n"
            f"   {achievement.description}"
        )

    return (
        "🎉 <b>New Achievements Unlocked!</b>\n\n"
        + "\n\n".join(achievement_lines)
    )
