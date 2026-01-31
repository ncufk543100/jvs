import requests
import json

def think(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "deepseek-r1:14b",
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json().get("response", "{}")
    except Exception as e:
        return f"LLM Error: {str(e)}"

def chat(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "deepseek-r1:14b",
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        return response.json().get("response", "无法连接模型")
    except Exception as e:
        return f"Chat Error: {str(e)}"
