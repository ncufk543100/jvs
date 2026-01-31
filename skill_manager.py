import os
import json
import re
from safe_io import safe_write, safe_read_json

SKILLS_DIR = "skills"

class SkillManager:
    def __init__(self):
        self.skills = {}
        self.scan_skills()

    def scan_skills(self):
        self.skills = {}
        if not os.path.exists(SKILLS_DIR):
            os.makedirs(SKILLS_DIR)
            return {}
            
        for skill_name in os.listdir(SKILLS_DIR):
            skill_path = os.path.join(SKILLS_DIR, skill_name)
            if os.path.isdir(skill_path):
                md_path = os.path.join(skill_path, "SKILL.md")
                if os.path.exists(md_path):
                    with open(md_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    # 简单的 Markdown 解析，提取描述和用法
                    description_match = re.search(r'description:\s*(.*)', content)
                    usage_match = re.search(r'## Quick Start: One-Shot Tasks\s*```bash\s*([^`]+)```', content, re.DOTALL)
                    
                    description = description_match.group(1).strip() if description_match else f"No description for {skill_name}"
                    usage = usage_match.group(1).strip() if usage_match else "No usage example"
                    
                    self.skills[skill_name] = {
                        "description": description,
                        "path": skill_path,
                        "usage": usage
                    }
        return self.skills

    def execute_skill(self, name, params):
        # 实际执行逻辑需要更复杂的代码，这里简化为提示
        return f"技能 {name} 已被调用，参数: {json.dumps(params)}"

    def create_skill(self, name, desc, code, usage):
        skill_path = os.path.join(SKILLS_DIR, name)
        os.makedirs(skill_path, exist_ok=True)
        
        # 写入 SKILL.md
        md_content = f"""---
name: {name}
description: {desc}
---

## Usage Example
```bash
{usage}
```
"""
        safe_write(os.path.join(skill_path, "SKILL.md"), md_content)
        
        # 写入 run.py
        safe_write(os.path.join(skill_path, "run.py"), code)
        
        self.scan_skills()
        return f"技能 {name} 创建成功，已添加到工具箱。"

manager = SkillManager()
