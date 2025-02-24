import json
from datetime import datetime


with open("dictionary.json", "r", encoding="utf-8") as f:
    TRANSLATIONS = json.load(f)


def translate_effects(effects_list):
    translated = []
    for effect in effects_list:
        # Приводим к нижнему регистру для унификации
        lower_effect = effect.lower()
        # Ищем частичное совпадение с ключами словаря
        for key in TRANSLATIONS:
            if key in lower_effect:
                translated.append(TRANSLATIONS[key])
                break
        else:
            # Если совпадений нет, оставляем оригинал
            translated.append(effect)
    return translated


def main():
    user_date_str = input("Введите дату (в формате dd_mm_yyyy): ")
    watch(user_date_str)


def watch(user_date_str):
    try:
        user_date = datetime.strptime(user_date_str, "%d_%m_%Y")
    except ValueError:
        print("Неверный формат даты. Пожалуйста, введите дату в формате dd_mm_yyyy.")
        return

    try:
        with open("side_effects_database.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Файл side_effects_database.json не найден.")
        return

    filtered_data = {}

    for drug, entries in data.items():
        for entry in entries:
            side_effects = entry.get("side effects", [])
            first_met_dates = entry.get("first met", [])
            filtered_side_effects = []
            for effect, date_str in zip(side_effects, first_met_dates):
                try:
                    effect_date = datetime.strptime(date_str, "%d_%m_%Y")
                except ValueError:
                    continue
                if effect_date >= user_date:
                    filtered_side_effects.append(effect)
            if filtered_side_effects:
                filtered_data[drug] = filtered_side_effects

    if filtered_data:
        print(f"\nПобочные эффекты, обнаруженные не ранее {user_date_str}:")
        for drug, effects in filtered_data.items():
            effects_str = ", ".join(effects)
            print(f"{drug}: {effects_str}")
    else:
        print(f"\nНет побочных эффектов, обнаруженных не ранее {user_date_str}.")


def watch_gui(user_date_str):
    try:
        user_date = datetime.strptime(user_date_str, "%d_%m_%Y")
    except ValueError:
        return "Неверный формат даты. Пожалуйста, введите дату в формате dd_mm_yyyy."

    try:
        with open("side_effects_database.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return "Файл side_effects_database.json не найден."

    filtered_data = {}

    for drug, entries in data.items():
        for entry in entries:
            side_effects = entry.get("side effects", [])
            first_met_dates = entry.get("first met", [])
            filtered_side_effects = []
            for effect, date_str in zip(side_effects, first_met_dates):
                try:
                    effect_date = datetime.strptime(date_str, "%d_%m_%Y")
                except ValueError:
                    continue
                if effect_date >= user_date:
                    filtered_side_effects.append(effect)

            # Перевод эффектов на русский
            translated_effects = translate_effects(filtered_side_effects)
            if translated_effects:
                filtered_data[drug] = translated_effects

    translated_effects = translate_effects(filtered_side_effects)

    if filtered_data:
        result_lines = [f"Побочные эффекты, обнаруженные не ранее {user_date_str}:"]
        for drug, effects in filtered_data.items():
            effects_str = ", ".join(effects)
            result_lines.append(f"{drug}: {effects_str}")
        return "\n".join(result_lines)
    else:
        return f"Нет побочных эффектов, обнаруженных не ранее {user_date_str}."


if __name__ == "__main__":
    main()
