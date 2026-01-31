import json, datetime, os
from pathlib import Path

_ROOT = Path(__file__).parent.absolute()
EVENT_FILE = str(_ROOT / "EVENTS.json")

def emit(type, message):
    try:
        if os.path.exists(EVENT_FILE):
            with open(EVENT_FILE, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                if isinstance(data, list): # 兼容旧的数组格式
                    data = {"events": data}
        else:
            data = {"events": []}
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"events": []}
    
    data["events"].append({
        "time": datetime.datetime.now().isoformat(),
        "type": type,
        "message": str(message)
    })
    
    with open(EVENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
