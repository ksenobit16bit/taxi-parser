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
        self.imap_server = config["IMAP_SERVER"]
        self.email = config["EMAIL"]
        self.password = config["PASSWORD"]
        self.mailbox_path = config["MAILBOX_PATH"]
    
    @contextmanager
    def connect(self):
        """Контекстный менеджер для подключения к серверу IMAP."""
        mail = None
        try:
            logging.info("Подключение к серверу IMAP...")
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email, self.password)
            mailbox_path_encoded = self.mailbox_path.encode('utf-7').decode('ascii')
            status, _ = mail.select(f'"{mailbox_path_encoded}"')
            if status != 'OK':
                raise Exception(f"Не удалось открыть папку: {self.mailbox_path}")
            logging.info(f"Успешно подключено к папке: {self.mailbox_path}")
            yield mail
        except Exception as e:
            logging.error(f"Ошибка подключения к почтовому серверу: {e}")
            raise
        finally:
            if mail:
                try:
                    mail.close()
                    mail.logout()
                    logging.info("Отключение от IMAP.")
                except:
                    pass
    
    def calculate_date_range(self, month):
        """Вычисление диапазона дат для поиска."""
        start_date = datetime.strptime(month, "%Y-%m")
        end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        logging.debug(f"Диапазон дат: {start_date.strftime('%d-%b-%Y')} - {end_date.strftime('%d-%b-%Y')}")
        return start_date.strftime("%d-%b-%Y"), end_date.strftime("%d-%b-%Y")
    
    def fetch_emails(self, mail, sender, month):
        """Поиск и загрузка писем."""
        try:
            start_date, end_date = self.calculate_date_range(month)
            query = f'FROM "{sender}" SINCE {start_date} BEFORE {end_date}'
            logging.debug(f"IMAP-запрос: {query}")
            status, messages = mail.search(None, query)
            if status != 'OK':
                logging.warning("Не удалось выполнить поиск писем.")
                return []
            email_ids = messages[0].split()
            logging.info(f"Найдено писем с поездками за месяц: {len(email_ids)}")
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
                        logging.debug(f"Извлечён HTML-содержимое письма (первые 500 символов): {html_content[:500]}...")
                        return html_content
            elif msg.get_content_type() == 'text/html':
                html_content = msg.get_payload(decode=True).decode()
                logging.debug(f"Извлечён HTML-содержимое письма (первые 500 символов): {html_content[:500]}...")
                return html_content
        except Exception as e:
            logging.error(f"Ошибка при извлечении HTML: {e}")
        return None 