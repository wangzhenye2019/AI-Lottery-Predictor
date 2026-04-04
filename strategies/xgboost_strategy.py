# -*- coding: utf-8 -*-
"""
XGBoost 策略
使用梯度提升树进行号码预测
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import xgboost as xgb
from .base_strategy import BaseStrategy
from loguru import logger


class XGBoostStrategy(BaseStrategy):
    """XGBoost 预测策略"""

    def __init__(self, name: str = "xgboost", config: Dict[str, Any] = None):
        """
        初始化 XGBoost 策略

        Args:
            config: {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'window_size': 10,  # 使用最近N期作为特征
                'top_k': 6  # 预测前K个最可能的号码
            }
        """
        default_config = {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'window_size': 10,
            'top_k': 6,
            'random_state': 42
        }
        config = {**default_config, **(config or {})}
        super().__init__(name, config)

        self.models: Dict[int, xgb.XGBClassifier] = {}  # 每个号码位置一个模型
        self.label_encoders: Dict[int, LabelEncoder] = {}
        self.feature_names: List[str] = []

    def _create_features(self, data: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        创建特征和标签

        Args:
            data: 历史数据
            target_col: 目标列名（如'红球_1'）

        Returns:
            X: 特征矩阵, y: 标签
        """
        window_size = self.config['window_size']
        red_cols = [col for col in data.columns if '红球' in col]
        blue_cols = [col for col in data.columns if '蓝球' in col]

        features_list = []
        labels = []

        for i in range(window_size, len(data)):
            # 特征：前 window_size 期的所有红球和蓝球
            window_data = data.iloc[i-window_size:i]

            feature_vector = []
            # 红球特征
            for col in red_cols:
                feature_vector.extend(window_data[col].astype(int).tolist())
            # 蓝球特征
            for col in blue_cols:
                if col in window_data.columns:
                    feature_vector.extend(window_data[col].astype(int).tolist())

            # 统计特征
            all_reds = window_data[red_cols].values.flatten().astype(int)
            feature_vector.extend([
                np.mean(all_reds),
                np.std(all_reds),
                np.min(all_reds),
                np.max(all_reds)
            ])

            features_list.append(feature_vector)
            labels.append(int(data.iloc[i][target_col]))

        return np.array(features_list), np.array(labels)

    def train(self, data: pd.DataFrame) -> None:
        """
        训练 XGBoost 模型（为每个红球位置训练一个分类器）

        Args:
            data: 历史数据 DataFrame
        """
        logger.info(f"开始训练 {self.name} 策略...")
        self.history_data = data.copy()

        red_cols = sorted([col for col in data.columns if '红球' in col])
        self.feature_names = [f"lag_{i}_{col}" for i in range(self.config['window_size']) for col in red_cols]

        for col in red_cols:
            try:
                X, y = self._create_features(data, col)

                # 标签编码（1-33）
                le = LabelEncoder()
                y_encoded = le.fit_transform(y)
                self.label_encoders[col] = le

                # 训练验证集分割
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y_encoded, test_size=0.2, random_state=self.config['random_state']
                )

                # 训练 XGBoost
                model = xgb.XGBClassifier(
                    n_estimators=self.config['n_estimators'],
                    max_depth=self.config['max_depth'],
                    learning_rate=self.config['learning_rate'],
                    random_state=self.config['random_state'],
                    use_label_encoder=False,
                    eval_metric='mlogloss'
                )

                model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    verbose=False
                )

                # 评估
                y_pred = model.predict(X_val)
                acc = accuracy_score(y_val, y_pred)
                logger.info(f"  位置 {col} 模型训练完成，验证集准确率: {acc:.4f}")

                self.models[col] = model

            except Exception as e:
                logger.error(f"  位置 {col} 模型训练失败: {e}")
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
            n_predictions: 预测期数（暂只支持1期）

        Returns:
            {'red': [6个红球], 'blue': [1个蓝球]}
        """
        if not self.is_trained:
            raise RuntimeError("模型未训练，请先调用 train()")

        # 准备特征
        window_size = self.config['window_size']
        if len(recent_data) < window_size:
            raise ValueError(f"需要至少 {window_size} 期数据作为输入")

        recent_window = recent_data.iloc[-window_size:]

        red_cols = sorted([col for col in recent_data.columns if '红球' in col])
        feature_vector = []

        for col in red_cols:
            feature_vector.extend(recent_window[col].astype(int).tolist())

        # 统计特征
        all_reds = recent_window[red_cols].values.flatten().astype(int)
        feature_vector.extend([
            np.mean(all_reds),
            np.std(all_reds),
            np.min(all_reds),
            np.max(all_reds)
        ])

        X = np.array([feature_vector])

        # 预测每个红球位置
        predicted_red = []
        for col in red_cols[:6]:  # 只预测6个红球位置
            if col not in self.models:
                continue

            model = self.models[col]
            le = self.label_encoders[col]

            # 获取预测概率
            proba = model.predict_proba(X)[0]
            top_k_indices = np.argsort(proba)[-self.config['top_k']:][::-1]
            top_k_numbers = le.inverse_transform(top_k_indices)

            # 取最可能的号码
            predicted_number = int(top_k_numbers[0])
            predicted_red.append(predicted_number)

        # 去重并排序
        predicted_red = sorted(set(predicted_red))
        while len(predicted_red) < 6:
            # 补充缺失的号码（从次优选择中选）
            for col in red_cols:
                if col not in self.models:
                    continue
                model = self.models[col]
                le = self.label_encoders[col]
                proba = model.predict_proba(X)[0]
                top_k_indices = np.argsort(proba)[-self.config['top_k']:][::-1]
                top_k_numbers = le.inverse_transform(top_k_indices)
                for num in top_k_numbers:
                    num_int = int(num)
                    if num_int not in predicted_red:
                        predicted_red.append(num_int)
                        break
                if len(predicted_red) >= 6:
                    break

        predicted_red = sorted(predicted_red[:6])

        # 蓝球预测（简单使用最近N期蓝球频率）
        blue_cols = [col for col in recent_data.columns if '蓝球' in col]
        if blue_cols:
            blue_history = recent_window[blue_cols[0]].astype(int).tolist()
            # 取最近出现频率最高的蓝球
            from collections import Counter
            blue_counter = Counter(blue_history)
            predicted_blue = [blue_counter.most_common(1)[0][0]]
        else:
            predicted_blue = [6]  # 默认值

        return {
            'red': predicted_red,
            'blue': predicted_blue
        }

    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if not self.models:
            return {}

        importance_dict = {}
        for col, model in self.models.items():
            if hasattr(model, 'feature_importances_'):
                importance_dict[col] = model.feature_importances_.mean()
        return importance_dict
