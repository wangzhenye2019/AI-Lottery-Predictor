# -*- coding:utf-8 -*-
"""
策略分析模块（重构版）
将大函数拆分为小函数，提高代码可维护性
"""
import numpy as np
import pandas as pd
from collections import Counter
from typing import Dict, List, Tuple
from utils.logger import log
from utils.validators import validate_lottery_number


class StrategyAnalyzer:
    """策略分析器 - 基础分析功能"""
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化分析器
        
        Args:
            data: 历史数据 DataFrame
        """
        self.data = data
        self.red_balls = self._get_ball_columns('红球')
        self.blue_balls = self._get_ball_columns('蓝球')
    
    def _get_ball_columns(self, ball_type: str) -> List[str]:
        """获取指定类型的球列名"""
        return [col for col in self.data.columns if ball_type in col]
    
    def calculate_frequency(
        self, 
        ball_type: str = 'red',
        recent_n: int = 50
    ) -> Dict[int, int]:
        """
        计算号码频率
        
        Args:
            ball_type: 球类型
            recent_n: 最近 N 期
        
        Returns:
            频率字典 {号码：出现次数}
        """
        balls = self.red_balls if ball_type == 'red' else self.blue_balls
        recent_data = self.data.tail(recent_n)[balls].values.flatten().astype(int)
        counter = Counter(recent_data)
        return dict(counter)
    
    def get_hot_numbers(
        self, 
        ball_type: str = 'red',
        recent_n: int = 50,
        top_ratio: float = 1/3
    ) -> List[int]:
        """
        获取热号（出现频率最高的号码）
        
        Args:
            ball_type: 球类型
            recent_n: 最近 N 期
            top_ratio: 前百分之多少
        
        Returns:
            热号列表
        """
        frequency = self.calculate_frequency(ball_type, recent_n)
        sorted_items = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
        top_count = max(1, int(len(sorted_items) * top_ratio))
        return [num for num, _ in sorted_items[:top_count]]
    
    def get_cold_numbers(
        self,
        ball_type: str = 'red',
        recent_n: int = 50,
        bottom_ratio: float = 1/3
    ) -> List[int]:
        """
        获取冷号（出现频率最低的号码）
        
        Args:
            ball_type: 球类型
            recent_n: 最近 N 期
            bottom_ratio: 后百分之多少
        
        Returns:
            冷号列表
        """
        frequency = self.calculate_frequency(ball_type, recent_n)
        sorted_items = sorted(frequency.items(), key=lambda x: x[1])
        bottom_count = max(1, int(len(sorted_items) * bottom_ratio))
        return [num for num, _ in sorted_items[:bottom_count]]
    
    def calculate_omission(
        self,
        ball_type: str = 'red'
    ) -> Dict[int, int]:
        """
        计算号码遗漏值
        
        Args:
            ball_type: 球类型
        
        Returns:
            遗漏字典 {号码：遗漏期数}
        """
        balls = self.red_balls if ball_type == 'red' else self.blue_balls
        max_num = self._get_max_number(ball_type)
        
        omission = {i: 0 for i in range(1, max_num + 1)}
        
        for idx in range(len(self.data)):
            row = self.data.iloc[idx][balls].values.astype(int)
            for num in range(1, max_num + 1):
                if num in row:
                    omission[num] = 0
                else:
                    omission[num] += 1
        
        return omission
    
    def get_top_omission(
        self,
        ball_type: str = 'red',
        top_n: int = 10
    ) -> List[Tuple[int, int]]:
        """
        获取遗漏值最高的号码
        
        Args:
            ball_type: 球类型
            top_n: 返回前 N 个
        
        Returns:
            [(号码，遗漏期数), ...]
        """
        omission = self.calculate_omission(ball_type)
        sorted_omission = sorted(omission.items(), key=lambda x: x[1], reverse=True)
        return sorted_omission[:top_n]
    
    def calculate_probability(
        self,
        ball_type: str = 'red'
    ) -> Dict[int, float]:
        """
        计算号码概率分布
        
        Args:
            ball_type: 球类型
        
        Returns:
            概率字典 {号码：出现概率}
        """
        balls = self.red_balls if ball_type == 'red' else self.blue_balls
        max_num = self._get_max_number(ball_type)
        
        all_balls = self.data[balls].values.flatten().astype(int)
        total = len(all_balls)
        counter = Counter(all_balls)
        
        probability = {
            num: count / total 
            for num, count in counter.items()
        }
        
        return probability
    
    def _get_max_number(self, ball_type: str) -> int:
        """获取指定球类型的最大号码"""
        if ball_type == 'red':
            if len(self.red_balls) == 6: return 33  # ssq
            if len(self.red_balls) == 5: return 35  # dlt
            if len(self.red_balls) == 7: return 30  # qlc
            return 35
        else:
            if len(self.red_balls) == 6: return 16  # ssq
            if len(self.red_balls) == 5: return 12  # dlt
            if len(self.red_balls) == 7: return 30  # qlc
            return 16


class StatisticsAnalyzer:
    """统计分析器 - 高级统计功能"""
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化统计分析器
        
        Args:
            data: 历史数据 DataFrame
        """
        self.data = data
        self.red_balls = [col for col in data.columns if '红球' in col]
    
    def analyze_sum_range(self) -> Dict[str, float]:
        """
        分析和值范围
        
        Returns:
            统计字典 {mean, std, min, max, median}
        """
        red_data = self.data[self.red_balls].values
        sums = red_data.sum(axis=1)
        
        return {
            'mean': float(sums.mean()),
            'std': float(sums.std()),
            'min': float(sums.min()),
            'max': float(sums.max()),
            'median': float(np.median(sums))
        }
    
    def analyze_ac_index(self) -> Dict[str, float]:
        """
        分析 AC 指数（数字复杂指数）
        
        Returns:
            统计字典 {mean, std, min, max}
        """
        red_data = self.data[self.red_balls].values
        ac_values = []
        
        for row in red_data:
            diffs = []
            for i in range(len(row)):
                for j in range(i+1, len(row)):
                    diffs.append(abs(int(row[i]) - int(row[j])))
            unique_diffs = len(set(diffs))
            ac = unique_diffs - (len(row) - 1)
            ac_values.append(ac)
        
        return {
            'mean': float(np.mean(ac_values)),
            'std': float(np.std(ac_values)),
            'min': float(min(ac_values)),
            'max': float(max(ac_values))
        }
    
    def analyze_consecutive_numbers(self) -> Dict[int, int]:
        """
        分析连号情况
        
        Returns:
            计数字典 {连号数量：期数}
        """
        red_data = self.data[self.red_balls].values
        consecutive_counts = []
        
        for row in red_data:
            count = 0
            sorted_row = sorted([int(x) for x in row])
            for i in range(len(sorted_row) - 1):
                if sorted_row[i+1] - sorted_row[i] == 1:
                    count += 1
            consecutive_counts.append(count)
        
        counter = Counter(consecutive_counts)
        return dict(counter)
    
    def analyze_span(self) -> Dict[str, float]:
        """
        分析首尾间距
        
        Returns:
            统计字典 {mean, std, min, max}
        """
        red_data = self.data[self.red_balls].values
        spans = red_data[:, -1] - red_data[:, 0]
        
        return {
            'mean': float(np.mean(spans)),
            'std': float(np.std(spans)),
            'min': float(spans.min()),
            'max': float(spans.max())
        }


class BallRecommender:
    """号码推荐器 - 综合推荐功能"""
    
    def __init__(self, strategy_analyzer: StrategyAnalyzer, stats_analyzer: StatisticsAnalyzer):
        """
        初始化推荐器
        
        Args:
            strategy_analyzer: 策略分析器
            stats_analyzer: 统计分析器
        """
        self.strategy = strategy_analyzer
        self.stats = stats_analyzer
    
    def calculate_score(
        self,
        number: int,
        ball_type: str = 'red',
        weights: Dict[str, float] = None
    ) -> float:
        """
        计算号码得分
        
        Args:
            number: 号码
            ball_type: 球类型
            weights: 权重配置
        
        Returns:
            得分
        """
        if weights is None:
            weights = {
                'hot': 0.35,
                'cold': 0.25,
                'omission': 0.25,
                'probability': 0.15
            }
        
        score = 0.0
        
        # 热号得分
        hot_numbers = self.strategy.get_hot_numbers(ball_type)
        if number in hot_numbers:
            score += weights['hot'] * 10
        
        # 冷号得分
        cold_numbers = self.strategy.get_cold_numbers(ball_type)
        if number in cold_numbers:
            score += weights['cold'] * 5
        
        # 遗漏得分
        top_omission = [num for num, _ in self.strategy.get_top_omission(ball_type, 15)]
        if number in top_omission:
            score += weights['omission'] * 8
        
        # 概率得分
        probability = self.strategy.calculate_probability(ball_type)
        if number in probability:
            score += weights['probability'] * probability[number] * 100
        
        return score
    
    def recommend_candidates(
        self,
        ball_type: str = 'red',
        candidate_count: int = 12,
        weights: Dict[str, float] = None
    ) -> List[int]:
        """
        推荐候选号码
        
        Args:
            ball_type: 球类型
            candidate_count: 候选数量
            weights: 权重配置
        
        Returns:
            推荐号码列表
        """
        max_num = self.strategy._get_max_number(ball_type)
        
        scores = {}
        for num in range(1, max_num + 1):
            scores[num] = self.calculate_score(num, ball_type, weights)
        
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [num for num, _ in sorted_scores[:candidate_count]]
    
    def filter_by_sum(
        self,
        combinations,
        min_sum: int = 90,
        max_sum: int = 120
    ):
        """
        根据和值过滤组合
        
        Args:
            combinations: 组合列表，支持 List[List[int]] 或 List[Dict{'red': List[int], 'blue': int}]
            min_sum: 最小和值
            max_sum: 最大和值
        
        Returns:
            过滤后的组合
        """
        filtered = []
        for combo in combinations:
            # 支持字典格式（包含红球和蓝球）和列表格式（仅红球）
            if isinstance(combo, dict):
                combo_numbers = combo.get('red', [])
            else:
                combo_numbers = combo
            
            combo_sum = sum(combo_numbers)
            if min_sum <= combo_sum <= max_sum:
                filtered.append(combo)
        return filtered
    
    def filter_by_ac(
        self,
        combinations,
        min_ac: int = 4,
        max_ac: int = 10
    ):
        """
        根据 AC 指数过滤组合
        
        Args:
            combinations: 组合列表，支持 List[List[int]] 或 List[Dict{'red': List[int], 'blue': int}]
            min_ac: 最小 AC 指数
            max_ac: 最大 AC 指数
        
        Returns:
            过滤后的组合
        """
        filtered = []
        for combo in combinations:
            # 支持字典格式（包含红球和蓝球）和列表格式（仅红球）
            if isinstance(combo, dict):
                combo_numbers = combo.get('red', [])
            else:
                combo_numbers = combo
            
            diffs = []
            for i in range(len(combo_numbers)):
                for j in range(i+1, len(combo_numbers)):
                    diffs.append(abs(combo_numbers[i] - combo_numbers[j]))
            ac = len(set(diffs)) - (len(combo_numbers) - 1)
            
            if min_ac <= ac <= max_ac:
                filtered.append(combo)
        
        return filtered


# 兼容旧版本的接口
class LotteryStrategy:
    """彩票选球策略类（兼容旧版本）"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.strategy = StrategyAnalyzer(data)
        self.stats = StatisticsAnalyzer(data)
        self.recommender = BallRecommender(self.strategy, self.stats)
    
    def analyze_hot_cold(self, ball_type='red', recent_n=50):
        """分析冷热号码（兼容旧接口）"""
        hot = self.strategy.get_hot_numbers(ball_type, recent_n)
        cold = self.strategy.get_cold_numbers(ball_type, recent_n)
        log.info(f"{ball_type}球 - 热号 (最近{recent_n}期): {hot}")
        log.info(f"{ball_type}球 - 冷号 (最近{recent_n}期): {cold}")
        return hot, cold
    
    def analyze_omission(self, ball_type='red'):
        """分析遗漏（兼容旧接口）"""
        return self.strategy.calculate_omission(ball_type)
    
    def get_omission_top(self, ball_type='red', top_n=10):
        """获取高遗漏号码（兼容旧接口）"""
        top = self.strategy.get_top_omission(ball_type, top_n)
        top_nums = [num for num, _ in top]
        log.info(f"{ball_type}球 - 遗漏最高的{top_n}个号码：{top_nums}")
        return top_nums
    
    def analyze_probability_distribution(self, ball_type='red'):
        """分析概率分布（兼容旧接口）"""
        return self.strategy.calculate_probability(ball_type)
    
    def analyze_sum_range(self):
        """分析和值（兼容旧接口）"""
        stats = self.stats.analyze_sum_range()
        log.info(f"红球和值统计 - 均值：{stats['mean']:.2f}, 标准差：{stats['std']:.2f}")
        log.info(f"红球和值范围：[{stats['min']}, {stats['max']}], 中位数：{stats['median']}")
        return stats
    
    def analyze_ac_ratio(self):
        """分析 AC 指数（兼容旧接口）"""
        stats = self.stats.analyze_ac_index()
        log.info(f"AC 指数统计 - 均值：{stats['mean']:.2f}, 范围：[{stats['min']}, {stats['max']}]")
        return stats
    
    def recommend_balls(self, strategy='hybrid', n_red=6, n_blue=1, **kwargs):
        """推荐号码（兼容旧接口）"""
        red_candidates = self.recommender.recommend_candidates('red', candidate_count=12)
        blue_candidates = self.recommender.recommend_candidates('blue', candidate_count=6)
        
        log.info(f"推荐红球候选：{sorted(red_candidates)}")
        log.info(f"推荐蓝球候选：{sorted(blue_candidates)}")
        
        return {
            'red_candidates': sorted(red_candidates),
            'blue_candidates': sorted(blue_candidates)
        }
    
    def generate_combinations(self, red_candidates, blue_candidates, n_combinations=5):
        """生成组合（增强版，根据历史中奖概率加权）"""
        import random
        
        # 计算红球和蓝球的历史频率权重
        red_freq = self.strategy.calculate_frequency('red')
        blue_freq = self.strategy.calculate_frequency('blue')
        
        combinations = []
        for _ in range(n_combinations):
            # 获取候选红球的权重
            red_weights = []
            for r in red_candidates:
                # 基础权重 1.0，加上历史频率的加权
                weight = 1.0 + (red_freq.get(r, 0) / max(1, sum(red_freq.values()))) * 10
                red_weights.append(weight)
                
            # 转换为概率分布
            red_probs = np.array(red_weights) / sum(red_weights)
            
            # 使用 np.random.choice 进行加权无放回抽样
            red_count = len(self.strategy.red_balls)
            red_balls = sorted(np.random.choice(
                red_candidates, 
                size=min(red_count, len(red_candidates)), 
                replace=False, 
                p=red_probs
            ).tolist())
            
            # 蓝球同样加权
            blue_weights = []
            for b in blue_candidates:
                weight = 1.0 + (blue_freq.get(b, 0) / max(1, sum(blue_freq.values()))) * 10
                blue_weights.append(weight)
            blue_probs = np.array(blue_weights) / sum(blue_weights)
            
            blue_ball = np.random.choice(blue_candidates, p=blue_probs)
            
            combinations.append({'red': red_balls, 'blue': int(blue_ball)})
            
        return combinations
    
    def smart_filter(self, combinations, sum_range=(90, 120), ac_range=(4, 10)):
        """智能过滤（兼容旧接口）"""
        filtered = self.recommender.filter_by_sum(combinations, *sum_range)
        filtered = self.recommender.filter_by_ac(filtered, *ac_range)
        log.info(f"过滤前：{len(combinations)}组，过滤后：{len(filtered)}组")
        return filtered
