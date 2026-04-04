# -*- coding: utf-8 -*-
"""
基础策略抽象类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from loguru import logger


class BaseStrategy(ABC):
    """策略基类"""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        初始化策略

        Args:
            name: 策略名称
            config: 策略配置
        """
        self.name = name
        self.config = config or {}
        self.is_trained = False
        self.history_data: Optional[pd.DataFrame] = None

    @abstractmethod
    def train(self, data: pd.DataFrame) -> None:
        """
        训练策略模型

        Args:
            data: 历史数据
        """
        pass

    @abstractmethod
    def predict(
        self,
        recent_data: pd.DataFrame,
        n_predictions: int = 1
    ) -> Dict[str, List[int]]:
        """
        生成预测

        Args:
            recent_data: 最近N期数据
            n_predictions: 预测期数

        Returns:
            预测结果字典 {'red': [...], 'blue': [...]}
        """
        pass

    def evaluate(
        self,
        historical_data: pd.DataFrame,
        train_ratio: float = 0.8
    ) -> Dict[str, float]:
        """
        评估策略性能

        Args:
            historical_data: 完整历史数据
            train_ratio: 训练集比例

        Returns:
            评估指标字典
        """
        # 划分训练集和测试集
        split_idx = int(len(historical_data) * train_ratio)
        train_data = historical_data.iloc[:split_idx]
        test_data = historical_data.iloc[split_idx:]

        # 训练
        self.train(train_data)

        # 滚动预测
        correct_predictions = 0
        total_predictions = 0
        hit_counts = []

        window_size = self.config.get('window_size', 5)

        for i in range(window_size, len(test_data)):
            recent = test_data.iloc[i-window_size:i]
            actual_next = test_data.iloc[i]

            prediction = self.predict(recent, n_predictions=1)

            # 计算命中情况
            actual_red = self._extract_red_balls(actual_next)
            pred_red = prediction.get('red', [])

            hit = len(set(pred_red) & set(actual_red))
            hit_counts.append(hit)

            if hit >= 3:  # 至少命中3个红球算一次"正确"
                correct_predictions += 1
            total_predictions += 1

        metrics = {
            'accuracy': correct_predictions / total_predictions if total_predictions > 0 else 0,
            'avg_hit_red': np.mean(hit_counts) if hit_counts else 0,
            'max_hit_red': np.max(hit_counts) if hit_counts else 0,
            'total_tests': total_predictions
        }

        logger.info(f"策略 {self.name} 评估完成: {metrics}")
        return metrics

    def _extract_red_balls(self, row: pd.Series) -> List[int]:
        """从数据行中提取红球列表"""
        red_cols = [col for col in row.index if '红球' in col]
        return [int(row[col]) for col in sorted(red_cols)]

    def _extract_blue_ball(self, row: pd.Series) -> Optional[int]:
        """从数据行中提取蓝球"""
        if '蓝球' in row:
            return int(row['蓝球'])
        return None

    def save(self, path: str) -> None:
        """保存策略模型"""
        import pickle
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        logger.info(f"策略 {self.name} 已保存到 {path}")

    @classmethod
    def load(cls, path: str) -> 'BaseStrategy':
        """加载策略模型"""
        import pickle
        with open(path, 'rb') as f:
            strategy = pickle.load(f)
        logger.info(f"策略 {strategy.name} 已从 {path} 加载")
        return strategy
