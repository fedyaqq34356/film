from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню выбора типа поиска."""
    keyboard = [
        [InlineKeyboardButton(text="🔍 Простой поиск", callback_data="simple_search")],
        [InlineKeyboardButton(text="🎯 Расширенный поиск", callback_data="advanced_search")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_skip_button() -> InlineKeyboardMarkup:
    """Кнопка пропустить."""
    keyboard = [
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_genres_keyboard(genres: Dict[str, int], selected: List[int] = None) -> InlineKeyboardMarkup:
    """Клавиатура выбора жанров."""
    if selected is None:
        selected = []
    
    keyboard = []
    row = []
    
    # Популярные жанры в начале
    popular_genres = [
        "боевик", "комедия", "драма", "фантастика", "триллер", 
        "ужасы", "романтика", "приключения", "криминал", "детектив"
    ]
    
    # Сначала популярные жанры
    for genre_name in popular_genres:
        if genre_name in genres:
            genre_id = genres[genre_name]
            text = f"✅ {genre_name.title()}" if genre_id in selected else genre_name.title()
            row.append(InlineKeyboardButton(
                text=text, 
                callback_data=f"genre_{genre_id}"
            ))
            
            if len(row) == 2:
                keyboard.append(row)
                row = []
    
    # Остальные жанры
    remaining_genres = {k: v for k, v in genres.items() if k not in popular_genres}
    for genre_name, genre_id in sorted(remaining_genres.items()):
        text = f"✅ {genre_name.title()}" if genre_id in selected else genre_name.title()
        row.append(InlineKeyboardButton(
            text=text, 
            callback_data=f"genre_{genre_id}"
        ))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Кнопки управления
    control_buttons = []
    if selected:
        control_buttons.append(InlineKeyboardButton(
            text="🗑 Очистить", 
            callback_data="clear_genres"
        ))
    
    control_buttons.append(InlineKeyboardButton(
        text="✅ Готово", 
        callback_data="genres_done"
    ))
    
    keyboard.append(control_buttons)
    keyboard.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_pagination_keyboard(current_page: int, total_pages: int, prefix: str = "page") -> InlineKeyboardMarkup:
    """Клавиатура пагинации."""
    keyboard = []
    
    # Навигация по страницам
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}_{current_page - 1}"))
    
    nav_row.append(InlineKeyboardButton(
        text=f"{current_page}/{total_pages}", 
        callback_data="current_page"
    ))
    
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}_{current_page + 1}"))
    
    keyboard.append(nav_row)
    
    # Быстрые переходы
    if total_pages > 3:
        quick_nav = []
        if current_page > 3:
            quick_nav.append(InlineKeyboardButton(text="1", callback_data=f"{prefix}_1"))
        if current_page < total_pages - 2:
            quick_nav.append(InlineKeyboardButton(text=str(total_pages), callback_data=f"{prefix}_{total_pages}"))
        
        if quick_nav:
            keyboard.append(quick_nav)
    
    # Кнопки действий
    keyboard.append([
        InlineKeyboardButton(text="🔄 Новый поиск", callback_data="new_search"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_movie_details_keyboard(movie_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для детальной информации о фильме."""
    keyboard = [
        [InlineKeyboardButton(text="📖 Подробнее", callback_data=f"details_{movie_id}")],
        [InlineKeyboardButton(text="🔙 К результатам", callback_data="back_to_results")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_yes_no_keyboard(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
    """Клавиатура Да/Нет."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data=yes_callback),
            InlineKeyboardButton(text="❌ Нет", callback_data=no_callback)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_sort_options_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора сортировки."""
    keyboard = [
        [InlineKeyboardButton(text="🔥 По популярности", callback_data="sort_popularity.desc")],
        [InlineKeyboardButton(text="⭐ По рейтингу", callback_data="sort_vote_average.desc")],
        [InlineKeyboardButton(text="📅 По дате выхода", callback_data="sort_primary_release_date.desc")],
        [InlineKeyboardButton(text="🔤 По названию", callback_data="sort_original_title.asc")],
        [InlineKeyboardButton(text="✅ Готово", callback_data="sort_done")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)