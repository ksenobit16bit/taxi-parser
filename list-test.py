import os
import imaplib
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

# Загрузка переменных окружения
load_dotenv()
IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")


def connect_to_mail():
    """Подключение к серверу IMAP и авторизация."""
    try:
        logging.info("Подключение к серверу IMAP...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        logging.info("Успешно подключено к почтовому ящику.")
        return mail
    except imaplib.IMAP4.error as e:
        logging.error(f"Ошибка авторизации: {e}")
        raise
    except Exception as e:
        logging.error(f"Ошибка подключения к серверу: {e}")
        raise


def list_folders(mail):
    """Вывод доступных папок."""
    try:
        status, folders = mail.list()
        if status != 'OK':
            logging.error("Не удалось получить список папок.")
            return

        logging.info("Доступные папки:")
        for folder in folders:
            print(folder.decode())
    except Exception as e:
        logging.error(f"Ошибка при получении списка папок: {e}")


def main():
    """Основная логика."""
    try:
        if not IMAP_SERVER or not EMAIL or not PASSWORD:
            logging.critical("Отсутствуют параметры подключения (IMAP_SERVER, EMAIL, PASSWORD).")
            return

        mail = connect_to_mail()
        list_folders(mail)
        mail.logout()

    except Exception as e:
        logging.error(f"Общая ошибка: {e}")


if __name__ == "__main__":
    main()
