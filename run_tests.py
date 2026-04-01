#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
运行所有测试
"""
import subprocess
import sys
import os


def run_tests():
    """运行测试"""
    # 切换到项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # 运行 pytest（不重复添加覆盖率参数，使用 pyproject.toml 中的配置）
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误追踪
    ]
    
    print("=" * 60)
    print("开始运行测试...")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("[OK] 所有测试通过！")
        print("[INFO] 查看覆盖率报告：打开 ./htmlcov/index.html")
    else:
        print("[FAIL] 有测试失败，请检查输出")
    print("=" * 60)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
