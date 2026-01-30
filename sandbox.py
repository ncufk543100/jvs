import os

ROOT = os.path.abspath(open("PROJECT_ROOT.txt", encoding="utf-8").read().strip())

def assert_in_sandbox(path: str):
    p = os.path.abspath(path)
    if not p.startswith(ROOT):
        raise PermissionError(f"路径越界：{p}")
    return p
