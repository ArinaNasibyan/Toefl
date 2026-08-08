from aiogram.fsm.state import State, StatesGroup


class VocabularyMiniTestStates(StatesGroup):
    waiting_for_answer = State()
    quiz_finished = State()
