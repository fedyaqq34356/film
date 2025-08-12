import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from config import (
    TMDB_API_KEY, 
    TMDB_BASE_URL, 
    MAX_CONCURRENT_REQUESTS, 
    MAX_RETRIES, 
    BASE_RETRY_DELAY
)


class TMDBApi:
    def __init__(self):
        self.api_key = TMDB_API_KEY
        self.base_url = TMDB_BASE_URL
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self._genres_cache = None

    def _clean_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Удаляет пустые параметры и преобразует булевы значения."""
        out = {}
        for k, v in params.items():
            if v is None or v == "":
                continue
            if isinstance(v, bool):
                out[k] = "true" if v else "false"
            else:
                out[k] = v
        return out

    async def _fetch_with_retries(
        self, 
        session: aiohttp.ClientSession, 
        url: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Выполняет запрос с повторными попытками при ошибках."""
        params = self._clean_params(params)
        attempt = 0
        
        while attempt < MAX_RETRIES:
            attempt += 1
            async with self.semaphore:
                try:
                    async with session.get(url, params=params, timeout=30) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        elif resp.status == 429:
                            # Rate limit - ждем и повторяем
                            delay = BASE_RETRY_DELAY * (2 ** (attempt - 1))
                            await asyncio.sleep(delay)
                            continue
                        elif resp.status == 400:
                            print(f"[ERROR] 400 Bad Request: {await resp.text()}")
                            return {}
                        else:
                            print(f"[ERROR] HTTP {resp.status}: {await resp.text()}")
                            return {}
                            
                except asyncio.TimeoutError:
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"[ERROR] Request exception: {e}")
                    await asyncio.sleep(1)
        
        return {}

    async def get_genres(self) -> Dict[str, int]:
        """Получает список жанров с кэшированием."""
        if self._genres_cache:
            return self._genres_cache
            
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/genre/movie/list"
            params = {"api_key": self.api_key, "language": "ru-RU"}
            data = await self._fetch_with_retries(session, url, params)
            
            genres = data.get("genres", []) if data else []
            self._genres_cache = {g["name"].lower(): g["id"] for g in genres}
            
        return self._genres_cache

    async def _fetch_all_pages(
        self,
        session: aiohttp.ClientSession,
        url: str,
        base_params: Dict[str, Any],
        max_pages: int = 50
    ) -> List[Dict[str, Any]]:
        """Загружает все страницы результатов."""
        movies = []
        
        # Первая страница для определения общего количества
        params = base_params.copy()
        params["page"] = 1
        first_page = await self._fetch_with_retries(session, url, params)
        
        if not first_page:
            return []
            
        total_pages = min(first_page.get("total_pages", 1), max_pages)
        results = first_page.get("results", [])
        movies.extend(results)
        
        # Остальные страницы асинхронно
        if total_pages > 1:
            tasks = []
            for page in range(2, total_pages + 1):
                page_params = base_params.copy()
                page_params["page"] = page
                tasks.append(self._fetch_with_retries(session, url, page_params))
            
            pages = await asyncio.gather(*tasks)
            for page_data in pages:
                if page_data and "results" in page_data:
                    movies.extend(page_data["results"])
        
        return movies

    def _filter_movies(
        self, 
        movies: List[Dict[str, Any]], 
        genre_ids: Optional[List[int]] = None,
        min_rating: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Фильтрует фильмы по жанрам и рейтингу."""
        filtered = []
        
        for movie in movies:
            # Фильтрация по жанрам
            if genre_ids:
                movie_genres = set(movie.get("genre_ids", []))
                if not all(g_id in movie_genres for g_id in genre_ids):
                    continue
            
            # Фильтрация по рейтингу
            if min_rating is not None:
                movie_rating = movie.get("vote_average")
                if movie_rating is None or movie_rating < min_rating:
                    continue
            
            filtered.append(movie)
        
        return filtered

    async def search_movies(
        self,
        title: Optional[str] = None,
        genre_ids: Optional[List[int]] = None,
        year: Optional[int] = None,
        min_rating: Optional[float] = None,
        language: str = "ru-RU",
        region: Optional[str] = None,
        include_adult: bool = False,
        sort_by: str = "popularity.desc"
    ) -> List[Dict[str, Any]]:
        """Ищет фильмы по заданным критериям."""
        async with aiohttp.ClientSession() as session:
            movies = []
            
            # Поиск по названию
            if title:
                search_url = f"{self.base_url}/search/movie"
                search_params = {
                    "api_key": self.api_key,
                    "language": language,
                    "query": title,
                    "include_adult": include_adult,
                    "year": year
                }
                search_results = await self._fetch_all_pages(session, search_url, search_params)
                # Фильтруем результаты поиска по названию
                filtered_search = self._filter_movies(search_results, genre_ids, min_rating)
                movies.extend(filtered_search)
            
            # Discover для дополнительных фильтров
            discover_url = f"{self.base_url}/discover/movie"
            discover_params = {
                "api_key": self.api_key,
                "language": language,
                "with_genres": ",".join(map(str, genre_ids)) if genre_ids else None,
                "primary_release_year": year,
                "vote_average.gte": min_rating,
                "region": region,
                "include_adult": include_adult,
                "sort_by": sort_by
            }
            
            discover_results = await self._fetch_all_pages(session, discover_url, discover_params)
            
            # Объединяем результаты, убирая дубликаты
            seen_ids = set()
            combined_movies = []
            
            for movie in movies + discover_results:
                movie_id = movie.get("id")
                if movie_id and movie_id not in seen_ids:
                    seen_ids.add(movie_id)
                    combined_movies.append(movie)
            
            return combined_movies

    async def get_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Получает детальную информацию о фильме."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/movie/{movie_id}"
            params = {
                "api_key": self.api_key,
                "language": "ru-RU",
                "append_to_response": "credits,videos"
            }
            return await self._fetch_with_retries(session, url, params)