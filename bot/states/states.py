from aiogram.fsm.state import State, StatesGroup


class AppealStates(StatesGroup):
    WAITING_FOR_CONTENT = State()
    ADDING_MORE = State()
    WAITING_FOLLOWUP = State()


class AdminReplyStates(StatesGroup):
    WAITING_FOR_REPLY = State()


class AdminSearchStates(StatesGroup):
    WAITING_FOR_QUERY = State()


class BroadcastStates(StatesGroup):
    WAITING_FOR_MESSAGE = State()
    CONFIRMING = State()
