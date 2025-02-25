import os
import csv
import json
from datetime import datetime


def extract_info_from_filename(filename):
    if not filename.endswith('_table.csv'):
        return None, None, None
    base = filename[:-10]  # удаляем "_table.csv"
    parts = base.split('_')
    if len(parts) < 4:
        return None, None, None
    # Последние три токена – это день, месяц, год
    day, month, year = parts[-3], parts[-2], parts[-1]
    date_str = f"{day}_{month}_{year}"
    # Остальные токены составляют название препарата (объединяем через пробел)
    drug_tokens = parts[:-3]
    drug = " ".join(drug_tokens)
    try:
        date_obj = datetime.strptime(date_str, "%d_%m_%Y")
    except Exception:
        return drug, date_str, None
    return drug, date_str, date_obj


def scavenge():
    # Путь к папке refined, где расположены CSV файлы
    script_dir = os.path.dirname(os.path.abspath(__file__))
    refined_folder = os.path.join(script_dir, 'refined')

    # Структура: drug -> { side_effect: (date_str, date_obj) }
    drug_effects = {}

    for filename in os.listdir(refined_folder):
        if filename.endswith('_table.csv'):
            drug, date_str, date_obj = extract_info_from_filename(filename)
            if drug is None or date_obj is None:
                continue
            file_path = os.path.join(refined_folder, filename)
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                # Если CSV содержит заголовок, раскомментируйте следующую строку:
                # next(reader, None)
                for row in reader:
                    if len(row) < 3:
                        continue
                    effects_str = row[2].strip()
                    if not effects_str:
                        continue
                    # Разбиваем строку по запятой, удаляем лишние пробелы и приводим к нижнему регистру
                    effects = [effect.strip().lower() for effect in effects_str.split(',') if effect.strip()]
                    # Инициализируем запись для препарата, если её ещё нет
                    if drug not in drug_effects:
                        drug_effects[drug] = {}
                    for effect in effects:
                        # Если эффект уже встречался, обновляем дату, если новая раньше
                        if effect in drug_effects[drug]:
                            _, stored_date_obj = drug_effects[drug][effect]
                            if date_obj < stored_date_obj:
                                drug_effects[drug][effect] = (date_str, date_obj)
                        else:
                            drug_effects[drug][effect] = (date_str, date_obj)

    # Формируем итоговую базу данных
    output = {}
    for drug, effects in drug_effects.items():
        # Сортируем эффекты по дате первого обнаружения для сохранения соответствия списков
        sorted_effects = sorted(effects.items(), key=lambda item: item[1][1])
        side_effects_list = [effect for effect, (date_str, _) in sorted_effects]
        first_met_list = [date_str for effect, (date_str, _) in sorted_effects]
        output[drug] = [{
            "side effects": side_effects_list,
            "first met": first_met_list
        }]

    # Записываем итоговую базу данных в JSON-файл
    with open("side_effects_database.json", "w", encoding="utf-8") as jsonfile:
        json.dump(output, jsonfile, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    scavenge()
