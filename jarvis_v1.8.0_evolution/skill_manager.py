import os
import re
import json
import subprocess
from pathlib import Path

class SkillManager:
    def __init__(self, skills_dir="skills"):
        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(exist_ok=True)
        self.skills = {}

    def scan_skills(self):
        """扫描 skills 目录下的所有 SKILL.md 文件"""
        self.skills = {}
        if not self.skills_dir.exists():
            return {}
            
        for skill_folder in self.skills_dir.iterdir():
            if skill_folder.is_dir():
                skill_md = skill_folder / "SKILL.md"
                if skill_md.exists():
                    skill_info = self._parse_skill_md(skill_md)
                    if skill_info:
                        skill_info["path"] = str(skill_folder)
                        self.skills[skill_folder.name] = skill_info
        return self.skills

    def _parse_skill_md(self, md_path):
        """解析 SKILL.md 内容"""
        try:
            content = md_path.read_text(encoding="utf-8")
            name_match = re.search(r"# (.*)", content)
            desc_match = re.search(r"## Description\n(.*)", content, re.S)
            usage_match = re.search(r"## Usage\n```json\n(.*?)```", content, re.S)
            
            return {
                "name": name_match.group(1).strip() if name_match else md_path.parent.name,
                "description": desc_match.group(1).strip().split("\n")[0] if desc_match else "无描述",
                "usage": json.loads(usage_match.group(1).strip()) if usage_match else {}
            }
        except Exception as e:
            print(f"解析技能失败 {md_path}: {e}")
            return None

    def execute_skill(self, skill_name, params):
        """执行指定技能"""
        if skill_name not in self.skills:
            return f"错误：未找到技能 {skill_name}"
            
        skill_path = Path(self.skills[skill_name]["path"])
        run_py = skill_path / "run.py"
        run_sh = skill_path / "run.sh"
        
        # 准备参数
        param_str = json.dumps(params)
        
        try:
            if run_py.exists():
                cmd = ["python3", str(run_py), param_str]
            elif run_sh.exists():
                cmd = ["bash", str(run_sh), param_str]
            else:
                return f"错误：技能 {skill_name} 缺少执行脚本 (run.py 或 run.sh)"
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return f"✅ 技能 {skill_name} 执行成功:\n{result.stdout}"
            else:
                return f"❌ 技能 {skill_name} 执行失败:\n{result.stderr}"
        except Exception as e:
            return f"❌ 执行异常: {str(e)}"

    def create_skill(self, skill_name, description, code, usage_example):
        """自主创建一个新技能"""
        skill_folder = self.skills_dir / skill_name
        skill_folder.mkdir(exist_ok=True)
        
        # 写入 SKILL.md
        skill_md_content = f"""# {skill_name}
## Description
{description}

## Usage
```json
{json.dumps(usage_example, indent=2, ensure_ascii=False)}
```
"""
        (skill_folder / "SKILL.md").write_text(skill_md_content, encoding="utf-8")
        
        # 写入执行脚本 (默认 Python)
        (skill_folder / "run.py").write_text(code, encoding="utf-8")
        
        return f"✅ 技能 {skill_name} 已封装并存入技能库。"

# 全局单例
manager = SkillManager()
