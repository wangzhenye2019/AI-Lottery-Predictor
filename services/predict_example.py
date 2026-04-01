# -*- coding:utf-8 -*-
"""
简化版预测脚本（使用新的服务层）
演示如何使用 PredictService
"""
import argparse
import numpy as np
from config import model_args, ball_name, name_path
from get_data import get_current_number, spider
from services.predict_service import PredictService
from utils.logger import log


parser = argparse.ArgumentParser()
parser.add_argument('--name', default="ssq", type=str, help="选择训练数据：双色球/大乐透")
args = parser.parse_args()


def try_error(predict_features, windows_size):
    """处理异常情况"""
    if len(predict_features) != windows_size:
        log.warning("期号出现跳期，期号不连续！开始查找最近上一期期号！")
        # 这里可以添加更复杂的错误处理逻辑
    return predict_features


def run(name):
    """执行预测"""
    try:
        # 使用上下文管理器自动管理资源
        with PredictService(name) as service:
            windows_size = model_args[name]["model_args"]["windows_size"]
            current_number = get_current_number(name)
            
            log.info(f"【{name_path[name]['name']}】预测期号：{int(current_number) + 1}")
            
            # 获取预测特征
            data = spider(name, 1, current_number, "predict")
            predict_features = try_error(data.iloc[:windows_size], windows_size)
            
            # 执行预测
            result = service.get_final_prediction(predict_features)
            
            # 输出结果
            log.info("=" * 50)
            log.info("【预测结果】")
            if isinstance(result['blue'], list):
                blue_str = ", ".join(map(str, result['blue']))
            else:
                blue_str = str(result['blue'])
            
            red_str = ", ".join(map(str, result['red']))
            log.info(f"红球：{red_str}")
            log.info(f"蓝球：{blue_str}")
            log.info("=" * 50)
            
    except Exception as e:
        log.error(f"预测失败：{e}")
        raise


if __name__ == '__main__':
    if not args.name:
        raise Exception("玩法名称不能为空！")
    else:
        run(args.name)
