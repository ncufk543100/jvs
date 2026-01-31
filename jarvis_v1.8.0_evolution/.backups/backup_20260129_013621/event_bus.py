import json, datetime

EVENT_FILE = "EVENTS.json"

def emit(type, message):
    try:
        with open(EVENT_FILE, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"events": []}
    
    data["events"].append({
        "time": datetime.datetime.now().isoformat(),
        "type": type,
        "message": str(message)  # 确保消息是字符串
    })
    
    with open(EVENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
