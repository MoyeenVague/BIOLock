import json
import re
import pandas as pd
import os
import spacy
from spacy.matcher import PhraseMatcher

# Попытка загрузить модель scispaCy. Нужна en_core_sci_sm.
try:
    nlp = spacy.load("en_core_sci_sm")
except Exception as e:
    print("Error loading scispaCy model:", e)
    nlp = None


def extract_specific_side_effects(article):
    keywords = [
        # Базовые симптомы
        "nausea", "vomiting", "headache", "dizziness", "diarrhea",
        "constipation", "fatigue", "rash", "pain", "edema", "fever",

        # Метаболические/эндокринные
        "hyperglycemia", "hypoglycemia", "hypoglycaemia", "hyperglycaemia",
        "blood sugar", "glucose", "insulin resistance",

        # Окислительный стресс
        "ros", "reactive oxygen species", "oxidative stress",
        "lipid peroxidation", "antioxidant depletion",

        # Сердечно-сосудистые
        "hypertension", "hypotension", "tachycardia", "bradycardia",
        "arrhythmia", "palpitations",

        # Неврологические/психиатрические
        "anxiety", "depression", "insomnia", "seizure", "tremor",
        "confusion", "somnolence"
    ]

    patterns = [
        (r'\b(increased|elevated|high|raised)\s+(blood\s*)?sugar\b', "hyperglycemia"),
        (r'\b(low|decreased|reduced)\s+(blood\s*)?sugar\b', "hypoglycemia"),
        (r'\bROS\s+(production|levels?|generation)\b', "ROS increase"),
        (r'\boxidative\s+stress\b', "oxidative stress"),
        (r'\b(hyperglycemic|hypoglycemic)\s+episodes?\b', "glucose dysregulation"),
        (r'\b(HBA1C|HbA1c|A1C)\s+(increase|elevation)\b', "long-term glucose elevation")
    ]

    combined_text = ""
    for key in ["methods", "results", "conclusion", "figures_tables"]:
        if article.get(key):
            combined_text += " " + article.get(key).lower()

    found_effects = set()

    # Поиск по ключевым словам
    for kw in keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', combined_text):
            found_effects.add(kw.replace("_", " ").title())

    # Поиск по сложным паттернам
    for pattern, label in patterns:
        if re.search(pattern, combined_text):
            found_effects.add(label.title())

    # Поиск слов с -ache
    ache_matches = re.findall(r'\b\w*ache\b', combined_text)
    found_effects.update([m.title() for m in ache_matches])

    return ", ".join(sorted(found_effects)) if found_effects else None


def extract_sample_size(methods_text):
    if not methods_text:
        return None

    text_clean = re.sub(r'[\.,;]\s*', ' ', methods_text.lower())  # Удаляем пунктуацию
    text_clean = re.sub(r'\s+', ' ', text_clean)  # Убираем множественные пробелы

    patterns = [
        r'\b[nN][\s\-]*[=:]\s*(\d+[\d,]*)',  # N=100, n:50, N = 150
        r'(?:total|sample)\s+(?:of|size)\s*[=:]*\s*(\d+[\d,]*)',  # "total of 100", "sample size=50"
        r'enrolled\s+(\d+[\d,]*)',  # "enrolled 200 patients"
        r'\b(\d+[\d,]*)\s*(?:participants|subjects|patients|individuals)\b',  # "100 participants"
        r'(\d+[\d,]*)\s*subjects\s*were\s*enrolled',  # "50 subjects were enrolled"
        r'\b(\d+[\d,]*)\s*\(\s*\d+[\d,]*\s*\)'  # Числа в скобках
    ]

    matches = set()
    for pattern in patterns:
        for match in re.findall(pattern, text_clean):
            if isinstance(match, tuple):
                num = match[0].replace(',', '')
            else:
                num = match.replace(',', '')

            if num.isdigit():
                matches.add(int(num))

    if matches:
        sorted_matches = sorted(matches)
        return str(sorted_matches[0]) if len(sorted_matches) == 1 else ", ".join(map(str, sorted_matches))

    # Поиск текстовых чисел
    word_numbers = {
        'ten': 10, 'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
        'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
        'hundred': 100, 'thousand': 1000
    }
    for word, num in word_numbers.items():
        if re.search(r'\b' + word + r'\b', text_clean):
            return str(num)

    return None


def extract_research_method(methods_text):
    if not methods_text:
        return None

    text_lower = methods_text.lower()

    # Типы исследований
    research_type_keywords = {
        "in vivo": ["in vivo", "animal model", "mice", "rats", "rabbits", "in-vivo"],
        "in vitro": ["in vitro", "cell culture", "cell line", "petri dish", "in-vitro"],
        "clinical": ["clinical trial", "phase \d", "patients", "subjects", "volunteers"]
    }

    # Методология
    method_keywords = [
        'double blind', 'single blind', 'randomized',
        'placebo-controlled', 'open label', 'cross-over',
        'cohort', 'case-control', 'longitudinal'
    ]

    found_types = set()
    for type_name, keywords in research_type_keywords.items():
        if any(re.search(r'\b' + re.escape(kw) + r'\b', text_lower) for kw in keywords):
            found_types.add(type_name)

    found_methods = [kw for kw in method_keywords if kw in text_lower]

    result = []
    if found_types:
        result.append("Type: " + "/".join(sorted(found_types)))
    if found_methods:
        result.append("Methods: " + ", ".join(sorted(found_methods)))

    return " | ".join(result) if result else None


def extract_medical_entities(article):
    if not nlp:
        return None
    combined_text = ""
    for key in ["methods", "results", "figures_tables"]:
        if article.get(key):
            combined_text += article.get(key) + " "
    doc = nlp(combined_text)
    entities = [ent.text for ent in doc.ents]
    # Remove duplicates while preserving order
    entities = list(dict.fromkeys(entities))
    return ", ".join(entities) if entities else None


def semantic_rule_based_analysis(article):
    if not nlp:
        return None
    combined_text = ""
    for key in ["methods", "results", "figures_tables"]:
        if article.get(key):
            combined_text += article.get(key) + " "
    doc = nlp(combined_text)

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    # Phrases characteristic of significant clinical outcomes
    phrases = [nlp(text) for text in
               ["statistically significant", "significant improvement", "marked reduction", "adverse event"]]
    matcher.add("SignificancePhrases", phrases)

    matches = matcher(doc)
    phrases_found = set()
    for match_id, start, end in matches:
        span = doc[start:end]
        phrases_found.add(span.text)

    return ", ".join(phrases_found) if phrases_found else None


def safe_convert(value):
    try:
        import numpy as np
        if isinstance(value, np.ndarray):
            # Преобразуем массив в плоский список и затем в строку
            flattened = value.flatten()
            return ", ".join(map(str, flattened.tolist()))
    except ImportError:
        pass

    if isinstance(value, (list, tuple)):
        return ", ".join(map(str, value))
    return str(value) if value is not None else None


def main():
    # Ask for the JSON file name for analysis
    filename = input("Enter the JSON file name for analysis (e.g., aspirin_16_02_2025.json): ").strip()
    if not filename:
        print("Filename cannot be empty.")
        return

    analyze(filename)


def analyze(filename):
    # Получаем путь к папке, где находится .py файл
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Формируем путь к папке drug_data
    drug_data_dir = os.path.join(script_dir, "drug_data")
    # Формируем полный путь к файлу
    file_path = os.path.join(drug_data_dir, filename)

    # Проверяем существование файла (замените эту часть в вашем коде)
    if not os.path.isfile(file_path):
        print(f"File {filename} not found in {drug_data_dir}.")
        return

    if not os.path.exists(file_path):
        print(f"File '{filename}' not found in 'drug_data' directory.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            articles = json.load(f)
    except Exception as e:
        print(f"Error opening file {file_path}: {e}")
        return

    table_data = []

    for article in articles:
        specific_side_effects = extract_specific_side_effects(article)
        sample_size = extract_sample_size(article.get("methods"))
        research_method = extract_research_method(article.get("methods"))
        ner_entities = extract_medical_entities(article)
        semantic_analysis = semantic_rule_based_analysis(article)

        # Формируем словарь и гарантируем, что все значения скалярные
        row = {
            "Article ID": safe_convert(article.get("article_id")),
            "Title": safe_convert(article.get("title")),
            "Side Effects": safe_convert(specific_side_effects),
            "Sample Size": safe_convert(sample_size),
            "Research Method": safe_convert(research_method),
            "NER Entities": safe_convert(ner_entities),
            "Semantic Analysis": safe_convert(semantic_analysis)
        }
        table_data.append(row)

    df = pd.DataFrame(table_data)
    print("Extracted Data Table:")
    print(df.to_string(index=False))

    base_name = os.path.splitext(filename)[0]
    table_filename = f"{base_name}_table.csv"

    # Создаем папку reports (если ее нет)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(script_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)  # exist_ok=True игнорирует ошибку, если папка уже существует

    # Формируем полный путь для сохранения
    table_path = os.path.join(reports_dir, table_filename)

    # Сохраняем CSV в папку reports
    df.to_csv(table_path, sep=';', index=False, encoding="utf-8")
    print(f"\nData saved to file {table_path}")


if __name__ == "__main__":
    main()
