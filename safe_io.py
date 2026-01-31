import json
import os

def safe_write(path, content):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def safe_write_json(path, data):
    safe_write(path, json.dumps(data, indent=2, ensure_ascii=False))

def safe_read_json(path, default=None):
    if not os.path.exists(path): return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default
