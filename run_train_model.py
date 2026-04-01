# -*- coding:utf-8 -*-
"""
Author: BigCat
"""
import argparse
from loguru import logger
from services.train_service import TrainService

parser = argparse.ArgumentParser()
parser.add_argument('--name', default="ssq", type=str, help="选择训练数据: 双色球/大乐透")
parser.add_argument('--train_test_split', default=0.7, type=float, help="训练集占比, 设置大于0.5")
args = parser.parse_args()


def run(name, train_test_split):
    """ 执行训练 """
    try:
        service = TrainService(name=name, train_test_split=train_test_split)
        service.train(
            use_optimization=False,
            save_best_only=False
        )
    except Exception as e:
        logger.error(f"训练失败：{e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    if not args.name:
        raise Exception("玩法名称不能为空！")
    else:
        run(args.name, args.train_test_split)
