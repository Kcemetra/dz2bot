from aiogram.fsm.state import State, StatesGroup

# состояния для настройки профиля
class ProfileStates(StatesGroup):
    weight = State()
    height = State()
    age = State()
    gender = State()
    activity = State()
    city = State()

# состояние для ожидания описания еды
class FoodStates(StatesGroup):
    waiting_for_food = State()