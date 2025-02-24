import json

def main():
    drug_name = input("Введите название препарата: ").strip()
    watch(drug_name)

def watch(drug_name):
    # Загружаем базу с датами и побочными эффектами
    try:
        with open("side_effects_database.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Файл side_effects_database.json не найден.")
        return

    # Загружаем базу источников из прикрепленного файла
    try:
        with open("source_database.json", "r", encoding="utf-8") as f:
            sources_data = json.load(f)
    except FileNotFoundError:
        print("Файл source_database.json не найден.")
        sources_data = {}

    # Ищем препарат без учёта регистра
    matching_drug = None
    for key in data:
        if key.lower() == drug_name.lower():
            matching_drug = key
            break

    if not matching_drug:
        print(f"Препарат '{drug_name}' не найден в базе данных.")
        return

    result_lines = [f"Побочные эффекты для препарата '{matching_drug}':"]
    entries = data[matching_drug]
    # Приводим название препарата к нижнему регистру для поиска в источниках
    drug_key = matching_drug.lower()
    for entry in entries:
        side_effects = entry.get("side effects", [])
        first_met_dates = entry.get("first met", [])
        # Для каждого побочного эффекта выводим дату и соответствующие ID источников (если найдены)
        for effect, date_str in zip(side_effects, first_met_dates):
            # Ищем источник по названию эффекта (без учета регистра)
            effect_key = effect.lower()
            source_ids = []
            if effect_key in sources_data:
                # Если для данного эффекта присутствует информация по препарату, берём её
                if drug_key in sources_data[effect_key]:
                    source_ids = sources_data[effect_key][drug_key]
            # Если список пустой, выводим Н/Д
            source_ids_str = ", ".join(source_ids) if source_ids else "Н/Д"
            result_lines.append(f"{effect}: {date_str} (ID источников: {source_ids_str})")

    print("\n".join(result_lines))

def watch_gui(drug_name):
    # Функция для интеграции с GUI. Принимает название препарата и возвращает результаты в виде строки.
    try:
        with open("side_effects_database.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return "Файл side_effects_database.json не найден."

    try:
        with open("source_database.json", "r", encoding="utf-8") as f:
            sources_data = json.load(f)
    except FileNotFoundError:
        sources_data = {}
        # Можно также вернуть сообщение об ошибке, если требуется:
        # return "Файл source_database.json не найден."

    matching_drug = None
    for key in data:
        if key.lower() == drug_name.lower():
            matching_drug = key
            break

    if not matching_drug:
        return f"Препарат '{drug_name}' не найден в базе данных."

    result_lines = [f"Побочные эффекты для препарата '{matching_drug}':"]
    drug_key = matching_drug.lower()
    entries = data[matching_drug]
    for entry in entries:
        side_effects = entry.get("side effects", [])
        first_met_dates = entry.get("first met", [])
        for effect, date_str in zip(side_effects, first_met_dates):
            effect_key = effect.lower()
            source_ids = []
            if effect_key in sources_data:
                if drug_key in sources_data[effect_key]:
                    source_ids = sources_data[effect_key][drug_key]
            source_ids_str = ", ".join(source_ids) if source_ids else "Н/Д"
            result_lines.append(f"{effect}: {date_str} (ID источников: {source_ids_str})")

    return "\n".join(result_lines)

if __name__ == "__main__":
    main()
