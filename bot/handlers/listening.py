from html import escape
from pathlib import Path
import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.use_cases.check_achievements import CheckAchievementsUseCase
from application.use_cases.get_user_statistics import GetUserStatisticsUseCase
from application.use_cases.listening_practice import (
    StartListeningPracticeUseCase,
    SubmitListeningAnswerUseCase,
)
from application.use_cases.update_streak import UpdateStreakUseCase
from bot.callbacks.listening import ListeningCallback
from bot.keyboards.main_menu import build_main_menu_keyboard
from bot.keyboards.listening import (
    build_listening_finished_keyboard,
    build_listening_question_keyboard,
    build_listening_start_keyboard,
    build_listening_feedback_keyboard,
)
from bot.states.listening import ListeningStates
from domain.entities.listening_question import ListeningQuestion
from domain.entities.listening_passage import ListeningPassage
from domain.services.achievement_service import AchievementService
from infrastructure.content.json_content_loader import JsonContentLoader
from infrastructure.database.repositories import AttemptRepository, UserRepository, AchievementRepository


logger = logging.getLogger(__name__)

router = Router(name="listening")

# Caches Telegram's file_id for sent MP3s to avoid re-uploading on subsequent requests
_audio_file_id_cache: dict[str, str] = {}


@router.message(Command("listening"))
@router.message(F.text == "🎧 Listening")
@router.message(F.text == "🎧 Listening Practice")
async def show_listening_passage(message: Message, state: FSMContext) -> None:
    await state.clear()
    passages = await JsonContentLoader().load_listening_passages()

    if not passages:
        await message.answer(
            text="No listening passages available at the moment.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    try:
        use_case = StartListeningPracticeUseCase(passages)
        passage = use_case.execute()
    except ValueError as error:
        await message.answer(
            text=str(error),
            reply_markup=build_main_menu_keyboard(),
        )
        return

    await state.set_state(ListeningStates.listening_audio)
    await state.update_data(passage=passage.to_state_dict())

    # Build file path to the audio file
    audio_path = Path("data") / passage.audio_file
    
    caption_text = _format_listening_passage(passage)
    keyboard = build_listening_start_keyboard()

    file_id = _audio_file_id_cache.get(passage.id)
    try:
        if file_id:
            # Send using cached file_id (near instant)
            await message.answer_audio(
                audio=file_id,
                caption=caption_text,
                reply_markup=keyboard,
            )
        else:
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found at: {audio_path}")
            
            # Send by uploading the file
            audio_file = FSInputFile(str(audio_path), filename=f"{passage.id}.mp3")
            sent_msg = await message.answer_audio(
                audio=audio_file,
                caption=caption_text,
                reply_markup=keyboard,
            )
            if sent_msg.audio:
                _audio_file_id_cache[passage.id] = sent_msg.audio.file_id
    except Exception as e:
        logger.exception("Error sending listening audio")
        await message.answer(
            text=f"Error loading listening passage: {e}\nPlease make sure data files are generated.",
            reply_markup=build_main_menu_keyboard()
        )


@router.callback_query(ListeningCallback.filter(F.action == "next_passage"))
async def show_next_listening_passage(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.answer()
    except Exception:
        pass
    
    await state.clear()
    passages = await JsonContentLoader().load_listening_passages()

    if not passages:
        await callback.answer(
            text="No listening passages available.",
            show_alert=True,
        )
        return

    try:
        use_case = StartListeningPracticeUseCase(passages)
        passage = use_case.execute()
    except ValueError as error:
        await callback.answer(text=str(error), show_alert=True)
        return

    await state.set_state(ListeningStates.listening_audio)
    await state.update_data(passage=passage.to_state_dict())

    audio_path = Path("data") / passage.audio_file
    caption_text = _format_listening_passage(passage)
    keyboard = build_listening_start_keyboard()

    if callback.message is not None:
        # Delete previous audio card to avoid clutter
        try:
            await callback.message.delete()
        except Exception:
            pass

        file_id = _audio_file_id_cache.get(passage.id)
        try:
            if file_id:
                await callback.message.answer_audio(
                    audio=file_id,
                    caption=caption_text,
                    reply_markup=keyboard,
                )
            else:
                if not audio_path.exists():
                    raise FileNotFoundError(f"Audio file not found at: {audio_path}")
                
                audio_file = FSInputFile(str(audio_path), filename=f"{passage.id}.mp3")
                sent_msg = await callback.message.answer_audio(
                    audio=audio_file,
                    caption=caption_text,
                    reply_markup=keyboard,
                )
                if sent_msg.audio:
                    _audio_file_id_cache[passage.id] = sent_msg.audio.file_id
        except Exception as e:
            logger.exception("Error sending next listening audio")
            await callback.message.answer(
                text=f"Error loading listening passage: {e}",
                reply_markup=build_main_menu_keyboard()
            )


@router.callback_query(
    ListeningCallback.filter(F.action == "start_test"),
    StateFilter(ListeningStates.listening_audio),
)
async def start_listening_test(
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

    data = await state.get_data()
    passage_data = data.get("passage")

    if not passage_data:
        await callback.answer(
            text="Session expired. Please select a listening passage again.",
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

    passage = ListeningPassage.from_state_dict(passage_data)
    total_questions = len(passage.questions)

    await state.set_state(ListeningStates.answering_questions)
    await state.update_data(
        current_index=0,
        score=0,
        user_id=user_id,
        total_questions=total_questions,
    )

    first_question = passage.questions[0]
    
    # Mechanics "clean chat": editing caption of the same audio message
    await callback.message.edit_caption(
        caption=_format_listening_question(
            first_question,
            question_number=1,
            total_questions=total_questions,
        ),
        reply_markup=build_listening_question_keyboard(first_question.options),
    )


@router.callback_query(
    ListeningCallback.filter(F.action == "answer"),
    StateFilter(ListeningStates.answering_questions),
)
async def submit_listening_answer(
    callback: CallbackQuery,
    callback_data: ListeningCallback,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    telegram_user = callback.from_user
    if telegram_user is None or callback.message is None:
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
            text="This test session has expired. Start a new listening test.",
            show_alert=True,
        )
        return

    passage = ListeningPassage.from_state_dict(passage_data)

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
        submit_answer = SubmitListeningAnswerUseCase(
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

    # Clear loading spinner immediately
    try:
        await callback.answer()
    except Exception:
        pass

    await state.update_data(score=score)

    selected_text = question.options[selected_index]
    correct_text = question.options[question.correct_index]
    result_emoji = "✅" if is_correct else "❌"
    result_text = "Correct!" if is_correct else "Incorrect."

    # Build detailed feedback caption showing the explanation in the message caption
    feedback_caption = (
        "🎧 <b>Listening Comprehension Test</b>\n\n"
        f"<b>Question {current_index + 1} of {total_questions}</b>\n\n"
        f"{escape(question.question)}\n\n"
        f"Your answer: <i>{escape(selected_text)}</i>\n"
        f"{result_emoji} <b>{result_text}</b>\n\n"
        f"<b>Correct Answer:</b> {escape(correct_text)}\n\n"
        f"<b>Explanation:</b>\n{escape(question.explanation)}"
    )

    # Edit caption to show explanation feedback screen
    await callback.message.edit_caption(
        caption=feedback_caption,
        reply_markup=build_listening_feedback_keyboard(is_last_question),
    )


@router.callback_query(
    ListeningCallback.filter(F.action == "next_question"),
    StateFilter(ListeningStates.answering_questions),
)
async def handle_listening_next_question(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    try:
        await callback.answer()
    except Exception:
        pass

    telegram_user = callback.from_user
    if telegram_user is None or callback.message is None:
        return

    data = await state.get_data()
    passage_data = data.get("passage")
    current_index = int(data.get("current_index", 0))
    total_questions = int(data.get("total_questions", 0))

    if not passage_data:
        await state.clear()
        await callback.message.answer(
            text="Session expired. Start a new listening test.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    passage = ListeningPassage.from_state_dict(passage_data)
    next_index = current_index + 1
    next_question = passage.questions[next_index]

    await state.update_data(current_index=next_index)

    await callback.message.edit_caption(
        caption=_format_listening_question(
            next_question,
            question_number=next_index + 1,
            total_questions=total_questions,
        ),
        reply_markup=build_listening_question_keyboard(next_question.options),
    )


@router.callback_query(
    ListeningCallback.filter(F.action == "show_results"),
    StateFilter(ListeningStates.answering_questions),
)
async def handle_listening_show_results(
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

    data = await state.get_data()
    score = int(data.get("score", 0))
    user_id = data.get("user_id")
    total_questions = int(data.get("total_questions", 0))

    if user_id is None:
        await state.clear()
        await callback.message.answer(
            text="Session expired. Start a new listening test.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

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
            test_type="listening_passage",
        )
        await session.commit()

    await state.set_state(ListeningStates.quiz_finished)
    result_text = _format_test_results(score, total_questions)

    # Add streak notification
    if streak_increased:
        result_text += f"\n\n🔥 <b>Streak increased!</b> {new_streak} days in a row!"
    else:
        result_text += f"\n\n🔥 Your current streak: {new_streak} days"

    if newly_unlocked:
        result_text += "\n\n" + _format_achievements_unlocked(newly_unlocked)

    await callback.message.edit_caption(
        caption=result_text,
        reply_markup=build_listening_finished_keyboard(),
    )


@router.callback_query(ListeningCallback.filter(F.action == "back"))
async def back_to_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    try:
        await callback.answer()
    except Exception:
        pass
    
    await state.clear()

    if callback.message is not None:
        await callback.message.answer(
            text="Back to the main menu.",
            reply_markup=build_main_menu_keyboard(),
        )
        # Delete audio card message
        try:
            await callback.message.delete()
        except Exception:
            pass


def _format_listening_passage(passage: ListeningPassage) -> str:
    icon = "🏫" if passage.type == "lecture" else "💬"
    return (
        f"🎧 <b>TOEFL Listening Practice</b>\n\n"
        f"{icon} <b>{escape(passage.title)}</b> ({passage.type.capitalize()})\n\n"
        f"Listen to the audio lecture/conversation carefully, then click <b>Start Questions</b> to test your comprehension."
    )


def _format_listening_question(
    question: ListeningQuestion,
    *,
    question_number: int,
    total_questions: int,
) -> str:
    return (
        "🎧 <b>Listening Comprehension Test</b>\n\n"
        f"<b>Question {question_number} of {total_questions}</b>\n\n"
        f"{escape(question.question)}"
    )


def _format_answer_feedback(question: ListeningQuestion, is_correct: bool) -> str:
    if is_correct:
        return f"✅ Correct!\n\n{question.explanation}"

    correct_answer = question.options[question.correct_index]
    return f"❌ Wrong.\n\nCorrect answer: {correct_answer}\n\n{question.explanation}"


def _format_test_results(score: int, total_questions: int) -> str:
    percentage = round((score / total_questions) * 100) if total_questions else 0

    if percentage >= 80:
        emoji = "🎉"
        message = "Excellent listening skills!"
    elif percentage >= 60:
        emoji = "👍"
        message = "Good job!"
    else:
        emoji = "📚"
        message = "Keep practicing your listening!"

    return (
        f"{emoji} <b>Listening Test Complete</b>\n\n"
        f"Your score: <b>{score}/{total_questions}</b> ({percentage}%)\n\n"
        f"{message}"
    )


def _format_achievements_unlocked(achievements: list) -> str:
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
