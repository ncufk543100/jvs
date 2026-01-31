import json, datetime

EVENT_FILE = "EVENTS.json"

def emit(type, message):
    data = json.load(open(EVENT_FILE, encoding="utf-8"))
    data["events"].append({
        "time": datetime.datetime.now().isoformat(),
        "type": type,
        "message": message
    })
    json.dump(data, open(EVENT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
