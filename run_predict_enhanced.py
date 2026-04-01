# -*- coding:utf-8 -*-
"""
Author: BigCat
Description: 增强版预测脚本 - 结合 AI 模型和策略分析
"""
import argparse
import time
import numpy as np
import pandas as pd
import os
from loguru import logger

from config import model_args, name_path, data_file_name
from get_data import get_current_number, spider
from core.strategies import LotteryStrategy
from services.predict_service import PredictService

parser = argparse.ArgumentParser()
parser.add_argument('--name', default="ssq", type=str, help="选择训练数据：双色球/大乐透")
parser.add_argument('--strategy', default="hybrid", type=str, 
                   choices=['model_only', 'strategy_only', 'hybrid'],
                   help="预测策略：仅模型/仅策略/混合")
parser.add_argument('--n_combinations', default=5, type=int, help="生成投注组合数量")
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


def generate_hybrid_prediction(model_pred, strategy_recommendation, name):
    """
    生成混合预测（模型 + 策略）
    """
    data_path = "{}{}".format(name_path[name]["path"], data_file_name)
    if not os.path.exists(data_path):
        logger.warning("数据文件不存在，使用纯模型预测")
        return model_pred
    
    # 获取策略推荐的候选号码
    red_candidates = set(strategy_recommendation['red_candidates'][:12])
    blue_candidates = set(strategy_recommendation['blue_candidates'][:6])
    
    # 模型预测的号码
    model_red = set(model_pred['red'])
    model_blue = model_pred['blue'] if isinstance(model_pred['blue'], int) else model_pred['blue'][0]
    
    # 混合策略：保留模型预测中与策略推荐重合的号码
    final_red = []
    for red in model_pred['red']:
        if red in red_candidates:
            final_red.append(red)
    
    # 如果重合号码不足红球数，从策略推荐中补充
    target_red_count = 6 if name == "ssq" else 5
    if len(final_red) < target_red_count:
        for red in sorted(red_candidates):
            if red not in final_red:
                final_red.append(red)
            if len(final_red) >= target_red_count:
                break
    
    # 蓝球处理
    if isinstance(model_pred['blue'], int):
        final_blue = model_blue if model_blue in blue_candidates else list(blue_candidates)[0]
    else:
        final_blue = model_pred['blue'][0] if model_pred['blue'][0] in blue_candidates else list(blue_candidates)[0]
    
    return {
        'red': sorted(final_red[:target_red_count]),
        'blue': final_blue
    }


def run(name, strategy_type, n_combinations):
    """ 执行增强预测 """
    try:
        current_number = get_current_number(name)
        logger.info("【{}】最近一期:{}".format(name_path[name]["name"], current_number))
        
        data_path = "{}{}".format(name_path[name]["path"], data_file_name)
        recommendation = None
        strategy = None
        
        if os.path.exists(data_path):
            data = pd.read_csv(data_path)
            strategy = LotteryStrategy(data)
            
            logger.info("=" * 50)
            logger.info("【策略分析】")
            recommendation = strategy.recommend_balls(strategy='hybrid')
            
            if strategy_type == 'strategy_only':
                combos = strategy.generate_combinations(
                    recommendation['red_candidates'],
                    recommendation['blue_candidates'],
                    n_combinations=n_combinations
                )
                filtered_combos = strategy.smart_filter(combos)
                
                logger.info("=" * 50)
                logger.info("【策略推荐组合】")
                for i, combo in enumerate(filtered_combos[:n_combinations], 1):
                    logger.info(f"组合{i}: 红球 {combo['red']} + 蓝球 {combo['blue']}")
                return
        else:
            logger.warning("数据文件不存在，跳过策略分析")
        
        if strategy_type != 'strategy_only':
            windows_size = model_args[name]["model_args"]["windows_size"]
            data_spider = spider(name, 1, current_number, "predict")
            logger.info("=" * 50)
            logger.info("【AI 模型预测】")
            
            predict_features_ = try_error(1, name, data_spider.iloc[:windows_size], windows_size)
            
            with PredictService(name) as service:
                model_pred = service.get_final_prediction(predict_features_)
                logger.info(f"模型预测：红球 {model_pred['red']} + 蓝球 {model_pred['blue']}")
                
                if strategy_type == 'hybrid' and recommendation and strategy:
                    logger.info("=" * 50)
                    logger.info("【混合优化预测】")
                    hybrid_pred = generate_hybrid_prediction(model_pred, recommendation, name)
                    logger.info(f"混合预测：红球 {hybrid_pred['red']} + 蓝球 {hybrid_pred['blue']}")
                    
                    target_red_count = 6 if name == "ssq" else 5
                    red_pool = list(set(hybrid_pred['red'] + recommendation['red_candidates'][:target_red_count]))
                    blue_pool = list(set([hybrid_pred['blue']] + recommendation['blue_candidates'][:3])) if isinstance(hybrid_pred['blue'], int) else list(set(hybrid_pred['blue'] + recommendation['blue_candidates'][:3]))
                    
                    combos = strategy.generate_combinations(red_pool, blue_pool, n_combinations)
                    filtered = strategy.smart_filter(combos)
                    
                    logger.info("=" * 50)
                    logger.info("【最终推荐组合】")
                    for i, combo in enumerate(filtered[:n_combinations], 1):
                        logger.info(f"组合{i}: 红球 {combo['red']} + 蓝球 {combo['blue']}")
                
                elif strategy_type == 'model_only':
                    logger.info("=" * 50)
                    logger.info("【最终预测】")
                    logger.info(f"红球 {model_pred['red']} + 蓝球 {model_pred['blue']}")
                
    except Exception as e:
        logger.error(f"预测失败：{e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    if not args.name:
        raise Exception("玩法名称不能为空！")
    else:
        run(args.name, args.strategy, args.n_combinations)
