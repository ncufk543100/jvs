#!/usr/bin/env python3
"""
事件日志清理脚本
用于清空EVENTS.json，避免文件无限增长
"""

import json
import os

EVENT_FILE = "EVENTS.json"

def clear_events():
    """清空事件日志"""
    data = {"events": []}
    with open(EVENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 事件日志已清空: {EVENT_FILE}")

if __name__ == "__main__":
    clear_events()
