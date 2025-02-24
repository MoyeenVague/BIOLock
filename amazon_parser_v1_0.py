import requests
import hashlib
from datetime import datetime
import time
import urllib.parse
from bs4 import BeautifulSoup
from requests_html import HTMLSession

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

def get_with_retries(url, headers, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса {url}: {e}. Попытка {attempt+1} из {retries}.")
            time.sleep(delay)
    return None

def fetch_amazon_reviews(drug_name):
    query_date = datetime.now().strftime("%d_%m_%Y")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.amazon.com/",
    }

    session = HTMLSession()
    try:
        search_response = session.get(
            f"https://www.amazon.com/s?k={urllib.parse.quote(drug_name)}",
            headers=headers,
            timeout=20
        )
        search_response.html.render(sleep=2)
    except Exception as e:
        print(f"Amazon search error: {e}")
        return None

    matching_products = []
    for item in search_response.html.find('div[data-asin]'):
        asin = item.attrs.get('data-asin')
        title_elem = item.find('span.a-text-normal', first=True)
        if asin and title_elem:
            title_text = title_elem.text.lower()
            if drug_name.lower() in title_text:
                matching_products.append({
                    "asin": asin,
                    "title": title_elem.text
                })
        if len(matching_products) >= 10:
            break

    all_reviews = []
    for product in matching_products:
        reviews_url = f"https://www.amazon.com/product-reviews/{product['asin']}/"
        reviews_response = get_with_retries(reviews_url, headers)
        if not reviews_response:
            continue
        reviews_soup = BeautifulSoup(reviews_response.text, "html.parser")
        for span in reviews_soup.find_all("span", class_="a-size-base review-text"):
            text = span.get_text(strip=True)
            if text and len(text) > 20:
                all_reviews.append(text)
            if len(all_reviews) >= 5:
                break
        if len(all_reviews) >= 5:
            continue

    if not all_reviews:
        print("Отзывы не найдены на страницах товаров Amazon.")
        return None

    results_text = " ".join(all_reviews)
    title = f"Amazon post: {drug_name}, {query_date}"
    return create_entry(None, title, None, results_text, None, "Amazon", query_date)

def parse_amazon(drug_name):
    review = fetch_amazon_reviews(drug_name)
    return [review] if review else []
