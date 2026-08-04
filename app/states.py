from aiogram.fsm.state import State, StatesGroup


class SettingsState(StatesGroup):
    opds = State()
    emails = State()
    subject = State()