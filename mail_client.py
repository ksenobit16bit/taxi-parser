# mail_client.py - Работа с почтой
import imaplib
import email
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta

class EmailClient:
    """Класс для работы с почтой."""
    
    def __init__(self, config):
        """Инициализация клиента."""
        self.config = config
    
    def connect(self):
        """Подключение к почтовому серверу."""
        try:
            logging.info("Подключение к серверу IMAP...")
            mail = imaplib.IMAP4_SSL(self.config["IMAP_SERVER"])
            mail.login(self.config["EMAIL"], self.config["PASSWORD"])
            
            # Получаем список папок
            status, mailboxes = mail.list()
            if status != 'OK':
                logging.error("Не удалось получить список папок.")
                return None
            
            # Ищем папку, содержащую "taxi" или "такси"
            target_mailbox = None
            for mailbox in mailboxes:
                mailbox_name = mailbox.decode('utf-8', errors='ignore')
                if "taxi" in mailbox_name.lower() or "такси" in mailbox_name.lower():
                    # Извлекаем имя папки
                    parts = mailbox_name.split(' "')
                    if len(parts) > 1:
                        target_mailbox = parts[-1].strip('"')
                        break
            
            # Если не нашли специальную папку, используем INBOX
            if not target_mailbox:
                target_mailbox = self.config["MAILBOX_PATH"]
            
            # Выбираем папку
            status, data = mail.select(target_mailbox)
            if status != 'OK':
                logging.warning(f"Не удалось выбрать папку {target_mailbox}, пробуем INBOX")
                status, data = mail.select("INBOX")
                if status != 'OK':
                    logging.error("Не удалось выбрать папку INBOX")
                    return None
                logging.info("Успешно подключено к папке: INBOX")
            else:
                logging.info(f"Успешно подключено к папке: {target_mailbox}")
            
            return mail
        except Exception as e:
            logging.error(f"Ошибка при подключении к почте: {e}")
            return None
    
    def calculate_date_range(self, month):
        """Вычисление диапазона дат для поиска."""
        start_date = datetime.strptime(month, "%Y-%m")
        end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        logging.debug(f"Диапазон дат: {start_date.strftime('%d-%b-%Y')} - {end_date.strftime('%d-%b-%Y')}")
        return start_date.strftime("%d-%b-%Y"), end_date.strftime("%d-%b-%Y")
    
    def fetch_emails(self, mail, month):
        """Поиск и загрузка писем."""
        try:
            start_date, end_date = self.calculate_date_range(month)
            
            # Используем запрос только по дате
            query = f'SINCE {start_date} BEFORE {end_date}'
            logging.debug(f"IMAP-запрос: {query}")
            
            status, messages = mail.search(None, query)
            if status != 'OK':
                logging.warning("Не удалось выполнить поиск писем.")
                return []
            
            email_ids = messages[0].split()
            if not email_ids:
                logging.info("Писем за указанный период не найдено.")
                return []
            
            logging.info(f"Найдено писем за месяц: {len(email_ids)}")
            return email_ids
        except Exception as e:
            logging.error(f"Ошибка при поиске писем: {e}")
            return []
    
    def extract_html_from_email(self, email_data):
        """Извлечение HTML-содержимого письма."""
        try:
            msg = email.message_from_bytes(email_data)
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/html':
                        html_content = part.get_payload(decode=True).decode()
                        return html_content
            elif msg.get_content_type() == 'text/html':
                html_content = msg.get_payload(decode=True).decode()
                return html_content
        except Exception as e:
            logging.error(f"Ошибка при извлечении HTML: {e}")
        return None 