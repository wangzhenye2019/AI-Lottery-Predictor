# -*- coding: utf-8 -*-
"""
策略管理器
统一管理所有预测策略，提供统一的接口
"""
import pandas as pd
from typing import List, Dict, Any, Optional
from loguru import logger
from .base_strategy import BaseStrategy
from .xgboost_strategy import XGBoostStrategy
from .arima_strategy import ARIMAStrategy
from .apriori_strategy import AprioriStrategy
from .clustering_strategy import ClusteringStrategy
from .genetic_strategy import GeneticStrategy
from .ensemble_strategy import EnsembleStrategy
from core.strategies import LotteryStrategy  # 原有策略


class StrategyManager:
    """策略管理器"""

    def __init__(self, lottery_type: str = "ssq"):
        """
        初始化策略管理器

        Args:
            lottery_type: 彩种类型
        """
        self.lottery_type = lottery_type
        self.strategies: Dict[str, BaseStrategy] = {}
        self.legacy_strategy: Optional[LotteryStrategy] = None
        self._register_all_strategies()

    def _register_all_strategies(self):
        """注册所有可用策略"""
        # 新策略
        new_strategies = {
            'xgboost': XGBoostStrategy,
            'arima': ARIMAStrategy,
            'apriori': AprioriStrategy,
            'clustering': ClusteringStrategy,
            'genetic': GeneticStrategy,
            'ensemble': EnsembleStrategy
        }

        for name, cls in new_strategies.items():
            try:
                strategy = cls(name=name)
                self.strategies[name] = strategy
                logger.debug(f"注册策略: {name}")
            except Exception as e:
                logger.warning(f"策略 {name} 注册失败: {e}")

        # 原有策略（兼容旧代码）
        try:
            from core.strategies import LotteryStrategy
            self.legacy_strategy = LotteryStrategy
            logger.debug("注册遗留策略: LotteryStrategy")
        except ImportError:
            logger.warning("未找到遗留策略模块")

    def get_strategy(self, name: str) -> Optional[BaseStrategy]:
        """
        获取指定策略

        Args:
            name: 策略名称

        Returns:
            策略对象
        """
        if name in self.strategies:
            return self.strategies[name]
        elif name == 'legacy' and self.legacy_strategy:
            return self.legacy_strategy
        else:
            logger.warning(f"策略 '{name}' 不存在")
            return None

    def list_strategies(self) -> List[str]:
        """列出所有可用策略"""
        return list(self.strategies.keys()) + (['legacy'] if self.legacy_strategy else [])

    def train_strategy(
        self,
        strategy_name: str,
        data: pd.DataFrame,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        训练指定策略

        Args:
            strategy_name: 策略名称
            data: 训练数据
            config: 策略配置（覆盖默认配置）

        Returns:
            是否成功
        """
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            return False

        try:
            if config:
                strategy.config.update(config)
            strategy.train(data)
            logger.info(f"策略 {strategy_name} 训练成功")
            return True
        except Exception as e:
            logger.error(f"策略 {strategy_name} 训练失败: {e}")
            return False

    def predict_with_strategy(
        self,
        strategy_name: str,
        recent_data: pd.DataFrame,
        n_predictions: int = 1
    ) -> Optional[Dict[str, List[int]]]:
        """
        使用指定策略预测

        Args:
            strategy_name: 策略名称
            recent_data: 最近N期数据
            n_predictions: 预测期数

        Returns:
            预测结果
        """
        strategy = self.get_strategy(strategy_name)
        if not strategy or not strategy.is_trained:
            logger.warning(f"策略 {strategy_name} 未训练或不存在")
            return None

        try:
            result = strategy.predict(recent_data, n_predictions)
            logger.info(f"策略 {strategy_name} 预测完成: {result}")
            return result
        except Exception as e:
            logger.error(f"策略 {strategy_name} 预测失败: {e}")
            return None

    def predict_all(
        self,
        recent_data: pd.DataFrame,
        n_predictions: int = 1
    ) -> Dict[str, Dict[str, List[int]]]:
        """
        使用所有已训练的策略进行预测

        Args:
            recent_data: 最近N期数据
            n_predictions: 预测期数

        Returns:
            {strategy_name: prediction_result}
        """
        results = {}
        for name, strategy in self.strategies.items():
            if strategy.is_trained:
                try:
                    result = strategy.predict(recent_data, n_predictions)
                    results[name] = result
                except Exception as e:
                    logger.warning(f"策略 {name} 预测失败: {e}")

        return results

    def evaluate_all(
        self,
        data: pd.DataFrame,
        train_ratio: float = 0.8
    ) -> Dict[str, Dict[str, float]]:
        """
        评估所有策略

        Args:
            data: 历史数据
            train_ratio: 训练集比例

        Returns:
            {strategy_name: metrics_dict}
        """
        results = {}
        for name, strategy in self.strategies.items():
            try:
                metrics = strategy.evaluate(data, train_ratio)
                results[name] = metrics
            except Exception as e:
                logger.error(f"策略 {name} 评估失败: {e}")

        return results

    def get_best_strategy(self, metric: str = 'accuracy') -> Optional[str]:
        """
        获取表现最好的策略

        Args:
            metric: 评估指标（accuracy, avg_hit_red等）

        Returns:
            策略名称
        """
        scores = {}
        for name, strategy in self.strategies.items():
            if hasattr(strategy, 'evaluate'):
                try:
                    # 这里需要先有评估结果，暂时返回 None
                    # 实际使用中应该缓存评估结果
                    pass
                except:
                    pass

        if not scores:
            return None

        return max(scores, key=scores.get)

    def save_all(self, directory: str) -> None:
        """保存所有策略"""
        import os
        os.makedirs(directory, exist_ok=True)

        for name, strategy in self.strategies.items():
            if strategy.is_trained:
                path = os.path.join(directory, f"{name}_strategy.pkl")
                try:
                    strategy.save(path)
                    logger.info(f"策略 {name} 已保存到 {path}")
                except Exception as e:
                    logger.error(f"保存策略 {name} 失败: {e}")

    def load_all(self, directory: str) -> None:
        """加载所有策略"""
        import os
        import pickle

        for name in self.strategies.keys():
            path = os.path.join(directory, f"{name}_strategy.pkl")
            if os.path.exists(path):
                try:
                    self.strategies[name] = BaseStrategy.load(path)
                    logger.info(f"策略 {name} 已从 {path} 加载")
                except Exception as e:
                    logger.error(f"加载策略 {name} 失败: {e}")
