# -*- coding:utf-8 -*-
"""
Author: BigCat
"""
import argparse
import time
import numpy as np
from loguru import logger

from config import model_args, name_path
from get_data import get_current_number, spider
from services.predict_service import PredictService


parser = argparse.ArgumentParser()
parser.add_argument('--name', default="ssq", type=str, help="选择训练数据: 双色球/大乐透")
args = parser.parse_args()


def try_error(mode, name, predict_features, windows_size):
    """ 处理异常 """
    if mode:
        return predict_features
    else:
        if len(predict_features) != windows_size:
            logger.warning("期号出现跳期，期号不连续！开始查找最近上一期期号！本期预测时间较久！")
            last_current_year = (int(time.strftime("%y")) - 1) * 1000
            max_times = 160
            while len(predict_features) != windows_size:
                from config import ball_name
                predict_features = spider(name, last_current_year + max_times, get_current_number(name), "predict")[[x[0] for x in ball_name]]
                time.sleep(np.random.random(1).tolist()[0])
                max_times -= 1
            return predict_features
        return predict_features


def run(name):
    """ 执行预测 """
    try:
        windows_size = model_args[name]["model_args"]["windows_size"]
        from get_data import spider_cwl, spider
        if name in ["ssq", "qlc"]:
            data = spider_cwl(name, windows_size)
            if not data.empty:
                current_number = data.iloc[0]["期数"]
            else:
                current_number = "未知"
        else:
            current_number = get_current_number(name)
            data = spider(name, 1, current_number, "predict")
            
        logger.info("【{}】最近一期:{}".format(name_path[name]["name"], current_number))
        
        logger.info("【{}】预测期号：{}".format(name_path[name]["name"], int(current_number) + 1 if current_number != "未知" else "未知"))
        
        predict_features_ = try_error(1, name, data.iloc[:windows_size], windows_size)
        
        with PredictService(name) as service:
            result = service.get_final_prediction(predict_features_)
            logger.info("预测结果：{}".format(result))
            
    except Exception as e:
        logger.error("预测失败，请检查模型是否训练，错误：{}".format(e))


if __name__ == '__main__':
    if not args.name:
        raise Exception("玩法名称不能为空！")
    else:
        run(args.name)
