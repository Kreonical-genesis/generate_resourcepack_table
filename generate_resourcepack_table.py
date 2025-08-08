import zipfile
import os
import json
import tempfile
import shutil
from pathlib import Path
from html import escape

def extract_when_model(obj, item_name, results):
    if isinstance(obj, dict):
        # Если есть нужная пара "when" и "model" (строка)
        if "when" in obj and "model" in obj:
            whens = obj["when"]
            model_data = obj["model"]
            model_path = model_data.get("model") if isinstance(model_data, dict) else None

            if isinstance(whens, str):
                results.append((whens, model_path or "", item_name))
            elif isinstance(whens, list):
                for when_val in whens:
                    results.append((when_val, model_path or "", item_name))

        # Рекурсивный проход по всем вложенным объектам
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


    # Если это просто список (а не объект с "overrides")
    if isinstance(data, list):
        for entry in data:
            when = entry.get("when", "")
            model = entry.get("model", {}).get("model", "")
            results.append((when, model, item_name))
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
h2 { margin-top: 40px; }
table { border-collapse: collapse; width: 100%; margin-bottom: 40px; }
th, td { border: 1px solid #ccc; padding: 6px 12px; text-align: left; }
th { background: #f9f9f9; }
</style></head><body>
<h2>Список переименований / моделей / предметов </h2>
"""
    for pack_name, rows in tables.items():
        html += f"<h2>{escape(pack_name)}</h2>\n"
        html += "<table><tr><th>Переименование</th><th>Модель</th><th>Предмет</th></tr>\n"
        for rename, model, item in rows:
            html += f"<tr><td>{escape(rename)}</td><td>{escape(model)}</td><td>{escape(item)}</td></tr>\n"
        html += "</table>\n"

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
