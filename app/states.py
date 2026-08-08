from aiogram.fsm.state import State, StatesGroup


class SettingsState(StatesGroup):
    catalog = State()
    opds = State()
    emails = State()
    subject = State()
