from aiogram.fsm.state import State, StatesGroup


class ReadingStates(StatesGroup):
    reading_text = State()
    answering_questions = State()
    quiz_finished = State()
