import os
from pathlib import Path

_ROOT = Path(__file__).parent.absolute()
LOCK_FILE = _ROOT / "RUNNING.lock"

def acquire():
    """尝试获取运行锁"""
    if LOCK_FILE.exists():
        return False
    try:
        LOCK_FILE.touch()
        return True
    except:
        return False

def release():
    """释放运行锁"""
    if LOCK_FILE.exists():
        try:
            LOCK_FILE.unlink()
        except:
            pass
