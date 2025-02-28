import logging
from bs4 import BeautifulSoup

class EmailParser:
    """Класс для парсинга содержимого писем."""
    
    def __init__(self, addresses_to_find, required_address="", excluded_addresses=None):
        """Инициализация парсера."""
        self.addresses_to_find = addresses_to_find
        self.required_address = required_address
        self.excluded_addresses = excluded_addresses or []
    
    def parse_email_content(self, content):
        """Парсинг содержимого письма с учётом адресов."""
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
            
            # Логируем найденные точки маршрута
            logging.debug(f"Найдены точки маршрута: начало='{start_point}', конец='{end_point}'")
            logging.debug(f"Искомые адреса: {self.addresses_to_find}")
            
            # Проверка на исключаемые адреса
            for excluded_address in self.excluded_addresses:
                if excluded_address in start_point or excluded_address in end_point:
                    logging.debug(f"Маршрут содержит исключаемый адрес '{excluded_address}', пропускаем")
                    return []
            
            # Проверка на обязательный адрес
            required_address_found = True
            if self.required_address:
                required_address_found = (self.required_address in start_point or self.required_address in end_point)
                if not required_address_found:
                    logging.debug(f"Обязательный адрес '{self.required_address}' не найден в маршруте")
                else:
                    logging.debug(f"Обязательный адрес '{self.required_address}' найден в маршруте")

            # Извлечение времени
            start_time = route_points[0].find('p', class_='hint').get_text(strip=True) if route_points[0].find('p', class_='hint') else "N/A"
            end_time = route_points[-1].find('p', class_='hint').get_text(strip=True) if route_points[-1].find('p', class_='hint') else "N/A"

            # Извлечение стоимости
            cost = soup.find('td', class_='report__value_main')
            cost_text = cost.get_text(strip=True) if cost else "N/A"

            # Извлечение даты
            date_row = soup.find('td', string="Дата")
            date_text = date_row.find_next_sibling('td').get_text(strip=True) if date_row else "N/A"

            # Проверка, содержит ли маршрут хотя бы один из искомых адресов
            addresses_found = True  # По умолчанию считаем, что адреса найдены
            if self.addresses_to_find:
                start_matches = [address for address in self.addresses_to_find if address in start_point]
                end_matches = [address for address in self.addresses_to_find if address in end_point]
                
                # Логируем результаты проверки
                if start_matches:
                    logging.debug(f"Найдено совпадение в начальной точке: {start_matches}")
                if end_matches:
                    logging.debug(f"Найдено совпадение в конечной точке: {end_matches}")
                
                addresses_found = len(start_matches) > 0 or len(end_matches) > 0
            
            # Поездка учитывается только если найдены и адреса из списка, и обязательный адрес
            if addresses_found and required_address_found:
                # Определяем направление с учетом ранее обнаруженного сообщения
                if has_direction_change:
                    direction = f"{end_point} -> {start_point}"
                else:
                    direction = f"{start_point} -> {end_point}"

                result = f"Маршрут: {direction}, Стоимость: {cost_text}, Дата: {date_text}, Время: {start_time} - {end_time}"
                logging.debug(f"Найден подходящий маршрут: {result}")
                return [result]
            else:
                if not addresses_found:
                    logging.debug("Маршрут не соответствует искомым адресам")
                if not required_address_found:
                    logging.debug("Маршрут не содержит обязательный адрес")

            return []
        except Exception as e:
            logging.error(f"Ошибка при парсинге содержимого письма: {e}")
            return []
