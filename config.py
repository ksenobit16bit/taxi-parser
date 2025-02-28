# config.py - Работа с конфигурацией
import os
import ast
import logging
from dotenv import load_dotenv

def setup_logging():
    """Настройка логирования."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )

def load_config():
    """Загрузка конфигурации из .env файла."""
    load_dotenv()
    config = {
        "IMAP_SERVER": os.getenv("IMAP_SERVER"),
        "EMAIL": os.getenv("EMAIL"),
        "PASSWORD": os.getenv("PASSWORD"),
        "MAILBOX_PATH": os.getenv("MAILBOX_PATH", "INBOX"),
        "ROUTES_TO_FIND": ast.literal_eval(os.getenv("ROUTES_TO_FIND", "[]"))
    }
    return config 