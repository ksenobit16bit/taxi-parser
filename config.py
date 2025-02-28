# config.py - Работа с конфигурацией
import os
import ast
import logging
from dotenv import load_dotenv

def setup_logging(level=logging.INFO):
    """Настройка логирования."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )

def load_config():
    """Загрузка конфигурации из .env файла."""
    load_dotenv()
    
    # Получаем строку ADDRESSES_TO_FIND
    addresses_str = os.getenv("ADDRESSES_TO_FIND", "[]")
    logging.debug(f"Загружена строка ADDRESSES_TO_FIND: {addresses_str[:100]}...")
    
    # Обрабатываем строку с адресами
    addresses = []
    try:
        # Удаляем начальные и конечные скобки
        if addresses_str.startswith("[") and addresses_str.endswith("]"):
            addresses_str = addresses_str[1:-1].strip()
            
            # Разбиваем на отдельные адреса
            import re
            # Находим все строки в кавычках
            address_matches = re.findall(r'[\'"]([^\'"]+)[\'"]', addresses_str)
            
            for address in address_matches:
                addresses.append(address.strip())
                
        logging.debug(f"Распознано {len(addresses)} адресов: {addresses}")
    except Exception as e:
        logging.error(f"Ошибка при разборе ADDRESSES_TO_FIND: {e}")
        addresses = []
    
    # Получаем обязательный адрес
    required_address = os.getenv("REQUIRED_ADDRESS", "")
    if required_address:
        logging.debug(f"Обязательный адрес: {required_address}")
    
    # Получаем адреса для исключения
    excluded_addresses_str = os.getenv("EXCLUDED_ADDRESSES", "[]")
    excluded_addresses = []
    try:
        # Удаляем начальные и конечные скобки
        if excluded_addresses_str.startswith("[") and excluded_addresses_str.endswith("]"):
            excluded_addresses_str = excluded_addresses_str[1:-1].strip()
            
            # Разбиваем на отдельные адреса
            import re
            # Находим все строки в кавычках
            address_matches = re.findall(r'[\'"]([^\'"]+)[\'"]', excluded_addresses_str)
            
            for address in address_matches:
                excluded_addresses.append(address.strip())
                
        logging.debug(f"Распознано {len(excluded_addresses)} адресов для исключения: {excluded_addresses}")
    except Exception as e:
        logging.error(f"Ошибка при разборе EXCLUDED_ADDRESSES: {e}")
        excluded_addresses = []
    
    config = {
        "IMAP_SERVER": os.getenv("IMAP_SERVER"),
        "EMAIL": os.getenv("EMAIL"),
        "PASSWORD": os.getenv("PASSWORD"),
        "MAILBOX_PATH": os.getenv("MAILBOX_PATH", "INBOX"),
        "ADDRESSES_TO_FIND": addresses,
        "REQUIRED_ADDRESS": required_address,
        "EXCLUDED_ADDRESSES": excluded_addresses
    }
    return config 