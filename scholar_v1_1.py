import os
import pandas as pd
from collections import Counter


def complete_date(date_str):
    """
    Дополняет дату, если задана только часть строки.
    Например, '2020' преобразуется в '2020-01-01', а '2020-05' в '2020-05-01'.
    """
    if len(date_str) == 4:
        return f"{date_str}-01-01"
    elif len(date_str) == 7:
        return f"{date_str}-01"
    return date_str


def get_side_effects_info(df):
    """
    Обрабатывает DataFrame с данными о побочных эффектах.

    Ожидается, что DataFrame содержит следующие колонки:
      - last_mention (дата упоминания)
      - side_effects (строка с побочными эффектами, разделёнными запятыми)
      - source_id (опционально; если отсутствует, подставляется значение "N/A")

    Функция:
      - Приводит имена столбцов к нижнему регистру и заменяет пробелы на '_'.
      - Дополняет дату и преобразует её в формат datetime.
      - Разбивает строку побочных эффектов по запятым.
      - Группирует данные по дате и идентификатору источника.
      - Подсчитывает частоту каждого побочного эффекта.
      - Формирует строку с результатами в формате:
            Дата - Побочный эффект - Количество - source_id
    """
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
    """
    Читает CSV-файл из папки refined/ по шаблону:
      [название_препарата]_[дата_запроса]_table.csv
    и возвращает строку с информацией о частоте побочных эффектов и id источников.

    Параметры:
      - drug_name: название препарата (используется при построении имени файла)
      - request_date: дата запроса (также используется в имени файла)

    Если файл не найден или возникает ошибка при чтении, возвращается строка с описанием ошибки.
    """
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

