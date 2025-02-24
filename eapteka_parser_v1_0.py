import requests
from bs4 import BeautifulSoup
import uuid
from datetime import datetime
import asyncio
from googletrans import Translator


async def async_translate_to_russian(text):
    """
    Асинхронно переводит текст на русский язык, если исходный язык не русский.
    """
    translator = Translator()
    detected = await translator.detect(text)
    if detected.lang != 'ru':
        translated = await translator.translate(text, dest='ru')
        return translated.text
    return text


def translate_to_russian(text):
    """
    Синхронная обёртка для асинхронного перевода.
    """
    return asyncio.run(async_translate_to_russian(text))


def parse_eapteka(drug_name):
    """
    Парсит отзывы о лекарственном препарате с сайта eapteka.ru.

    При необходимости переводит drug_name на русский язык.
    Возвращает список словарей, где каждый отзыв имеет следующую структуру:
      - pub_date: дата публикации отзыва,
      - title: заголовок отзыва,
      - methods: текст отзыва (подробное содержание),
      - results: оценка препарата (если имеется),
      - figures_tables: оставлено как None (нет графических данных),
      - source: источник ("eapteka.ru"),
      - article_id: уникальный идентификатор отзыва,
      - query_date: дата запроса.
    """
    # Перевод названия препарата на русский язык, если требуется
    drug_name_ru = translate_to_russian(drug_name)

    # Формирование URL для поиска по препарату
    url = f"https://www.eapteka.ru/search/?q={drug_name_ru}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Ошибка при запросе к {url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    reviews = []

    # Предположим, что каждый отзыв находится в блоке <div class="eapteka-review">
    review_items = soup.find_all("div", class_="eapteka-review")
    for item in review_items:
        # Извлечение даты публикации отзыва
        pub_date = item.find("span", class_="review-date").get_text(strip=True) if item.find("span",
                                                                                             class_="review-date") else ""
        # Заголовок отзыва (если отсутствует, формируем стандартный заголовок)
        title = item.find("h3", class_="review-title").get_text(strip=True) if item.find("h3",
                                                                                         class_="review-title") else f"Отзыв о {drug_name_ru}"
        # Текст отзыва
        content = item.find("div", class_="review-text").get_text(strip=True) if item.find("div",
                                                                                           class_="review-text") else ""
        # Оценка препарата
        rating = item.find("span", class_="review-rating").get_text(strip=True) if item.find("span",
                                                                                             class_="review-rating") else ""

        # Генерация уникального идентификатора отзыва
        article_id = str(uuid.uuid4())
        query_date = datetime.now().strftime("%d_%m_%Y")

        review = {
            "pub_date": pub_date,
            "title": title,
            "methods": content,
            "results": rating,
            "figures_tables": None,
            "source": "eapteka.ru",
            "article_id": article_id,
            "query_date": query_date
        }
        reviews.append(review)

    return reviews


if __name__ == "__main__":
    drug_name_input = input("Введите название лекарственного препарата: ").strip()
    if not drug_name_input:
        print("Название препарата не может быть пустым.")
    else:
        parsed_reviews = parse_eapteka(drug_name_input)
        import json

        print(json.dumps(parsed_reviews, ensure_ascii=False, indent=2))
