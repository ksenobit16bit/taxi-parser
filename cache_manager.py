# cache_manager.py - Кеширование данных
import os
import json
import logging
from datetime import datetime

class CacheManager:
    """Класс для кеширования данных о поездках."""
    
    def __init__(self, cache_dir="cache"):
        """Инициализация менеджера кеша."""
        self.cache_dir = cache_dir
        # Создаем директорию для кеша, если она не существует
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def get_cache_path(self, month):
        """Получение пути к файлу кеша для указанного месяца."""
        return os.path.join(self.cache_dir, f"{month}.json")
    
    def has_cache(self, month):
        """Проверка наличия кеша для указанного месяца."""
        cache_path = self.get_cache_path(month)
        return os.path.exists(cache_path)
    
    def save_to_cache(self, month, trips):
        """Сохранение данных о поездках в кеш."""
        try:
            cache_path = self.get_cache_path(month)
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            
            # Добавляем метаданные кеша
            cache_data = {
                "created_at": datetime.now().isoformat(),
                "month": month,
                "trips_count": len(trips),
                "trips": trips
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logging.info(f"Данные успешно сохранены в кеш: {cache_path}")
            return True
        except Exception as e:
            logging.error(f"Ошибка при сохранении данных в кеш: {e}")
            return False
    
    def load_from_cache(self, month):
        """Загрузка данных о поездках из кеша."""
        try:
            cache_path = self.get_cache_path(month)
            if not os.path.exists(cache_path):
                logging.warning(f"Кеш для месяца {month} не найден")
                return None
                
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            logging.info(f"Данные успешно загружены из кеша: {cache_path}")
            return cache_data.get("trips", [])
        except Exception as e:
            logging.error(f"Ошибка при загрузке данных из кеша: {e}")
            return None 