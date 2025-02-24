import os
import glob
import re
import pandas as pd
import json


def extract_drug_name(filename):
    """
    Извлекает полное название препарата из имени файла.
    Ожидается, что имя файла имеет формат:
        [название_препарата]_[дата]_table.csv
    где дата в формате ДД_ММ_ГГГГ.
    Название препарата может содержать подчеркивания, которые означают пробелы.
    """
    base = os.path.basename(filename)
    # Регулярное выражение для извлечения названия препарата и даты в формате ДД_ММ_ГГГГ
    pattern = r"^(.*?)_\d{2}_\d{2}_\d{4}_table\.csv$"
    match = re.match(pattern, base)
    if match:
        # Замена подчеркиваний на пробелы в названии препарата
        drug_raw = match.group(1)
        drug_name = drug_raw.replace("_", " ")
        return drug_name
    return None


def build_side_effects_database():
    """
    Проходит по всем CSV-файлам в папке refined/, содержащим данные о побочных эффектах,
    и составляет базу данных, где для каждого побочного эффекта сохраняется информация по препаратам:
      ключ – название препарата, а значение – список уникальных ID источников,
    в которых этот эффект упоминался.

    Ожидается, что в каждом CSV-файле:
      - разделителем является ';'
      - имеются столбцы "side effects" и "article id"

    Результат сохраняется в файл source_database.json и возвращается в виде словаря.
    Структура результата:
    {
        "effect1": {
            "Drug A": [id1, id2, ...],
            "Drug B": [id3, id4, ...]
        },
        "effect2": {
            "Drug A": [...],
            ...
        },
        ...
    }
    """
    side_effects_db = {}
    csv_files = glob.glob(os.path.join("refined", "*.csv"))

    if not csv_files:
        print("В папке refined/ не найдено CSV файлов.")
        return side_effects_db

    for file in csv_files:
        drug_name = extract_drug_name(file)
        if not drug_name:
            print(f"Не удалось извлечь название препарата из файла {file}")
            continue

        try:
            df = pd.read_csv(file, delimiter=';')
        except Exception as e:
            print(f"Ошибка чтения файла {file}: {e}")
            continue

        # Приводим имена столбцов к единообразному виду
        df.rename(columns=lambda x: x.strip().replace(" ", "_").lower(), inplace=True)

        if 'side_effects' not in df.columns or 'article_id' not in df.columns:
            print(f"Файл {file} не содержит необходимых столбцов 'side_effects' или 'article_id'.")
            continue

        # Итерируем по строкам DataFrame
        for _, row in df.iterrows():
            effects = row['side_effects']
            article_id = str(row['article_id']).strip()
            if pd.isna(effects):
                continue
            # Разбиваем строку побочных эффектов по запятой и удаляем лишние пробелы
            effects_list = [effect.strip() for effect in str(effects).split(",") if effect.strip()]
            for effect in effects_list:
                if effect not in side_effects_db:
                    side_effects_db[effect] = {}
                if drug_name not in side_effects_db[effect]:
                    side_effects_db[effect][drug_name] = set()
                side_effects_db[effect][drug_name].add(article_id)

    # Преобразуем множества в отсортированные списки для каждого препарата
    for effect in side_effects_db:
        for drug in side_effects_db[effect]:
            side_effects_db[effect][drug] = sorted(list(side_effects_db[effect][drug]))

    # Сохраняем базу данных в JSON-файл
    output_file = "source_database.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(side_effects_db, f, ensure_ascii=False, indent=4)
        print(f"База данных побочных эффектов сохранена в {output_file}")
    except Exception as e:
        print(f"Ошибка сохранения базы данных: {e}")

    return side_effects_db


if __name__ == "__main__":
    db = build_side_effects_database()
    # Вывод базы данных для проверки
    for effect, drugs in db.items():
        print(f"{effect}:")
        for drug, ids in drugs.items():
            print(f"  {drug}: {', '.join(ids)}")
