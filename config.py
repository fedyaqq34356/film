import os
from typing import Dict

# Telegram Bot
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# TMDB API
TMDB_API_KEY = os.getenv('TMDB_API_KEY', '8fd2a26ac2210a28d8e7f7315aa0aa1d')
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# API Settings
MAX_CONCURRENT_REQUESTS = 5
MAX_RETRIES = 4
BASE_RETRY_DELAY = 2

# Pagination
MOVIES_PER_PAGE = 10
MAX_PAGES_TO_SHOW = 50

# Messages
MESSAGES = {
    'start': '🎬 <b>Добро пожаловать в Movie Search Bot!</b>\n\n'
             'Я помогу вам найти фильмы по различным критериям.\n\n'
             'Выберите тип поиска:',
    
    'simple_search_start': '🔍 <b>Простой поиск</b>\n\n'
                          'Введите название фильма или нажмите "Пропустить" для поиска по жанру:',
    
    'advanced_search_start': '🎯 <b>Расширенный поиск</b>\n\n'
                            'Настройте фильтры для точного поиска фильмов.',
    
    'no_movies_found': '😔 К сожалению, фильмы по вашим критериям не найдены.\n'
                      'Попробуйте изменить параметры поиска.',
    
    'search_error': '❌ Произошла ошибка при поиске. Попробуйте еще раз.',
    
    'loading': '🔄 Ищем фильмы...',
}

# Проверка наличия необходимых переменных
def validate_config() -> bool:
    """Проверяет корректность конфигурации."""
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE' or not BOT_TOKEN:
        print("❌ Ошибка: BOT_TOKEN не настроен!")
        print("Установите переменную окружения BOT_TOKEN или отредактируйте config.py")
        return False
    
    if not TMDB_API_KEY:
        print("❌ Ошибка: TMDB_API_KEY не настроен!")
        print("Установите переменную окружения TMDB_API_KEY или отредактируйте config.py")
        return False
    
    return True