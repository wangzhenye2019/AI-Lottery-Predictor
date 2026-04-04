#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
发布脚本 - 创建GitHub Release并上传exe文件
Author: BigCat
"""
import os
import sys
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime


def get_version():
    """获取版本号"""
    # 从git tag获取版本
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # 没有tag，使用默认版本
        return "v2.0.0"


def get_git_log():
    """获取最近的提交日志"""
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=format:- %s", "-10"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "无提交记录"


def check_gh_cli():
    """检查是否安装了GitHub CLI"""
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def create_release_notes(version):
    """创建发布说明"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    git_log = get_git_log()

    notes = f"""## 🎉 {version} 发布

**发布日期**: {date_str}

### ✨ 新增功能
- 优化版UI界面，提升用户体验
- 统一启动脚本 `start.py`
- 应用状态管理器，实时显示进度
- 环境自动检查，启动前诊断
- 错误分类处理，友好提示

### 🔧 改进
- 简化代码结构（从4654行减少到约500行）
- 统一配置管理，支持环境变量
- 优化错误处理机制
- 完善日志系统

### 📦 构建信息
- 单文件可执行程序
- 支持 Windows 10/11
- 包含所有依赖，无需Python环境

### 📋 最近提交
{git_log}

### 🚀 使用方法
1. 下载 `AI彩票预测系统.exe`
2. 双击运行，无需安装
3. 首次运行会自动检查环境

### ⚠️ 注意事项
- 需要联网获取最新数据
- 首次使用建议先运行环境检查
- 模型文件需要单独下载或训练

---
**完整文档**: [README_OPTIMIZATION.md](README_OPTIMIZATION.md)
"""
    return notes


def create_release(version, exe_path):
    """创建GitHub Release"""
    if not check_gh_cli():
        print("❌ 未安装 GitHub CLI (gh)")
        print("请先安装: https://cli.github.com/")
        return False

    print(f"🚀 创建 Release {version}...")

    # 创建发布说明文件
    notes = create_release_notes(version)
    notes_path = Path("RELEASE_NOTES.md")
    notes_path.write_text(notes, encoding='utf-8')

    # 创建release
    cmd = [
        "gh", "release", "create", version,
        "--title", f"AI彩票预测系统 {version}",
        "--notes-file", str(notes_path),
        "--latest"
    ]

    # 如果exe文件存在，添加附件
    if exe_path and Path(exe_path).exists():
        cmd.append(exe_path)

    print(f"执行: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    # 清理临时文件
    if notes_path.exists():
        notes_path.unlink()

    return result.returncode == 0


def upload_asset(version, file_path):
    """上传资源文件到Release"""
    if not Path(file_path).exists():
        print(f"❌ 文件不存在: {file_path}")
        return False

    print(f"📤 上传 {file_path}...")

    cmd = [
        "gh", "release", "upload", version, file_path,
        "--clobber"
    ]

    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='发布到GitHub Release')
    parser.add_argument('--version', '-v', help='版本号 (默认从git tag获取)')
    parser.add_argument('--file', '-f', help='要上传的exe文件路径')
    parser.add_argument('--notes-only', '-n', action='store_true', help='仅显示发布说明')

    args = parser.parse_args()

    # 获取版本号
    version = args.version or get_version()
    if not version.startswith('v'):
        version = f'v{version}'

    print(f"📦 版本: {version}")

    # 仅显示发布说明
    if args.notes_only:
        notes = create_release_notes(version)
        print("\n" + "=" * 60)
        print(notes)
        print("=" * 60)
        return

    # 检查exe文件
    exe_path = args.file or "dist/AI彩票预测系统.exe"
    if not Path(exe_path).exists():
        print(f"❌ 找不到exe文件: {exe_path}")
        print("请先运行: python build_exe.py")
        sys.exit(1)

    # 创建release
    if create_release(version, exe_path):
        print(f"\n✅ Release {version} 创建成功!")
        print(f"🔗 访问: https://github.com/{get_repo_name()}/releases/tag/{version}")
    else:
        print(f"\n❌ Release 创建失败")
        sys.exit(1)


def get_repo_name():
    """获取仓库名"""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True
        )
        url = result.stdout.strip()
        # 提取 owner/repo
        match = re.search(r'github\.com[/:]([^/]+/[^/]+)\.git', url)
        if match:
            return match.group(1)
    except:
        pass
    return "wangzhenye2019/AI-Lottery-Predictor"


if __name__ == "__main__":
    main()
