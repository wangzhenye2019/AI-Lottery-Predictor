# -*- coding:utf-8 -*-
"""
优化版训练脚本（使用 TrainService）
支持早停、学习率衰减等优化特性
"""
import argparse
from services.train_service import TrainService
from utils.logger import log, setup_logger

parser = argparse.ArgumentParser()
parser.add_argument('--name', default="ssq", type=str, help="选择训练数据：双色球/大乐透")
parser.add_argument('--train_test_split', default=0.8, type=float, help="训练集占比")
parser.add_argument('--use_early_stopping', action='store_true', help="是否使用早停")
parser.add_argument('--patience', default=10, type=int, help="早停耐心值")
parser.add_argument('--use_lr_decay', action='store_true', help="是否使用学习率衰减")
parser.add_argument('--decay_rate', default=0.95, type=float, help="学习率衰减率")
parser.add_argument('--save_best_only', action='store_true', help="仅保存最佳模型")
args = parser.parse_args()


def run():
    """执行训练"""
    # 配置日志
    setup_logger(level="INFO")
    
    log.info("=" * 50)
    log.info("开始训练双色球/大乐透模型")
    log.info("=" * 50)
    
    # 创建训练服务
    service = TrainService(
        name=args.name,
        train_test_split=args.train_test_split
    )
    
    # 执行训练
    use_optimization = args.use_early_stopping or args.use_lr_decay
    
    service.train(
        use_optimization=use_optimization,
        patience=args.patience,
        use_lr_decay=args.use_lr_decay,
        decay_rate=args.decay_rate,
        save_best_only=args.save_best_only
    )
    
    log.info("=" * 50)
    log.info("训练完成！")
    log.info("=" * 50)


if __name__ == '__main__':
    if not args.name:
        raise Exception("玩法名称不能为空！")
    else:
        run()
