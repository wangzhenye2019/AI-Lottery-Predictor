# -*- coding: utf-8 -*-
"""
Apriori 关联规则策略
发现历史开奖号码中的频繁项集和关联规则
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Set, Tuple
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
from .base_strategy import BaseStrategy
from loguru import logger


class AprioriStrategy(BaseStrategy):
    """Apriori 关联规则预测策略"""

    def __init__(self, name: str = "apriori", config: Dict[str, Any] = None):
        """
        初始化 Apriori 策略

        Args:
            config: {
                'min_support': 0.02,      # 最小支持度
                'min_confidence': 0.3,    # 最小置信度
                'max_len': 6,             # 最大项集大小
                'top_k_rules': 50,        # 保留 top_k 条规则
                'window_size': 100        # 使用最近N期数据
            }
        """
        default_config = {
            'min_support': 0.02,
            'min_confidence': 0.3,
            'max_len': 6,
            'top_k_rules': 50,
            'window_size': 100
        }
        config = {**default_config, **(config or {})}
        super().__init__(name, config)

        self.frequent_itemsets = None
        self.rules = None
        self.transactions: List[List[int]] = []

    def _create_transactions(self, data: pd.DataFrame) -> List[List[int]]:
        """
        将每期开奖号码转换为事务列表

        Args:
            data: 历史数据

        Returns:
            事务列表，每个事务是一组红球号码
        """
        transactions = []
        red_cols = sorted([col for col in data.columns if '红球' in col])

        for _, row in data.iterrows():
            balls = [int(row[col]) for col in red_cols]
            transactions.append(balls)

        return transactions

    def train(self, data: pd.DataFrame) -> None:
        """
        训练 Apriori 模型，发现频繁项集和关联规则

        Args:
            data: 历史数据
        """
        logger.info(f"开始训练 {self.name} 策略...")
        self.history_data = data.copy()

        window_size = self.config['window_size']
        if len(data) > window_size:
            data = data.iloc[-window_size:]

        # 创建事务列表
        self.transactions = self._create_transactions(data)

        # 转换为 one-hot 编码
        te = TransactionEncoder()
        te_ary = te.fit_transform(self.transactions)
        df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

        # 挖掘频繁项集
        logger.info("挖掘频繁项集...")
        self.frequent_itemsets = apriori(
            df_encoded,
            min_support=self.config['min_support'],
            use_colnames=True,
            max_len=self.config['max_len']
        )

        logger.info(f"发现 {len(self.frequent_itemsets)} 个频繁项集")

        # 生成关联规则
        if len(self.frequent_itemsets) > 0:
            self.rules = association_rules(
                self.frequent_itemsets,
                metric="confidence",
                min_threshold=self.config['min_confidence']
            )

            # 按提升度（lift）排序，保留 top_k
            if self.rules is not None and len(self.rules) > 0:
                self.rules = self.rules.sort_values('lift', ascending=False)
                self.rules = self.rules.head(self.config['top_k_rules'])

            logger.info(f"生成 {len(self.rules) if self.rules is not None else 0} 条关联规则")

        self.is_trained = True
        logger.info(f"{self.name} 策略训练完成")

    def predict(
        self,
        recent_data: pd.DataFrame,
        n_predictions: int = 1
    ) -> Dict[str, List[int]]:
        """
        基于关联规则预测号码

        Args:
            recent_data: 最近N期数据（用于获取当前号码组合）
            n_predictions: 预测期数

        Returns:
            {'red': [...], 'blue': [...]}
        """
        if not self.is_trained or self.rules is None or len(self.rules) == 0:
            logger.warning("Apriori 策略未训练或无有效规则，返回随机预测")
            return {
                'red': sorted(np.random.choice(range(1, 34), 6, replace=False).tolist()),
                'blue': [np.random.randint(1, 17)]
            }

        # 获取最近一期的红球组合作为 antecedent
        latest_red = self._extract_red_balls(recent_data.iloc[-1])
        latest_set = set(latest_red)

        # 寻找匹配的规则
        matched_rules = []
        for _, rule in self.rules.iterrows():
            antecedents = set(rule['antecedents'])
            if antecedents.issubset(latest_set) and len(antecedents) > 0:
                matched_rules.append(rule)

        # 计算候选号码的得分
        candidate_scores: Dict[int, float] = {}

        if matched_rules:
            for rule in matched_rules:
                consequents = list(rule['consequents'])
                confidence = float(rule['confidence'])
                lift = float(rule['lift'])
                support = float(rule['support'])

                for ball in consequents:
                    if ball not in latest_set:  # 只考虑新号码
                        candidate_scores[ball] = candidate_scores.get(ball, 0) + confidence * lift

        # 如果没有匹配规则，使用频繁项集
        if not candidate_scores and self.frequent_itemsets is not None:
            for _, row in self.frequent_itemsets.iterrows():
                itemset = list(row['itemsets'])
                support = float(row['support'])
                if len(itemset) >= 3:  # 至少3个号码
                    for ball in itemset:
                        if ball not in latest_set:
                            candidate_scores[ball] = candidate_scores.get(ball, 0) + support * 10

        # 选择得分最高的6个号码
        if candidate_scores:
            sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
            predicted_red = [ball for ball, _ in sorted_candidates[:6]]
        else:
            # 回退：使用最近高频号码
            all_reds = []
            for _, row in recent_data.iterrows():
                all_reds.extend(self._extract_red_balls(row))
            from collections import Counter
            freq = Counter(all_reds)
            predicted_red = [ball for ball, _ in freq.most_common(6)]

        # 确保有6个不重复号码
        predicted_red = sorted(set(predicted_red))
        while len(predicted_red) < 6:
            # 随机补充
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

    def get_rules_summary(self) -> pd.DataFrame:
        """获取关联规则摘要"""
        if self.rules is None:
            return pd.DataFrame()

        summary = self.rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()
        summary['antecedents'] = summary['antecedents'].apply(lambda x: ','.join(map(str, sorted(x))))
        summary['consequents'] = summary['consequents'].apply(lambda x: ','.join(map(str, sorted(x))))
        return summary
