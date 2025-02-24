import requests
import xml.etree.ElementTree as ET
import hashlib
from datetime import datetime
import spacy

SIDE_EFFECT_KEYWORDS = ['side effect', 'adverse event', 'safety', 'tolerability', 'toxicity', 'complication']
FIGURE_LABELS = {"figure", "fig", "table", "tbl", "figure caption", "table caption"}

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

def search_pubmed(query, retstart=0, retmax=30):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "retstart": retstart,
        "retmode": "json"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    total_count = int(data["esearchresult"]["count"])
    id_list = data["esearchresult"]["idlist"]
    return total_count, id_list

def fetch_article(article_id):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": article_id,
        "retmode": "xml"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.text

def parse_article(xml_data):
    root = ET.fromstring(xml_data)
    pub_date = None
    pub_date_elem = root.find(".//PubDate")
    if pub_date_elem is not None:
        year = pub_date_elem.find("Year")
        month = pub_date_elem.find("Month")
        day = pub_date_elem.find("Day")
        if year is not None:
            pub_date = year.text
            if month is not None:
                pub_date += "-" + month.text
            if day is not None:
                pub_date += "-" + day.text

    title_elem = root.find(".//ArticleTitle")
    title = ''.join(title_elem.itertext()) if title_elem is not None else None

    methods_text = None
    results_text = None
    figures_texts = []
    for abstract in root.findall(".//Abstract"):
        for abstract_text in abstract.findall("AbstractText"):
            label = abstract_text.attrib.get("Label", "").lower()
            text_content = ''.join(abstract_text.itertext())
            if label == "methods":
                methods_text = text_content
            elif label == "results":
                results_text = text_content
            elif label in FIGURE_LABELS:
                figures_texts.append(text_content)
    figures_tables = " ".join(figures_texts) if figures_texts else None

    query_date = datetime.now().strftime("%d_%m_%Y")
    return create_entry(pub_date, title, methods_text, results_text, figures_tables, "pubmed", query_date)

def is_side_effect_study(entry):
    combined_text = ""
    for key in ["methods", "results", "figures_tables"]:
        if entry.get(key):
            combined_text += entry.get(key).lower() + " "
    return any(keyword in combined_text for keyword in SIDE_EFFECT_KEYWORDS)

def parse_pubmed(drug_name, accepted_required=33):
    enhanced_query = f'{drug_name} AND ("side effect" OR "adverse event" OR safety OR tolerability)'
    results = []
    accepted_count = 0
    retstart = 0
    batch_size = 30
    query_date = datetime.now().strftime("%d_%m_%Y")

    try:
        total_count, id_list = search_pubmed(enhanced_query, retstart=retstart, retmax=batch_size)
    except Exception as e:
        print(f"Ошибка при поиске статей: {e}")
        return []

    while accepted_count < accepted_required and retstart < total_count:
        try:
            _, id_list = search_pubmed(enhanced_query, retstart=retstart, retmax=batch_size)
        except Exception as e:
            print(f"Ошибка при запросе статей: {e}")
            break

        for article_id in id_list:
            if accepted_count >= accepted_required:
                break
            try:
                xml_data = fetch_article(article_id)
                entry = parse_article(xml_data)
                if is_side_effect_study(entry):
                    results.append(entry)
                    accepted_count += 1
            except Exception as e:
                print(f"Ошибка обработки статьи {article_id}: {e}")
        retstart += batch_size

    return results
