# generate_resourcepack_table

# 🧊 Генератор таблицы для Minecraft-ресурспаков

Этот скрипт ищет ZIP-архивы с ресурспаками в текущей папке, извлекает из них переименования предметов и соответствующие модели, и создаёт красивый HTML-отчёт (`resourcepack.html`) с таблицами.

## 📂 Как использовать

1. Помести `.zip` файлы ресурспаков в ту же папку, что и скрипт.
2. Запусти скрипт:
   ```bash
   python generate_resourcepack_table.py


3. Открой `resourcepack.html` в браузере.

## 🔎 Что он ищет

Скрипт находит JSON-файлы внутри `assets/**/item/*.json`, извлекает пары `when` + `model` и группирует их по предметам.

## 📄 Пример отчёта

* Название ресурспака

  * Предмет: `clock`

    * Переименование: `Ykropsio v11 pink`
    * Модель: `item/clock/v11/v11pink`

---

# 🧊 Resourcepack Table Generator for Minecraft

This script scans `.zip` files in the same folder for Minecraft resourcepacks, extracts item rename conditions and corresponding models, and generates a neat `resourcepack.html` report.

## 📂 How to use

1. Put `.zip` resourcepacks in the same folder as the script.
2. Run it:

   ```bash
   python generate_resourcepack_table.py
   ```
3. Open `resourcepack.html` in your browser.

## 🔍 What it finds

It extracts `when` + `model` pairs from `*.json` files under `assets/**/item/` and groups them by item.

## 📄 Report example

* Pack name

  * Item: `clock`

    * Rename: `Ykropsio v11 pink`
    * Model: `item/clock/v11/v11pink`
