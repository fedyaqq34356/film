import g4f
import json
from typing import Dict, List, Any, Optional


class AIRecommendationService:
    """Сервис для AI-рекомендаций фильмов."""
    
    def __init__(self):
        self.user_preferences = {}  # В реальном проекте использовать БД
    
    def save_user_preference(self, user_id: int, genre_ids: List[int], selected_movie: Dict[str, Any]):
        """Сохраняет предпочтения пользователя."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'selected_genres': [],
                'selected_movies': [],
                'genre_frequency': {}
            }
        
        # Добавляем жанры
        self.user_preferences[user_id]['selected_genres'].extend(genre_ids)
        
        # Добавляем фильм
        self.user_preferences[user_id]['selected_movies'].append({
            'id': selected_movie.get('id'),
            'title': selected_movie.get('title'),
            'genres': selected_movie.get('genre_ids', []),
            'rating': selected_movie.get('vote_average')
        })
        
        # Обновляем частоту жанров
        for genre_id in genre_ids:
            if genre_id in self.user_preferences[user_id]['genre_frequency']:
                self.user_preferences[user_id]['genre_frequency'][genre_id] += 1
            else:
                self.user_preferences[user_id]['genre_frequency'][genre_id] = 1
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Получает предпочтения пользователя."""
        return self.user_preferences.get(user_id, {})
    
    async def ask_gpt4free(self, prompt: str) -> str:
        """Запрос к GPT через g4f."""
        try:
            response = g4f.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response
        except Exception as e:
            print(f"[ERROR] GPT request failed: {e}")
            return ""
    
    async def get_ai_recommendations(self, user_id: int, genres_map: Dict[str, int]) -> str:
        """Получает рекомендации от AI на основе предпочтений пользователя."""
        preferences = self.get_user_preferences(user_id)
        
        if not preferences:
            return "Пока недостаточно данных для рекомендаций. Воспользуйтесь поиском несколько раз."
        
        # Создаем обратную карту жанров (id -> название)
        genres_reverse_map = {v: k for k, v in genres_map.items()}
        
        # Формируем данные о предпочтениях
        favorite_genres = []
        for genre_id, count in sorted(preferences.get('genre_frequency', {}).items(), 
                                    key=lambda x: x[1], reverse=True)[:5]:
            genre_name = genres_reverse_map.get(genre_id, f"Жанр {genre_id}")
            favorite_genres.append(f"{genre_name.title()} ({count} раз)")
        
        selected_movies = preferences.get('selected_movies', [])[-5:]  # Последние 5 фильмов
        
        # Создаем промпт для AI
        prompt = f"""
Пользователь выбирал фильмы и жанры со следующими предпочтениями:

Любимые жанры (по частоте выбора):
{chr(10).join(favorite_genres) if favorite_genres else "Нет данных"}

Последние выбранные фильмы:
{chr(10).join([f"- {movie['title']} (рейтинг: {movie.get('rating', 'N/A')})" for movie in selected_movies]) if selected_movies else "Нет данных"}

На основе этих данных дай краткие рекомендации (максимум 300 символов):
1. Какие жанры лучше всего подходят этому пользователю
2. Конкретные названия 2-3 фильмов которые могут понравиться
3. Краткое объяснение почему именно эти рекомендации

Отвечай на русском языке, кратко и по делу.
"""
        
        response = await self.ask_gpt4free(prompt)
        return response if response else "Не удалось получить рекомендации. Попробуйте позже."
