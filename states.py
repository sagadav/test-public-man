from aiogram.fsm.state import State, StatesGroup


class TriggerJournal(StatesGroup):
    """Состояния для журнала триггеров"""
    emotion = State()
    emotion_custom = State()
    location = State()
    location_custom = State()
    company = State()
    company_custom = State()


class GoalStates(StatesGroup):
    """Состояния для работы с целями"""
    setting_goal = State()
    setting_result = State()
    confirming_replace = State()
    brainstorming_failure = State()
    analyzing_goals = State()


class SettingsStates(StatesGroup):
    """Состояния для настройки часового пояса"""
    setting_timezone_by_time = State()

