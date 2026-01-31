import os
LOCK_FILE = "RUNNING.lock"

def acquire():
    if os.path.exists(LOCK_FILE):
        return False
    with open(LOCK_FILE, "w") as f:
        f.write("1")
    return True

def release():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
