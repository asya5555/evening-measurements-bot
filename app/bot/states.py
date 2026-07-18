from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    timezone = State()
    first_reminder_time = State()
    second_reminder_time = State()
    required_sections = State()
    analytics = State()


class EntryFlow(StatesGroup):
    collecting = State()
    clarifying = State()
    confirming = State()
    editing = State()
    adding = State()


class SettingsFlow(StatesGroup):
    choosing = State()
    editing = State()


class DeleteDataFlow(StatesGroup):
    first_confirm = State()
    second_confirm = State()
