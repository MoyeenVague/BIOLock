import os
import csv
import json

# Создаем список ключевых слов для идентификации побочных эффектов
SIDE_EFFECT_KEYWORDS = {
    # Желудочно-кишечные симптомы:
    "nausea", "vomiting", "diarrhea", "constipation", "abdominal pain", "dyspepsia",
    "indigestion", "gastric upset", "heartburn", "reflux", "loss of appetite", "bloating", "flatulence",

    # Общие симптомы:
    "fatigue", "drowsiness", "lethargy", "weakness", "malaise",

    # Неврологические и психические реакции:
    "headache", "dizziness", "vertigo", "confusion", "cognitive impairment", "memory loss",
    "insomnia", "anxiety", "depression", "mood swings", "irritability", "psychosis", "hallucinations",
    "seizure", "tremor", "ataxia", "syncope", "fainting",

    # Кожные и аллергические реакции:
    "rash", "pruritus", "urticaria", "eczema", "photosensitivity", "itching", "skin lesion", "petechiae", "purpura",
    "flushing", "swelling", "edema", "allergic reaction", "anaphylaxis", "hypersensitivity",

    # Сердечно-сосудистые эффекты:
    "chest pain", "palpitations", "arrhythmia", "bradycardia", "tachycardia", "hypertension", "hypotension",
    "cardiac arrest", "myocardial infarction", "heart failure", "stroke",

    # Дыхательная система:
    "dyspnea", "shortness of breath", "respiratory distress", "cough",

    # Органные токсины:
    "liver toxicity", "hepatotoxicity", "hepatitis", "jaundice", "elevated liver enzymes",
    "renal toxicity", "nephrotoxicity", "kidney failure", "renal injury", "nephritis", "proteinuria", "hematuria",

    # Мышечно-скелетные реакции:
    "myalgia", "arthralgia", "muscle cramps", "joint pain", "joint swelling", "arthritis", "back pain", "limb pain",
    "musculoskeletal pain", "muscle weakness",

    # Нарушения чувств:
    "blurred vision", "double vision", "visual disturbance", "ocular irritation", "dry eyes", "eye pain",
    "hearing loss", "tinnitus",

    # Метаболические нарушения:
    "weight gain", "weight loss", "hyperglycemia", "hypoglycemia", "metabolic acidosis", "lactic acidosis",

    # Гематологические реакции:
    "anemia", "neutropenia", "thrombocytopenia", "leukopenia", "bleeding", "bruising", "coagulopathy", "thrombosis",

    # Прочие системные реакции:
    "infection", "sepsis", "immune suppression", "immunosuppression", "fever", "chills", "sweating",

    # Нарушения работы желудочно-кишечного тракта:
    "stomatitis", "oral ulcer", "sore throat", "dysgeusia", "taste disturbance",

    # Специфические термины:
    "cytopenia", "eosinophilia", "drug-induced", "adverse reaction", "side effect", "undesirable effect"
}


def is_side_effect(term):
    """Проверяет, относится ли термин к побочным эффектам"""
    return any(keyword in term.lower() for keyword in SIDE_EFFECT_KEYWORDS)


def process_file(input_path, output_path):
    # Определяем имя JSON-файла из папки /drug_data
    csv_filename = os.path.basename(input_path)
    base, _ = os.path.splitext(csv_filename)  # Например, "aspirin_17_02_2025_table"
    json_base = base.replace("_table", "")      # Получим "aspirin_17_02_2025"
    json_filename = json_base + ".json"           # Итог: "aspirin_17_02_2025.json"
    json_path = os.path.join("drug_data", json_filename)

    # Загружаем данные из JSON-файла: создаем словарь article_id -> pub_date
    try:
        with open(json_path, 'r', encoding='utf-8') as json_file:
            json_data = json.load(json_file)
        article_pub = {entry["article_id"]: entry.get("pub_date", "") for entry in json_data}
    except Exception as e:
        print(f"Ошибка при загрузке JSON-файла {json_path}: {e}")
        article_pub = {}

    # Открываем CSV-файл для чтения и создаем новый CSV для записи с нужными столбцами
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile, delimiter=';')
        fieldnames = ["last mention", "article id", "side effects"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        for row in reader:
            # Гибкое извлечение article_id
            article_id = ""
            for key in row.keys():
                key_normalized = key.strip().lower().replace(' ', '_')
                if key_normalized == 'article_id':
                    article_id = row[key].strip()
                    break

            # Если не нашли, проверяем другие варианты
            if not article_id:
                article_id = row.get('article id', '').strip() or row.get('article_id', '').strip()

            print(f"Extracted Article ID: '{article_id}'")

            # Обрабатываем существующие побочные эффекты (удаляем дубликаты без учета регистра)
            existing = row.get('Side Effects', '')
            existing_effects = [s.strip() for s in existing.split(',') if s.strip()]
            unique_effects = []
            seen_lower = set()
            for effect in existing_effects:
                key = effect.lower()
                # Пропускаем термин, если он равен "побочные эффекты"
                if key == "побочные эффекты":
                    continue
                if key not in seen_lower:
                    unique_effects.append(effect)
                    seen_lower.add(key)

            # Обрабатываем NER-сущности и добавляем, если они относятся к побочным эффектам
            ner_entities = row.get('NER Entities', '')
            if ner_entities:
                ner_list = [s.strip() for s in ner_entities.split(',') if s.strip()]
                for entity in ner_list:
                    # Пропускаем термин, если он равен "побочные эффекты"
                    if entity.lower() == "побочные эффекты":
                        continue
                    if is_side_effect(entity):
                        key = entity.lower()
                        if key not in seen_lower:
                            unique_effects.append(entity)
                            seen_lower.add(key)

            # Если побочных эффектов не найдено, ставим "nothing"
            if unique_effects:
                side_effects_str = ', '.join(e.lower() for e in unique_effects)
            else:
                side_effects_str = "nothing"

            # Получаем дату публикации статьи из JSON (из поля pub_date)
            last_mention = article_pub.get(article_id, "")

            out_row = {
                "last mention": last_mention,
                "article id": article_id,
                "side effects": side_effects_str
            }
            writer.writerow(out_row)


def purify():
    # Создаем папку для обработанных файлов, если ее нет
    if not os.path.exists("refined"):
        os.makedirs("refined")

    # Обрабатываем каждый CSV-файл из папки reports
    for filename in os.listdir("reports"):
        if filename.endswith(".csv"):
            input_file = os.path.join("reports", filename)
            output_file = os.path.join("refined", filename)
            process_file(input_file, output_file)
            print(f'Processed: {filename}')


if __name__ == '__main__':
    purify()
