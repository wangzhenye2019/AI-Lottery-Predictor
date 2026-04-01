import os
import sys
import platform
import shutil
import zipfile
import tarfile
import hashlib
import subprocess
from datetime import datetime

# 配置项目路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
RELEASE_DIR = os.path.join(PROJECT_ROOT, "releases")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")

APP_NAME = "lottery-predictor"
VERSION = "v1.0.0"


def clean_up():
    """清理之前的构建残留"""
    for d in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(d):
            print(f"[*] 清理目录: {d}")
            shutil.rmtree(d)


def build_executable():
    """使用 PyInstaller 打包主程序"""
    print("[*] 开始打包可执行文件...")
    
    # 动态检测系统类型来决定分隔符 (Windows 为 ; Linux/Mac 为 :)
    sep = ';' if platform.system() == 'Windows' else ':'
    
    # 构建 CLI 版本
    cmd_cli = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"{APP_NAME}-cli",
        "--onefile",
        "--clean",
        "--hidden-import", "tqdm",
        "--hidden-import", "loguru",
        "--hidden-import", "pandas",
        "--hidden-import", "numpy",
        "--hidden-import", "requests",
        "--hidden-import", "bs4",
        "main.py"
    ]
    print(f"[*] 执行命令 (CLI): {' '.join(cmd_cli)}")
    subprocess.check_call(cmd_cli, cwd=PROJECT_ROOT)
    
    # 如果是在 Windows 下，额外构建带 GUI 的窗口版本
    if platform.system().lower() == "windows":
        print("[*] 开始打包 Windows GUI 图形界面版本...")
        cmd_gui = [
            sys.executable, "-m", "PyInstaller",
            "--name", f"{APP_NAME}-gui",
            "--onefile",
            "--windowed", # 隐藏控制台黑框
            "--clean",
            "--hidden-import", "tqdm",
            "--hidden-import", "loguru",
            "--hidden-import", "pandas",
            "--hidden-import", "numpy",
            "--hidden-import", "requests",
            "--hidden-import", "bs4",
            "gui_main.py"
        ]
        print(f"[*] 执行命令 (GUI): {' '.join(cmd_gui)}")
        subprocess.check_call(cmd_gui, cwd=PROJECT_ROOT)
        
    print("[+] 所有打包任务完成！")


def create_release_package():
    """将打包好的可执行文件和其他必要资源压缩为 zip/tar.gz"""
    os.makedirs(RELEASE_DIR, exist_ok=True)
    sys_name = platform.system().lower()
    arch = platform.machine().lower()
    date_str = datetime.now().strftime("%Y%m%d")
    
    package_name = f"{APP_NAME}-{VERSION}-{sys_name}-{arch}-{date_str}"
    
    # 确定打包后的可执行文件路径
    exe_cli_name = f"{APP_NAME}-cli.exe" if sys_name == "windows" else f"{APP_NAME}-cli"
    exe_cli_path = os.path.join(DIST_DIR, exe_cli_name)
    
    if not os.path.exists(exe_cli_path):
        raise FileNotFoundError(f"找不到编译后的文件: {exe_cli_path}")
    
    # 创建临时组装目录
    temp_dir = os.path.join(RELEASE_DIR, package_name)
    os.makedirs(temp_dir, exist_ok=True)
    
    # 复制可执行文件
    shutil.copy2(exe_cli_path, temp_dir)
    
    # 如果是 Windows，尝试复制 GUI 版本
    if sys_name == "windows":
        exe_gui_name = f"{APP_NAME}-gui.exe"
        exe_gui_path = os.path.join(DIST_DIR, exe_gui_name)
        if os.path.exists(exe_gui_path):
            shutil.copy2(exe_gui_path, temp_dir)
    
    # 复制其他必要文件 (配置、说明等)
    extras = ["DEPLOYMENT.md", "README.md", "docker-compose.yml", "run.sh"]
    for extra in extras:
        extra_path = os.path.join(PROJECT_ROOT, extra)
        if os.path.exists(extra_path):
            shutil.copy2(extra_path, temp_dir)
            
    # 根据系统打包成不同格式
    print(f"[*] 正在生成发布压缩包: {package_name}...")
    if sys_name == "windows":
        archive_path = os.path.join(RELEASE_DIR, f"{package_name}.zip")
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
    else:
        archive_path = os.path.join(RELEASE_DIR, f"{package_name}.tar.gz")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(temp_dir, arcname=package_name)
            
    # 清理临时目录
    shutil.rmtree(temp_dir)
    print(f"[+] 发布包已生成: {archive_path}")
    
    return archive_path


def generate_checksum(file_path):
    """计算文件的 SHA256 校验和并写入同名 .sha256 文件"""
    print(f"[*] 正在计算校验和 (SHA256): {os.path.basename(file_path)}...")
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # 按块读取以节省内存
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
            
    checksum = sha256_hash.hexdigest()
    checksum_file = f"{file_path}.sha256"
    
    with open(checksum_file, "w", encoding="utf-8") as f:
        f.write(f"{checksum} *{os.path.basename(file_path)}\n")
        
    print(f"[+] 校验和已保存: {checksum_file}")
    print(f"    SHA256: {checksum}")


def main():
    print("=====================================")
    print(f"   构建 {APP_NAME} Release 包   ")
    print("=====================================")
    
    clean_up()
    
    try:
        build_executable()
        archive_path = create_release_package()
        generate_checksum(archive_path)
        print("\n🎉 全部构建任务完成！可以在 releases 目录查看产物。")
    except Exception as e:
        print(f"\n❌ 构建失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
