from typing import List, Dict, Any, Tuple
from math import ceil


class Paginator:
    """Класс для работы с пагинацией."""
    
    def __init__(self, items: List[Any], per_page: int = 10):
        self.items = items
        self.per_page = per_page
        self.total_items = len(items)
        self.total_pages = ceil(self.total_items / per_page) if items else 0
    
    def get_page(self, page: int) -> Tuple[List[Any], Dict[str, Any]]:
        """Возвращает элементы страницы и информацию о пагинации."""
        if page < 1 or page > self.total_pages:
            return [], {}
        
        start_idx = (page - 1) * self.per_page
        end_idx = min(start_idx + self.per_page, self.total_items)
        
        page_items = self.items[start_idx:end_idx]
        
        pagination_info = {
            'current_page': page,
            'total_pages': self.total_pages,
            'total_items': self.total_items,
            'items_on_page': len(page_items),
            'start_index': start_idx + 1,
            'end_index': end_idx,
            'has_previous': page > 1,
            'has_next': page < self.total_pages,
            'previous_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < self.total_pages else None
        }
        
        return page_items, pagination_info
    
    def get_page_range(self, current_page: int, delta: int = 2) -> List[int]:
        """Возвращает диапазон страниц для отображения."""
        if self.total_pages <= 2 * delta + 1:
            return list(range(1, self.total_pages + 1))
        
        start = max(1, current_page - delta)
        end = min(self.total_pages, current_page + delta)
        
        # Корректируем если мы близко к началу или концу
        if start == 1:
            end = min(self.total_pages, 2 * delta + 1)
        elif end == self.total_pages:
            start = max(1, self.total_pages - 2 * delta)
        
        return list(range(start, end + 1))


def create_page_text(items: List[Dict[str, Any]], pagination_info: Dict[str, Any], 
                    title: str = "Результаты", format_func=None) -> str:
    """Создает текст страницы с элементами."""
    if not items:
        return f"😔 {title} не найдены"
    
    header = f"📋 <b>{title}</b>\n"
    header += f"📄 Страница {pagination_info['current_page']}/{pagination_info['total_pages']}\n"
    header += f"📊 Показано: {pagination_info['items_on_page']} из {pagination_info['total_items']}\n"
    header += "─" * 30 + "\n\n"
    
    # Форматируем элементы
    formatted_items = []
    start_index = pagination_info['start_index']
    
    for i, item in enumerate(items, start=start_index):
        if format_func:
            formatted_item = format_func(item, i)
        else:
            formatted_item = f"{i}. {item.get('title', 'Без названия')}"
        formatted_items.append(formatted_item)
    
    return header + "\n\n".join(formatted_items)


def validate_page_number(page_str: str, total_pages: int) -> int:
    """Валидирует номер страницы."""
    try:
        page = int(page_str)
        if 1 <= page <= total_pages:
            return page
    except (ValueError, TypeError):
        pass
    
    return 1  # Возвращаем первую страницу по умолчанию