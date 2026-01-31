import os
import psutil
import json

def run():
    info = {
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2)
    }
    print(json.dumps(info))

if __name__ == "__main__":
    run()
