import os
import pandas as pd
from collections import Counter


def complete_date(date_str):
    if len(date_str) == 4:
        return f"{date_str}-01-01"
    elif len(date_str) == 7:
        return f"{date_str}-01"
    return date_str


def get_side_effects_info(df):
    # Приводим имена столбцов к единообразному виду
    df.rename(columns=lambda x: x.strip().replace(" ", "_").lower(), inplace=True)

    # Обработка даты: дополняем и преобразуем в datetime
    if 'last_mention' in df.columns:
        df['last_mention'] = df['last_mention'].astype(str).apply(complete_date)
        df['last_mention'] = pd.to_datetime(df['last_mention'], errors='coerce')
    else:
        return "Ошибка: нет столбца 'last_mention'"

    # Разбиваем побочные эффекты по запятым
    if 'side_effects' in df.columns:
        df['side_effects'] = df['side_effects'].astype(str).str.split(',')
    else:
        return "Ошибка: нет столбца 'side_effects'"

    # Если столбца source_id нет, создаём его
    if 'source_id' not in df.columns:
        df['source_id'] = "N/A"

    results = []
    # Группируем по дате и source_id
    for (date, source), group in df.groupby(['last_mention', 'source_id']):
        # Получаем список всех побочных эффектов с удалением лишних пробелов
        effects = [effect.strip() for sublist in group['side_effects'] for effect in sublist if effect.strip()]
        effect_counts = Counter(effects)
        date_str = date.strftime('%Y-%m-%d') if pd.notnull(date) else ''
        for effect, count in effect_counts.items():
            results.append(f"{date_str} - {effect} - {count} - {source}")

    return "\n".join(results)


def get_side_effects_info_from_file(drug_name, request_date):
    filename = os.path.join("refined", f"{drug_name}_{request_date}_table.csv")
    if not os.path.isfile(filename):
        return f"Ошибка: файл '{filename}' не найден."

    try:
        # Читаем CSV с разделителем ';'
        df = pd.read_csv(filename, delimiter=';')
    except Exception as e:
        return f"Ошибка при чтении файла: {str(e)}"

    # Получаем строку с результатами
    result_string = get_side_effects_info(df)
    return result_string

