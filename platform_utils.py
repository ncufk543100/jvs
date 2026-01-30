import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Union

class PlatformUtils:
    @staticmethod
    def is_windows() -> bool:
        return os.name == 'nt'
    
    @staticmethod
    def is_linux() -> bool:
        return os.name == 'posix'
    
    @staticmethod
    def get_home_dir() -> Path:
        if PlatformUtils.is_windows():
            return Path(os.path.expanduser('~'))
        else:
            return Path.home()
    
    @staticmethod
    def path_separator() -> str:
        return os.path.sep
    
    @staticmethod
    def normalize_path(path: Union[str, Path]) -> Path:
        path_obj = Path(path) if isinstance(path, str) else path
        if PlatformUtils.is_windows():
            return Path(str(path_obj).replace('/', '\\'))
        return path_obj
    
    @staticmethod
    def run_command(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, '', str(e)
    
    @staticmethod
    def find_executable(name: str) -> Optional[Path]:
        if PlatformUtils.is_windows():
            paths = os.environ.get('PATH', '').split(';')
            exts = os.environ.get('PATHEXT', '.EXE;.COM;.BAT;.CMD').split(';')
        else:
            paths = os.environ.get('PATH', '').split(':')
            exts = ['']
        
        for path in paths:
            for ext in exts:
                full_path = Path(path) / f"{name}{ext}"
                if full_path.exists() and os.access(full_path, os.X_OK):
                    return full_path
        return None
    
    @staticmethod
    def kill_process(pid: int) -> bool:
        try:
            if PlatformUtils.is_windows():
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
            else:
                os.kill(pid, 9)
            return True
        except:
            return False