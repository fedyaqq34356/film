from typing import Dict, List, Any, Optional
from services.tmdb_api import TMDBApi


class MovieService:
    """Сервис для работы с фильмами."""
    
    def __init__(self):
        self.tmdb_api = TMDBApi()
        self._popular_genres = [
            "боевик", "комедия", "драма", "фантастика", "триллер",
            "ужасы", "романтика", "приключения", "криминал", "детектив"
        ]
    
    async def get_popular_genres(self) -> List[str]:
        """Возвращает список популярных жанров."""
        return self._popular_genres
    
    async def search_movies_with_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Поиск фильмов с применением фильтров."""
        try:
            movies = await self.tmdb_api.search_movies(
                title=filters.get("title"),
                genre_ids=filters.get("genre_ids"),
                year=filters.get("year"),
                min_rating=filters.get("min_rating"),
                language=filters.get("language"),
                region=filters.get("region"),
                include_adult=filters.get("include_adult", False),
                sort_by=filters.get("sort_by", "popularity.desc")
            )
            
            # Дополнительная фильтрация если нужно
            return self._post_process_movies(movies, filters)
            
        except Exception as e:
            print(f"[ERROR] Movie search failed: {e}")
            return []
    
    def _post_process_movies(self, movies: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Дополнительная обработка результатов."""
        if not movies:
            return []
        
        # Удаляем фильмы без постеров для лучшего UX
        movies = [m for m in movies if m.get("poster_path")]
        
        # Сортируем по популярности если не задано другое
        if not filters.get("sort_by") or filters.get("sort_by") == "popularity.desc":
            movies.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        
        return movies
    
    async def get_movie_recommendations(self, movie_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает рекомендации для фильма."""
        try:
            # Используем TMDB API для получения рекомендаций
            # Этот метод нужно добавить в TMDBApi класс
            return []
        except Exception as e:
            print(f"[ERROR] Failed to get recommendations: {e}")
            return []
    
    def parse_genre_input(self, genre_input: str, genres_map: Dict[str, int]) -> List[int]:
        """Парсит ввод пользователя для жанров."""
        genre_ids = []
        
        for token in [t.strip() for t in genre_input.split(",") if t.strip()]:
            if token.isdigit():
                genre_ids.append(int(token))
            else:
                genre_id = genres_map.get(token.lower())
                if genre_id:
                    genre_ids.append(genre_id)
        
        return genre_ids
    
    def validate_year(self, year_str: str) -> Optional[int]:
        """Валидирует год выпуска."""
        if not year_str or not year_str.isdigit():
            return None
        
        year = int(year_str)
        if 1900 <= year <= 2030:
            return year
        
        return None
    
    def validate_rating(self, rating_str: str) -> Optional[float]:
        """Валидирует рейтинг."""
        if not rating_str:
            return None
        
        try:
            rating = float(rating_str)
            if 0 <= rating <= 10:
                return rating
        except ValueError:
            pass
        
        return None