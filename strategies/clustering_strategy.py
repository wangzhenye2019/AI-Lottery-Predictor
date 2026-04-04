# -*- coding: utf-8 -*-
"""
聚类策略
使用 K-Means 对历史开奖模式进行聚类，识别相似模式
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from .base_strategy import BaseStrategy
from loguru import logger


class ClusteringStrategy(BaseStrategy):
    """K-Means 聚类预测策略"""

    def __init__(self, name: str = "clustering", config: Dict[str, Any] = None):
        """
        初始化聚类策略

        Args:
            config: {
                'n_clusters': 10,         # 聚类数量
                'window_size': 20,        # 使用最近N期作为特征
                'pca_components': 5,      # PCA降维维度
                'top_k_similar': 5,       # 取最相似的K个邻居
                'random_state': 42
            }
        """
        default_config = {
            'n_clusters': 10,
            'window_size': 20,
            'pca_components': 5,
            'top_k_similar': 5,
            'random_state': 42
        }
        config = {**default_config, **(config or {})}
        super().__init__(name, config)

        self.kmeans: Optional[KMeans] = None
        self.scaler: Optional[StandardScaler] = None
        self.pca: Optional[PCA] = None
        self.cluster_patterns: Dict[int, List[List[int]]] = {}  # 每个聚类的典型模式
        self.historical_features: Optional[np.ndarray] = None
        self.historical_labels: Optional[np.ndarray] = None

    def _extract_features_from_window(self, window_data: pd.DataFrame) -> np.ndarray:
        """
        从时间窗口提取特征向量

        Args:
            window_data: 窗口期数据

        Returns:
            特征向量
        """
        red_cols = sorted([col for col in window_data.columns if '红球' in col])
        blue_cols = [col for col in window_data.columns if '蓝球' in col]

        features = []

        # 1. 每期红球 one-hot 编码（33维）
        for _, row in window_data.iterrows():
            reds = [int(row[col]) for col in red_cols]
            one_hot = np.zeros(33, dtype=int)
            one_hot[np.array(reds) - 1] = 1
            features.extend(one_hot)

        # 2. 统计特征
        all_reds = window_data[red_cols].values.flatten().astype(int)
        features.extend([
            np.mean(all_reds),
            np.std(all_reds),
            np.min(all_reds),
            np.max(all_reds),
            np.median(all_reds)
        ])

        # 3. 和值特征
        sums = window_data[red_cols].astype(int).sum(axis=1)
        features.extend([
            np.mean(sums),
            np.std(sums)
        ])

        # 4. 蓝球特征（如果有）
        if blue_cols:
            blues = window_data[blue_cols[0]].astype(int).tolist()
            features.extend([
                np.mean(blues),
                np.std(blues)
            ])
            # 蓝球 one-hot（16维）
            blue_one_hot = np.zeros(16, dtype=int)
            for b in blues:
                if 1 <= b <= 16:
                    blue_one_hot[b-1] = 1
            features.extend(blue_one_hot)

        return np.array(features, dtype=float)

    def train(self, data: pd.DataFrame) -> None:
        """
        训练聚类模型

        Args:
            data: 历史数据
        """
        logger.info(f"开始训练 {self.name} 策略...")
        self.history_data = data.copy()

        window_size = self.config['window_size']
        n_clusters = self.config['n_clusters']

        # 构建特征矩阵
        features_list = []
        valid_indices = []

        for i in range(window_size, len(data)):
            window = data.iloc[i-window_size:i]
            feature_vector = self._extract_features_from_window(window)
            features_list.append(feature_vector)
            valid_indices.append(i)

        if len(features_list) < n_clusters:
            logger.warning(f"数据不足，无法训练 {n_clusters} 个聚类")
            return

        X = np.array(features_list)

        # 标准化
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # PCA 降维
        if self.config['pca_components'] < X_scaled.shape[1]:
            self.pca = PCA(n_components=self.config['pca_components'])
            X_reduced = self.pca.fit_transform(X_scaled)
        else:
            X_reduced = X_scaled

        # K-Means 聚类
        self.kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=self.config['random_state'],
            n_init=10
        )
        labels = self.kmeans.fit_predict(X_reduced)

        self.historical_features = X_reduced
        self.historical_labels = labels

        # 分析每个聚类的典型模式（最近一期开奖号码）
        for cluster_id in range(n_clusters):
            cluster_indices = [valid_indices[i] for i, l in enumerate(labels) if l == cluster_id]
            if cluster_indices:
                # 取该聚类中最近的一期作为代表
                latest_idx = max(cluster_indices)
                latest_reds = self._extract_red_balls(data.iloc[latest_idx])
                self.cluster_patterns[cluster_id] = [latest_reds]
                logger.debug(f"聚类 {cluster_id}: {len(cluster_indices)} 条记录, 代表模式: {latest_reds}")

        self.is_trained = True
        logger.info(f"{self.name} 策略训练完成，共 {n_clusters} 个聚类")

    def predict(
        self,
        recent_data: pd.DataFrame,
        n_predictions: int = 1
    ) -> Dict[str, List[int]]:
        """
        预测：找到最相似的聚类，使用该聚类的典型模式

        Args:
            recent_data: 最近N期数据
            n_predictions: 预测期数

        Returns:
            {'red': [...], 'blue': [...]}
        """
        if not self.is_trained or self.kmeans is None:
            raise RuntimeError("模型未训练，请先调用 train()")

        window_size = self.config['window_size']
        if len(recent_data) < window_size:
            raise ValueError(f"需要至少 {window_size} 期数据作为输入")

        # 提取当前窗口特征
        current_window = recent_data.iloc[-window_size:]
        current_feature = self._extract_features_from_window(current_window)

        # 标准化和降维
        current_scaled = self.scaler.transform(current_feature.reshape(1, -1))
        if self.pca:
            current_reduced = self.pca.transform(current_scaled)
        else:
            current_reduced = current_scaled

        # 预测聚类
        cluster_id = self.kmeans.predict(current_reduced)[0]

        # 计算与历史样本的距离，找到最相似的 top_k
        distances = np.linalg.norm(self.historical_features - current_reduced, axis=1)
        top_k_indices = np.argsort(distances)[:self.config['top_k_similar']]

        # 收集这些相似样本的下一期红球号码
        candidate_reds = []
        for idx in top_k_indices:
            # 历史样本对应的下一期
            next_idx = idx + 1
            if next_idx < len(self.history_data):
                next_reds = self._extract_red_balls(self.history_data.iloc[next_idx])
                candidate_reds.append(next_reds)

        # 统计候选号码的频率
        from collections import Counter
        all_candidates = [ball for combo in candidate_reds for ball in combo]
        ball_counter = Counter(all_candidates)

        # 选择频率最高的6个号码
        predicted_red = [ball for ball, _ in ball_counter.most_common(6)]

        # 如果不足6个，使用聚类代表模式补充
        if len(predicted_red) < 6:
            if cluster_id in self.cluster_patterns:
                pattern = self.cluster_patterns[cluster_id][0]
                for ball in pattern:
                    if ball not in predicted_red:
                        predicted_red.append(ball)
                    if len(predicted_red) >= 6:
                        break

        # 补充随机号码
        predicted_red = sorted(set(predicted_red))
        while len(predicted_red) < 6:
            available = [n for n in range(1, 34) if n not in predicted_red]
            if available:
                predicted_red.append(np.random.choice(available))
            else:
                break
        predicted_red = sorted(predicted_red[:6])

        # 蓝球预测
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
        from collections import Counter
        counter = Counter(blue_series)
        most_common = counter.most_common(3)
        if most_common:
            return [most_common[0][0]]
        else:
            return [int(blue_series.mode()[0]) if len(blue_series.mode()) > 0 else 6]

    def get_cluster_info(self) -> Dict[str, Any]:
        """获取聚类信息"""
        if not self.is_trained:
            return {}

        info = {
            'n_clusters': self.kmeans.n_clusters if self.kmeans else 0,
            'cluster_sizes': {},
            'cluster_patterns': self.cluster_patterns
        }

        if self.historical_labels is not None:
            unique, counts = np.unique(self.historical_labels, return_counts=True)
            for cluster_id, count in zip(unique, counts):
                info['cluster_sizes'][int(cluster_id)] = int(count)

        return info
