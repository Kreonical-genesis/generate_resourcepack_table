# 📦 Resourcepack Table Generator English

**generate\_resourcepack\_table.py** — is a tool for parsing Minecraft resource packs (1.21.6+) and generating an interactive HTML report with tables of renames and related models.

## 🚀 Features

* 📂 **Supports Minecraft 1.21.6+** — parses new model formats and conditions.
* 🔍 **Recursive search** for `"when"` conditions and related models.
* 🔗 **Resolves references** via `model`, `parent`, arrays `models`, and some new `type` entries.
* 📑 **Groups** identical renames into a single row.
* 🖱 **Interactive HTML table**:

  * Filter rows by input.
  * Sort by clicking column headers.
  * Drag and reorder columns with the mouse.
  * Toggle grouping on/off.
* ⚙ **Configurable via config.json**.
* 🎨 **Supports custom HTML template** (`cfg.html`).

---

## 📂 Project Structure

```
.
├── generate_resourcepack_table.py  # Main script
├── config.json                     # Configuration
├── cfg.html                        # HTML template
├── resourcepack.html               # Generated report
├── *.zip                           # Resourcepacks to process
```

---

## ⚙ Configuration (`config.json`)

You can adjust generator behavior in the config:

| Parameter             | Description                                                         |
| --------------------- | ------------------------------------------------------------------- |
| `group_by_rename`     | `true/false` — group identical renames into one row.                |
| `show_all_items_list` | `true/false` — show a list of all items at the end.                 |
| `columns_order`       | Order of columns in the table, e.g. `["Renames", "Item", "Model"]`. |
| `table_class`         | CSS class for the table.                                            |
| `open_all_details`    | `true/false` — open all `<details>` elements by default.            |
| `title`               | Page title.                                                         |

💡 Keys starting with `_comment` are ignored and serve only as descriptions.

---

## 🎨 HTML Template (`cfg.html`)

The HTML template must contain two placeholders:

* `{{TITLE}}` — replaced by the title from `config.json`.
* `{{TABLES}}` — replaced by generated tables and interactive JS/CSS.

You can customize styles, fonts, and design as you wish.

---

## 🛠 Installation and Usage

1. **Place** `generate_resourcepack_table.py`, `config.json`, and `cfg.html` in the same folder.
2. **Copy** `.zip` resourcepack files into the same folder.
3. Install Python 3.7+.
4. Run in terminal:

```bash
python3 generate_resourcepack_table.py
```

5. After completion, open `resourcepack.html` in your browser.

---

## 📋 Example Output

After generation, you will get a page with interactive tables:

* Text filter — filters rows by input.
* Click column headers to sort.
* Drag column headers to reorder.
* "Group by model" button toggles visibility of the "Item" column.

---

## 📄 License

MIT License — free to use and modify.

---

# 📦 Resourcepack Table Generator Русский

**generate\_resourcepack\_table.py** — это инструмент для парсинга ресурспаков Minecraft (1.21.6+) и генерации интерактивного HTML-отчёта с таблицами переименований и связанных моделей.

## 🚀 Возможности

* 📂 **Поддержка Minecraft 1.21.6+** — парсинг новых форматов моделей и условий.
* 🔍 **Рекурсивный поиск** условий `"when"` и связанных моделей.
* 🔗 **Разрешение ссылок** через `model`, `parent`, массивы `models` и некоторые новые типы (`type`).
* 📑 **Группировка** одинаковых переименований в одну строку.
* 🖱 **Интерактивная HTML-таблица**:

  * Фильтрация строк по вводу.
  * Сортировка по клику на заголовок.
  * Перетаскивание колонок мышью.
  * Переключение группировки.
* ⚙ **Настройка через config.json**.
* 🎨 **Поддержка собственного HTML-шаблона** (cfg.html).

---

## 📂 Структура проекта

```
.
├── generate_resourcepack_table.py  # Основной скрипт
├── config.json                     # Конфигурация
├── cfg.html                        # HTML-шаблон
├── resourcepack.html               # Генерируемый отчёт
├── *.zip                           # Ресурспаки для обработки
```

---

## ⚙ Конфигурация (`config.json`)

В конфиге можно менять поведение генератора:

| Параметр              | Описание                                                                       |
| --------------------- | ------------------------------------------------------------------------------ |
| `group_by_rename`     | `true/false` — группировать одинаковые переименования в одну строку.           |
| `show_all_items_list` | `true/false` — показывать список всех предметов в конце.                       |
| `columns_order`       | Порядок колонок в таблице, например `["Переименования", "Предмет", "Модель"]`. |
| `table_class`         | CSS-класс для таблицы.                                                         |
| `open_all_details`    | `true/false` — открывать все `<details>` по умолчанию.                         |
| `title`               | Заголовок страницы.                                                            |

💡 Ключи, начинающиеся с `_comment`, игнорируются и используются только для описания настроек.

---

## 🎨 HTML-шаблон (`cfg.html`)

Шаблон HTML должен содержать два плейсхолдера:

* `{{TITLE}}` — заменяется на заголовок из `config.json`.
* `{{TABLES}}` — заменяется на сгенерированные таблицы и интерактивный JS/CSS.

Можно менять стили, шрифты и оформление по своему вкусу.

---

## 🛠 Установка и запуск

1. **Поместите** `generate_resourcepack_table.py`, `config.json` и `cfg.html` в одну папку.
2. **Скопируйте** `.zip` файлы ресурспаков в ту же папку.
3. Установите Python 3.7+.
4. В терминале запустите:

```bash
python3 generate_resourcepack_table.py
```

5. После выполнения в папке появится `resourcepack.html` — откройте его в браузере.

---

## 📋 Пример работы

После генерации вы получите страницу с интерактивными таблицами:

* Фильтр по тексту — отсекает строки.
* Клик по заголовку сортирует колонку.
* Заголовки колонок можно перетаскивать.
* Кнопка "Group by model" скрывает/показывает колонку "Предмет".

---

## 📄 Лицензия

MIT License — свободно используйте и изменяйте.