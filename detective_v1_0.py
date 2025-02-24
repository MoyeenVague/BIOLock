import os
import glob
import json
import tkinter as tk
from tkinter import messagebox


def create_source_lookup_tab(parent):
    """
    Создает вкладку для поиска источника по уникальному ID.
    Выбор отдельной вкладки обусловлен тем, что данная функция специализирована и не пересекается с
    остальными задачами приложения (парсинг, анализ и т.д.).
    """
    frame = tk.Frame(parent, bg="#B8D5FD")

    # Метка и поле для ввода ID источника
    tk.Label(frame, text="Введите ID источника:", bg="#B8D5FD", fg="#192B69") \
        .grid(row=0, column=0, padx=10, pady=10, sticky="e")
    id_entry = tk.Entry(frame, width=40)
    id_entry.grid(row=0, column=1, padx=10, pady=10)

    # Текстовое поле для вывода результатов
    result_text = tk.Text(frame, width=80, height=10, bg="#000000", fg="#00FF00")
    result_text.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    def lookup_source():
        user_id = id_entry.get().strip()
        if not user_id:
            messagebox.showerror("Ошибка", "Введите ID источника")
            return

        found = False
        # Перебор всех файлов .json в папке drug_data
        for file_path in glob.glob(os.path.join("drug_data", "*.json")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue  # Пропускаем файлы, которые не удалось прочитать

            # Поиск источника с указанным ID
            for source in data:
                if source.get("article_id") == user_id:
                    title = source.get("title", "Неизвестно")
                    source_type = source.get("source", "Неизвестно")
                    pub_date = source.get("pub_date", "Неизвестно")

                    # Извлечение названия препарата и даты отчёта из имени файла
                    base = os.path.basename(file_path)
                    name_without_ext = os.path.splitext(base)[0]  # например, "ibuprofen_20_02_2025"
                    parts = name_without_ext.split("_")
                    if len(parts) >= 2:
                        drug_name = parts[0]
                        report_date = "_".join(parts[1:])
                    else:
                        drug_name = "Неизвестно"
                        report_date = "Неизвестно"

                    # Вывод результата
                    result_text.delete("1.0", tk.END)
                    result_text.insert(tk.END, f"ID: {user_id}\n")
                    result_text.insert(tk.END, f"Название источника: {title}\n")
                    result_text.insert(tk.END, f"Тип источника: {source_type}\n")
                    result_text.insert(tk.END, f"Дата публикации: {pub_date}\n")
                    result_text.insert(tk.END, f"Препарат: {drug_name}\n")
                    result_text.insert(tk.END, f"Дата отчёта: {report_date}\n")
                    found = True
                    break
            if found:
                break

        if not found:
            result_text.delete("1.0", tk.END)
            result_text.insert(tk.END, "Источник с указанным ID не найден")

    # Кнопка для запуска поиска
    search_button = tk.Button(frame, text="Поиск", width=15, bg="#C13E70", fg="#CDDBF5", command=lookup_source)
    search_button.grid(row=1, column=0, columnspan=2, pady=10)

    return frame
