from aiogram.fsm.state import State, StatesGroup


class DailyChallengeStates(StatesGroup):
    viewing_challenge = State()
    in_quiz = State()
    quiz_finished = State()
