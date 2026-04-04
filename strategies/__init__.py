# -*- coding: utf-8 -*-
"""
高级策略模块
包含多种新的预测策略
"""
from .base_strategy import BaseStrategy
from .xgboost_strategy import XGBoostStrategy
from .arima_strategy import ARIMAStrategy
from .apriori_strategy import AprioriStrategy
from .clustering_strategy import ClusteringStrategy
from .genetic_strategy import GeneticStrategy
from .ensemble_strategy import EnsembleStrategy
from .strategy_manager import StrategyManager

__all__ = [
    'BaseStrategy',
    'XGBoostStrategy',
    'ARIMAStrategy',
    'AprioriStrategy',
    'ClusteringStrategy',
    'GeneticStrategy',
    'EnsembleStrategy',
    'StrategyManager'
]
