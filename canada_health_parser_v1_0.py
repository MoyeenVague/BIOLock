import requests
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime


def generate_article_id(title, results):
    """Генерирует уникальный идентификатор на основе заголовка и текста результатов."""
    unique_str = title + (results if results else "")
    return hashlib.md5(unique_str.encode("utf-8")).hexdigest()


def create_entry(pub_date, title, methods, results_text, figures_tables, source, query_date):
    """Создает словарь с данными записи."""
    article_id = generate_article_id(title, results_text)
    return {
        "pub_date": pub_date,
        "title": title,
        "methods": methods,
        "results": results_text,
        "figures_tables": figures_tables,
        "source": source,
        "article_id": article_id,
        "query_date": query_date
    }


def parse_health_canada(drug_name):
    """
    Выполняет поиск по сайту Health Canada (https://cvp-pcv.hc-sc.gc.ca/arq-rei/index-eng.jsp)
    с использованием GET-параметра 'drugName'. Затем парсит HTML-страницу и извлекает записи из таблицы.

    Предполагается, что результаты размещены в таблице с id="resultsTable", где:
      - 1-я колонка: заголовок/название документа,
      - 2-я колонка: дата публикации,
      - 3-я колонка: краткое описание или аннотация.

    Если структура сайта изменится, необходимо скорректировать селекторы.
    """
    results = []
    base_url = "https://cvp-pcv.hc-sc.gc.ca/arq-rei/index-eng.jsp"
    params = {"drugName": drug_name}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Ошибка при запросе к {base_url}: {e}")
        return results

    soup = BeautifulSoup(response.text, "html.parser")

    # Попытка найти таблицу с результатами.
    table = soup.find("table", {"id": "resultsTable"})
    if not table:
        print("Не удалось найти таблицу с результатами.")
        return results

    rows = table.find_all("tr")
    # Предполагается, что первая строка – заголовок
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) >= 3:
            title = cols[0].get_text(strip=True)
            pub_date = cols[1].get_text(strip=True)
            summary = cols[2].get_text(strip=True)
            entry = create_entry(pub_date, title, None, summary, None, "health_canada",
                                 datetime.now().strftime("%d_%m_%Y"))
            results.append(entry)

    return results


if __name__ == "__main__":
    query = input("Введите название препарата для поиска на Health Canada: ").strip()
    if query:
        entries = parse_health_canada(query)
        if entries:
            for entry in entries:
                print("------------------------------------------------")
                print(f"Название: {entry['title']}")
                print(f"Дата публикации: {entry['pub_date']}")
                print(f"Описание: {entry['results']}")
                print(f"Article ID: {entry['article_id']}")
                print("------------------------------------------------")
        else:
            print("Не найдено записей для данного препарата.")
    else:
        print("Пустой запрос.")
