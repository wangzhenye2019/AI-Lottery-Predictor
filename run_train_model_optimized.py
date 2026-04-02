# -*- coding:utf-8 -*-
"""
Author: BigCat
Description: 优化版训练脚本 - 包含早停机制、学习率衰减和模型检查点
"""
import argparse
from loguru import logger
from services.train_service import TrainService

def run(args):
    """ 执行优化训练 """
    try:
        service = TrainService(name=args.name, train_test_split=args.train_test_split)
        service.train(
            use_optimization=True,
            patience=args.patience if args.use_early_stopping else 9999,
            use_lr_decay=args.use_lr_decay,
            decay_rate=args.decay_rate,
            save_best_only=args.save_best_only
        )
    except Exception as e:
        logger.error(f"优化训练失败：{e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default="ssq", type=str, help="选择训练数据: 双色球/大乐透")
    parser.add_argument('--train_test_split', default=0.8, type=float, help="训练集占比, 建议 0.8")
    parser.add_argument('--use_early_stopping', action='store_true', default=True, help="是否使用早停机制")
    parser.add_argument('--patience', default=10, type=int, help="早停机制的耐心值")
    parser.add_argument('--use_lr_decay', action='store_true', default=True, help="是否使用学习率衰减")
    parser.add_argument('--decay_rate', default=0.95, type=float, help="学习率衰减率")
    parser.add_argument('--save_best_only', action='store_true', default=True, help="是否仅保存最佳模型")
    args = parser.parse_args()

    if not args.name:
        raise Exception("玩法名称不能为空！")
    else:
        run(args)
