import tkinter as tk
from tkinter import messagebox, Menu
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import threading
from PIL import Image, ImageTk
import itertools
import json

# Импорт функционала из других модулей
from parser_v4_0 import master_parser as parser_main
from analyzer_v2_0 import analyze as analyzer_main
from purifier_v1_2 import purify as purifier_main
from datascavenger_v1_0 import scavenge as datascavenger_main
from watcher_v2_0 import watch_gui as watcher_main
from lite_v1_1 import watch_gui as drug_watch_gui
from scholar_v1_1 import get_side_effects_info_from_file
from organizer_v1_1 import build_side_effects_database
from detective_v1_0 import create_source_lookup_tab
from filter_v1_2 import filter_side_effects

# ===== Цветовая схема =====
BG_COLOR = "#F1F1F1"       # фон основного окна
TAB_BG_COLOR = "#B8D5FD"   # фон вкладок
BUTTON_BG_COLOR = "#C13E70"  # фон кнопок
BUTTON_FG_COLOR = "#CDDBF5"  # цвет текста на кнопках
LABEL_FG_COLOR = "#192B69"  # цвет текста лейблов
LOG_BG_COLOR = "#B8D5FD"   # фон текстовых областей логов
LOG_FG_COLOR = "#192B69"   # цвет текста логов

# Настройка шрифтов:
default_font = ("Mathcad UniMath", 11)
important_font = ("Mathcad UniMath", 14)  # для важных данных (названия побочных эффектов)
id_font = ("Mathcad UniMath", 10)         # для ID источников

# ==== Пути к ассетам ====
LOADING_GIF_PATH = r"assets\loading.gif"
LOADING_WIDTH = 400
LOADING_HEIGHT = 300

# Глобальный словарь для хранения переменных чекбоксов по источникам
source_vars = {}

# Управление загрузками
class LoadingManager:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.loading_label = None
        self.button_reference = None
        self.frames = []
        self.current_frame = 0
        self.is_playing = False
        self.load_animation()

    def load_animation(self):
        try:
            image = Image.open(LOADING_GIF_PATH)
            self.frames = []
            for frame in itertools.count():
                try:
                    image.seek(frame)
                    frame_image = image.copy().resize((LOADING_WIDTH, LOADING_HEIGHT), Image.ANTIALIAS)
                    self.frames.append(ImageTk.PhotoImage(frame_image))
                except EOFError:
                    break
            self.loading_label = tk.Label(self.parent, bg=TAB_BG_COLOR)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load animation: {str(e)}")

    def show_loading(self, button):
        if not self.frames:
            return
        self.button_reference = button
        button.grid_remove()
        self.loading_label.grid(row=1, column=0, columnspan=2, pady=10)
        self.is_playing = True
        self.animate()

    def hide_loading(self):
        self.is_playing = False
        self.loading_label.grid_remove()
        if self.button_reference:
            self.button_reference.grid()

    def animate(self):
        if self.is_playing:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.loading_label.configure(image=self.frames[self.current_frame])
            self.parent.after(50, self.animate)

# ===== Функции логирования =====
def log_message(message):
    log_text.configure(state="normal")
    log_text.insert(tk.END, message + "\n")
    log_text.configure(state="disabled")
    log_text.yview_moveto(1.0)

def safe_log(message):
    root.after(0, lambda: log_message(message))

# ===== Обёртки для выполнения задач в отдельных потоках =====

# --- Парсинг ---
def run_parser():
    drug_name = parser_drug_entry.get().strip()
    if not drug_name:
        messagebox.showerror("Ошибка", "Введите препарат")
        return

    sources = [src for src, var in source_vars.items() if var.get()]
    if not sources:
        messagebox.showerror("Ошибка", "Выберите источники")
        return

    loading_manager.show_loading(search_button)
    threading.Thread(target=run_parser_task, args=(drug_name, sources), daemon=True).start()

def run_parser_task(drug_name, sources):
    try:
        output_path = parser_main(drug_name, sources)
        safe_log(f"Парсинг завершён! Результат: {output_path}")
    except Exception as e:
        safe_log(f"Ошибка парсера: {str(e)}")
    finally:
        root.after(0, loading_manager.hide_loading)

def create_parser_tab(parent):
    frame = tk.Frame(parent, bg=TAB_BG_COLOR)
    source_list = [
        ("pubmed", "PubMed", True),
        ("amazon", "Amazon", False),
        ("drugscom", "Drugs.com", False),
        ("uppsala", "Uppsala", False),
        ("semanticscholar", "Semantic Scholar", False)
    ]

    sources_frame = tk.LabelFrame(frame, text="Источники", bg=TAB_BG_COLOR, fg=LABEL_FG_COLOR)
    sources_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

    source_vars.clear()
    for src, display, default in source_list:
        var = tk.BooleanVar(value=default)
        source_vars[src] = var
        tk.Checkbutton(sources_frame, text=display, variable=var, bg=TAB_BG_COLOR) \
            .pack(side='left', padx=10, pady=5)

    tk.Button(frame, text="Поиск", width=15, bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR,
              command=run_parser) \
        .grid(row=2, column=0, columnspan=3, pady=10)

    return frame

# --- Очистка и сбор ---
def run_purifier_task():
    safe_log("Очистка...")
    try:
        purifier_main()
        safe_log("Очистка завершена")
    except Exception as e:
        safe_log("Ошибка очистки: " + str(e))

def run_purifier():
    threading.Thread(target=run_purifier_task, daemon=True).start()

def run_datascavenger_task():
    safe_log("Сбор данных...")
    try:
        datascavenger_main()
        safe_log("Сбор завершён")
    except Exception as e:
        safe_log("Ошибка сбора: " + str(e))

def run_datascavenger():
    threading.Thread(target=run_datascavenger_task, daemon=True).start()

def run_source_db_builder():
    try:
        result_db = build_side_effects_database()
        json_str = json.dumps(result_db, ensure_ascii=False, indent=4)
    except Exception as e:
        json_str = f"Ошибка БД: {e}"
    source_db_text.configure(state="normal")
    source_db_text.delete(1.0, tk.END)
    source_db_text.insert(tk.END, json_str)
    source_db_text.configure(state="disabled")

# --- Отслеживание ---
def run_watcher_task(date_input):
    safe_log("Отслеживание...")
    try:
        result = watcher_main(date_input)
        watcher_text.configure(state="normal")
        watcher_text.delete(1.0, tk.END)
        watcher_text.insert(tk.END, result)
        watcher_text.configure(state="disabled")
        safe_log("Отслеживание завершено")
    except Exception as e:
        safe_log("Ошибка Watcher: " + str(e))

def run_watcher():
    date_input = watcher_date_entry.get().strip()
    if not date_input:
        messagebox.showerror("Ошибка", "Введите дату")
        return
    threading.Thread(target=run_watcher_task, args=(date_input,), daemon=True).start()

# --- Анализ (оригинальный) ---
def run_analyzer_task(filename):
    safe_log("Анализ...")
    try:
        analyzer_main(filename)
        safe_log("Анализ завершён")
    except Exception as e:
        safe_log("Ошибка анализа: " + str(e))

def run_analyzer():
    drug_name = analyzer_drug_entry.get().strip()
    date_str = analyzer_date_entry.get().strip()
    if not drug_name or not date_str:
        messagebox.showerror("Ошибка", "Введите препарат и дату")
        return
    filename = f"{drug_name.lower()}_{date_str}.json"
    threading.Thread(target=run_analyzer_task, args=(filename,), daemon=True).start()

# --- Анализ побочных эффектов ---
def run_side_effects_analyzer():
    drug_name = analyzer_drug_entry.get().strip()
    req_date = analyzer_date_entry.get().strip()
    if not drug_name or not req_date:
        messagebox.showerror("Ошибка", "Введите препарат и дату")
        return
    try:
        result = get_side_effects_info_from_file(drug_name, req_date)
    except Exception as e:
        result = f"Ошибка: {str(e)}"
    analysis_text.configure(state="normal")
    analysis_text.delete(1.0, tk.END)
    analysis_text.insert(tk.END, result)
    analysis_text.configure(state="disabled")

# --- Препарат ---
def run_drug_watch(drug_name, text_widget):
    if not drug_name:
        messagebox.showerror("Ошибка", "Введите препарат")
        return

    def task():
        result = drug_watch_gui(drug_name)
        text_widget.configure(state="normal")
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, result)
        text_widget.configure(state="disabled")

    threading.Thread(target=task, daemon=True).start()

def create_drug_tab(parent):
    frame = tk.Frame(parent, bg=TAB_BG_COLOR)
    tk.Label(frame, text="Препарат:", bg=TAB_BG_COLOR, fg=LABEL_FG_COLOR) \
        .grid(row=0, column=0, padx=10, pady=10, sticky="e")
    drug_entry = tk.Entry(frame, width=30)
    drug_entry.grid(row=0, column=1, padx=10, pady=10)
    drug_text = ScrolledText(frame, width=80, height=10, state="disabled", bg=LOG_BG_COLOR, fg=LOG_FG_COLOR,
                             font=default_font)
    drug_text.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
    tk.Button(frame, text="Инфо", width=15, bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR,
              command=lambda: run_drug_watch(drug_entry.get().strip(), drug_text)) \
        .grid(row=1, column=0, columnspan=2, padx=10, pady=10)
    return frame

# --- Фильтр побочных эффектов (новая вкладка) ---
def create_filter_tab(parent):
    frame = tk.Frame(parent, bg=TAB_BG_COLOR)

    title = tk.Label(frame, text="Фильтр побочных эффектов", bg=TAB_BG_COLOR,
                     fg=LABEL_FG_COLOR, font=("Mathcad UniMath", 14, "bold"))
    title.grid(row=0, column=0, columnspan=2, pady=10)

    # Поле ввода ключевого слова
    tk.Label(frame, text="Ключевое слово:", bg=TAB_BG_COLOR, fg=LABEL_FG_COLOR, font=default_font) \
        .grid(row=1, column=0, padx=10, pady=5, sticky="e")
    global filter_keyword_entry
    filter_keyword_entry = tk.Entry(frame, width=30, font=default_font)
    filter_keyword_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

    # Поле ввода названия препарата
    tk.Label(frame, text="Название препарата:", bg=TAB_BG_COLOR, fg=LABEL_FG_COLOR, font=default_font) \
        .grid(row=2, column=0, padx=10, pady=5, sticky="e")
    global filter_drug_entry
    filter_drug_entry = tk.Entry(frame, width=30, font=default_font)
    filter_drug_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

    # Кнопка запуска поиска
    tk.Button(frame, text="Найти", bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR, font=default_font,
              command=run_filter).grid(row=3, column=0, columnspan=2, pady=10)

    # Текстовое поле для вывода найденных ID источников (используем меньший шрифт)
    tk.Label(frame, text="Найденные ID источников:", bg=TAB_BG_COLOR, fg=LABEL_FG_COLOR, font=default_font) \
        .grid(row=4, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")
    global filter_ids_text
    filter_ids_text = ScrolledText(frame, width=80, height=5, bg=LOG_BG_COLOR, fg=LOG_FG_COLOR, font=id_font)
    filter_ids_text.grid(row=5, column=0, columnspan=2, padx=10, pady=5)

    # Текстовое поле для вывода побочных эффектов (важная информация – крупный шрифт)
    tk.Label(frame, text="Побочные эффекты:", bg=TAB_BG_COLOR, fg=LABEL_FG_COLOR, font=default_font) \
        .grid(row=6, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")
    global filter_effects_text
    filter_effects_text = ScrolledText(frame, width=80, height=10, bg=LOG_BG_COLOR, fg=LOG_FG_COLOR, font=important_font)
    filter_effects_text.grid(row=7, column=0, columnspan=2, padx=10, pady=5)

    return frame

def run_filter():
    keyword = filter_keyword_entry.get().strip()
    drug = filter_drug_entry.get().strip()
    if not keyword:
        messagebox.showerror("Ошибка", "Введите ключевое слово")
        return
    try:
        found_ids, side_effects = filter_side_effects(keyword, drug)
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))
        return
    filter_ids_text.delete("1.0", tk.END)
    filter_effects_text.delete("1.0", tk.END)
    if not found_ids:
        messagebox.showinfo("Результат", "Записи с указанным ключевым словом не найдены.")
        return
    filter_ids_text.insert(tk.END, "\n".join(found_ids))
    if side_effects:
        filter_effects_text.insert(tk.END, "\n".join(side_effects))
    else:
        filter_effects_text.insert(tk.END, "Побочные эффекты не найдены.")

# ===== Создание главного окна =====
root = tk.Tk()
root.title("BIOLock")
root.configure(bg=BG_COLOR)
# Устанавливаем увеличенную геометрию и разрешаем масштабирование окна
root.geometry("1000x800")
root.resizable(True, True)

loading_manager = LoadingManager(root)
loading_manager.load_animation()

# Меню навигации
menu_bar = Menu(root)
nav_menu = Menu(menu_bar, tearoff=0)
nav_menu.add_command(label="Поиск", command=lambda: notebook.select(frame_parser))
nav_menu.add_command(label="Анализ", command=lambda: notebook.select(frame_analyzer))
nav_menu.add_command(label="Очистка", command=lambda: notebook.select(frame_clearcollect))
nav_menu.add_command(label="Отслеживание", command=lambda: notebook.select(frame_watcher))
nav_menu.add_command(label="Параметры", command=lambda: notebook.select(create_parser_tab(notebook)))
nav_menu.add_command(label="Препарат", command=lambda: notebook.select(create_drug_tab(notebook)))
nav_menu.add_command(label="Источник по ID", command=lambda: notebook.select(frame_source_lookup))
nav_menu.add_command(label="Фильтр побочных эффектов", command=lambda: notebook.select(frame_filter))
menu_bar.add_cascade(label="Навигация", menu=nav_menu)
root.config(menu=menu_bar)

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True, padx=10, pady=10)

frame_parser = tk.Frame(notebook, bg=TAB_BG_COLOR)
frame_analyzer = tk.Frame(notebook, bg=TAB_BG_COLOR)
frame_clearcollect = tk.Frame(notebook, bg=TAB_BG_COLOR)
frame_watcher = tk.Frame(notebook, bg=TAB_BG_COLOR)
frame_source_lookup = create_source_lookup_tab(notebook)
frame_filter = create_filter_tab(notebook)

notebook.add(frame_parser, text="Поиск")
notebook.add(frame_analyzer, text="Анализ")
notebook.add(frame_clearcollect, text="Очистка")
notebook.add(frame_watcher, text="Отслеживание")
notebook.add(create_parser_tab(notebook), text="Параметры")
notebook.add(create_drug_tab(notebook), text="Препарат")
notebook.add(frame_source_lookup, text="Источник по ID")
notebook.add(frame_filter, text="Фильтр побочных эффектов")

# ===== Вкладка "Поиск" =====
tk.Label(frame_parser, text="Препарат:", bg=TAB_BG_COLOR, fg=LABEL_FG_COLOR) \
    .grid(row=0, column=0, padx=10, pady=10, sticky="e")
parser_drug_entry = tk.Entry(frame_parser, width=30)
parser_drug_entry.grid(row=0, column=1, padx=10, pady=10)
search_button = tk.Button(frame_parser, text="Поиск", width=15, bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR,
                          command=run_parser)
search_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
loading_manager = LoadingManager(frame_parser)

# ===== Вкладка "Анализ" =====
tk.Label(frame_analyzer, text="Препарат:", bg=TAB_BG_COLOR, fg=LABEL_FG_COLOR) \
    .grid(row=0, column=0, padx=10, pady=10, sticky="e")
analyzer_drug_entry = tk.Entry(frame_analyzer, width=30)
analyzer_drug_entry.grid(row=0, column=1, padx=10, pady=10)
tk.Label(frame_analyzer, text="Дата:", bg=TAB_BG_COLOR, fg=LABEL_FG_COLOR) \
    .grid(row=1, column=0, padx=10, pady=10, sticky="e")
analyzer_date_entry = tk.Entry(frame_analyzer, width=30)
analyzer_date_entry.grid(row=1, column=1, padx=10, pady=10)
tk.Button(frame_analyzer, text="Анализ", width=15, bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR, command=run_analyzer) \
    .grid(row=2, column=0, columnspan=2, padx=10, pady=5)
tk.Button(frame_analyzer, text="Побочные эффекты", width=15, bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR,
          command=run_side_effects_analyzer) \
    .grid(row=3, column=0, columnspan=2, padx=10, pady=5)
analysis_text = ScrolledText(frame_analyzer, width=80, height=10, state="disabled", bg=LOG_BG_COLOR, fg=LOG_FG_COLOR,
                             font=default_font)
analysis_text.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

# ===== Вкладка "Очистка" =====
tk.Button(frame_clearcollect, text="Очистить", width=12, bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR, command=run_purifier) \
    .grid(row=0, column=0, padx=10, pady=10)
tk.Button(frame_clearcollect, text="Собрать", width=12, bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR,
          command=run_datascavenger) \
    .grid(row=0, column=1, padx=10, pady=10)
tk.Button(frame_clearcollect, text="БД источников", width=12, bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR,
          command=run_source_db_builder) \
    .grid(row=0, column=2, padx=10, pady=10)
source_db_text = ScrolledText(frame_clearcollect, width=90, height=10, state="disabled", bg=LOG_BG_COLOR,
                              fg=LOG_FG_COLOR, font=default_font)
source_db_text.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

# ===== Вкладка "Отслеживание" =====
tk.Label(frame_watcher, text="Дата:", bg=TAB_BG_COLOR, fg=LABEL_FG_COLOR) \
    .grid(row=0, column=0, padx=10, pady=10, sticky="e")
watcher_date_entry = tk.Entry(frame_watcher, width=30)
watcher_date_entry.grid(row=0, column=1, padx=10, pady=10)
tk.Button(frame_watcher, text="Отслеживать", width=15, bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR, command=run_watcher) \
    .grid(row=1, column=0, columnspan=2, padx=10, pady=10)
tk.Label(frame_watcher, text="Результат:", bg=TAB_BG_COLOR, fg=LABEL_FG_COLOR) \
    .grid(row=2, column=0, padx=10, pady=(20, 5), sticky="w")
watcher_text = ScrolledText(frame_watcher, width=80, height=10, state="disabled", bg=LOG_BG_COLOR, fg=LOG_FG_COLOR,
                            font=default_font)
watcher_text.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

# ===== Окно логов =====
log_frame = tk.Frame(root, bg=BG_COLOR)
# Добавляем expand=True, чтобы лог-окно адаптировалось при изменении размера
log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
tk.Label(log_frame, text="Логи:", bg=BG_COLOR, fg=LABEL_FG_COLOR) \
    .pack(anchor="w", padx=5, pady=(5, 0))
log_text = ScrolledText(log_frame, width=90, height=8, state="disabled", bg=LOG_BG_COLOR, fg=LOG_FG_COLOR,
                        font=default_font)
log_text.pack(fill="both", expand=True, padx=5, pady=5)

root.mainloop()
