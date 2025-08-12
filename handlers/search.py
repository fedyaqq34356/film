from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import List, Dict, Any

from config import ai_service, MESSAGES, MOVIES_PER_PAGE
from states.search_states import SimpleSearchStates, AdvancedSearchStates, MovieSelectionState
from services.tmdb_api import TMDBApi
from services.ai_service import AIRecommendationService
from utils.formatters import (
    format_movies_page, format_genre_selection, format_search_params,
    format_error_message, format_movie_details
)
from keyboards.inline import (
    get_skip_button, get_genres_keyboard,
    get_yes_no_keyboard, get_sort_options_keyboard, get_main_menu,
    get_movie_selection_keyboard, get_pagination_with_movie_choice_keyboard
)

router = Router()
tmdb_api = TMDBApi()


# ===== ПРОСТОЙ ПОИСК =====

@router.callback_query(F.data == "simple_search")
async def simple_search_start(callback: CallbackQuery, state: FSMContext):
    """Начало простого поиска."""
    await state.set_state(SimpleSearchStates.waiting_for_title)
    await state.update_data(search_type="simple", title=None, genres=[], year=None)
    
    await callback.message.edit_text(
        MESSAGES['simple_search_start'],
        reply_markup=get_skip_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(SimpleSearchStates.waiting_for_title)
async def simple_search_title(message: Message, state: FSMContext):
    """Получение названия фильма в простом поиске."""
    await state.update_data(title=message.text.strip())
    await ask_for_genres(message, state, is_simple=True)


@router.callback_query(F.data == "skip", SimpleSearchStates.waiting_for_title)
async def simple_search_skip_title(callback: CallbackQuery, state: FSMContext):
    """Пропуск названия в простом поиске."""
    await ask_for_genres(callback.message, state, is_simple=True, edit=True)
    await callback.answer()


async def ask_for_genres(message, state: FSMContext, is_simple: bool = True, edit: bool = False):
    """Запрос жанров."""
    try:
        genres_map = await tmdb_api.get_genres()
        await state.update_data(genres_map=genres_map)
        
        next_state = SimpleSearchStates.waiting_for_genre if is_simple else AdvancedSearchStates.waiting_for_genres
        await state.set_state(next_state)
        
        text = "🎭 Выберите жанры (обязательно для простого поиска):"
        keyboard = get_genres_keyboard(genres_map)
        
        if edit:
            await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            
    except Exception as e:
        await message.answer(format_error_message("api"), parse_mode="HTML")


@router.callback_query(F.data.startswith("genre_"))
async def toggle_genre(callback: CallbackQuery, state: FSMContext):
    """Переключение жанра."""
    genre_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    selected_genres = data.get("selected_genres", [])
    genres_map = data.get("genres_map", {})
    
    if genre_id in selected_genres:
        selected_genres.remove(genre_id)
    else:
        selected_genres.append(genre_id)
    
    await state.update_data(selected_genres=selected_genres)
    
    # Обновляем клавиатуру
    keyboard = get_genres_keyboard(genres_map, selected_genres)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except:
        pass  # Игнорируем если сообщение не изменилось
    
    await callback.answer()


@router.callback_query(F.data == "clear_genres")
async def clear_genres(callback: CallbackQuery, state: FSMContext):
    """Очистка выбранных жанров."""
    data = await state.get_data()
    genres_map = data.get("genres_map", {})
    
    await state.update_data(selected_genres=[])
    keyboard = get_genres_keyboard(genres_map, [])
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer("Жанры очищены")


@router.callback_query(F.data == "genres_done")
async def genres_done(callback: CallbackQuery, state: FSMContext):
    """Завершение выбора жанров."""
    data = await state.get_data()
    selected_genres = data.get("selected_genres", [])
    search_type = data.get("search_type", "simple")
    
    if search_type == "simple" and not selected_genres:
        await callback.answer("Выберите хотя бы один жанр для простого поиска!", show_alert=True)
        return
    
    # Сохраняем названия жанров для отображения
    genres_map = data.get("genres_map", {})
    genre_names = []
    for name, genre_id in genres_map.items():
        if genre_id in selected_genres:
            genre_names.append(name.title())
    
    await state.update_data(genres=genre_names, genre_ids=selected_genres)
    
    if search_type == "simple":
        await ask_for_year(callback.message, state, is_simple=True)
    else:
        await ask_for_year(callback.message, state, is_simple=False)
    
    await callback.answer()


async def ask_for_year(message, state: FSMContext, is_simple: bool = True):
    """Запрос года выпуска."""
    next_state = SimpleSearchStates.waiting_for_year if is_simple else AdvancedSearchStates.waiting_for_year
    await state.set_state(next_state)
    
    text = "📅 Введите год выпуска фильма (например: 2023):"
    await message.edit_text(text, reply_markup=get_skip_button(), parse_mode="HTML")


@router.message(SimpleSearchStates.waiting_for_year)
async def simple_search_year(message: Message, state: FSMContext):
    """Получение года в простом поиске."""
    year_text = message.text.strip()
    year = None
    
    if year_text.isdigit() and 1900 <= int(year_text) <= 2030:
        year = int(year_text)
    elif year_text:
        await message.answer("⚠️ Введите корректный год (1900-2030) или нажмите 'Пропустить'")
        return
    
    await state.update_data(year=year)
    await execute_simple_search(message, state)


@router.callback_query(F.data == "skip", SimpleSearchStates.waiting_for_year)
async def simple_search_skip_year(callback: CallbackQuery, state: FSMContext):
    """Пропуск года в простом поиске."""
    await execute_simple_search(callback.message, state, edit=True)
    await callback.answer()


async def execute_simple_search(message, state: FSMContext, edit: bool = False):
    """Выполнение простого поиска."""
    data = await state.get_data()
    
    # Показываем индикатор загрузки
    loading_msg = await message.answer(MESSAGES['loading']) if not edit else None
    if edit:
        try:
            await message.edit_text(MESSAGES['loading'])
        except:
            loading_msg = await message.answer(MESSAGES['loading'])
    
    try:
        # Выполняем поиск
        movies = await tmdb_api.search_movies(
            title=data.get("title"),
            genre_ids=data.get("genre_ids"),
            year=data.get("year")
        )
        
        if not movies:
            error_text = MESSAGES['no_movies_found']
            keyboard = get_main_menu()
        else:
            # Сохраняем результаты и показываем первую страницу
            await state.update_data(movies=movies, current_page=1)
            total_pages = (len(movies) + MOVIES_PER_PAGE - 1) // MOVIES_PER_PAGE
            
            error_text = format_movies_page(movies, 1, MOVIES_PER_PAGE)
            error_text += "\n\n💡 Выберите понравившийся фильм для персональных рекомендаций!"
            
            # Добавляем кнопку выбора фильма
            keyboard = get_pagination_with_movie_choice_keyboard(1, total_pages, "search_page")
        
        if loading_msg:
            await loading_msg.delete()
        
        if edit:
            await message.edit_text(error_text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await message.answer(error_text, reply_markup=keyboard, parse_mode="HTML")
            
    except Exception as e:
        if loading_msg:
            await loading_msg.delete()
        
        error_text = format_error_message("api")
        keyboard = get_main_menu()
        
        if edit:
            await message.edit_text(error_text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await message.answer(error_text, reply_markup=keyboard, parse_mode="HTML")



# ===== РАСШИРЕННЫЙ ПОИСК =====

@router.callback_query(F.data == "advanced_search")
async def advanced_search_start(callback: CallbackQuery, state: FSMContext):
    """Начало расширенного поиска."""
    await state.set_state(AdvancedSearchStates.waiting_for_title)
    await state.update_data(
        search_type="advanced", title=None, genres=[], year=None,
        min_rating=None, language=None, region=None, include_adult=False, sort_by="popularity.desc"
    )
    
    await callback.message.edit_text(
        "🎯 <b>Расширенный поиск</b>\n\nВведите название фильма:",
        reply_markup=get_skip_button(),
        parse_mode="HTML"
    )
    await callback.answer()


# ===== ПАГИНАЦИЯ =====

@router.callback_query(F.data.startswith("search_page_"))
async def search_pagination(callback: CallbackQuery, state: FSMContext):
    """Пагинация результатов поиска."""
    page = int(callback.data.split("_")[2])
    data = await state.get_data()
    movies = data.get("movies", [])
    
    if not movies:
        await callback.answer("Результаты поиска не найдены")
        return
    
    total_pages = (len(movies) + MOVIES_PER_PAGE - 1) // MOVIES_PER_PAGE
    
    if 1 <= page <= total_pages:
        await state.update_data(current_page=page)
        
        text = format_movies_page(movies, page, MOVIES_PER_PAGE)
        text += "\n\n💡 Выберите понравившийся фильм для персональных рекомендаций!"  # ДОБАВИТЬ
        
        # ЗАМЕНИТЬ НА НОВУЮ ФУНКЦИЮ клавиатуры
        keyboard = get_pagination_with_movie_choice_keyboard(page, total_pages, "search_page")
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    
    await callback.answer()


@router.callback_query(F.data == "new_search")
async def new_search(callback: CallbackQuery, state: FSMContext):
    """Начать новый поиск."""
    await state.clear()
    await callback.message.edit_text(
        MESSAGES['start'],
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("details_"))
async def show_movie_details(callback: CallbackQuery, state: FSMContext):
    """Показать детальную информацию о фильме."""
    movie_id = int(callback.data.split("_")[1])
    
    try:
        movie_details = await tmdb_api.get_movie_details(movie_id)
        if movie_details:
            details_text = format_movie_details(movie_details)
            # Возвращаемся к результатам поиска
            back_keyboard = [[{"text": "🔙 К результатам", "callback_data": "back_to_results"}]]
            
            await callback.message.edit_text(
                details_text, 
                reply_markup={"inline_keyboard": back_keyboard}, 
                parse_mode="HTML"
            )
        else:
            await callback.answer("Не удалось загрузить информацию о фильме", show_alert=True)
    except Exception as e:
        print(f"[ERROR] Failed to load movie details: {e}")
        await callback.answer("Ошибка при загрузке информации", show_alert=True)


@router.callback_query(F.data == "back_to_results")
async def back_to_results(callback: CallbackQuery, state: FSMContext):
    """Возврат к результатам поиска."""
    data = await state.get_data()
    movies = data.get("movies", [])
    current_page = data.get("current_page", 1)
    
    if not movies:
        await callback.message.edit_text(
            MESSAGES['start'],
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        return
    
    total_pages = (len(movies) + MOVIES_PER_PAGE - 1) // MOVIES_PER_PAGE
    text = format_movies_page(movies, current_page, MOVIES_PER_PAGE)
    keyboard = get_pagination_with_movie_choice_keyboard(current_page, total_pages, "search_page")
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "ai_recommendations")
async def show_ai_recommendations(callback: CallbackQuery, state: FSMContext):
    """Показать AI рекомендации."""
    user_id = callback.from_user.id
    
    try:
        genres_map = await tmdb_api.get_genres()
        recommendations = await ai_service.get_ai_recommendations(user_id, genres_map)
        
        text = MESSAGES['ai_recommendations'].format(recommendations=recommendations)
        await callback.message.edit_text(
            text,
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[ERROR] AI recommendations failed: {e}")
        await callback.message.edit_text(
            "❌ Не удалось получить рекомендации. Попробуйте позже.",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    
    await callback.answer()

@router.callback_query(F.data == "ask_movie_choice")
async def ask_movie_choice(callback: CallbackQuery, state: FSMContext):
    """Запрос выбора фильма пользователем."""
    await state.set_state(MovieSelectionState.waiting_for_movie_choice)
    
    await callback.message.edit_text(
        MESSAGES['ask_movie_choice'],
        reply_markup=get_movie_selection_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(MovieSelectionState.waiting_for_movie_choice)
async def process_movie_choice(message: Message, state: FSMContext):
    """Обработка выбора фильма пользователем."""
    user_id = message.from_user.id
    choice = message.text.strip()
    
    try:
        data = await state.get_data()
        movies = data.get("movies", [])
        selected_genres = data.get("genre_ids", [])
        
        # Ищем фильм по названию или ID
        selected_movie = None
        
        if choice.isdigit():
            # Поиск по ID в списке результатов
            movie_id = int(choice)
            selected_movie = next((m for m in movies if m.get("id") == movie_id), None)
            
            # Если не найден в списке, попробуем получить из API
            if not selected_movie:
                selected_movie = await tmdb_api.get_movie_details(movie_id)
        else:
            # Поиск по названию
            choice_lower = choice.lower()
            selected_movie = next(
                (m for m in movies if choice_lower in m.get("title", "").lower() or 
                 choice_lower in m.get("original_title", "").lower()), 
                None
            )
        
        if selected_movie:
            # Сохраняем предпочтения пользователя
            ai_service.save_user_preference(user_id, selected_genres, selected_movie)
            
            await message.answer(
                MESSAGES['movie_saved'],
                reply_markup=get_main_menu(),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "❌ Фильм не найден. Попробуйте ввести точное название или выберите из результатов поиска.",
                reply_markup=get_movie_selection_keyboard(),
                parse_mode="HTML"
            )
            return
    
    except Exception as e:
        print(f"[ERROR] Movie choice processing failed: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    
    await state.clear()

@router.callback_query(F.data == "skip_movie_choice")
async def skip_movie_choice(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора фильма."""
    await state.clear()
    await callback.message.edit_text(
        MESSAGES['start'],
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()