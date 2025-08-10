from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.search_states import AdvancedSearchStates
from keyboards.inline import (
    get_skip_button, get_yes_no_keyboard, get_sort_options_keyboard,
    get_pagination_keyboard, get_main_menu
)
from services.tmdb_api import TMDBApi
from services.movie_service import MovieService
from utils.formatters import (
    format_movies_page, format_error_message, format_search_params
)
from config import MESSAGES, MOVIES_PER_PAGE

router = Router()
tmdb_api = TMDBApi()
movie_service = MovieService()


@router.message(AdvancedSearchStates.waiting_for_title)
async def advanced_search_title(message: Message, state: FSMContext):
    """Получение названия для расширенного поиска."""
    await state.update_data(title=message.text.strip())
    await ask_for_rating(message, state)


@router.callback_query(F.data == "skip", AdvancedSearchStates.waiting_for_title)
async def advanced_search_skip_title(callback: CallbackQuery, state: FSMContext):
    """Пропуск названия в расширенном поиске."""
    await ask_for_rating(callback.message, state, edit=True)
    await callback.answer()


async def ask_for_rating(message, state: FSMContext, edit: bool = False):
    """Запрос минимального рейтинга."""
    await state.set_state(AdvancedSearchStates.waiting_for_rating)
    
    text = "⭐ Введите минимальный рейтинг (0-10, например: 7.5):"
    
    if edit:
        await message.edit_text(text, reply_markup=get_skip_button(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=get_skip_button(), parse_mode="HTML")


@router.message(AdvancedSearchStates.waiting_for_rating)
async def advanced_search_rating(message: Message, state: FSMContext):
    """Получение рейтинга."""
    rating = movie_service.validate_rating(message.text.strip())
    
    if message.text.strip() and rating is None:
        await message.answer("⚠️ Введите рейтинг от 0 до 10 (например: 7.5) или нажмите 'Пропустить'")
        return
    
    await state.update_data(min_rating=rating)
    await ask_for_language(message, state)


@router.callback_query(F.data == "skip", AdvancedSearchStates.waiting_for_rating)
async def advanced_search_skip_rating(callback: CallbackQuery, state: FSMContext):
    """Пропуск рейтинга."""
    await ask_for_language(callback.message, state, edit=True)
    await callback.answer()


async def ask_for_language(message, state: FSMContext, edit: bool = False):
    """Запрос языка фильма."""
    await state.set_state(AdvancedSearchStates.waiting_for_language)
    
    text = ("🌐 Введите код языка фильма (например: en-US, ru-RU, fr-FR):\n\n"
           "<i>ru-RU</i> - русский\n"
           "<i>en-US</i> - английский\n" 
           "<i>fr-FR</i> - французский\n"
           "<i>de-DE</i> - немецкий\n"
           "<i>es-ES</i> - испанский")
    
    if edit:
        await message.edit_text(text, reply_markup=get_skip_button(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=get_skip_button(), parse_mode="HTML")


@router.message(AdvancedSearchStates.waiting_for_language)
async def advanced_search_language(message: Message, state: FSMContext):
    """Получение языка."""
    language = message.text.strip()
    
    # Простая валидация языкового кода
    if language and (len(language) < 2 or len(language) > 5):
        await message.answer("⚠️ Введите корректный код языка (например: ru-RU, en-US) или нажмите 'Пропустить'")
        return
    
    await state.update_data(language=language if language else "ru-RU")
    await ask_for_region(message, state)


@router.callback_query(F.data == "skip", AdvancedSearchStates.waiting_for_language)
async def advanced_search_skip_language(callback: CallbackQuery, state: FSMContext):
    """Пропуск языка."""
    await state.update_data(language="ru-RU")
    await ask_for_region(callback.message, state, edit=True)
    await callback.answer()


async def ask_for_region(message, state: FSMContext, edit: bool = False):
    """Запрос региона."""
    await state.set_state(AdvancedSearchStates.waiting_for_region)
    
    text = ("🌍 Введите код региона/страны (например: US, RU, GB):\n\n"
           "<i>RU</i> - Россия\n"
           "<i>US</i> - США\n"
           "<i>GB</i> - Великобритания\n"
           "<i>FR</i> - Франция\n"
           "<i>DE</i> - Германия")
    
    if edit:
        await message.edit_text(text, reply_markup=get_skip_button(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=get_skip_button(), parse_mode="HTML")


@router.message(AdvancedSearchStates.waiting_for_region)
async def advanced_search_region(message: Message, state: FSMContext):
    """Получение региона."""
    region = message.text.strip().upper()
    
    if region and len(region) != 2:
        await message.answer("⚠️ Введите двухбуквенный код страны (например: US, RU) или нажмите 'Пропустить'")
        return
    
    await state.update_data(region=region if region else None)
    await ask_for_adult_content(message, state)


@router.callback_query(F.data == "skip", AdvancedSearchStates.waiting_for_region)
async def advanced_search_skip_region(callback: CallbackQuery, state: FSMContext):
    """Пропуск региона."""
    await ask_for_adult_content(callback.message, state, edit=True)
    await callback.answer()


async def ask_for_adult_content(message, state: FSMContext, edit: bool = False):
    """Запрос включения adult-контента."""
    await state.set_state(AdvancedSearchStates.waiting_for_adult_content)
    
    text = "🔞 Включать фильмы для взрослых в результаты поиска?"
    keyboard = get_yes_no_keyboard("adult_yes", "adult_no")
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.in_(["adult_yes", "adult_no"]))
async def advanced_search_adult_content(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора adult-контента."""
    include_adult = callback.data == "adult_yes"
    await state.update_data(include_adult=include_adult)
    
    await ask_for_sort(callback.message, state, edit=True)
    await callback.answer()


async def ask_for_sort(message, state: FSMContext, edit: bool = False):
    """Запрос типа сортировки."""
    await state.set_state(AdvancedSearchStates.waiting_for_sort)
    
    text = "📊 Выберите тип сортировки результатов:"
    keyboard = get_sort_options_keyboard()
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("sort_"))
async def advanced_search_sort(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора сортировки."""
    if callback.data == "sort_done":
        await execute_advanced_search(callback.message, state, edit=True)
    else:
        sort_by = callback.data[5:]  # убираем префикс "sort_"
        await state.update_data(sort_by=sort_by)
        
        # Показываем выбранную сортировку
        sort_names = {
            "popularity.desc": "По популярности",
            "vote_average.desc": "По рейтингу", 
            "primary_release_date.desc": "По дате выхода",
            "original_title.asc": "По названию"
        }
        
        sort_name = sort_names.get(sort_by, sort_by)
        await callback.answer(f"✅ Выбрана сортировка: {sort_name}")
    
    await callback.answer()


async def execute_advanced_search(message, state: FSMContext, edit: bool = False):
    """Выполнение расширенного поиска."""
    data = await state.get_data()
    
    # Показываем параметры поиска и индикатор загрузки
    search_params = format_search_params({
        'title': data.get('title'),
        'genres': data.get('genres', []),
        'year': data.get('year'),
        'min_rating': data.get('min_rating'),
        'language': data.get('language'),
        'region': data.get('region')
    })
    
    loading_text = search_params + MESSAGES['loading']
    
    if edit:
        await message.edit_text(loading_text, parse_mode="HTML")
    else:
        await message.answer(loading_text, parse_mode="HTML")
    
    try:
        # Выполняем поиск
        search_filters = {
            'title': data.get('title'),
            'genre_ids': data.get('genre_ids', []),
            'year': data.get('year'),
            'min_rating': data.get('min_rating'),
            'language': data.get('language', 'ru-RU'),
            'region': data.get('region'),
            'include_adult': data.get('include_adult', False),
            'sort_by': data.get('sort_by', 'popularity.desc')
        }
        
        movies = await movie_service.search_movies_with_filters(search_filters)
        
        if not movies:
            result_text = MESSAGES['no_movies_found']
            keyboard = get_main_menu()
        else:
            # Сохраняем результаты и показываем первую страницу
            await state.update_data(movies=movies, current_page=1)
            total_pages = (len(movies) + MOVIES_PER_PAGE - 1) // MOVIES_PER_PAGE
            
            result_text = format_movies_page(movies, 1, MOVIES_PER_PAGE)
            keyboard = get_pagination_keyboard(1, total_pages, "search_page")
        
        await message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
            
    except Exception as e:
        print(f"[ERROR] Advanced search failed: {e}")
        error_text = format_error_message("api")
        keyboard = get_main_menu()
        
        await message.edit_text(error_text, reply_markup=keyboard, parse_mode="HTML")


# Обработка года для расширенного поиска (после выбора жанров)
@router.message(AdvancedSearchStates.waiting_for_year)
async def advanced_search_year(message: Message, state: FSMContext):
    """Получение года в расширенном поиске."""
    year = movie_service.validate_year(message.text.strip())
    
    if message.text.strip() and year is None:
        await message.answer("⚠️ Введите корректный год (1900-2030) или нажмите 'Пропустить'")
        return
    
    await state.update_data(year=year)
    await ask_for_rating(message, state)


@router.callback_query(F.data == "skip", AdvancedSearchStates.waiting_for_year)
async def advanced_search_skip_year(callback: CallbackQuery, state: FSMContext):
    """Пропуск года в расширенном поиске."""
    await ask_for_rating(callback.message, state, edit=True)
    await callback.answer()