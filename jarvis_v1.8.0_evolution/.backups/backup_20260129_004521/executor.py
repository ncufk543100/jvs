"""
JARVIS 执行器模块
支持多种工具：文件操作、Shell 命令、代码分析等
"""
import json
import os
import glob
import datetime
import subprocess
import re
from collections import Counter
from sandbox import assert_in_sandbox
from safe_io import safe_write, safe_write_json
from agent_sovereignty import check_venv_for_command

STATE_FILE = "STATE.json"
SCAN_RULES = json.load(open("SCAN_RULES.json", encoding="utf-8"))
PROJECT_MAP_JSON = "PROJECT_MAP.json"
PROJECT_MAP_MD = "PROJECT_MAP.md"

# Shell 命令白名单前缀
ALLOWED_COMMANDS = [
    "ls", "cat", "head", "tail", "wc", "grep", "find", "echo",
    "pwd", "cd", "mkdir", "cp", "mv", "rm",
    "python", "python3", "pip", "pip3",
    "node", "npm", "pnpm", "yarn", "npx",
    "git",
]


def load_state():
    return json.load(open(STATE_FILE, encoding="utf-8"))


def save_state(state):
    safe_write_json(STATE_FILE, state)


# ==================== 文件操作工具 ====================

def scan_files(params=None):
    """扫描项目文件"""
    if params and "path" in params:
        root = params["path"]
    else:
        root = SCAN_RULES.get("root") or "."
    files = []
    for pattern in SCAN_RULES["include"]:
        files += glob.glob(os.path.join(root, pattern), recursive=True)

    files = [
        assert_in_sandbox(f)
        for f in files
        if not any(x.replace("**/", "") in f for x in SCAN_RULES["exclude"])
    ]

    state = load_state()
    state["files_touched"] = files
    save_state(state)
    return f"扫描完成，发现 {len(files)} 个文件"


def generate_project_map(params=None):
    """生成项目地图"""
    state = load_state()
    files = state.get("files_touched", [])
    
    by_ext = Counter([os.path.splitext(f)[1] or "no_ext" for f in files])
    data = {
        "root": open("PROJECT_ROOT.txt").read().strip(),
        "files": files,
        "summary": {
            "total_files": len(files),
            "by_ext": dict(by_ext)
        },
        "generated_at": datetime.datetime.now().isoformat()
    }
    safe_write_json(PROJECT_MAP_JSON, data)

    lines = [
        "# Project Map",
        "",
        f"- Root: {data['root']}",
        f"- Total files: {data['summary']['total_files']}",
        "",
        "## 文件类型统计",
    ]
    for ext, count in sorted(by_ext.items(), key=lambda x: -x[1]):
        lines.append(f"- {ext}: {count} 个")
    
    lines.append("")
    lines.append("## 文件列表")
    lines += [f"- {f}" for f in files]

    safe_write(PROJECT_MAP_MD, "\n".join(lines))
    return f"项目地图已生成，包含 {len(files)} 个文件"


def read_file(params):
    """读取文件内容"""
    path = params.get("path", "")
    if not path:
        return "错误：未指定文件路径"
    
    path = assert_in_sandbox(path)
    
    if not os.path.exists(path):
        return f"错误：文件不存在 - {path}"
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 如果文件太大，只返回前 2000 字符
        if len(content) > 2000:
            return f"文件内容（前 2000 字符）:\n\n{content[:2000]}\n\n... (文件共 {len(content)} 字符)"
        return f"文件内容:\n\n{content}"
    except Exception as e:
        return f"读取文件失败: {str(e)}"


def write_file(params):
    """写入文件"""
    path = params.get("path", "")
    content = params.get("content", "")
    
    if not path:
        return "错误：未指定文件路径"
    
    path = assert_in_sandbox(path)
    
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        safe_write(path, content)
        return f"文件已写入: {path} ({len(content)} 字符)"
    except Exception as e:
        return f"写入文件失败: {str(e)}"


def append_file(params):
    """追加内容到文件"""
    path = params.get("path", "")
    content = params.get("content", "")
    
    if not path:
        return "错误：未指定文件路径"
    
    path = assert_in_sandbox(path)
    
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return f"内容已追加到: {path}"
    except Exception as e:
        return f"追加文件失败: {str(e)}"


def list_files(params=None):
    """列出目录内容"""
    params = params or {}
    path = params.get("path", ".")
    
    path = assert_in_sandbox(path)
    
    if not os.path.exists(path):
        return f"错误：路径不存在 - {path}"
    
    try:
        if os.path.isfile(path):
            stat = os.stat(path)
            return f"文件: {path}\n大小: {stat.st_size} 字节\n修改时间: {datetime.datetime.fromtimestamp(stat.st_mtime)}"
        
        items = os.listdir(path)
        dirs = [d for d in items if os.path.isdir(os.path.join(path, d))]
        files = [f for f in items if os.path.isfile(os.path.join(path, f))]
        
        result = [f"目录: {path}", f"共 {len(dirs)} 个文件夹, {len(files)} 个文件", ""]
        
        if dirs:
            result.append("📁 文件夹:")
            for d in sorted(dirs)[:20]:
                result.append(f"  - {d}/")
            if len(dirs) > 20:
                result.append(f"  ... 还有 {len(dirs) - 20} 个文件夹")
        
        if files:
            result.append("📄 文件:")
            for f in sorted(files)[:30]:
                size = os.path.getsize(os.path.join(path, f))
                result.append(f"  - {f} ({size} bytes)")
            if len(files) > 30:
                result.append(f"  ... 还有 {len(files) - 30} 个文件")
        
        return "\n".join(result)
    except Exception as e:
        return f"列出目录失败: {str(e)}"


def search_files(params):
    """搜索文件内容"""
    keyword = params.get("keyword", "")
    path = params.get("path", ".")
    
    if not keyword:
        return "错误：未指定搜索关键词"
    
    path = assert_in_sandbox(path)
    
    results = []
    try:
        for root, dirs, files in os.walk(path):
            # 排除特定目录
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', '.venv']]
            
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if keyword.lower() in content.lower():
                            # 找到匹配的行
                            lines = content.split('\n')
                            matches = []
                            for i, line in enumerate(lines, 1):
                                if keyword.lower() in line.lower():
                                    matches.append(f"  第{i}行: {line.strip()[:80]}")
                            results.append(f"📄 {filepath}")
                            results.extend(matches[:3])  # 每个文件最多显示3个匹配
                            if len(matches) > 3:
                                results.append(f"  ... 还有 {len(matches) - 3} 处匹配")
                except:
                    pass
                
                if len(results) > 50:
                    break
        
        if results:
            return f"搜索 '{keyword}' 的结果:\n\n" + "\n".join(results)
        return f"未找到包含 '{keyword}' 的文件"
    except Exception as e:
        return f"搜索失败: {str(e)}"


# ==================== Shell 命令执行 ====================

def run_shell(params):
    """执行 Shell 命令"""
    command = params.get("command", "")
    
    if not command:
        return "错误：未指定命令"
    
    # 获取项目根目录
    try:
        project_root = open("PROJECT_ROOT.txt").read().strip()
    except FileNotFoundError:
        project_root = os.getcwd()
    
    # 【硬性要求】检查是否需要虚拟环境，如果需要则自动包装命令
    can_proceed, venv_msg, wrapped_command = check_venv_for_command(command, project_root)
    if not can_proceed:
        return venv_msg
    
    # 如果有包装后的命令，使用它
    actual_command = wrapped_command if wrapped_command else command
    
    # 安全检查：只允许白名单命令（检查原始命令，不检查包装后的）
    cmd_parts = command.strip().split()
    if not cmd_parts:
        return "错误：空命令"
    
    base_cmd = cmd_parts[0]
    if not any(base_cmd.startswith(allowed) for allowed in ALLOWED_COMMANDS):
        return f"错误：不允许执行命令 '{base_cmd}'。允许的命令: {', '.join(ALLOWED_COMMANDS)}"
    
    # 危险命令检查
    dangerous_patterns = ['rm -rf /', 'rm -rf ~', '> /dev/', 'mkfs', 'dd if=']
    for pattern in dangerous_patterns:
        if pattern in command:
            return f"错误：检测到危险命令模式"
    
    # 如果使用了虚拟环境包装，输出提示
    venv_notice = ""
    if wrapped_command:
        venv_notice = f"🐍 已在虚拟环境中执行\n\n"
    
    try:
        result = subprocess.run(
            actual_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,  # 虚拟环境命令可能需要更长时间
            cwd=project_root
        )
        
        output = ""
        if result.stdout:
            output += f"输出:\n{result.stdout[:2000]}"
            if len(result.stdout) > 2000:
                output += f"\n... (输出共 {len(result.stdout)} 字符)"
        if result.stderr:
            output += f"\n错误:\n{result.stderr[:500]}"
        if result.returncode != 0:
            output += f"\n返回码: {result.returncode}"
        
        return venv_notice + (output or "命令执行完成（无输出）")
    except subprocess.TimeoutExpired:
        return "错误：命令执行超时（60秒）"
    except Exception as e:
        return f"执行命令失败: {str(e)}"


def run_python(params):
    """执行 Python 代码"""
    code = params.get("code", "")
    
    if not code:
        return "错误：未指定代码"
    
    # 创建临时文件
    temp_file = "/tmp/clawedbot_temp.py"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)
        
        result = subprocess.run(
            ["python3", temp_file],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=open("PROJECT_ROOT.txt").read().strip()
        )
        
        output = ""
        if result.stdout:
            output += f"输出:\n{result.stdout[:2000]}"
        if result.stderr:
            output += f"\n错误:\n{result.stderr[:500]}"
        
        return output or "代码执行完成（无输出）"
    except subprocess.TimeoutExpired:
        return "错误：代码执行超时（30秒）"
    except Exception as e:
        return f"执行代码失败: {str(e)}"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


# ==================== 代码分析工具 ====================

def analyze_code(params):
    """分析代码文件"""
    path = params.get("path", "")
    
    if not path:
        return "错误：未指定文件路径"
    
    path = assert_in_sandbox(path)
    
    if not os.path.exists(path):
        return f"错误：文件不存在 - {path}"
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.split("\n")
        total_lines = len(lines)
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith("#")])
        comment_lines = len([l for l in lines if l.strip().startswith("#")])
        blank_lines = len([l for l in lines if not l.strip()])
        
        # 提取函数和类
        functions = re.findall(r'def\s+(\w+)\s*\(', content)
        classes = re.findall(r'class\s+(\w+)\s*[:\(]', content)
        imports = re.findall(r'^(?:from\s+\S+\s+)?import\s+(.+)$', content, re.MULTILINE)
        
        result = [
            f"📊 代码分析: {path}",
            "",
            f"总行数: {total_lines}",
            f"代码行: {code_lines}",
            f"注释行: {comment_lines}",
            f"空白行: {blank_lines}",
            "",
        ]
        
        if classes:
            result.append(f"🏛️ 类 ({len(classes)}):")
            for c in classes[:10]:
                result.append(f"  - {c}")
        
        if functions:
            result.append(f"⚡ 函数 ({len(functions)}):")
            for f in functions[:15]:
                result.append(f"  - {f}()")
        
        if imports:
            result.append(f"📦 导入 ({len(imports)}):")
            for i in imports[:10]:
                result.append(f"  - {i}")
        
        return "\n".join(result)
    except Exception as e:
        return f"分析代码失败: {str(e)}"


def check_dependencies(params=None):
    """检查项目依赖"""
    root = open("PROJECT_ROOT.txt").read().strip()
    results = []
    
    # 检查 Python 依赖
    requirements_file = os.path.join(root, "requirements.txt")
    if os.path.exists(requirements_file):
        with open(requirements_file, "r") as f:
            deps = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        results.append(f"📦 Python 依赖 (requirements.txt): {len(deps)} 个")
        for d in deps[:10]:
            results.append(f"  - {d}")
        if len(deps) > 10:
            results.append(f"  ... 还有 {len(deps) - 10} 个")
    
    # 检查 Node.js 依赖
    package_json = os.path.join(root, "package.json")
    if os.path.exists(package_json):
        with open(package_json, "r") as f:
            pkg = json.load(f)
        deps = pkg.get("dependencies", {})
        dev_deps = pkg.get("devDependencies", {})
        results.append(f"\n📦 Node.js 依赖 (package.json):")
        results.append(f"  生产依赖: {len(deps)} 个")
        results.append(f"  开发依赖: {len(dev_deps)} 个")
    
    if not results:
        return "未找到依赖文件 (requirements.txt 或 package.json)"
    
    return "\n".join(results)# ==================== 工具请示机制 ====================

def request_tool_installation(params):
    """请示主人安装工具"""
    tool_name = params.get("tool_name", "")
    install_command = params.get("install_command", "")
    purpose = params.get("purpose", "")
    
    if not tool_name or not install_command:
        return "错误：未指定工具名称或安装命令"
    
    from event_bus import emit_event
    
    message = f"""🛠️ 主人，我需要安装 {tool_name}

💻 **安装命令**: `{install_command}`

🎯 **用途**: {purpose}

是否允许安装？"""
    
    emit_event("confirm", message)
    
    # 返回等待状态，实际安装由主人确认后手动执行
    return f"✅ 已向主人请示安装 {tool_name}，等待批准..."


# ==================== 网络和HTTP ====================

def browse_url(params):
    """访问网页并提取内容"""
    url = params.get("url", "")
    
    if not url:
        return "错误：未指定URL"
    
    try:
        import urllib.request
        from html.parser import HTMLParser
        
        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.in_script = False
                self.in_style = False
            
            def handle_starttag(self, tag, attrs):
                if tag in ['script', 'style']:
                    if tag == 'script':
                        self.in_script = True
                    else:
                        self.in_style = True
            
            def handle_endtag(self, tag):
                if tag == 'script':
                    self.in_script = False
                elif tag == 'style':
                    self.in_style = False
            
            def handle_data(self, data):
                if not self.in_script and not self.in_style:
                    text = data.strip()
                    if text:
                        self.text.append(text)
            
            def get_text(self):
                return '\n'.join(self.text)
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; JARVIS/1.0)'
        })
        
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        parser = TextExtractor()
        parser.feed(html)
        content = parser.get_text()
        
        # 限制返回内容长度
        if len(content) > 5000:
            content = content[:5000] + "\n\n...内容过长，已截断"
        
        return f"网页内容 ({url}):\n\n{content}"
        
    except Exception as e:
        return f"访问网页失败: {str(e)}"


def http_request(params):
    """发送HTTP请求"""
    url = params.get("url", "")
    method = params.get("method", "GET").upper()
    headers = params.get("headers", {})
    data = params.get("data", None)
    
    if not url:
        return "错误：未指定URL"
    
    try:
        import urllib.request
        import urllib.parse
        
        # 准备请求
        headers['User-Agent'] = headers.get('User-Agent', 'JARVIS/1.0')
        
        if data and isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        elif data and isinstance(data, str):
            data = data.encode('utf-8')
        
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
            status = response.status
        
        return f"HTTP {status}\n\n{content}"
        
    except Exception as e:
        return f"HTTP请求失败: {str(e)}"


def download_file(params):
    """下载文件"""
    url = params.get("url", "")
    save_path = params.get("path", "")
    
    if not url:
        return "错误：未指定URL"
    if not save_path:
        return "错误：未指定保存路径"
    
    try:
        import urllib.request
        save_path = assert_in_sandbox(save_path)
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; JARVIS/1.0)'
        })
        
        with urllib.request.urlopen(req, timeout=60) as response:
            content = response.read()
        
        with open(save_path, 'wb') as f:
            f.write(content)
        
        size = len(content)
        return f"文件已下载: {save_path} ({size} bytes)"
        
    except Exception as e:
        return f"下载文件失败: {str(e)}"


def web_search(params):
    """网络搜索（使用 DuckDuckGo）"""
    query = params.get("query", "")
    
    if not query:
        return "错误：未指定搜索关键词"
    
    try:
        import urllib.request
        import urllib.parse
        
        # 使用 DuckDuckGo Instant Answer API
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'JARVIS/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        results = []
        
        # 摘要
        if data.get("Abstract"):
            results.append(f"摘要: {data['Abstract']}")
            if data.get("AbstractSource"):
                results.append(f"   来源: {data['AbstractSource']}")
        
        # 相关主题
        if data.get("RelatedTopics"):
            results.append("\n相关结果:")
            for topic in data["RelatedTopics"][:5]:
                if isinstance(topic, dict) and topic.get("Text"):
                    text = topic["Text"][:150]
                    results.append(f"  - {text}")
        
        if results:
            return f"搜索 '{query}' 的结果:\n\n" + "\n".join(results)
        return f"未找到 '{query}' 的相关信息，请尝试其他关键词"
    except Exception as e:
        return f"搜索失败: {str(e)}"


# ==================== Git 操作 ====================

def git_status(params=None):
    """查看 Git 状态"""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            cwd=open("PROJECT_ROOT.txt").read().strip()
        )
        
        if result.returncode != 0:
            return f"Git 错误: {result.stderr}"
        
        if not result.stdout.strip():
            return "✅ 工作区干净，没有未提交的更改"
        
        return f"📋 Git 状态:\n{result.stdout}"
    except Exception as e:
        return f"获取 Git 状态失败: {str(e)}"


def git_log(params=None):
    """查看 Git 提交历史"""
    params = params or {}
    count = params.get("count", 10)
    
    try:
        result = subprocess.run(
            ["git", "log", f"-{count}", "--oneline", "--decorate"],
            capture_output=True,
            text=True,
            cwd=open("PROJECT_ROOT.txt").read().strip()
        )
        
        if result.returncode != 0:
            return f"Git 错误: {result.stderr}"
        
        return f"📜 最近 {count} 次提交:\n{result.stdout}"
    except Exception as e:
        return f"获取 Git 历史失败: {str(e)}"


def git_diff(params=None):
    """查看 Git 差异"""
    try:
        result = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True,
            text=True,
            cwd=open("PROJECT_ROOT.txt").read().strip()
        )
        
        if not result.stdout.strip():
            return "没有未暂存的更改"
        
        return f"📝 文件更改:\n{result.stdout}"
    except Exception as e:
        return f"获取 Git 差异失败: {str(e)}"


# ==================== 工具注册表 ====================

TOOLS = {
    # 文件操作
    "scan_files": {"func": scan_files, "desc": "扫描项目文件", "params": "path (项目路径)"},
    "generate_project_map": {"func": generate_project_map, "desc": "生成项目地图", "params": "path (项目路径)"},
    "read_file": {"func": read_file, "desc": "读取文件内容", "params": "path (文件路径，必须是绝对路径)"},
    "write_file": {"func": write_file, "desc": "写入文件", "params": "path (文件路径), content (文件内容)"},
    "append_file": {"func": append_file, "desc": "追加内容到文件", "params": "path (文件路径), content (追加内容)"},
    "list_files": {"func": list_files, "desc": "列出目录内容", "params": "path (目录路径)"},
    "search_files": {"func": search_files, "desc": "搜索文件内容", "params": "path (搜索路径), pattern (搜索模式)"},
    
    # Shell 和代码执行
    "run_shell": {"func": run_shell, "desc": "执行 Shell 命令", "params": "command (Shell命令字符串)"},
    "run_python": {"func": run_python, "desc": "执行 Python 代码", "params": "code (Python代码字符串)"},
    
    # 代码分析
    "analyze_code": {"func": analyze_code, "desc": "分析代码文件"},
    "check_dependencies": {"func": check_dependencies, "desc": "检查项目依赖"},
    
    # Git 操作
    "git_status": {"func": git_status, "desc": "查看 Git 状态"},
    "git_log": {"func": git_log, "desc": "查看提交历史"},
    "git_diff": {"func": git_diff, "desc": "查看文件差异"},
    
    # 工具请示
    "request_tool_installation": {"func": request_tool_installation, "desc": "请示主人安装新工具"},
    
    # 网络和HTTP
    "web_search": {"func": web_search, "desc": "网络搜索（DuckDuckGo）", "params": "query (搜索关键词)"},
    "browse_url": {"func": browse_url, "desc": "访问网页并提取内容", "params": "url (网页URL)"},
    "http_request": {"func": http_request, "desc": "发送HTTP请求（支持GET/POST等）", "params": "url (请求URL), method (请求方法，默认GET), data (请求数据，可选)"},
    "download_file": {"func": download_file, "desc": "下载文件到本地", "params": "url (文件URL), save_path (保存路径)"},
}


def get_available_tools():
    """获取所有可用工具列表，包含参数说明"""
    result = {}
    for name, info in TOOLS.items():
        desc = info["desc"]
        if "params" in info:
            desc += f" [参数: {info['params']}]"
        result[name] = desc
    return result


def find_similar_tool(tool_name):
    import difflib
    available_tools = list(TOOLS.keys())
    matches = difflib.get_close_matches(tool_name, available_tools, n=3, cutoff=0.6)
    return matches

def execute(command: str):
    if not command.startswith("RUN"):
        raise RuntimeError("非法命令格式")

    payload = json.loads(command[3:].strip())
    tool = payload.get("tool", "")
    params = payload.get("params", {})

    if tool not in TOOLS:
        similar = find_similar_tool(tool)
        if similar:
            suggestion = f"未知工具: {tool}。你可能想用: {', '.join(similar)}。请使用正确的工具名称。"
        else:
            available = ", ".join(list(TOOLS.keys())[:10])
            suggestion = f"未知工具: {tool}。可用工具包括: {available}...。如需要新工具，请使用 request_tool_installation 请示主人。"
        return suggestion

    return TOOLS[tool]["func"](params)


# ==================== 删除文件确认机制 ====================

PENDING_DELETE_FILE = "PENDING_DELETE.json"

def _load_pending_deletes():
    """加载待确认删除列表"""
    try:
        with open(PENDING_DELETE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"pending": []}

def _save_pending_deletes(data):
    """保存待确认删除列表"""
    with open(PENDING_DELETE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def delete_file(params):
    """请求删除文件（需要用户确认）"""
    path = params.get("path", "")
    if not path:
        return "错误：未指定文件路径"
    
    if not os.path.isabs(path):
        root = open("PROJECT_ROOT.txt").read().strip()
        path = os.path.join(root, path)
    
    if not os.path.exists(path):
        return f"错误：文件不存在 - {path}"
    
    pending = _load_pending_deletes()
    for item in pending["pending"]:
        if item["path"] == path:
            return f"⚠️ 文件已在待确认删除队列中: {path}"
    
    pending["pending"].append({
        "path": path,
        "size": os.path.getsize(path),
        "is_dir": os.path.isdir(path),
        "requested_at": datetime.datetime.now().isoformat()
    })
    _save_pending_deletes(pending)
    
    file_type = "目录" if os.path.isdir(path) else "文件"
    return f"""⚠️ 删除请求已记录，等待用户确认

{file_type}: {path}
大小: {os.path.getsize(path)} 字节

请用户确认是否删除：
- 确认删除：使用 confirm_delete 工具
- 取消删除：使用 cancel_delete 工具"""

def confirm_delete(params):
    """确认删除文件"""
    import shutil
    path = params.get("path", "")
    confirm_all = params.get("all", False)
    
    pending = _load_pending_deletes()
    if not pending["pending"]:
        return "没有待确认删除的文件"
    
    results = []
    
    if confirm_all:
        for item in pending["pending"]:
            try:
                if os.path.isdir(item["path"]):
                    shutil.rmtree(item["path"])
                    results.append(f"✅ 已删除目录: {item['path']}")
                else:
                    os.remove(item["path"])
                    results.append(f"✅ 已删除文件: {item['path']}")
            except Exception as e:
                results.append(f"❌ 删除失败 {item['path']}: {e}")
        pending["pending"] = []
        _save_pending_deletes(pending)
        return "\n".join(results)
    
    if not path:
        if len(pending["pending"]) == 1:
            path = pending["pending"][0]["path"]
        else:
            lines = ["待确认删除的文件："]
            for i, item in enumerate(pending["pending"], 1):
                lines.append(f"{i}. {item['path']}")
            return "\n".join(lines)
    
    for i, item in enumerate(pending["pending"]):
        if item["path"] == path:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    results.append(f"✅ 已删除目录: {path}")
                else:
                    os.remove(path)
                    results.append(f"✅ 已删除文件: {path}")
                pending["pending"].pop(i)
                _save_pending_deletes(pending)
            except Exception as e:
                results.append(f"❌ 删除失败: {e}")
            break
    else:
        return f"文件不在待删除队列中: {path}"
    
    return "\n".join(results) if results else "操作完成"

def cancel_delete(params):
    """取消删除请求"""
    path = params.get("path", "")
    cancel_all = params.get("all", False)
    
    pending = _load_pending_deletes()
    if not pending["pending"]:
        return "没有待确认删除的文件"
    
    if cancel_all:
        count = len(pending["pending"])
        pending["pending"] = []
        _save_pending_deletes(pending)
        return f"✅ 已取消 {count} 个删除请求"
    
    if not path:
        if len(pending["pending"]) == 1:
            path = pending["pending"][0]["path"]
        else:
            return "请指定要取消的文件路径，或使用 all=True 取消全部"
    
    for i, item in enumerate(pending["pending"]):
        if item["path"] == path:
            pending["pending"].pop(i)
            _save_pending_deletes(pending)
            return f"✅ 已取消删除: {path}"
    
    return f"文件不在待删除队列中: {path}"

def list_pending_deletes(params=None):
    """查看待删除文件列表"""
    pending = _load_pending_deletes()
    if not pending["pending"]:
        return "没有待确认删除的文件"
    
    lines = ["待确认删除的文件："]
    for i, item in enumerate(pending["pending"], 1):
        file_type = "目录" if item.get("is_dir") else "文件"
        lines.append(f"{i}. [{file_type}] {item['path']} ({item['size']} 字节)")
    return "\n".join(lines)


# ==================== 微信开发者工具 ====================

try:
    from wechat_devtools import (
        wechat_check_status,
        wechat_open,
        wechat_get_errors,
        wechat_preview,
        wechat_upload,
        wechat_screenshot
    )
    WECHAT_AVAILABLE = True
except ImportError:
    WECHAT_AVAILABLE = False


# 添加删除工具到注册表
TOOLS["delete_file"] = {"func": delete_file, "desc": "请求删除文件（需用户确认）"}
TOOLS["confirm_delete"] = {"func": confirm_delete, "desc": "确认删除文件"}
TOOLS["cancel_delete"] = {"func": cancel_delete, "desc": "取消删除请求"}
TOOLS["list_pending_deletes"] = {"func": list_pending_deletes, "desc": "查看待删除文件列表"}

# 添加微信开发者工具（如果可用）
if WECHAT_AVAILABLE:
    TOOLS["wechat_check_status"] = {"func": wechat_check_status, "desc": "检查微信开发者工具状态"}
    TOOLS["wechat_open"] = {"func": wechat_open, "desc": "打开微信开发者工具"}
    TOOLS["wechat_get_errors"] = {"func": wechat_get_errors, "desc": "获取小程序编译错误"}
    TOOLS["wechat_preview"] = {"func": wechat_preview, "desc": "预览小程序"}
    TOOLS["wechat_upload"] = {"func": wechat_upload, "desc": "上传小程序代码"}
    TOOLS["wechat_screenshot"] = {"func": wechat_screenshot, "desc": "截取小程序截图"}


# ==================== 安全自我修改工具 ====================

try:
    from self_modify import (
        get_or_create_session,
        clear_session,
        request_restart
    )
    SELF_MODIFY_AVAILABLE = True
except ImportError:
    SELF_MODIFY_AVAILABLE = False


def self_modify_start(params=None):
    """启动安全自我修改会话"""
    if not SELF_MODIFY_AVAILABLE:
        return "❌ 自我修改模块不可用"
    
    try:
        session = get_or_create_session()
        success, msg = session.start_session()
        return msg
    except Exception as e:
        return f"❌ 启动会话失败: {str(e)}"


def self_modify_read(params):
    """读取临时目录中的 JARVIS 代码文件"""
    if not SELF_MODIFY_AVAILABLE:
        return "❌ 自我修改模块不可用"
    
    filename = params.get("filename", "")
    if not filename:
        return "❌ 请指定要读取的文件名"
    
    try:
        session = get_or_create_session()
        success, content = session.read_temp_file(filename)
        if success:
            return f"📄 {filename} 内容:\n\n{content}"
        return content
    except Exception as e:
        return f"❌ 读取失败: {str(e)}"


def self_modify_write(params):
    """修改临时目录中的 JARVIS 代码文件"""
    if not SELF_MODIFY_AVAILABLE:
        return "❌ 自我修改模块不可用"
    
    filename = params.get("filename", "")
    content = params.get("content", "")
    
    if not filename:
        return "❌ 请指定要修改的文件名"
    if not content:
        return "❌ 请指定新内容"
    
    try:
        session = get_or_create_session()
        success, msg = session.modify_temp_file(filename, content)
        return msg
    except Exception as e:
        return f"❌ 修改失败: {str(e)}"


def self_modify_test(params=None):
    """运行自我修改测试"""
    if not SELF_MODIFY_AVAILABLE:
        return "❌ 自我修改模块不可用"
    
    params = params or {}
    test_code = params.get("test_code", "")
    
    try:
        session = get_or_create_session()
        
        if test_code:
            success, msg = session.run_custom_test(test_code)
        else:
            success, msg = session.run_all_tests()
        
        return msg
    except Exception as e:
        return f"❌ 测试失败: {str(e)}"


def self_modify_apply(params=None):
    """应用自我修改（测试通过后）"""
    if not SELF_MODIFY_AVAILABLE:
        return "❌ 自我修改模块不可用"
    
    params = params or {}
    force = params.get("force", False)
    
    try:
        session = get_or_create_session()
        success, msg = session.apply_modifications(force=force)
        return msg
    except Exception as e:
        return f"❌ 应用修改失败: {str(e)}"


def self_modify_rollback(params=None):
    """回滚到备份版本"""
    if not SELF_MODIFY_AVAILABLE:
        return "❌ 自我修改模块不可用"
    
    try:
        session = get_or_create_session()
        success, msg = session.rollback()
        return msg
    except Exception as e:
        return f"❌ 回滚失败: {str(e)}"


def self_modify_status(params=None):
    """查看自我修改会话状态"""
    if not SELF_MODIFY_AVAILABLE:
        return "❌ 自我修改模块不可用"
    
    try:
        session = get_or_create_session()
        status = session.get_session_status()
        
        lines = ["📊 自我修改会话状态", ""]
        lines.append(f"会话 ID: {status['session_id']}")
        lines.append(f"会话激活: {'是' if status['active'] else '否'}")
        
        if status['active']:
            lines.append(f"临时目录: {status['temp_dir']}")
            lines.append(f"备份目录: {status['backup_dir']}")
            lines.append(f"修改数量: {len(status['modifications'])}")
            lines.append(f"测试数量: {len(status['test_results'])}")
            
            if status['modifications']:
                lines.append("\n已修改的文件:")
                for mod in status['modifications']:
                    lines.append(f"  - {mod['filename']}")
        
        return "\n".join(lines)
    except Exception as e:
        return f"❌ 获取状态失败: {str(e)}"


def self_modify_end(params=None):
    """结束自我修改会话"""
    if not SELF_MODIFY_AVAILABLE:
        return "❌ 自我修改模块不可用"
    
    params = params or {}
    cleanup = params.get("cleanup", True)
    
    try:
        session = get_or_create_session()
        success, msg = session.end_session(cleanup=cleanup)
        clear_session()
        return msg
    except Exception as e:
        return f"❌ 结束会话失败: {str(e)}"


def self_modify_restart(params=None):
    """请求重启 JARVIS 服务"""
    if not SELF_MODIFY_AVAILABLE:
        return "❌ 自我修改模块不可用"
    
    try:
        success, msg = request_restart()
        return msg
    except Exception as e:
        return f"❌ 请求重启失败: {str(e)}"


# 添加自我修改工具到注册表
if SELF_MODIFY_AVAILABLE:
    TOOLS["self_modify_start"] = {"func": self_modify_start, "desc": "启动安全自我修改会话"}
    TOOLS["self_modify_read"] = {"func": self_modify_read, "desc": "读取临时目录中的代码文件"}
    TOOLS["self_modify_write"] = {"func": self_modify_write, "desc": "修改临时目录中的代码文件"}
    TOOLS["self_modify_test"] = {"func": self_modify_test, "desc": "运行自我修改测试"}
    TOOLS["self_modify_apply"] = {"func": self_modify_apply, "desc": "应用自我修改（测试通过后）"}
    TOOLS["self_modify_rollback"] = {"func": self_modify_rollback, "desc": "回滚到备份版本"}
    TOOLS["self_modify_status"] = {"func": self_modify_status, "desc": "查看自我修改会话状态"}
    TOOLS["self_modify_end"] = {"func": self_modify_end, "desc": "结束自我修改会话"}
    TOOLS["self_modify_restart"] = {"func": self_modify_restart, "desc": "请求重启服务"}
