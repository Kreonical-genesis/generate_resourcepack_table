import zipfile
import os
import json
import tempfile
import shutil
from pathlib import Path
from html import escape
from collections import defaultdict

def extract_when_model(obj, item_name, results):
    if isinstance(obj, dict):
        if "when" in obj and "model" in obj:
            whens = obj["when"]
            model_data = obj["model"]
            model_path = model_data.get("model") if isinstance(model_data, dict) else None

            if isinstance(whens, str):
                results.append((item_name, whens, model_path or ""))
            elif isinstance(whens, list):
                for when_val in whens:
                    results.append((item_name, when_val, model_path or ""))

        for key, value in obj.items():
            extract_when_model(value, item_name, results)

    elif isinstance(obj, list):
        for entry in obj:
            extract_when_model(entry, item_name, results)

def parse_when_model_file(file_path, item_name):
    results = []
    with open(file_path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    extract_when_model(data, item_name, results)
    return results

def process_resourcepack(zip_path):
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    results = []
    assets_path = Path(temp_dir, "assets")
    if not assets_path.exists():
        shutil.rmtree(temp_dir)
        return results

    for root, dirs, files in os.walk(assets_path):
        for file in files:
            if file.endswith(".json"):
                file_path = Path(root) / file
                item_name = file_path.stem
                rows = parse_when_model_file(file_path, item_name)
                results.extend(rows)

    shutil.rmtree(temp_dir)
    return results

def generate_html(tables):
    html = """<html>
<head><meta charset="utf-8"><style>
body { font-family: sans-serif; padding: 20px; }
h1 { font-size: 28px; }
h2 { margin-top: 40px; font-size: 22px; }
details { margin-bottom: 20px; }
summary { font-weight: bold; font-size: 18px; cursor: pointer; margin: 10px 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 20px 0; }
th, td { border: 1px solid #ccc; padding: 6px 12px; text-align: left; }
th { background: #f9f9f9; }
</style></head><body>
<h1>📦 Отчёт по ресурспакам</h1>
"""

    all_items_set = set()

    for pack_name, rows in tables.items():
        html += f"<h2>{escape(pack_name)}</h2>\n"

        # Удаление дубликатов
        unique_rows = list(set(rows))

        # Группировка: item -> model -> [rename1, rename2, ...]
        grouped = defaultdict(lambda: defaultdict(list))
        for item, rename, model in unique_rows:
            grouped[item][model].append(rename)
            all_items_set.add(item)

        html += f"<details open>\n<summary>Все предметы</summary>\n"

        for item_name in sorted(grouped):
            html += f"<details>\n<summary>{escape(item_name)}</summary>\n"
            html += "<table><tr><th>Переименования</th><th>Предмет</th><th>Модель</th></tr>\n"
            for model, renames in sorted(grouped[item_name].items()):
                rename_str = ", ".join(sorted(set(renames)))
                html += f"<tr><td>{escape(rename_str)}</td><td>{escape(item_name)}</td><td>{escape(model)}</td></tr>\n"
            html += "</table></details>\n"

        html += "</details>\n"

    # Вкладка со списком всех предметов
    html += f"<details>\n<summary>📋 Все предметы ({len(all_items_set)})</summary>\n<ul>\n"
    for item in sorted(all_items_set):
        html += f"<li>{escape(item)}</li>\n"
    html += "</ul></details>\n"

    html += "</body></html>"
    return html


def main():
    current_dir = Path(__file__).parent.resolve()
    zip_files = list(current_dir.glob("*.zip"))
    if not zip_files:
        print("❌ Нет ZIP-файлов в папке со скриптом.")
        return

    tables = {}
    for zip_file in zip_files:
        print(f"📦 Обработка: {zip_file.name}")
        rows = process_resourcepack(zip_file)
        if rows:
            tables[zip_file.stem] = rows

    if tables:
        html = generate_html(tables)
        with open("resourcepack.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Файл resourcepack.html успешно создан.")
    else:
        print("⚠️ Не найдено переопределений в стиле 'when + model'.")

if __name__ == "__main__":
    main()

# todo модели, почему-то объеденились в одно и даже не повторяются 
# Код сортировки считает переименованиями
# другую руку всё ещё хавает - тоже самое с гуи
# то же самое с луком