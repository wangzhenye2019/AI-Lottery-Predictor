# -*- coding:utf-8 -*-
"""
Author: BigCat
Description: 一键运行主程序入口，支持进度条展示
"""
import os
import warnings

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from utils.runtime_config import apply_runtime_env

apply_runtime_env()

import argparse
import time
import sys
from loguru import logger
from tqdm import tqdm

# 导入各模块的主函数
from get_data import run as run_get_data
from run_train_model_optimized import run as run_train_optimized
from run_predict_enhanced import run as run_predict_enhanced

# 隐藏一些过于冗长的 loguru 默认输出
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{message}</level>", level="INFO")

warnings.filterwarnings('ignore', category=UserWarning, module='tensorflow')
warnings.filterwarnings('ignore', category=FutureWarning, module='tensorflow')
warnings.filterwarnings('ignore', module='keras')

parser = argparse.ArgumentParser(description="双色球/大乐透 AI 预测系统 - 一键执行")
parser.add_argument('--name', default="ssq", type=str, choices=['ssq', 'dlt', 'qlc', 'fc3d'], help="选择玩法：ssq(双色球)/dlt(大乐透)/qlc(七乐彩)/fc3d(福彩3D)")
parser.add_argument('--train', action='store_true', help="是否重新训练模型 (默认只预测)")
parser.add_argument('--strategy', default="hybrid", type=str, choices=['model_only', 'strategy_only', 'hybrid'], help="预测策略")
parser.add_argument('--combinations', default=5, type=int, help="生成的预测组合数量")
args = parser.parse_args()


class TrainArgsMock:
    """模拟 argparse 解析后的对象，传递给训练模块"""
    def __init__(self, name):
        self.name = name
        self.train_test_split = 0.8
        self.use_early_stopping = True
        self.patience = 10
        self.use_lr_decay = True
        self.decay_rate = 0.95
        self.save_best_only = True


def main():
    game_names = {'ssq': '双色球', 'dlt': '大乐透', 'qlc': '七乐彩', 'fc3d': '福彩3D'}
    print("\n" + "="*50)
    print(f"🚀 欢迎使用 AI 智能彩票预测系统 ({game_names.get(args.name, args.name)})")
    print("="*50 + "\n")

    steps = [
        {"name": "正在获取最新开奖数据...", "func": lambda: run_get_data(args.name), "run": True},
        {"name": "正在分析数据并训练 AI 模型 (耗时较长)...", "func": lambda: run_train_optimized(TrainArgsMock(args.name)), "run": args.train},
        {"name": "正在生成预测组合...", "func": lambda: run_predict_enhanced(args.name, args.strategy, args.combinations), "run": True}
    ]

    total_steps = sum(1 for step in steps if step["run"])
    current_step = 1

    try:
        for step in steps:
            if not step["run"]:
                continue
            
            print(f"\n[{current_step}/{total_steps}] {step['name']}")
            
            # 使用 tqdm 显示一个假进度条作为加载动画提示，实际进度由底层日志输出
            # 对于训练阶段，让其原生的日志穿透显示
            if "训练" in step["name"]:
                time.sleep(1)
                step["func"]()
            else:
                # 对于数据获取和预测，由于很快，加个简单的加载动画
                with tqdm(total=100, desc="执行进度", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
                    for i in range(10):
                        time.sleep(0.1)
                        pbar.update(5)
                    
                    step["func"]()
                    
                    for i in range(10):
                        time.sleep(0.05)
                        pbar.update(5)
                        
            current_step += 1
            time.sleep(1)
            
        print("\n" + "="*50)
        print("🎉 全部流程执行完毕，祝您好运！")
        print("="*50 + "\n")

    except Exception as e:
        logger.error(f"\n❌ 执行过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    main()
