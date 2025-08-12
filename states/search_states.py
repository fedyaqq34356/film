from aiogram.fsm.state import State, StatesGroup


class SimpleSearchStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_genre = State()
    waiting_for_year = State()


class AdvancedSearchStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_genres = State()
    waiting_for_year = State()
    waiting_for_rating = State()
    waiting_for_language = State()
    waiting_for_region = State()
    waiting_for_adult_content = State()
    waiting_for_sort = State()

class MovieSelectionState(StatesGroup):
    waiting_for_movie_choice = State()