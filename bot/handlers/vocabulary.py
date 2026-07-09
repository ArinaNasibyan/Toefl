from html import escape

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.use_cases.start_vocabulary_mini_test import (
    DEFAULT_MINI_TEST_QUESTION_COUNT,
    StartVocabularyMiniTestUseCase,
)
from application.use_cases.submit_vocabulary_answer import (
    SubmitVocabularyAnswerUseCase,
)
from bot.callbacks.vocabulary import VocabularyCallback
from bot.keyboards.main_menu import build_main_menu_keyboard
from bot.keyboards.vocabulary import (
    build_quiz_answer_keyboard,
    build_quiz_finished_keyboard,
    build_vocabulary_keyboard,
)
from bot.states.vocabulary import VocabularyMiniTestStates
from domain.entities.vocabulary_quiz_question import VocabularyQuizQuestion
from domain.entities.vocabulary_word import VocabularyWord
from domain.services.vocabulary_service import VocabularyService
from infrastructure.content.json_content_loader import JsonContentLoader
from infrastructure.database.repositories import AttemptRepository, UserRepository


router = Router(name="vocabulary")


@router.message(Command("vocabulary"))
@router.message(F.text == "📚 Vocabulary")
async def show_vocabulary_word(message: Message) -> None:
    word = await _get_random_vocabulary_word()
    await message.answer(
        text=_format_vocabulary_card(word),
        reply_markup=build_vocabulary_keyboard(),
    )


@router.callback_query(VocabularyCallback.filter(F.action == "next"))
async def show_next_vocabulary_word(callback: CallbackQuery) -> None:
    word = await _get_random_vocabulary_word()

    if callback.message is not None:
        await callback.message.edit_text(
            text=_format_vocabulary_card(word),
            reply_markup=build_vocabulary_keyboard(),
        )

    await callback.answer()


@router.callback_query(VocabularyCallback.filter(F.action == "mini_test"))
async def start_vocabulary_mini_test(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    telegram_user = callback.from_user
    if telegram_user is None or callback.message is None:
        return

    words = await JsonContentLoader().load_vocabulary()
    if len(words) < 4:
        await callback.answer(
            text="Not enough vocabulary words for a mini test.",
            show_alert=True,
        )
        return

    try:
        questions = StartVocabularyMiniTestUseCase(words).execute()
    except ValueError as error:
        await callback.answer(text=str(error), show_alert=True)
        return

    async with session_factory() as session:
        user_repository = UserRepository(session)
        user = await user_repository.get_by_telegram_id(telegram_user.id)

        if user is None:
            await callback.answer(
                text="Please send /start before taking the mini test.",
                show_alert=True,
            )
            return

        user_id = user.id
        await session.commit()

    await state.clear()
    await state.set_state(VocabularyMiniTestStates.waiting_for_answer)
    await state.update_data(
        questions=[question.to_state_dict() for question in questions],
        current_index=0,
        score=0,
        user_id=user_id,
        total_questions=len(questions),
    )

    first_question = questions[0]
    total_questions = len(questions)
    await callback.message.edit_text(
        text=_format_quiz_question(
            first_question,
            question_number=1,
            total_questions=total_questions,
        ),
        reply_markup=build_quiz_answer_keyboard(first_question.options),
    )
    await callback.answer()


@router.callback_query(
    VocabularyCallback.filter(F.action == "answer"),
    StateFilter(VocabularyMiniTestStates.waiting_for_answer),
)
async def submit_vocabulary_mini_test_answer(
    callback: CallbackQuery,
    callback_data: VocabularyCallback,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if callback.message is None:
        return

    data = await state.get_data()
    questions_data = data.get("questions", [])
    current_index = int(data.get("current_index", 0))
    score = int(data.get("score", 0))
    user_id = data.get("user_id")
    total_questions = int(data.get("total_questions", DEFAULT_MINI_TEST_QUESTION_COUNT))

    if user_id is None or current_index >= len(questions_data):
        await state.clear()
        await callback.answer(
            text="This quiz session has expired. Start a new mini test.",
            show_alert=True,
        )
        return

    question = VocabularyQuizQuestion.from_state_dict(questions_data[current_index])
    selected_index = callback_data.option_index

    if selected_index < 0 or selected_index >= len(question.options):
        await callback.answer(text="Invalid answer.", show_alert=True)
        return

    is_correct = selected_index == question.correct_index
    if is_correct:
        score += 1

    is_last_question = current_index + 1 >= total_questions

    async with session_factory() as session:
        submit_answer = SubmitVocabularyAnswerUseCase(
            AttemptRepository(session),
            UserRepository(session),
        )
        await submit_answer.execute(
            user_id=user_id,
            word_id=question.word.id,
            is_correct=is_correct,
            finish_quiz=is_last_question,
        )
        await session.commit()

    feedback = _format_answer_feedback(question, is_correct)
    await callback.answer(text=feedback, show_alert=True)

    if is_last_question:
        await state.set_state(VocabularyMiniTestStates.quiz_finished)
        await callback.message.edit_text(
            text=_format_quiz_results(score, total_questions),
            reply_markup=build_quiz_finished_keyboard(),
        )
        return

    next_index = current_index + 1
    next_question = VocabularyQuizQuestion.from_state_dict(questions_data[next_index])

    await state.update_data(current_index=next_index, score=score)
    await callback.message.edit_text(
        text=_format_quiz_question(
            next_question,
            question_number=next_index + 1,
            total_questions=total_questions,
        ),
        reply_markup=build_quiz_answer_keyboard(next_question.options),
    )


@router.callback_query(VocabularyCallback.filter(F.action == "back_to_vocab"))
async def back_to_vocabulary(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()

    if callback.message is not None:
        word = await _get_random_vocabulary_word()
        await callback.message.edit_text(
            text=_format_vocabulary_card(word),
            reply_markup=build_vocabulary_keyboard(),
        )

    await callback.answer()


@router.callback_query(VocabularyCallback.filter(F.action == "back"))
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


async def _get_random_vocabulary_word() -> VocabularyWord:
    words = await JsonContentLoader().load_vocabulary()
    vocabulary_service = VocabularyService(words)
    return vocabulary_service.get_random_word()


def _format_vocabulary_card(word: VocabularyWord) -> str:
    return (
        "📚 <b>Vocabulary Word</b>\n\n"
        f"<b>{escape(word.word)}</b> {escape(word.transcription)}\n"
        f"<b>Meaning:</b> {escape(word.translation)}\n"
        f"<b>Level:</b> {escape(word.level)}\n\n"
        f"<i>{escape(word.example)}</i>"
    )


def _format_quiz_question(
    question: VocabularyQuizQuestion,
    *,
    question_number: int,
    total_questions: int,
) -> str:
    return (
        "📝 <b>Vocabulary Mini Test</b>\n\n"
        f"<b>Question {question_number} of {total_questions}</b>\n\n"
        f"What is the meaning of <b>{escape(question.word.word)}</b> "
        f"{escape(question.word.transcription)}?"
    )


def _format_answer_feedback(question: VocabularyQuizQuestion, is_correct: bool) -> str:
    if is_correct:
        return "Correct!"

    correct_answer = question.options[question.correct_index]
    return f"Wrong. The correct answer is: {correct_answer}"


def _format_quiz_results(score: int, total_questions: int) -> str:
    percentage = round((score / total_questions) * 100) if total_questions else 0
    return (
        "📝 <b>Mini Test Complete</b>\n\n"
        f"Your score: <b>{score}/{total_questions}</b> ({percentage}%)\n\n"
        "Keep practicing to improve your TOEFL vocabulary."
    )
