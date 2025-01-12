from dateutil import parser
from urllib.parse import urlparse
import tldextract
from translator.translator import translate_text
import re


def convert_to_yyyy_mm_dd(date_string, from_lang):
    try:
        if from_lang.split('-')[0] != 'en':
            date_string = translate_text(date_string, from_lang=from_lang.split('-')[0])
        # Попытка распарсить дату с использованием dateutil.parser
        dt = parser.parse(date_string, fuzzy=True)
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        # Если не удалось распарсить, вернем None или оригинальную строку
        return date_string


def extract_domain(url):
    try:
        # Парсим URL
        parsed_url = urlparse(url)
        # Извлекаем домен
        extracted = tldextract.extract(parsed_url.netloc)
        # Возвращаем доменное имя в формате domain.suffix
        if extracted.subdomain == "www":
            return f"{extracted.domain}.{extracted.suffix}"
        elif extracted.subdomain:
            return f"{extracted.subdomain}.{extracted.domain}.{extracted.suffix}"
        else:
            return f"{extracted.domain}.{extracted.suffix}"
    except Exception as e:
        return None


def check_and_update_status(data):
    """
    Проверяет словарь на наличие значения "Not found".
    Если такое значение найдено, добавляет в словарь ключ "status" со значением "Failed".

    :param data: Входной словарь
    :return: Обновлённый словарь
    """
    if "Not found" in data.values():
        data["status"] = "Failed"
    else:
        data["status"] = "Completed"

    return data


def get_file_path_from_url(url):
    """
    Извлекает категорию из URL, если она присутствует.
    Категория — это первый сегмент пути после имени хоста.

    :param url: URL для проверки
    :return: Категория (путь), если найдена, иначе None
    """
    # Регулярное выражение для поиска первого сегмента после имени хоста
    pattern = r'^(?:https?:\/\/)?[^\/]+\/([^\/]+)\/'

    # Ищем категорию в URL
    match = re.search(pattern, url)

    # Если категория найдена, возвращаем её
    if match:
        return f'/{match.group(1)}/'
    else:
    # Если категории нет, возвращаем None
        return None