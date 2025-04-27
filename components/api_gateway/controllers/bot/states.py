from aiogram.fsm.state import StatesGroup, State


class ProfileCreationStates(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_bio = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_city = State()
    waiting_for_photo = State()
    waiting_for_gender_preference = State()
    waiting_for_age_preference = State()


class ViewingStates(StatesGroup):
    viewing = State()


class ViewingLikerProfiles(StatesGroup):
    viewing = State()
