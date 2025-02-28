# main.py - Точка входа
import logging
import os
from config import setup_logging, load_config
from mail_client import EmailClient
from parser import EmailParser
from analytics import TripAnalytics
from cache_manager import CacheManager

def main():
    try:
        # Настройка логирования и загрузка конфигурации
        setup_logging()
        config = load_config()
        
        # Создание необходимых объектов
        email_client = EmailClient(config)
        email_parser = EmailParser(config["ROUTES_TO_FIND"])
        cache_manager = CacheManager()
        
        # Запрос месяца
        month = input("Введите месяц в формате 'YYYY-MM': ").strip()
        
        # Проверяем, есть ли данные в кеше
        all_results = cache_manager.load_from_cache(month)
        
        if all_results:
            logging.info(f"Используются данные из кеша для месяца {month}")
        else:
            # Работа с почтой
            with email_client.connect() as mail:
                email_ids = email_client.fetch_emails(mail, "taxi.yandex.ru", month)
                if not email_ids:
                    logging.info("Писем за указанный месяц не найдено.")
                    return

                all_results = []
                for email_id in email_ids:
                    status, data = mail.fetch(email_id, '(RFC822)')
                    if status == 'OK' and data:
                        logging.debug(f"Обработка письма ID: {email_id.decode()}")
                        content = email_client.extract_html_from_email(data[0][1])
                        if content:
                            results = email_parser.parse_email_content(content)
                            if results:
                                all_results.extend(results)

                # Сохраняем результаты в кеш
                if all_results:
                    cache_manager.save_to_cache(month, all_results)

        # Вывод результатов
        if all_results:
            # Вывод информации о поездках
            for result in all_results:
                print(result)
            logging.info(f"Поездок по заданным адресам: {len(all_results)}")
            
            try:
                # Добавляем вывод недель и формул с табуляцией
                print("\n# Рабочие недели месяца:")
                weeks_str, formulas_str = TripAnalytics.format_weekly_costs(all_results, month)
                print(weeks_str)
                print("\n# Формулы расчета стоимости по неделям:")
                print(formulas_str)
            except Exception as e:
                logging.error(f"Ошибка при формировании аналитики: {e}")
        else:
            logging.info("Маршруты с заданными параметрами не найдены.")
    except Exception as e:
        logging.error(f"Общая ошибка: {e}")

if __name__ == "__main__":
    main() 