"""\nJARVIS 自我进化沙盒系统（GitHub版本）\n在隔离的沙盒环境中安全地进化代码，使用GitHub进行版本管理\n\n安全策略：\n- 从GitHub克隆到本地沙盒\n- 在本地evolution分支上进化\n- 不自动推送到GitHub\n- 生成详细对比报告供用户review\n- 用户手动决定是否同步改动\n"""

import os
import json
import subprocess
from typing import Dict, List
from datetime import datetime
from pathlib import Path

class EvolutionSandbox:
    """进化沙盒管理器（GitHub版本）"""
    
    def __init__(
        self,
        github_repo: str = "https://github.com/ncufk543100/jarvis.git",
        sandbox_base: str = "/home/ubuntu/jarvis_evolution",
        github_token: str = None
    ):
        # 如果提供了token，构建带认证的URL
        if github_token:
            # 将https://github.com/替换为https://TOKEN@github.com/
            self.github_repo = github_repo.replace(
                "https://github.com/",
                f"https://{github_token}@github.com/"
            )
        else:
            # 尝试从现有仓库获取带token的URL
            try:
                result = subprocess.run(
                    ["git", "config", "--get", "remote.origin.url"],
                    cwd="/home/ubuntu/jarvis",
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and "@github.com" in result.stdout:
                    self.github_repo = result.stdout.strip()
                else:
                    self.github_repo = github_repo
            except:
                self.github_repo = github_repo
        
        self.sandbox_base = sandbox_base
        self.current_sandbox = None
        self.current_branch = None
        
        # 确保沙盒基础目录存在
        os.makedirs(sandbox_base, exist_ok=True)
    
    def create_sandbox(self, version: str = "3.0") -> str:
        """
        从GitHub创建进化沙盒
        
        Args:
            version: 目标版本号
        
        Returns:
            str: 沙盒路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sandbox_name = f"v{version}_{timestamp}"
        sandbox_path = os.path.join(self.sandbox_base, sandbox_name)
        branch_name = f"evolution_v{version}_{timestamp}"
        
        print(f"🔨 从GitHub创建进化沙盒: {sandbox_path}")
        print(f"📦 仓库: {self.github_repo}")
        print(f"🌿 分支: {branch_name}")
        
        # 1. 克隆仓库
        try:
            result = subprocess.run(
                ["git", "clone", self.github_repo, sandbox_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                raise Exception(f"Git clone失败: {result.stderr}")
            print(f"   ✅ 克隆成功")
        except Exception as e:
            print(f"   ❌ 克隆失败: {e}")
            return None
        
        # 2. 创建进化分支
        try:
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=sandbox_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise Exception(f"创建分支失败: {result.stderr}")
            print(f"   ✅ 创建分支: {branch_name}")
        except Exception as e:
            print(f"   ❌ 创建分支失败: {e}")
            return None
        
        # 3. 创建沙盒元数据
        metadata = {
            "version": version,
            "branch": branch_name,
            "created_at": datetime.now().isoformat(),
            "github_repo": self.github_repo,
            "status": "created"
        }
        
        metadata_path = os.path.join(sandbox_path, "SANDBOX_META.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.current_sandbox = sandbox_path
        self.current_branch = branch_name
        
        print(f"✅ 沙盒创建完成: {sandbox_path}")
        return sandbox_path
    
    def evolve(
        self,
        goal: str,
        max_iterations: int = 10
    ) -> Dict:
        """
        在沙盒中进化代码
        
        Args:
            goal: 进化目标
            max_iterations: 最大迭代次数
        
        Returns:
            Dict: 进化结果
        """
        if not self.current_sandbox:
            raise Exception("请先创建沙盒")
        
        print(f"\n🚀 开始进化循环...")
        print(f"🎯 目标: {goal}")
        print(f"📍 沙盒: {self.current_sandbox}")
        print(f"🌿 分支: {self.current_branch}")
        
        evolution_result = {
            "goal": goal,
            "iterations": [],
            "final_state": "in_progress"
        }
        
        for i in range(1, max_iterations + 1):
            print(f"\n{'='*60}")
            print(f"🔄 迭代 {i}/{max_iterations}")
            print(f"{'='*60}")
            
            iteration_result = self._run_single_iteration(goal, i)
            evolution_result["iterations"].append(iteration_result)
            
            # 提交改进到Git
            self._commit_changes(f"evolution: iteration {i}")
            
            if iteration_result["status"] == "goal_achieved":
                evolution_result["final_state"] = "goal_achieved"
                print(f"\n🎉 进化目标达成！")
                break
            
            if iteration_result["status"] == "failed":
                print(f"\n❌ 迭代失败: {iteration_result.get('error')}")
                # 继续尝试
        
        # 保存进化报告
        self._save_evolution_report(evolution_result)
        
        return evolution_result
    
    def _run_single_iteration(self, goal: str, iteration: int) -> Dict:
        """运行单次迭代"""
        print(f"\n💭 分析当前状态...")
        
        # 1. 分析当前代码状态
        current_state = self._analyze_current_state()
        print(f"   📊 {current_state['total_files']} 个文件, 版本 {current_state['version']}")
        
        # 2. 生成改进方案
        print(f"💡 生成改进方案...")
        improvement_plan = self._generate_improvement_plan_simple(goal, current_state)
        
        # 3. 应用改进
        print(f"🔧 应用改进...")
        apply_result = self._apply_improvements_simple(improvement_plan)
        
        # 4. 评估进展
        progress = self._evaluate_progress_simple(goal, apply_result)
        
        return {
            "iteration": iteration,
            "status": progress["status"],
            "improvements": improvement_plan,
            "apply_result": apply_result,
            "progress": progress["percentage"]
        }
    
    def _analyze_current_state(self) -> Dict:
        """分析当前代码状态"""
        py_files = list(Path(self.current_sandbox).glob("*.py"))
        
        # 读取VERSION.json
        version_file = os.path.join(self.current_sandbox, "VERSION.json")
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                version_info = json.load(f)
        else:
            version_info = {"version": "unknown"}
        
        return {
            "total_files": len(py_files),
            "version": version_info.get("version"),
            "modules": [f.name for f in py_files[:10]]  # 只列出前10个
        }
    
    def _generate_improvement_plan_simple(self, goal: str, state: Dict) -> Dict:
        """生成简单的改进方案"""
        return {
            "description": f"迭代改进以达成目标: {goal}",
            "changes": []
        }
    
    def _apply_improvements_simple(self, plan: Dict) -> Dict:
        """应用简单的改进"""
        return {
            "applied": 0,
            "failed": 0
        }
    
    def _evaluate_progress_simple(self, goal: str, apply_result: Dict) -> Dict:
        """简单的进展评估"""
        return {
            "status": "in_progress",
            "percentage": 0
        }
    
    def _commit_changes(self, message: str):
        """提交改进到Git"""
        try:
            # 添加所有改动
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.current_sandbox,
                capture_output=True
            )
            
            # 提交
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.current_sandbox,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"   ✅ Git提交: {message}")
            else:
                # 可能没有改动
                if "nothing to commit" not in result.stdout:
                    print(f"   ⚠️  Git提交失败: {result.stderr}")
        except Exception as e:
            print(f"   ❌ Git提交错误: {e}")
    
    def _save_evolution_report(self, result: Dict):
        """保存进化报告"""
        report_path = os.path.join(self.current_sandbox, "EVOLUTION_REPORT.json")
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n📄 进化报告已保存: {report_path}")
    
    # 注意: 不推送到GitHub，所有改动只在本地沙盒中
    # 用户需要手动review并同步改动
    
    def generate_comparison_report(self) -> Dict:
        """生成与main分支的对比报告"""
        if not self.current_sandbox:
            raise Exception("没有活动的沙盒")
        
        print(f"\n📊 生成对比报告...")
        
        try:
            # 获取diff统计
            result = subprocess.run(
                ["git", "diff", "--stat", "main"],
                cwd=self.current_sandbox,
                capture_output=True,
                text=True
            )
            
            diff_stat = result.stdout
            
            # 获取改动的文件列表
            result = subprocess.run(
                ["git", "diff", "--name-status", "main"],
                cwd=self.current_sandbox,
                capture_output=True,
                text=True
            )
            
            changed_files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        status = parts[0]
                        filename = parts[1]
                        changed_files.append({
                            "status": status,
                            "file": filename
                        })
            
            report = {
                "sandbox": self.current_sandbox,
                "branch": self.current_branch,
                "diff_stat": diff_stat,
                "changed_files": changed_files,
                "total_changes": len(changed_files)
            }
            
            print(f"   ✅ 对比报告生成完成")
            print(f"   📝 {len(changed_files)} 个文件有改动")
            
            return report
            
        except Exception as e:
            print(f"   ❌ 生成报告失败: {e}")
            return {}
    
    def cleanup(self):
        """清理沙盒"""
        if self.current_sandbox and os.path.exists(self.current_sandbox):
            import shutil
            shutil.rmtree(self.current_sandbox)
            print(f"🗑️  已清理沙盒: {self.current_sandbox}")
            self.current_sandbox = None
            self.current_branch = None


if __name__ == "__main__":
    # 测试代码
    print("=== JARVIS 自我进化沙盒系统（GitHub版本）测试 ===\n")
    
    sandbox = EvolutionSandbox()
    
    # 测试1: 创建沙盒
    print("1. 测试创建沙盒...")
    sandbox_path = sandbox.create_sandbox("3.0")
    
    if sandbox_path:
        print(f"\n✅ 沙盒创建成功: {sandbox_path}")
        
        # 测试2: 生成对比报告
        print("\n2. 测试对比报告...")
        report = sandbox.generate_comparison_report()
        print(f"   改动文件数: {report.get('total_changes', 0)}")
        
        # 测试3: 清理
        print("\n3. 清理沙盒...")
        sandbox.cleanup()
        print("✅ 测试完成")
    else:
        print("❌ 沙盒创建失败")
