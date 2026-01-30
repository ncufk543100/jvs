import threading

_lock = threading.Lock()

def acquire():
    if not _lock.acquire(blocking=False):
        raise RuntimeError("已有任务在执行")

def release():
    if _lock.locked():
        _lock.release()
