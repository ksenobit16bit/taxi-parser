# analytics.py - Анализ и форматирование результатов
import re
from datetime import datetime, timedelta
import logging

class TripAnalytics:
    """Класс для анализа поездок."""
    
    @staticmethod
    def get_workweeks_in_month(month):
        """Возвращает список рабочих недель в месяце."""
        try:
            year, month_num = map(int, month.split('-'))
            start_date = datetime(year, month_num, 1)
            
            # Находим последний день месяца
            if month_num == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month_num + 1, 1)
            last_day = (next_month - timedelta(days=1)).day
            
            weeks = []
            current_week = []
            
            # Проходим по всем дням месяца
            for day in range(1, last_day + 1):
                current_date = datetime(year, month_num, day)
                
                # Если это будний день (0 = понедельник, 4 = пятница)
                if current_date.weekday() <= 4:
                    current_week.append(day)
                
                # Если это пятница или последний день месяца
                if current_date.weekday() == 4 or day == last_day:
                    if current_week:
                        weeks.append((min(current_week), max(current_week)))
                    current_week = []
            
            # Добавляем последнюю неделю, если она есть
            if current_week:
                weeks.append((min(current_week), max(current_week)))
            
            return weeks
        except Exception as e:
            logging.error(f"Ошибка при определении рабочих недель: {e}")
            return []
    
    @staticmethod
    def format_weekly_costs(trips, month):
        """Форматирует строки с неделями и формулами расчета."""
        try:
            # Получаем год и месяц из строки формата YYYY-MM
            year, month_num = map(int, month.split('-'))
            
            # Создаем словарь для хранения всех поездок по дням и времени
            all_trips = {}
            
            for trip in trips:
                # Извлекаем дату, стоимость и время из строки результата
                match_date = re.search(r'Дата: (\d+) \w+ (\d{4})', trip)
                match_cost = re.search(r'Стоимость: (\d+)', trip)
                match_time = re.search(r'Время: (\d{2}):(\d{2})', trip)
                
                if match_date and match_cost and match_time:
                    day = int(match_date.group(1))
                    trip_year = int(match_date.group(2))
                    
                    # Пропускаем поездки, если год не совпадает с запрошенным
                    if trip_year != year:
                        continue
                        
                    cost = int(match_cost.group(1))
                    hour = int(match_time.group(1))
                    minute = int(match_time.group(2))
                    
                    # Создаем ключ для словаря в формате (день, час, минута)
                    trip_key = (day, hour, minute)
                    all_trips[trip_key] = cost
            
            # Сортируем поездки по дате и времени
            sorted_trips = sorted(all_trips.items())
            
            # Создаем словарь для хранения утренних и вечерних поездок по рабочим дням
            trips_by_date = {}
            
            # Проходим по всем поездкам в хронологическом порядке
            for (day, hour, minute), cost in sorted_trips:
                try:
                    date = datetime(year, month_num, day)
                    
                    # Если это ранняя утренняя поездка (00:00-04:00)
                    if 0 <= hour < 4:
                        # Проверяем предыдущий день
                        prev_day = day - 1
                        try:
                            prev_date = datetime(year, month_num, prev_day)
                            # Если предыдущий день - рабочий день
                            if prev_date.weekday() <= 4:
                                # Если предыдущего дня нет в словаре, добавляем его
                                if prev_day not in trips_by_date:
                                    trips_by_date[prev_day] = {'morning': 0, 'evening': 0}
                                
                                # Если у предыдущего дня нет вечерней поездки, добавляем эту
                                if trips_by_date[prev_day]['evening'] == 0:
                                    trips_by_date[prev_day]['evening'] = cost
                                    logging.debug(f"Добавлена вечерняя поездка для дня {prev_day}: {cost} (ранняя утренняя поездка дня {day})")
                                    continue
                        except ValueError:
                            pass
                    
                    # Если это рабочий день
                    if date.weekday() <= 4:
                        # Если дня нет в словаре, добавляем его
                        if day not in trips_by_date:
                            trips_by_date[day] = {'morning': 0, 'evening': 0}
                        
                        # Если поездка до 12:00, считаем ее утренней
                        if hour < 12:
                            # Если утренней поездки еще нет, добавляем
                            if trips_by_date[day]['morning'] == 0:
                                trips_by_date[day]['morning'] = cost
                        # Иначе считаем вечерней
                        else:
                            # Если вечерней поездки еще нет, добавляем
                            if trips_by_date[day]['evening'] == 0:
                                trips_by_date[day]['evening'] = cost
                except ValueError:
                    logging.warning(f"Пропущена невалидная дата: {year}-{month_num}-{day}")
            
            # Вывод содержимого словаря для отладки
            for day in sorted(trips_by_date.keys()):
                logging.debug(f"День {day}: утро={trips_by_date[day]['morning']}, вечер={trips_by_date[day]['evening']}")
            
            # Получаем рабочие недели
            weeks = TripAnalytics.get_workweeks_in_month(month)
            if not weeks:
                return "Не удалось определить рабочие недели", ""
            
            # Форматируем вывод
            weeks_str = "\t".join(f"{w[0]}-{w[1]}" for w in weeks)
            
            formulas = []
            for week_start, week_end in weeks:
                daily_costs = []
                for day in range(week_start, week_end + 1):
                    if day in trips_by_date:
                        morning = trips_by_date[day]['morning']
                        evening = trips_by_date[day]['evening']
                        daily_costs.append(f"{morning}+{evening}")
                    else:
                        daily_costs.append("0+0")
                formula = "=(" + ")+(".join(daily_costs) + ")"
                formulas.append(formula)
            
            formulas_str = "\t".join(formulas)
            return weeks_str, formulas_str
        
        except Exception as e:
            logging.error(f"Ошибка при форматировании результатов: {e}")
            return "Ошибка при форматировании результатов", "" 