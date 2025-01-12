import deepl
from config import DEEPL_API_KEY
import logging

def translate_text(text, from_lang, formality=None):
    """Переводит текст с использованием DeepL API."""
    if not isinstance(text, str) or not text:
        raise ValueError("Text must be a non-empty string.")

    try:
        translator = deepl.Translator(DEEPL_API_KEY)
        result = translator.translate_text(text=text, source_lang=from_lang, target_lang='EN-GB')
        return result.text
    except Exception as e:
        logging.error(f"Ошибка при переводе текста: {e}")
        return text
