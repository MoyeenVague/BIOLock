import requests
import hashlib
from datetime import datetime
import urllib.parse
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from googletrans import Translator

SIDE_EFFECT_KEYWORDS = ['side effect', 'adverse event', 'safety', 'tolerability', 'toxicity', 'complication']

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

def fetch_uppsalareports(drug_name):
    query_date = datetime.now().strftime("%d_%m_%Y")
    session = HTMLSession()
    try:
        response = session.get(
            f"https://uppsalareports.org/?s={urllib.parse.quote(drug_name)}",
            timeout=20
        )
        response.html.render(sleep=1)
    except Exception as e:
        print(f"Uppsala error: {e}")
        return None

    matching_links = []
    for link in response.html.find('a'):
        href = link.attrs.get('href', '')
        if drug_name.lower() in href.lower() or drug_name.lower() in link.text.lower():
            matching_links.append(href)
        if len(matching_links) >= 5:
            break
    if not matching_links:
        print("Не найдено релевантных ссылок для препарата на uppsalareports.org.")
        return None

    collected_texts = []
    for url in matching_links:
        try:
            detail_response = requests.get(url)
            detail_response.raise_for_status()
        except Exception as e:
            print(f"Ошибка при запросе страницы {url}: {e}")
            continue
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")
        content = detail_soup.find("div", class_="entry-content")
        if not content:
            content = detail_soup.find("div", id="content")
        text = content.get_text(separator=" ", strip=True) if content else detail_soup.get_text(separator=" ", strip=True)
        if any(keyword in text.lower() for keyword in SIDE_EFFECT_KEYWORDS):
            collected_texts.append(text)
    if not collected_texts:
        print("Ни на одной из страниц uppsalareports.org не обнаружены ключевые слова, связанные с побочными эффектами.")
        return None

    combined_text = " ".join(collected_texts)
    title = f"Uppsala Reports post: {drug_name}, {query_date}"
    return create_entry(None, title, None, combined_text, None, "uppsalareports.org", query_date)

def parse_uppsala(drug_name):
    review = fetch_uppsalareports(drug_name)
    return [review] if review else []
