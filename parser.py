import imaplib
import email
import ast
import os
import logging
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from contextlib import contextmanager

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
MAILBOX_PATH = os.getenv("MAILBOX_PATH", "INBOX")

# Считывание ROUTES_TO_FIND из .env файла и преобразование строки в список
ROUTES_TO_FIND = ast.literal_eval(os.getenv("ROUTES_TO_FIND", "[]"))


@contextmanager
def imap_connection():
    """Контекстный менеджер для подключения к серверу IMAP."""
    mail = None
    try:
        logging.info("Подключение к серверу IMAP...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mailbox_path_encoded = MAILBOX_PATH.encode('utf-7').decode('ascii')
        status, _ = mail.select(f'"{mailbox_path_encoded}"')
        if status != 'OK':
            raise Exception(f"Не удалось открыть папку: {MAILBOX_PATH}")
        logging.info(f"Успешно подключено к папке: {MAILBOX_PATH}")
        yield mail
    except Exception as e:
        logging.error(f"Ошибка подключения к почтовому серверу: {e}")
        raise
    finally:
        if mail:
            mail.logout()
            logging.info("Отключение от IMAP.")


def calculate_date_range(month):
    """Вычисление диапазона дат для поиска."""
    start_date = datetime.strptime(month, "%Y-%m")
    end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    logging.debug(f"Диапазон дат: {start_date.strftime('%d-%b-%Y')} - {end_date.strftime('%d-%b-%Y')}")
    return start_date.strftime("%d-%b-%Y"), end_date.strftime("%d-%b-%Y")


def fetch_emails(mail, sender, month):
    """Поиск и загрузка писем."""
    try:
        start_date, end_date = calculate_date_range(month)
        query = f'FROM "{sender}" SINCE {start_date} BEFORE {end_date}'
        logging.debug(f"IMAP-запрос: {query}")
        status, messages = mail.search(None, query)
        if status != 'OK':
            logging.warning("Не удалось выполнить поиск писем.")
            return []
        email_ids = messages[0].split()
        logging.info(f"Найдено писем: {len(email_ids)}")
        return email_ids
    except Exception as e:
        logging.error(f"Ошибка при поиске писем: {e}")
        return []


def extract_html_from_email(email_data):
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


def parse_email_content(content):
    """Парсинг содержимого письма с учётом маршрутов из ROUTES_TO_FIND."""
    try:
        soup = BeautifulSoup(content, 'html.parser')

        # Извлечение маршрутов
        route_points = soup.find_all('tr', class_='route__point')
        if not route_points or len(route_points) < 2:
            logging.warning("Не удалось извлечь маршрутные точки.")
            return []

        # Получаем начальную и конечную точки маршрута
        start_point = route_points[0].find('p', class_='route__point-name').get_text(strip=True)
        end_point = route_points[-1].find('p', class_='route__point-name').get_text(strip=True)
        logging.debug(f"Начало маршрута: {start_point}, Конец маршрута: {end_point}")

        # Проверка на сообщения о маршруте
        route_message = soup.find('p', class_='route__message')
        if route_message:
            route_message_text = route_message.get_text(strip=True)
            logging.debug(f"Сообщение о маршруте: {route_message_text}")
        else:
            route_message_text = None

        # Извлечение времени
        start_time = route_points[0].find('p', class_='hint').get_text(strip=True) if route_points[0].find('p', class_='hint') else "N/A"
        end_time = route_points[-1].find('p', class_='hint').get_text(strip=True) if route_points[-1].find('p', class_='hint') else "N/A"
        logging.debug(f"Время отправления: {start_time}, Время прибытия: {end_time}")

        # Извлечение стоимости
        cost = soup.find('td', class_='report__value_main')
        cost_text = cost.get_text(strip=True) if cost else "N/A"
        logging.debug(f"Стоимость: {cost_text}")

        # Извлечение даты
        date_row = soup.find('td', string="Дата")
        date_text = date_row.find_next_sibling('td').get_text(strip=True) if date_row else "N/A"
        logging.debug(f"Дата поездки: {date_text}")

        # Проверка маршрута на соответствие ROUTES_TO_FIND
        for point_a, point_b in ROUTES_TO_FIND:
            if (point_a in start_point and point_b in end_point) or (point_a in end_point and point_b in start_point):
                # Если есть сообщение о смене направления, учесть его
                if route_message_text and "Точка назначения изменена" in route_message_text:
                    direction = f"{end_point} -> {start_point}"
                else:
                    direction = f"{start_point} -> {end_point}"

                # Формирование результата
                result = f"Маршрут: {direction}, Стоимость: {cost_text}, Дата: {date_text}, Время: {start_time} - {end_time}"
                logging.debug(f"Найден маршрут: {result}")
                return [result]

        # Если маршрут не соответствует ROUTES_TO_FIND, не возвращаем его
        return []
    except Exception as e:
        logging.error(f"Ошибка при парсинге содержимого письма: {e}")
        return []



def main():
    try:
        month = input("Введите месяц в формате 'YYYY-MM': ").strip()
        with imap_connection() as mail:
            email_ids = fetch_emails(mail, "taxi.yandex.ru", month)
            if not email_ids:
                logging.info("Писем за указанный месяц не найдено.")
                return

            all_results = []
            for email_id in email_ids:
                status, data = mail.fetch(email_id, '(RFC822)')
                if status == 'OK' and data:
                    logging.debug(f"Обработка письма ID: {email_id.decode()}")
                    content = extract_html_from_email(data[0][1])
                    if content:
                        results = parse_email_content(content)
                        if results:
                            all_results.extend(results)

            if all_results:
                for result in all_results:
                    print(result)
            else:
                logging.info("Маршруты с заданными параметрами не найдены.")
    except Exception as e:
        logging.error(f"Общая ошибка: {e}")


if __name__ == "__main__":
    main()
