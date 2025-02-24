import csv
import os


def get_column_field(fieldnames, target):
    target_norm = target.lower().replace(" ", "")
    for field in fieldnames:
        if target_norm in field.lower().replace(" ", ""):
            return field
    return None


def filter_side_effects_legacy(keyword, drug=""):
    keyword_lower = keyword.lower()
    reports_dir = os.path.join(os.getcwd(), "reports")
    refined_dir = os.path.join(os.getcwd(), "refined")

    found_ids = []
    side_effects_list = []

    try:
        reports_files = [f for f in os.listdir(reports_dir) if f.lower().endswith(".csv")]
    except Exception as e:
        raise Exception("Не удалось открыть папку reports: " + str(e))

    if not reports_files:
        raise Exception("CSV файлы не найдены в папке reports")

    for filename in reports_files:
        if drug:
            base_name = os.path.splitext(filename)[0].replace("_", " ")
            if drug.lower() not in base_name.lower():
                continue

        filepath = os.path.join(reports_dir, filename)
        file_matches = False
        try:
            with open(filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                if not reader.fieldnames:
                    continue
                ner_field = get_column_field(reader.fieldnames, "NER Entities")
                id_field = get_column_field(reader.fieldnames, "Article ID")
                if not ner_field or not id_field:
                    continue
                for row in reader:
                    ner_value = row.get(ner_field, "")
                    entities = [entity.strip().lower() for entity in ner_value.split(",")]
                    for ent in entities:
                        if keyword_lower in ent:
                            found_ids.append(row.get(id_field, ""))
                            file_matches = True
                            break  # Найдено совпадение, переходим к следующей строке
        except Exception:
            continue  # Пропускаем файлы с ошибками чтения

        if file_matches:
            refined_filepath = os.path.join(refined_dir, filename)
            if not os.path.exists(refined_filepath):
                raise Exception(f"Файл {filename} не найден в папке refined")
            try:
                with open(refined_filepath, newline='', encoding='utf-8') as refined_file:
                    reader = csv.DictReader(refined_file, delimiter=";")
                    if not reader.fieldnames:
                        raise Exception(f"Файл {filename} из папки refined не содержит заголовков")
                    effects_field = get_column_field(reader.fieldnames, "Side Effects")
                    if not effects_field:
                        raise Exception(f"В файле {filename} не найден столбец 'Побочные эффекты'")
                    for row in reader:
                        effect = row.get(effects_field, "").strip()
                        if effect:
                            side_effects_list.append(effect)
            except Exception as e:
                raise Exception(f"Ошибка при чтении файла {filename} из папки refined: {e}")

    unique_found_ids = list(dict.fromkeys(found_ids))
    unique_side_effects = list(dict.fromkeys(side_effects_list))

    return unique_found_ids, unique_side_effects


def filter_side_effects(keyword, drug=""):
    keyword_lower = keyword.lower()
    reports_dir = os.path.join(os.getcwd(), "reports")
    refined_dir = os.path.join(os.getcwd(), "refined")

    global_found_ids = []
    global_side_effects = []

    try:
        reports_files = [f for f in os.listdir(reports_dir) if f.lower().endswith(".csv")]
    except Exception as e:
        raise Exception("Не удалось открыть папку reports: " + str(e))

    if not reports_files:
        raise Exception("CSV файлы не найдены в папке reports")

    for filename in reports_files:
        # Если задан препарат, фильтруем файлы по его названию.
        if drug:
            base_name = os.path.splitext(filename)[0].replace("_", " ")
            if drug.lower() not in base_name.lower():
                continue

        filepath = os.path.join(reports_dir, filename)
        matched_ids = set()
        file_matches = False

        try:
            with open(filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                if not reader.fieldnames:
                    continue
                ner_field = get_column_field(reader.fieldnames, "NER Entities")
                id_field = get_column_field(reader.fieldnames, "Article ID")
                if not ner_field or not id_field:
                    continue
                for row in reader:
                    ner_value = row.get(ner_field, "")
                    # Разбиваем строку на сущности по запятой
                    entities = [entity.strip().lower() for entity in ner_value.split(",")]
                    for ent in entities:
                        if keyword_lower in ent:
                            raw_source_id = row.get(id_field, "").strip()
                            # Разделяем строку по ';' и берем первый элемент (чистый ID)
                            source_id = raw_source_id.split(';')[0].strip().lower()
                            if source_id:
                                matched_ids.add(source_id)  # Теперь matched_ids содержит только ID
                            file_matches = True
                            break  # Если найдено совпадение, переходим к следующей строке
        except Exception:
            continue  # Пропускаем файлы с ошибками чтения

        # Если для данного файла найдены совпадения, обрабатываем соответствующий refined-файл
        if file_matches and matched_ids:
            # Добавляем найденные id в общий список
            global_found_ids.extend(list(matched_ids))
            refined_filepath = os.path.join(refined_dir, filename)
            if not os.path.exists(refined_filepath):
                raise Exception(f"Файл {filename} не найден в папке refined")
            try:
                with open(refined_filepath, newline='', encoding='utf-8') as refined_file:
                    reader = csv.DictReader(refined_file, delimiter=";")
                    if not reader.fieldnames:
                        raise Exception(f"Файл {filename} из папки refined не содержит заголовков")
                    effects_field = get_column_field(reader.fieldnames, "Side Effects")
                    refined_id_field = get_column_field(reader.fieldnames, "Article ID")
                    if not effects_field or not refined_id_field:
                        raise Exception(
                            f"В файле {filename} отсутствуют необходимые столбцы ('Побочные эффекты' и/или 'ID источника')")
                    for row in reader:
                        raw_row_id = row.get(refined_id_field, "").strip()
                        row_id = raw_row_id.split(';')[0].strip()

                        if row_id in matched_ids:
                            effect = row.get(effects_field, "").strip()
                            if effect:
                                global_side_effects.append(effect)
            except Exception as e:
                raise Exception(f"Ошибка при чтении файла {filename} из папки refined: {e}")

    # Удаляем дубликаты
    unique_found_ids = list(dict.fromkeys(global_found_ids))
    unique_side_effects = list(dict.fromkeys(global_side_effects))
    print(unique_side_effects)

    return unique_found_ids, unique_side_effects


if __name__ == "__main__":
    try:
        ids, effects = filter_side_effects("adolescents", "imcivree")
        print("Найденные ID источников:")
        print(ids)
        print("Побочные эффекты:")
        # Выводим каждый эффект на новой строке
        for effect in effects:
            print(effect)
    except Exception as ex:
        print("Ошибка:", ex)
