#!/usr/bin/env python3
"""
generate_resourcepack_table.py
Improved resourcepack parser for Minecraft 1.21.6+ with interactive HTML output.

Features:
- Recursively extracts "when" conditions and associated "model" references from JSON files.
- Resolves model references through 'model', 'parent', composite 'models' arrays and some new model types.
- Tries to resolve referenced model JSON files inside the resourcepack assets.
- Groups multiple "when" values that point to the same model into one row.
- Produces interactive HTML with filtering, sortable columns and drag&drop column reordering.
- Reads settings from config.json (supports comment keys prefixed with "_comment").
- Uses cfg.html as an HTML template with {{TABLES}} placeholder.
"""

import zipfile
import os
import json
import tempfile
import shutil
from pathlib import Path
from html import escape
from collections import defaultdict

# -------------------------
# Config / template names
# -------------------------
CONFIG_FILE = "config.json"
TEMPLATE_FILE = "cfg.html"
OUTPUT_FILE = "resourcepack.html"

# -------------------------
# Helpers: load config (ignore _comment_ keys)
# -------------------------
def load_config(path):
    if not path.exists():
        raise FileNotFoundError(f"Config '{path}' not found.")
    raw = json.loads(path.read_text(encoding="utf-8"))
    cfg = {k: v for k, v in raw.items() if not k.startswith("_comment")}
    # defaults
    cfg.setdefault("group_by_rename", True)
    cfg.setdefault("show_all_items_list", True)
    cfg.setdefault("columns_order", ["Переименования", "Предмет", "Модель"])
    cfg.setdefault("table_class", "default-table")
    cfg.setdefault("open_all_details", True)
    cfg.setdefault("title", "📦 Resourcepack report")
    return cfg

# -------------------------
# Parsing JSON models: extraction utilities
# -------------------------
def as_list(v):
    if isinstance(v, list):
        return v
    if v is None:
        return []
    return [v]

def get_models_from_model_data(model_data):
    """
    Return list of model references (strings) found inside model_data.
    Handles:
      - dict with "model": "namespace:..."
      - dict with "models": [ ... ] (composite)
      - direct string (rare)
      - dict with "type" 'minecraft:player_head' etc (we'll return a type marker)
    """
    found = []

    if isinstance(model_data, str):
        found.append(model_data)
        return found

    if not isinstance(model_data, dict):
        return found

    # direct model field
    m = model_data.get("model")
    if isinstance(m, str) and m:
        found.append(m)

    # composite models
    models_list = model_data.get("models")
    if isinstance(models_list, list):
        for sub in models_list:
            found.extend(get_models_from_model_data(sub))

    # type markers (player head etc.)
    t = model_data.get("type")
    if isinstance(t, str):
        # keep the type as an info fallback
        found.append(f"[type:{t}]")

    return found

# -------------------------
# Resolve model reference to a file path inside assets root (if possible)
# -------------------------
def resolve_model_ref(model_ref, assets_root):
    """
    Try to resolve model reference like "namespace:item/name" or "item/name" to a .json path under assets_root.
    Returns list of candidate resolved JSON relative paths (strings) or empty list if not found.
    This function is best-effort: searches assets/*/models/** for matching name.
    """
    if not model_ref:
        return []

    # if it's a special type marker like "[type:minecraft:player_head]" -> return it as-is
    if isinstance(model_ref, str) and model_ref.startswith("[type:"):
        return [model_ref]

    candidates = []

    # Normalize: remove leading slash, ensure no .json
    mr = model_ref.strip().lstrip("/")
    if mr.endswith(".json"):
        mr = mr[:-5]

    # If contains namespace "ns:path"
    if ":" in mr:
        ns, path = mr.split(":", 1)
        # path may start with "item/..." or "models/..." but commonly "item/..."
        # construct expected file
        parts = path.split("/")
        # Try path as-is under ns/models/
        candidate = assets_root / ns / "models" / Path(*parts)
        if (candidate.with_suffix(".json")).exists():
            candidates.append(str(candidate.with_suffix(".json").relative_to(assets_root)))
        # Also try direct path under ns/models/item/... (if path didn't include "item")
        if parts[0] not in ("item", "block", "entity"):
            candidate2 = assets_root / ns / "models" / "item" / Path(*parts)
            if (candidate2.with_suffix(".json")).exists():
                candidates.append(str(candidate2.with_suffix(".json").relative_to(assets_root)))
    else:
        # No namespace: search any namespace for a matching models/**/<mr>.json
        # Try exact matches first (mr may include item/... or just name)
        mr_parts = mr.split("/")
        # search assets_root/*/models/**/<last>.json and filter by tail containing mr
        last = mr_parts[-1]
        for ns_dir in assets_root.iterdir():
            if not ns_dir.is_dir():
                continue
            for p in ns_dir.rglob("models"):
                # search for files with matching tail
                for file in p.rglob(f"{last}.json"):
                    # quick check: if path ends with the mr (joined) or contains mr parts
                    rel = file.relative_to(assets_root)
                    # try to match deeper: if "/".join(last k) in rel
                    # accept it
                    candidates.append(str(rel))
    # dedupe preserve order
    seen = set()
    out = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out

# -------------------------
# Recursive extractor: find all objects that contain "when" and "model"
# -------------------------
def extract_when_model(obj, item_name, results, assets_root):
    """
    Walks the JSON object recursively and appends tuples:
      (item_name, list_of_when_values, list_of_model_references, source_info)
    where model references are resolved (if possible) to file paths or type markers.
    """
    if isinstance(obj, dict):
        # If structure has "when" and "model" (new style)
        if "when" in obj and "model" in obj:
            whens_raw = obj["when"]
            whens = []
            if isinstance(whens_raw, list):
                for w in whens_raw:
                    whens.append(str(w))
            else:
                whens.append(str(whens_raw))
            whens = sorted(dict.fromkeys([w.strip() for w in whens if w is not None and str(w).strip() != ""]))

            model_data = obj["model"]
            models = get_models_from_model_data(model_data)
            # If no explicit models collected, try parent in same object
            if not models and "parent" in obj:
                parent_val = obj.get("parent")
                if isinstance(parent_val, str) and parent_val:
                    models.append(parent_val)

            # Resolve model refs to files if possible
            resolved = []
            for m in models:
                candidates = resolve_model_ref(m, assets_root)
                if candidates:
                    resolved.extend(candidates)
                else:
                    # if nothing resolved just keep original m
                    resolved.append(m)

            results.append((item_name, whens, resolved))
        # Recurse into all values
        for v in obj.values():
            extract_when_model(v, item_name, results, assets_root)
    elif isinstance(obj, list):
        for entry in obj:
            extract_when_model(entry, item_name, results, assets_root)

# -------------------------
# Parse single JSON file and return results
# -------------------------
def parse_when_model_file(file_path: Path, assets_root: Path):
    results = []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return results
    item_name = str(file_path.relative_to(assets_root)).replace("\\", "/")
    extract_when_model(data, item_name, results, assets_root)
    return results

# -------------------------
# Process a resourcepack zip, return list of rows
# -------------------------
def process_resourcepack(zip_path: Path):
    temp_dir = Path(tempfile.mkdtemp(prefix="rp_"))
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(temp_dir)
        assets_root = temp_dir / "assets"
        results = []
        if not assets_root.exists():
            return results
        # Walk json files under assets (we will parse all .json because newer packs may store models/items in different folders)
        for json_file in assets_root.rglob("*.json"):
            # parse file
            parsed = parse_when_model_file(json_file, assets_root)
            # parsed items are (item_name, [whens], [model_refs_or_files])
            for item_name, whens, model_refs in parsed:
                # join model refs into one list (can be multiple)
                if not model_refs:
                    model_refs = [""]
                results.append((item_name, whens, model_refs))
        return results
    finally:
        # keep temp until function ends, then cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

# -------------------------
# Build table data structure
# -------------------------
def build_table_from_packs(packs_rows):
    """
    packs_rows: dict pack_name -> list of tuples (item_name, [whens], [model_refs])
    Return a structure suitable for HTML generation:
      pack_name -> list of rows where each row is dict:
        { "item": item_name, "whens": [..], "models": [..], "models_display": "a, b", "source_files": [..] }
    """
    out = {}
    for pack, rows in packs_rows.items():
        rows_out = []
        for item_name, whens, model_refs in rows:
            # normalize whens -> string
            whens_str = ", ".join(whens) if isinstance(whens, (list, tuple)) else str(whens)
            # models_display: join unique model refs
            models_flat = []
            for m in model_refs:
                if isinstance(m, list):
                    models_flat.extend(m)
                else:
                    models_flat.append(m)
            # unique preserve order
            seen = set()
            models_unique = []
            for m in models_flat:
                if m not in seen:
                    seen.add(m)
                    models_unique.append(m)
            models_display = ", ".join(models_unique) if models_unique else ""
            rows_out.append({
                "item": item_name,
                "whens": whens,
                "whens_str": whens_str,
                "models": models_unique,
                "models_display": models_display
            })
        out[pack] = rows_out
    return out

# -------------------------
# Generate interactive HTML (uses cfg.html as template with {{TABLES}} placeholder)
# -------------------------
def generate_html(template_html, data_by_pack, cfg):
    # Build HTML pieces into a table block per pack
    parts = []
    all_items = set()

    for pack, rows in data_by_pack.items():
        parts.append(f"<h2>{escape(pack)}</h2>\n")
        # Optionally group by item
        # Build mapping item -> model -> set(whens)
        item_map = defaultdict(lambda: defaultdict(set))
        for r in rows:
            item = r["item"]
            all_items.add(item)
            # each model in models list -> add whens
            if r["models"]:
                for m in r["models"]:
                    item_map[item][m].update(r["whens"])
            else:
                # no model -> use empty key
                item_map[item][""].update(r["whens"])

        # If config requests group_by_rename we'll show grouped; but interactive UI also allows toggle
        # Create a container with data attributes for JS manipulation
        table_container_id = f"pack_{escape(pack).replace(' ', '_')}"
        parts.append(f"<div class='pack' id='{table_container_id}'>\n")

        # Control bar: toggle grouping (JS will sync), copy/paste or other controls could be added
        parts.append("""
<div class="controls">
  <label><input type="checkbox" class="toggle-grouping" checked> Group by model</label>
  <input type="text" class="filter-input" placeholder="Filter items / models / renames...">
</div>
""")

        # Start table area
        parts.append("<div class='tables-area'>\n")
        # We'll output one table: each row = grouped model; columns order from cfg
        cols = cfg.get("columns_order", ["Переименования", "Предмет", "Модель"])
        parts.append(f"<table class='{escape(cfg.get('table_class','default-table'))}' data-pack='{escape(pack)}'>")
        # header row (draggable)
        parts.append("<thead><tr>")
        for col in cols:
            parts.append(f"<th draggable='true' class='col-header'>{escape(col)}</th>")
        parts.append("</tr></thead>")

        parts.append("<tbody>")
        # iterate items -> models
        for item_name in sorted(item_map):
            models_for_item = item_map[item_name]
            for model_key in sorted(models_for_item.keys()):
                renames = sorted(models_for_item[model_key])
                renames_str = ", ".join(renames)
                model_display = model_key if model_key else ""
                # produce row with columns in order (we'll later allow JS to reorder them)
                row_cells = {
                    "Переименования": renames_str,
                    "Предмет": item_name,
                    "Модель": model_display
                }
                parts.append("<tr class='data-row'>")
                for col in cols:
                    parts.append(f"<td>{escape(str(row_cells.get(col, '')))}</td>")
                parts.append("</tr>")
        parts.append("</tbody></table>\n")
        parts.append("</div>")  # tables-area
        parts.append("</div>")  # pack container

    # All items list
    if cfg.get("show_all_items_list", True):
        parts.append(f"<details><summary>📋 All items ({len(all_items)})</summary>\n<ul>")
        for it in sorted(all_items):
            parts.append(f"<li>{escape(it)}</li>")
        parts.append("</ul></details>")

    tables_html = "\n".join(parts)

    # Insert interactive JS/CSS into template (template must include {{TABLES}})
    interactive_js = r"""
<script>
// Simple table filter & header drag-drop & sorting
document.addEventListener('DOMContentLoaded', function(){
  // filter input behavior
  document.querySelectorAll('.pack').forEach(function(pack){
    const filter = pack.querySelector('.filter-input');
    const table = pack.querySelector('table');
    if(!filter || !table) return;
    filter.addEventListener('input', function(){
      const q = filter.value.trim().toLowerCase();
      table.querySelectorAll('tbody tr.data-row').forEach(function(tr){
        const text = tr.textContent.toLowerCase();
        tr.style.display = text.includes(q) ? '' : 'none';
      });
    });
    // grouping toggle
    const toggle = pack.querySelector('.toggle-grouping');
    if(toggle){
      toggle.addEventListener('change', function(){
        // For now toggle will simply hide item column if unchecked (as an example)
        // can be extended to re-render grouping differently
        const idx = Array.from(table.tHead.rows[0].cells).findIndex(th=>th.textContent.trim() === 'Предмет' || th.textContent.trim()==='Item');
        if(idx>=0){
          table.querySelectorAll('tbody tr').forEach(function(tr){
            const cell = tr.cells[idx];
            if(cell) cell.style.display = toggle.checked ? '' : 'none';
          });
          table.tHead.rows[0].cells[idx].style.display = toggle.checked ? '' : 'none';
        }
      });
      // initialize to checked from template default
      if(!toggle.checked) toggle.dispatchEvent(new Event('change'));
    }

    // simple sortable headers
    table.querySelectorAll('th').forEach(function(th, colIndex){
      th.style.cursor = 'pointer';
      th.addEventListener('click', function(){
        const tbody = table.tBodies[0];
        const rows = Array.from(tbody.rows);
        const asc = !th.classList.contains('asc');
        tbody.append(...rows.sort(function(a,b){
          const A = a.cells[colIndex].textContent.trim().toLowerCase();
          const B = b.cells[colIndex].textContent.trim().toLowerCase();
          return (A>B?1:-1) * (asc?1:-1);
        }));
        table.querySelectorAll('th').forEach(h=>h.classList.remove('asc','desc'));
        th.classList.add(asc?'asc':'desc');
      });

      // drag-drop for headers (column reorder)
      th.addEventListener('dragstart', function(e){
        e.dataTransfer.setData('text/plain', colIndex);
        th.classList.add('dragging');
      });
      th.addEventListener('dragend', function(){
        th.classList.remove('dragging');
      });
      th.addEventListener('dragover', function(e){
        e.preventDefault();
      });
      th.addEventListener('drop', function(e){
        e.preventDefault();
        const from = parseInt(e.dataTransfer.getData('text/plain'));
        const to = colIndex;
        if(from === to) return;
        // reorder header cells
        const header = table.tHead.rows[0];
        const headerCells = Array.from(header.cells);
        const moved = headerCells.splice(from,1)[0];
        headerCells.splice(to,0,moved);
        header.innerHTML = '';
        headerCells.forEach(c=>header.appendChild(c));
        // reorder body cells in each row
        table.tBodies[0].querySelectorAll('tr').forEach(function(row){
          const cells = Array.from(row.cells);
          const mc = cells.splice(from,1)[0];
          cells.splice(to,0,mc);
          row.innerHTML = '';
          cells.forEach(c=>row.appendChild(c));
        });
      });
    });
  });
});
</script>
"""

    interactive_css = r"""
<style>
.default-table { border-collapse: collapse; width:100%; margin:6px 0;}
.default-table th, .default-table td { border:1px solid #ddd; padding:6px; text-align:left; }
.default-table th { background:#f6f6f6; }
.pack .controls { margin-bottom:6px; display:flex; gap:8px; align-items:center; }
.filter-input { flex:1; padding:6px; }
.col-header.dragging { opacity:0.5; }
th.asc::after{ content: " ▲"; }
th.desc::after{ content: " ▼"; }
</style>
"""

    final_html = template_html.replace("{{TABLES}}", tables_html + interactive_css + interactive_js)
    # also replace title if present
    final_html = final_html.replace("{{TITLE}}", escape(cfg.get("title","Resourcepack Report")))
    return final_html

# -------------------------
# Main runner
# -------------------------
def main():
    base = Path(__file__).parent.resolve()
    cfg = load_config(base / CONFIG_FILE)

    # Load template
    if not (base / TEMPLATE_FILE).exists():
        raise FileNotFoundError(f"Template '{TEMPLATE_FILE}' not found in folder.")
    template_html = (base / TEMPLATE_FILE).read_text(encoding="utf-8")

    # Find zip files
    zip_files = list(base.glob("*.zip"))
    if not zip_files:
        print("❌ No .zip resourcepacks found in folder.")
        return

    packs_rows = {}
    for z in zip_files:
        print(f"📦 Processing: {z.name}")
        rows = process_resourcepack(z)
        packs_rows[z.stem] = rows

    data_by_pack = build_table_from_packs(packs_rows)
    final_html = generate_html(template_html, data_by_pack, cfg)
    (base / OUTPUT_FILE).write_text(final_html, encoding="utf-8")
    print(f"✅ Generated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
