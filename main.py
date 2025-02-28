# main.py - Точка входа
import logging
import os
import argparse
from config import setup_logging, load_config
from mail_client import EmailClient
from parser import EmailParser
from analytics import TripAnalytics
from cache_manager import CacheManager

def main():
    # Обработка аргументов командной строки
    parser = argparse.ArgumentParser(description='Анализ поездок на такси')
    parser.add_argument('--logging-level', type=str, default='INFO',
                        help='Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    args = parser.parse_args()
    
    # Настройка логирования с учетом аргумента командной строки
    log_level = getattr(logging, args.logging_level.upper(), logging.INFO)
    setup_logging(log_level)
    
    try:
        # Загрузка конфигурации
        config = load_config()
        
        # Проверка содержимого .env файла
        logging.debug(f"Содержимое .env файла:")
        with open('.env', 'r') as f:
            env_content = f.read()
            logging.debug(env_content)
        
        # Запрос месяца от пользователя
        month = input("Введите месяц в формате 'YYYY-MM': ")
        
        # Инициализация кеш-менеджера
        cache_manager = CacheManager()
        
        # Проверка наличия кеша
        if cache_manager.has_cache(month):
            trips = cache_manager.load_from_cache(month)
            logging.info(f"Используются данные из кеша для месяца {month}")
        else:
            # Инициализация клиента электронной почты
            email_client = EmailClient(config)
            
            # Инициализация парсера писем
            addresses_to_find = config["ADDRESSES_TO_FIND"]
            required_address = config["REQUIRED_ADDRESS"]
            excluded_addresses = config["EXCLUDED_ADDRESSES"]
            email_parser = EmailParser(addresses_to_find, required_address, excluded_addresses)
            
            # Получение и обработка писем
            trips = []
            with email_client.connect() as mail:
                email_ids = email_client.fetch_emails(mail, month)
                
                for email_id in email_ids:
                    status, data = mail.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    email_data = data[0][1]
                    html_content = email_client.extract_html_from_email(email_data)
                    
                    if html_content:
                        trip_results = email_parser.parse_email_content(html_content)
                        trips.extend(trip_results)
            
            # Сохранение результатов в кеш
            cache_manager.save_to_cache(month, trips)
        
        # Вывод результатов
        for trip in trips:
            print(trip)
        
        logging.info(f"Поездок по заданным адресам: {len(trips)}")
        
        # Анализ поездок
        if trips:
            # Получение рабочих недель и формул расчета
            weeks_str, formulas_str = TripAnalytics.format_weekly_costs(trips, month)
            
            print("\n# Рабочие недели месяца:")
            print(weeks_str)
            
            print("\n# Формулы расчета стоимости по неделям:")
            print(formulas_str)
        else:
            logging.info("Маршруты с заданными параметрами не найдены.")
    except Exception as e:
        logging.error(f"Общая ошибка: {e}")

if __name__ == "__main__":
    main() 