# -*- coding: utf-8 -*-
"""
集成学习策略
融合多个基础策略的预测结果
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from .base_strategy import BaseStrategy
from .xgboost_strategy import XGBoostStrategy
from .arima_strategy import ARIMAStrategy
from .apriori_strategy import AprioriStrategy
from .clustering_strategy import ClusteringStrategy
from .genetic_strategy import GeneticStrategy
from loguru import logger


class EnsembleStrategy(BaseStrategy):
    """集成学习策略"""

    def __init__(self, name: str = "ensemble", config: Dict[str, Any] = None):
        """
        初始化集成策略

        Args:
            config: {
                'voting_method': 'weighted',  # 'weighted' 或 'majority'
                'weights': {                  # 各策略权重
                    'xgboost': 0.25,
                    'arima': 0.20,
                    'apriori': 0.20,
                    'clustering': 0.20,
                    'genetic': 0.15
                },
                'window_size': 50
            }
        """
        default_config = {
            'voting_method': 'weighted',
            'weights': {
                'xgboost': 0.25,
                'arima': 0.20,
                'apriori': 0.20,
                'clustering': 0.20,
                'genetic': 0.15
            },
            'window_size': 50
        }
        config = {**default_config, **(config or {})}
        super().__init__(name, config)

        self.strategies: Dict[str, BaseStrategy] = {}
        self.strategy_scores: Dict[str, float] = {}  # 各策略历史表现分数

    def _init_strategies(self):
        """初始化所有子策略"""
        strategy_classes = {
            'xgboost': XGBoostStrategy,
            'arima': ARIMAStrategy,
            'apriori': AprioriStrategy,
            'clustering': ClusteringStrategy,
            'genetic': GeneticStrategy
        }

        for name, cls in strategy_classes.items():
            try:
                strategy = cls(name=name)
                self.strategies[name] = strategy
                logger.info(f"已加载策略: {name}")
            except Exception as e:
                logger.warning(f"策略 {name} 加载失败: {e}")

    def train(self, data: pd.DataFrame) -> None:
        """
        训练所有子策略

        Args:
            data: 历史数据
        """
        logger.info(f"开始训练 {self.name} 集成策略...")
        self.history_data = data.copy()

        # 初始化策略
        if not self.strategies:
            self._init_strategies()

        # 训练每个策略
        for name, strategy in self.strategies.items():
            try:
                logger.info(f"训练子策略: {name}")
                strategy.train(data)
                # 评估策略
                scores = strategy.evaluate(data, train_ratio=0.8)
                self.strategy_scores[name] = scores['accuracy']
                logger.info(f"  {name} 准确率: {scores['accuracy']:.4f}")
            except Exception as e:
                logger.error(f"  策略 {name} 训练失败: {e}")

        self.is_trained = True
        logger.info(f"{self.name} 训练完成")

    def predict(
        self,
        recent_data: pd.DataFrame,
        n_predictions: int = 1
    ) -> Dict[str, List[int]]:
        """
        集成预测

        Args:
            recent_data: 最近N期数据
            n_predictions: 预测期数

        Returns:
            {'red': [...], 'blue': [...]}
        """
        if not self.is_trained:
            raise RuntimeError("模型未训练，请先调用 train()")

        # 收集所有策略的预测
        predictions: Dict[str, List[int]] = {}
        confidences: Dict[str, float] = {}

        for name, strategy in self.strategies.items():
            try:
                pred = strategy.predict(recent_data, n_predictions)
                predictions[name] = pred['red']
                # 使用策略的历史准确率作为置信度
                confidences[name] = self.strategy_scores.get(name, 0.5)
                logger.debug(f"  {name}: {pred['red']} (conf: {confidences[name]:.3f})")
            except Exception as e:
                logger.warning(f"策略 {name} 预测失败: {e}")
                continue

        if not predictions:
            logger.error("所有策略预测失败，返回随机结果")
            return {
                'red': sorted(np.random.choice(range(1, 34), 6, replace=False).tolist()),
                'blue': [np.random.randint(1, 17)]
            }

        # 投票集成
        method = self.config['voting_method']

        if method == 'weighted':
            predicted_red = self._weighted_vote(predictions, confidences)
        else:
            predicted_red = self._majority_vote(predictions)

        # 蓝球集成（简单取所有策略的众数）
        predicted_blue = self._ensemble_blue(predictions)

        return {
            'red': predicted_red,
            'blue': predicted_blue
        }

    def _weighted_vote(
        self,
        predictions: Dict[str, List[int]],
        confidences: Dict[str, float]
    ) -> List[int]:
        """加权投票"""
        weights = self.config['weights']
        ball_scores: Dict[int, float] = {}

        for strategy_name, reds in predictions.items():
            weight = weights.get(strategy_name, 1.0) * confidences.get(strategy_name, 1.0)
            for ball in reds:
                ball_scores[ball] = ball_scores.get(ball, 0) + weight

        # 选择得分最高的6个号码
        sorted_balls = sorted(ball_scores.items(), key=lambda x: x[1], reverse=True)
        selected = [ball for ball, _ in sorted_balls[:6]]
        return sorted(selected)

    def _majority_vote(self, predictions: Dict[str, List[int]]) -> List[int]:
        """多数投票"""
        from collections import Counter

        all_balls = []
        for reds in predictions.values():
            all_balls.extend(reds)

        counter = Counter(all_balls)
        most_common = counter.most_common(6)
        selected = [ball for ball, _ in most_common]
        return sorted(selected)

    def _ensemble_blue(self, predictions: Dict[str, List[int]]) -> List[int]:
        """集成蓝球预测"""
        all_blues = []
        for pred in predictions.values():
            if 'blue' in pred and pred['blue']:
                all_blues.extend(pred['blue'] if isinstance(pred['blue'], list) else [pred['blue']])

        if all_blues:
            from collections import Counter
            counter = Counter(all_blues)
            return [counter.most_common(1)[0][0]]
        else:
            return [6]

    def get_strategy_weights(self) -> Dict[str, float]:
        """获取当前策略权重"""
        return self.config['weights'].copy()

    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """更新策略权重"""
        for name, weight in new_weights.items():
            if name in self.config['weights']:
                self.config['weights'][name] = weight
        logger.info(f"策略权重已更新: {self.config['weights']}")

    def get_ensemble_report(self) -> Dict[str, Any]:
        """获取集成报告"""
        report = {
            'strategies': list(self.strategies.keys()),
            'weights': self.config['weights'],
            'strategy_scores': self.strategy_scores,
            'is_trained': self.is_trained
        }
        return report
