import requests
import hashlib
from datetime import datetime
import spacy
import time

# Ключевые слова для поиска побочных эффектов
SIDE_EFFECT_KEYWORDS = ['side effect', 'adverse event', 'safety', 'tolerability', 'toxicity', 'complication']

# Загрузка модели scispacy (при первом вызове)
try:
    nlp = spacy.load("en_core_sci_sm")
except Exception as e:
    print("Ошибка загрузки модели en_core_sci_sm. Убедитесь, что она установлена.")
    nlp = None


def generate_article_id(title, results):
    unique_str = title + (results if results else "")
    return hashlib.md5(unique_str.encode("utf-8")).hexdigest()


def create_entry(pub_date, title, methods, results, figures_tables, source, query_date):
    article_id = generate_article_id(title, results)
    return {
        "pub_date": pub_date,
        "title": title,
        "methods": methods,
        "results": results,
        "figures_tables": figures_tables,
        "source": source,
        "article_id": article_id,
        "query_date": query_date
    }


def is_side_effect_study(entry):
    """Проверяет, содержит ли объединённый текст (methods, results, figures_tables) ключевые слова, связанные с побочными эффектами."""
    combined_text = ""
    for key in ["methods", "results", "figures_tables"]:
        if entry.get(key):
            combined_text += entry.get(key).lower() + " "
    return any(keyword in combined_text for keyword in SIDE_EFFECT_KEYWORDS)


def search_semantic_api(query, limit, retries=3, backoff_factor=1):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,year,abstract,url"
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except requests.HTTPError as e:
            if response.status_code == 429:
                wait = backoff_factor * (2 ** attempt)
                print(f"Получен 429, повторная попытка через {wait} секунд...")
                time.sleep(wait)
            else:
                print(f"HTTP ошибка: {e}")
                break
    return []


def parse_semanticscholar(drug_name, accepted_required=33):
    """
    Выполняет поиск публикаций через API Semantic Scholar.

    1. Сначала используется расширенный запрос – препарат + ключевые слова для побочных эффектов.
    2. Если публикаций, удовлетворяющих критерию (наличие ключевых слов в аннотации), не найдено,
       выполняется fallback‑поиск по названию препарата.

    Результаты возвращаются в виде списка словарей со следующими ключами:
      - "pub_date"
      - "title"
      - "methods"        (для Semantic Scholar отсутствует, поэтому None)
      - "results"        (аннотация публикации)
      - "figures_tables" (отсутствуют, поэтому None)
      - "source"
      - "article_id"
      - "query_date"
    """
    results = []
    # Первый этап: расширенный запрос
    enhanced_query = f'{drug_name} side effect adverse event safety tolerability'
    # Запрашиваем больше результатов для возможности фильтрации
    api_results = search_semantic_api(enhanced_query, accepted_required * 2)

    accepted_count = 0
    for paper in api_results:
        title = paper.get("title")
        year = paper.get("year")
        abstract = paper.get("abstract")
        if not title or not abstract:
            continue
        pub_date = str(year) if year else None
        entry = create_entry(pub_date, title, None, abstract, None, "semanticscholar",
                             datetime.now().strftime("%d_%m_%Y"))
        if is_side_effect_study(entry):
            results.append(entry)
            accepted_count += 1
            if accepted_count >= accepted_required:
                break

    # Если по расширенному запросу не найдено публикаций – fallback: поиск только по названию препарата
    if accepted_count == 0:
        print("Публикации с упоминанием побочных эффектов не найдены. Выполняется fallback-поиск по препарату.")
        fallback_api_results = search_semantic_api(drug_name, accepted_required)
        for paper in fallback_api_results:
            title = paper.get("title")
            year = paper.get("year")
            abstract = paper.get("abstract")
            if not title or not abstract:
                continue
            pub_date = str(year) if year else None
            entry = create_entry(pub_date, title, None, abstract, None, "semanticscholar",
                                 datetime.now().strftime("%d_%m_%Y"))
            results.append(entry)
            accepted_count += 1
            if accepted_count >= accepted_required:
                break

    return results


if __name__ == "__main__":
    query = input("Введите название препарата для поиска побочных эффектов в Semantic Scholar: ").strip()
    if query:
        entries = parse_semanticscholar(query)
        if entries:
            for entry in entries:
                print("------------------------------------------------")
                print(f"Название: {entry['title']}")
                print(f"Дата публикации: {entry['pub_date']}")
                print(f"Аннотация: {entry['results']}")
                print(f"Article ID: {entry['article_id']}")
                print("------------------------------------------------")
        else:
            print("Не найдено публикаций.")
    else:
        print("Пустой запрос.")
