# -*- coding: utf-8 -*-
"""
ARIMA 时间序列策略
分析号码出现趋势
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.tools import constrain_stationary_univariate
from .base_strategy import BaseStrategy
from loguru import logger


class ARIMAStrategy(BaseStrategy):
    """ARIMA 时间序列预测策略"""

    def __init__(self, name: str = "arima", config: Dict[str, Any] = None):
        """
        初始化 ARIMA 策略

        Args:
            config: {
                'order': (2, 1, 2),  # ARIMA(p,d,q) 参数
                'window_size': 30,    # 使用最近N期数据
                'top_n': 10           # 返回概率最高的N个号码
            }
        """
        default_config = {
            'order': (2, 1, 2),
            'window_size': 30,
            'top_n': 10,
            'forecast_steps': 1
        }
        config = {**default_config, **(config or {})}
        super().__init__(name, config)

        self.models: Dict[int, Any] = {}  # 每个号码一个时间序列模型
        self.frequencies: Dict[int, List[float]] = {}  # 历史频率序列

    def _calculate_ball_frequency_series(
        self,
        data: pd.DataFrame,
        ball_number: int
    ) -> pd.Series:
        """
        计算指定号码的历史出现频率序列

        Args:
            data: 历史数据
            ball_number: 号码（1-33）

        Returns:
            频率时间序列
        """
        red_cols = [col for col in data.columns if '红球' in col]
        frequencies = []

        for idx, row in data.iterrows():
            reds = [int(row[col]) for col in red_cols]
            freq = 1 if ball_number in reds else 0
            frequencies.append(freq)

        return pd.Series(frequencies, index=data['期数'] if '期数' in data else range(len(data)))

    def train(self, data: pd.DataFrame) -> None:
        """
        训练 ARIMA 模型

        Args:
            data: 历史数据
        """
        logger.info(f"开始训练 {self.name} 策略...")
        self.history_data = data.copy()

        window_size = self.config['window_size']
        order = self.config['order']

        # 为每个号码（1-33）训练独立的 ARIMA 模型
        for ball_num in range(1, 34):
            try:
                freq_series = self._calculate_ball_frequency_series(data, ball_num)

                # 只使用最近 window_size 期数据
                if len(freq_series) > window_size:
                    freq_series = freq_series.iloc[-window_size:]

                # 检查序列是否平稳
                if freq_series.nunique() <= 1:
                    continue

                # 拟合 ARIMA 模型
                model = ARIMA(freq_series, order=order)
                fitted = model.fit()

                self.models[ball_num] = fitted
                self.frequencies[ball_num] = freq_series.tolist()

            except Exception as e:
                logger.debug(f"号码 {ball_num} ARIMA 训练失败: {e}")
                continue

        self.is_trained = True
        logger.info(f"{self.name} 策略训练完成，共训练 {len(self.models)} 个模型")

    def predict(
        self,
        recent_data: pd.DataFrame,
        n_predictions: int = 1
    ) -> Dict[str, List[int]]:
        """
        预测下一期号码

        Args:
            recent_data: 最近N期数据
            n_predictions: 预测期数

        Returns:
            {'red': [...], 'blue': [...]}
        """
        if not self.is_trained:
            raise RuntimeError("模型未训练，请先调用 train()")

        # 预测每个号码的出现概率
        probabilities = {}

        for ball_num in range(1, 34):
            if ball_num not in self.models:
                continue

            try:
                model = self.models[ball_num]
                forecast = model.forecast(steps=self.config['forecast_steps'])
                # 概率值限制在 [0, 1]
                prob = float(forecast.iloc[0])
                prob = max(0, min(1, prob))
                probabilities[ball_num] = prob
            except Exception as e:
                logger.debug(f"号码 {ball_num} 预测失败: {e}")
                continue

        # 选择概率最高的6个号码
        sorted_balls = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        predicted_red = [ball for ball, _ in sorted_balls[:6]]

        # 如果不足6个，补充高频号码
        if len(predicted_red) < 6:
            red_cols = [col for col in recent_data.columns if '红球' in col]
            all_reds = recent_data[red_cols].values.flatten().astype(int)
            from collections import Counter
            freq_counter = Counter(all_reds)
            for ball, _ in freq_counter.most_common(10):
                if ball not in predicted_red:
                    predicted_red.append(ball)
                if len(predicted_red) >= 6:
                    break

        predicted_red = sorted(predicted_red[:6])

        # 蓝球：使用最近N期蓝球的 ARIMA 预测
        predicted_blue = self._predict_blue(recent_data)

        return {
            'red': predicted_red,
            'blue': predicted_blue
        }

    def _predict_blue(self, recent_data: pd.DataFrame) -> List[int]:
        """预测蓝球"""
        blue_cols = [col for col in recent_data.columns if '蓝球' in col]
        if not blue_cols:
            return [6]

        blue_series = recent_data[blue_cols[0]].astype(int)

        # 简单策略：取最近出现频率最高的蓝球
        from collections import Counter
        counter = Counter(blue_series)
        most_common = counter.most_common(3)
        if most_common:
            return [most_common[0][0]]
        else:
            return [int(blue_series.mode()[0]) if len(blue_series.mode()) > 0 else 6]

    def get_forecast_confidence(self) -> Dict[str, float]:
        """获取预测置信度"""
        if not self.models:
            return {}

        confidences = {}
        for ball_num, model in self.models.items():
            if hasattr(model, 'fittedvalues'):
                # 使用残差的标准差作为置信度指标
                residuals = model.resid
                confidences[ball_num] = 1.0 / (1.0 + residuals.std())
        return confidences
