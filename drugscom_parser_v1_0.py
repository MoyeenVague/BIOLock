import hashlib
from datetime import datetime
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

def fetch_drugscom_reviews(drug_name):
    query_date = datetime.now().strftime("%d_%m_%Y")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.drugs.com/",
        "DNT": "1"
    }

    session = HTMLSession()
    try:
        response = session.get(
            f"https://www.drugs.com/drug-reviews/{drug_name.lower().replace(' ', '-')}.html",
            headers=headers,
            timeout=20
        )
        response.html.render(sleep=2)
    except Exception as e:
        print(f"Drugs.com error: {e}")
        return None

    reviews = []
    for review in response.html.find('div.ddc-comments-content'):
        text = review.text.strip()
        if text and len(text) > 20:
            reviews.append(text)
        if len(reviews) >= 5:
            break
    if not reviews:
        print("Отзывы не найдены на странице Drugs.com.")
        return None

    results_text = " ".join(reviews)
    title = f"Drugs.com post: {drug_name}, {query_date}"
    return create_entry(None, title, None, results_text, None, "Drugs.com", query_date)

def parse_drugscom(drug_name):
    review = fetch_drugscom_reviews(drug_name)
    return [review] if review else []
