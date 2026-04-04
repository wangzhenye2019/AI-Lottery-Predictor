#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一的启动脚本 - AI智能彩票预测系统
提供简化的启动流程和更好的错误处理
Author: BigCat
"""
import sys
import os
import argparse
from pathlib import Path


def setup_environment():
    """设置运行环境"""
    # 设置项目根目录
    project_root = Path(__file__).parent.absolute()
    os.chdir(project_root)

    # 添加项目路径
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # 设置环境变量
    os.environ.setdefault('LOTTERY_LOG_LEVEL', 'INFO')
    os.environ.setdefault('LOTTERY_DATA_DIR', 'data')


def check_environment():
    """检查运行环境"""
    from app_initializer import initialize_app
    return initialize_app()


def run_optimized_ui():
    """运行优化版UI"""
    print("🚀 启动优化版界面...")
    from main_window import MainWindow
    app = MainWindow()
    app.run()


def run_original_ui():
    """运行原始UI"""
    print("🚀 启动原始界面...")
    from commercial_main import main
    main()


def run_training(lottery_type: str = None):
    """运行训练"""
    print("🚀 启动训练模式...")
    from services.train_service import TrainingPipeline

    pipeline = TrainingPipeline()

    if lottery_type:
        print(f"训练 {lottery_type} 模型...")
        # TODO: 调用具体训练逻辑
    else:
        print("请指定彩票类型: python start.py train --type ssq")


def run_data_sync():
    """运行数据同步"""
    print("🚀 启动数据同步...")
    from services.data_sync_service import DataSyncService

    service = DataSyncService()
    # TODO: 调用同步逻辑


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AI智能彩票预测系统 - 启动脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python start.py              # 启动优化版界面（默认）
  python start.py --original   # 启动原始界面
  python start.py --check      # 仅运行环境检查
  python start.py train        # 启动训练模式
  python start.py sync         # 启动数据同步
        """
    )

    parser.add_argument(
        '--original', '-o',
        action='store_true',
        help='使用原始界面而非优化版'
    )

    parser.add_argument(
        '--check', '-c',
        action='store_true',
        help='仅运行环境检查'
    )

    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='启用调试模式'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 训练命令
    train_parser = subparsers.add_parser('train', help='训练模型')
    train_parser.add_argument(
        '--type', '-t',
        choices=['ssq', 'dlt', 'qlc', 'fc3d', 'kl8', 'pl3', 'pl5', 'qxc'],
        help='指定训练的彩票类型'
    )
    train_parser.add_argument(
        '--epochs', '-e',
        type=int,
        default=50,
        help='训练轮数（默认：50）'
    )

    # 同步命令
    sync_parser = subparsers.add_parser('sync', help='同步彩票数据')

    args = parser.parse_args()

    # 设置环境
    setup_environment()

    # 调试模式
    if args.debug:
        os.environ['LOTTERY_DEBUG'] = 'true'
        os.environ['LOTTERY_LOG_LEVEL'] = 'DEBUG'

    # 检查环境
    if args.check:
        success = check_environment()
        sys.exit(0 if success else 1)

    # 环境检查
    if not check_environment():
        print("\n⚠️ 环境检查未通过，请修复上述问题后重试")
        print("或者使用 --check 查看详细报告")
        sys.exit(1)

    try:
        # 执行命令
        if args.command == 'train':
            run_training(args.type)
        elif args.command == 'sync':
            run_data_sync()
        elif args.original:
            run_original_ui()
        else:
            run_optimized_ui()

    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
