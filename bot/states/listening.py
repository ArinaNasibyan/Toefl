from aiogram.fsm.state import State, StatesGroup


class ListeningStates(StatesGroup):
    listening_audio = State()
    answering_questions = State()
    quiz_finished = State()
