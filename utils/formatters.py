from typing import List, Dict, Any, Optional
import html


def format_movie_short(movie: Dict[str, Any], index: int) -> str:
    """Краткое форматирование фильма для списка."""
    title = html.escape(movie.get("title", "Без названия"))
    original_title = movie.get("original_title", "")
    release_date = movie.get("release_date", "")
    rating = movie.get("vote_average", 0)
    vote_count = movie.get("vote_count", 0)
    
    # Форматируем дату
    year = ""
    if release_date:
        try:
            year = f" ({release_date[:4]})"
        except:
            pass
    
    # Оригинальное название если отличается
    orig_title_text = ""
    if original_title and original_title != movie.get("title", ""):
        orig_title_text = f"\n<i>{html.escape(original_title)}</i>"
    
    # Рейтинг с эмодзи
    rating_emoji = "⭐" if rating >= 7.0 else "🌟" if rating >= 5.0 else "⚪"
    rating_text = f"{rating_emoji} <b>{rating:.1f}</b>"
    if vote_count > 0:
        rating_text += f" ({vote_count:,} оценок)"
    
    return f"<b>{index}.</b> <b>{title}</b>{year}{orig_title_text}\n{rating_text}"


def format_movies_page(movies: List[Dict[str, Any]], page: int, per_page: int) -> str:
    """Форматирует страницу с фильмами."""
    if not movies:
        return "😔 Фильмы не найдены"
    
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, len(movies))
    page_movies = movies[start_idx:end_idx]
    
    header = f"🎬 <b>Результаты поиска</b>\n"
    header += f"📄 Страница {page} • Найдено: {len(movies)}\n"
    header += "─" * 30 + "\n\n"
    
    movies_text = []
    for i, movie in enumerate(page_movies, start=start_idx + 1):
        movies_text.append(format_movie_short(movie, i))
    
    return header + "\n\n".join(movies_text)


def format_movie_details(movie: Dict[str, Any]) -> str:
    """Подробное форматирование информации о фильме."""
    title = html.escape(movie.get("title", "Без названия"))
    original_title = movie.get("original_title", "")
    overview = movie.get("overview", "Описание недоступно")
    release_date = movie.get("release_date", "")
    runtime = movie.get("runtime", 0)
    rating = movie.get("vote_average", 0)
    vote_count = movie.get("vote_count", 0)
    genres = movie.get("genres", [])
    production_countries = movie.get("production_countries", [])
    budget = movie.get("budget", 0)
    revenue = movie.get("revenue", 0)
    
    # Заголовок
    header = f"🎬 <b>{title}</b>\n"
    
    # Оригинальное название
    if original_title and original_title != movie.get("title", ""):
        header += f"<i>{html.escape(original_title)}</i>\n"
    
    header += "─" * 30 + "\n\n"
    
    # Основная информация
    info_lines = []
    
    # Дата выхода и продолжительность
    if release_date:
        info_lines.append(f"📅 <b>Дата выхода:</b> {format_release_date(release_date)}")
    
    if runtime > 0:
        hours = runtime // 60
        minutes = runtime % 60
        duration = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
        info_lines.append(f"⏱ <b>Длительность:</b> {duration}")
    
    # Рейтинг
    if rating > 0:
        rating_emoji = "⭐" if rating >= 7.0 else "🌟" if rating >= 5.0 else "⚪"
        rating_text = f"{rating_emoji} <b>Рейтинг:</b> {rating:.1f}/10"
        if vote_count > 0:
            rating_text += f" ({vote_count:,} оценок)"
        info_lines.append(rating_text)
    
    # Жанры
    if genres:
        genres_text = ", ".join([g["name"] for g in genres])
        info_lines.append(f"🎭 <b>Жанры:</b> {genres_text}")
    
    # Страны производства
    if production_countries:
        countries = ", ".join([c["name"] for c in production_countries[:3]])
        info_lines.append(f"🌍 <b>Страны:</b> {countries}")
    
    # Бюджет и сборы
    if budget > 0:
        info_lines.append(f"💰 <b>Бюджет:</b> ${budget:,}")
    
    if revenue > 0:
        info_lines.append(f"💵 <b>Сборы:</b> ${revenue:,}")
    
    # Описание
    description = f"\n📖 <b>Описание:</b>\n{html.escape(overview[:500])}..."
    
    return header + "\n".join(info_lines) + "\n" + description


def format_release_date(date_str: str) -> str:
    """Форматирует дату релиза."""
    if not date_str:
        return "Неизвестно"
    
    try:
        year, month, day = date_str.split("-")
        months = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]
        month_name = months[int(month) - 1]
        return f"{int(day)} {month_name} {year}"
    except:
        return date_str


def format_search_params(params: Dict[str, Any]) -> str:
    """Форматирует параметры поиска для отображения."""
    lines = ["🔍 <b>Параметры поиска:</b>"]
    
    if params.get("title"):
        lines.append(f"📝 Название: {html.escape(params['title'])}")
    
    if params.get("genres"):
        genres_text = ", ".join(params["genres"])
        lines.append(f"🎭 Жанры: {genres_text}")
    
    if params.get("year"):
        lines.append(f"📅 Год: {params['year']}")
    
    if params.get("min_rating"):
        lines.append(f"⭐ Мин. рейтинг: {params['min_rating']}")
    
    if params.get("language"):
        lines.append(f"🌐 Язык: {params['language']}")
    
    if params.get("region"):
        lines.append(f"🌍 Регион: {params['region']}")
    
    return "\n".join(lines) + "\n\n"


def format_genre_selection(selected_genres: List[str]) -> str:
    """Форматирует список выбранных жанров."""
    if not selected_genres:
        return "🎭 Выберите жанры из списка ниже:"
    
    genres_text = ", ".join(selected_genres)
    return f"🎭 <b>Выбранные жанры:</b>\n{genres_text}\n\nДобавьте еще или нажмите 'Готово':"


def format_error_message(error_type: str = "general") -> str:
    """Форматирует сообщения об ошибках."""
    error_messages = {
        "general": "❌ Произошла ошибка. Попробуйте еще раз.",
        "network": "🌐 Проблемы с сетью. Проверьте подключение и повторите попытку.",
        "api": "🔧 Проблемы с API фильмов. Попробуйте позже.",
        "not_found": "😔 По вашему запросу ничего не найдено. Попробуйте изменить критерии поиска.",
        "invalid_input": "⚠️ Некорректный ввод. Проверьте данные и попробуйте снова.",
        "timeout": "⏱️ Превышено время ожидания. Попробуйте еще раз."
    }
    
    return error_messages.get(error_type, error_messages["general"])


def truncate_text(text: str, max_length: int = 4000) -> str:
    """Обрезает текст до максимальной длины для Telegram."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def format_help_message() -> str:
    """Форматирует справочное сообщение."""
    return """
🎬 <b>Movie Search Bot - Справка</b>

<b>🔍 Простой поиск:</b>
• Поиск по названию фильма
• Фильтрация по жанру (обязательно)
• Указание года выпуска

<b>🎯 Расширенный поиск:</b>
• Все параметры простого поиска
• Минимальный рейтинг
• Язык фильма
• Регион релиза
• Включение контента 18+
• Сортировка результатов

<b>📖 Как пользоваться:</b>
1. Выберите тип поиска
2. Заполните параметры (следуйте подсказкам)
3. Просматривайте результаты с помощью кнопок
4. Нажмите на фильм для подробной информации

<b>💡 Советы:</b>
• Используйте "Пропустить" для необязательных полей
• Выбирайте несколько жанров для точного поиска
• Указывайте год для фильмов с популярными названиями

<b>⚙️ Техподдержка:</b>
Если возникли проблемы, попробуйте:
1. Перезапустить бота командой /start
2. Изменить параметры поиска
3. Проверить интернет-соединение
"""