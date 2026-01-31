#!/usr/bin/env python3
"""
获取系统CPU核心数和内存总量的脚本
"""

import os
import sys


def get_system_info():
    """获取系统CPU核心数和内存总量"""
    try:
        import psutil
    except ImportError:
        print("错误: 需要安装psutil库")
        print("请运行: pip install psutil")
        return None, None
    
    try:
        # 获取CPU核心数
        cpu_cores = psutil.cpu_count(logical=True)
        
        # 获取内存总量（以GB为单位）
        memory = psutil.virtual_memory()
        memory_total_gb = round(memory.total / (1024**3), 2)
        
        return cpu_cores, memory_total_gb
    except Exception as e:
        print(f"获取系统信息时出错: {e}")
        return None, None


def main():
    """主函数"""
    cpu_cores, memory_total = get_system_info()
    
    if cpu_cores is not None and memory_total is not None:
        print(f"CPU核心数: {cpu_cores}")
        print(f"内存总量: {memory_total} GB")
        return {
            "cpu_cores": cpu_cores,
            "memory_total_gb": memory_total
        }
    else:
        print("无法获取系统信息")
        return None


if __name__ == "__main__":
    result = main()
    if result:
        print(f"\n结果字典: {result}")