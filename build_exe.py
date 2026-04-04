#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包脚本 - 将应用打包为可执行文件
Author: BigCat
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__', '.pytest_cache']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 清理 {dir_name}/")
            shutil.rmtree(dir_name)
    print("✅ 清理完成")


def create_icon():
    """创建简单的图标文件（如果不存在）"""
    icon_path = Path("assets/icon.ico")
    if icon_path.exists():
        return str(icon_path)

    # 创建assets目录
    icon_path.parent.mkdir(parents=True, exist_ok=True)

    # 尝试生成一个简单的图标
    try:
        from PIL import Image, ImageDraw

        # 创建64x64的图标
        img = Image.new('RGBA', (64, 64), color=(24, 144, 255, 255))
        draw = ImageDraw.Draw(img)

        # 绘制简单的彩票球图案
        draw.ellipse([8, 8, 56, 56], fill=(245, 34, 45, 255), outline=(255, 255, 255, 255), width=2)

        # 保存为ico
        img.save(icon_path, format='ICO', sizes=[(64, 64), (32, 32), (16, 16)])
        print(f"✅ 图标已创建: {icon_path}")
        return str(icon_path)
    except ImportError:
        print("⚠️ PIL未安装，跳过图标创建")
        return None


def build_exe():
    """构建exe文件"""
    print("=" * 60)
    print("🚀 开始打包 AI智能彩票预测系统")
    print("=" * 60)

    # 清理旧构建
    clean_build_dirs()

    # 创建图标
    icon_path = create_icon()

    # PyInstaller参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=AI彩票预测系统",
        "--windowed",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--log-level=WARN",
        # 隐藏导入
        "--hidden-import=customtkinter",
        "--hidden-import=loguru",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=requests",
        "--hidden-import=bs4",
        "--hidden-import=lxml",
        "--hidden-import=PIL",
        "--hidden-import=sqlalchemy",
        "--hidden-import=tensorflow",
        "--hidden-import=sklearn",
        "--hidden-import=xgboost",
        "--hidden-import=statsmodels",
        "--hidden-import=scipy",
        "--hidden-import=matplotlib",
        "--hidden-import=seaborn",
        # 数据文件
        "--add-data=config;config",
        "--add-data=data;data",
        "--add-data=ui;ui",
        "--add-data=utils;utils",
        "--add-data=services;services",
        "--add-data=strategies;strategies",
        "--add-data=crawlers;crawlers",
        "--add-data=database;database",
    ]

    # 添加图标
    if icon_path:
        cmd.append(f"--icon={icon_path}")

    # 主入口文件
    cmd.append("start.py")

    print("\n📦 执行打包命令...")
    print(" ".join(cmd))
    print()

    # 执行打包
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("\n❌ 打包失败!")
        return False

    print("\n✅ 打包成功!")

    # 显示输出文件
    exe_path = Path("dist/AI彩票预测系统.exe")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n📁 输出文件: {exe_path}")
        print(f"📊 文件大小: {size_mb:.2f} MB")
        print(f"🕐 构建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return True


def create_portable_version():
    """创建便携版（文件夹形式）"""
    print("\n" + "=" * 60)
    print("📦 创建便携版...")
    print("=" * 60)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=AI彩票预测系统-便携版",
        "--windowed",
        "--onedir",  # 文件夹形式
        "--clean",
        "--noconfirm",
        "--log-level=WARN",
        "--hidden-import=customtkinter",
        "--hidden-import=loguru",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--add-data=config;config",
        "--add-data=data;data",
        "start.py"
    ]

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n✅ 便携版创建成功!")
        print("📁 输出目录: dist/AI彩票预测系统-便携版/")
        return True
    else:
        print("\n❌ 便携版创建失败!")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='打包AI彩票预测系统')
    parser.add_argument('--portable', '-p', action='store_true', help='同时创建便携版')
    parser.add_argument('--clean', '-c', action='store_true', help='仅清理构建目录')

    args = parser.parse_args()

    if args.clean:
        clean_build_dirs()
        return

    # 构建单文件版
    if not build_exe():
        sys.exit(1)

    # 构建便携版
    if args.portable:
        if not create_portable_version():
            sys.exit(1)

    print("\n" + "=" * 60)
    print("🎉 所有构建任务完成!")
    print("=" * 60)
    print("\n使用说明:")
    print("  单文件版: dist/AI彩票预测系统.exe")
    print("  直接运行，无需安装")
    print()


if __name__ == "__main__":
    main()
