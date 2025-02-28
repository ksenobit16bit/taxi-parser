import logging
from bs4 import BeautifulSoup

class EmailParser:
    """Класс для парсинга содержимого писем."""
    
    def __init__(self, routes_to_find):
        """Инициализация парсера."""
        self.routes_to_find = routes_to_find
    
    def parse_email_content(self, content):
        """Парсинг содержимого письма с учётом маршрутов."""
        try:
            # Проверяем наличие сообщения о смене направления перед очисткой
            has_direction_change = "Точка назначения изменена" in content
            
            # Предварительная очистка HTML от нежелательных текстов
            content = content.replace("Точка назначения изменена", "")
            
            soup = BeautifulSoup(content, 'html.parser')

            # Извлечение маршрутов
            route_points = soup.find_all('tr', class_='route__point')
            if not route_points or len(route_points) < 2:
                logging.warning("Не удалось извлечь маршрутные точки.")
                return []

            # Получаем начальную и конечную точки маршрута
            start_point = route_points[0].find('p', class_='route__point-name').get_text(strip=True)
            end_point = route_points[-1].find('p', class_='route__point-name').get_text(strip=True)

            # Извлечение времени
            start_time = route_points[0].find('p', class_='hint').get_text(strip=True) if route_points[0].find('p', class_='hint') else "N/A"
            end_time = route_points[-1].find('p', class_='hint').get_text(strip=True) if route_points[-1].find('p', class_='hint') else "N/A"

            # Извлечение стоимости
            cost = soup.find('td', class_='report__value_main')
            cost_text = cost.get_text(strip=True) if cost else "N/A"

            # Извлечение даты
            date_row = soup.find('td', string="Дата")
            date_text = date_row.find_next_sibling('td').get_text(strip=True) if date_row else "N/A"

            # Проверка маршрута на соответствие ROUTES_TO_FIND
            for point_a, point_b in self.routes_to_find:
                if (point_a in start_point and point_b in end_point) or (point_a in end_point and point_b in start_point):
                    # Определяем направление с учетом ранее обнаруженного сообщения
                    if has_direction_change:
                        direction = f"{end_point} -> {start_point}"
                    else:
                        direction = f"{start_point} -> {end_point}"

                    result = f"Маршрут: {direction}, Стоимость: {cost_text}, Дата: {date_text}, Время: {start_time} - {end_time}"
                    return [result]

            return []
        except Exception as e:
            logging.error(f"Ошибка при парсинге содержимого письма: {e}")
            return []
