import re, json

EXECUTOR_FILE = "executor.py"
TOOLS_FILE = "TOOLS.json"

def discover_tools():
    code = open(EXECUTOR_FILE, encoding="utf-8").read()
    tools = {}

    for m in re.finditer(r"def (\w+)\(", code):
        name = m.group(1)
        if name.startswith("_") or name in ("execute", "update_state"):
            continue
        tools[name] = {
            "description": f"auto discovered tool {name}",
            "params": {}
        }

    json.dump(tools, open(TOOLS_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    return tools

if __name__ == "__main__":
    discover_tools()
