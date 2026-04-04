# -*- coding:utf-8 -*-
"""
策略模块单元测试
"""
import pytest
import sys
import os
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from core.strategies import (
    StrategyAnalyzer, StatisticsAnalyzer, BallRecommender, LotteryStrategy
)


class TestStrategyAnalyzer:
    """策略分析器测试"""
    
    @pytest.fixture
    def analyzer(self, sample_data):
        """创建分析器实例"""
        return StrategyAnalyzer(sample_data)
    
    def test_get_ball_columns(self, analyzer):
        """测试获取球列名"""
        red_cols = analyzer._get_ball_columns('红球')
        assert len(red_cols) == 6
        assert '红球_1' in red_cols
        
        blue_cols = analyzer._get_ball_columns('蓝球')
        assert len(blue_cols) == 1
        assert '蓝球' in blue_cols
    
    def test_calculate_frequency(self, analyzer):
        """测试频率计算"""
        freq = analyzer.calculate_frequency('red', recent_n=5)
        assert isinstance(freq, dict)
        # 所有号码都应该出现
        assert len(freq) > 0
    
    def test_get_hot_numbers(self, analyzer):
        """测试热号获取"""
        hot = analyzer.get_hot_numbers('red', recent_n=5)
        assert isinstance(hot, list)
        assert len(hot) > 0
        # 所有号码都应在有效范围内
        assert all(1 <= num <= 33 for num in hot)
    
    def test_get_cold_numbers(self, analyzer):
        """测试冷号获取"""
        cold = analyzer.get_cold_numbers('red', recent_n=5)
        assert isinstance(cold, list)
        assert len(cold) > 0
    
    def test_calculate_omission(self, analyzer):
        """测试遗漏计算"""
        omission = analyzer.calculate_omission('red')
        assert isinstance(omission, dict)
        assert len(omission) == 33
        assert all(1 <= num <= 33 for num in omission.keys())
    
    def test_get_top_omission(self, analyzer):
        """测试高遗漏号码获取"""
        top = analyzer.get_top_omission('red', top_n=5)
        assert isinstance(top, list)
        assert len(top) == 5
        # 返回格式应为 [(号码，遗漏期数)]
        assert all(isinstance(item, tuple) and len(item) == 2 for item in top)
    
    def test_calculate_probability(self, analyzer):
        """测试概率计算"""
        prob = analyzer.calculate_probability('red')
        assert isinstance(prob, dict)
        assert len(prob) > 0
        # 所有概率应在 0-1 之间
        assert all(0 <= p <= 1 for p in prob.values())


class TestStatisticsAnalyzer:
    """统计分析器测试"""
    
    @pytest.fixture
    def stats_analyzer(self, sample_data):
        """创建统计分析器实例"""
        return StatisticsAnalyzer(sample_data)
    
    def test_analyze_sum_range(self, stats_analyzer):
        """技术和值分析"""
        stats = stats_analyzer.analyze_sum_range()
        assert isinstance(stats, dict)
        assert 'mean' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert 'median' in stats
        # 均值应在合理范围内
        assert 50 <= stats['mean'] <= 150
    
    def test_analyze_ac_index(self, stats_analyzer):
        """测试 AC 指数分析"""
        stats = stats_analyzer.analyze_ac_index()
        assert isinstance(stats, dict)
        assert 'mean' in stats
        assert 'std' in stats
        # AC 指数应在 0-10 之间
        assert 0 <= stats['min']
        assert stats['max'] <= 10
    
    def test_analyze_consecutive_numbers(self, stats_analyzer):
        """测试连号分析"""
        consecutive = stats_analyzer.analyze_consecutive_numbers()
        assert isinstance(consecutive, dict)
        # 连号数量应 >= 0
        assert all(count >= 0 for count in consecutive.keys())
    
    def test_analyze_span(self, stats_analyzer):
        """测试首尾间距分析"""
        stats = stats_analyzer.analyze_span()
        assert isinstance(stats, dict)
        assert 'mean' in stats
        # 间距应在 1-32 之间
        assert 1 <= stats['min']
        assert stats['max'] <= 32


class TestBallRecommender:
    """号码推荐器测试"""
    
    @pytest.fixture
    def recommender(self, sample_data):
        """创建推荐器实例"""
        strategy = StrategyAnalyzer(sample_data)
        stats = StatisticsAnalyzer(sample_data)
        return BallRecommender(strategy, stats)
    
    def test_calculate_score(self, recommender):
        """测试号码评分"""
        score = recommender.calculate_score(5, 'red')
        assert isinstance(score, float)
        assert score >= 0
    
    def test_recommend_candidates(self, recommender):
        """测试候选号码推荐"""
        candidates = recommender.recommend_candidates('red', candidate_count=12)
        assert isinstance(candidates, list)
        assert len(candidates) == 12
        # 所有号码应在有效范围内
        assert all(1 <= num <= 33 for num in candidates)
        # 不应有重复
        assert len(candidates) == len(set(candidates))
    
    def test_filter_by_sum(self, recommender):
        """测试和值过滤"""
        combinations = [
            [1, 5, 12, 18, 25, 30],  # sum=91
            [10, 15, 20, 25, 30, 33],  # sum=133
            [5, 10, 15, 20, 25, 30]   # sum=105
        ]
        
        filtered = recommender.filter_by_sum(combinations, min_sum=90, max_sum=120)
        assert len(filtered) == 2  # 第 1 和第 3 个组合符合
        assert sum(filtered[0]) <= 120
        assert sum(filtered[1]) <= 120
    
    def test_filter_by_ac(self, recommender):
        """测试 AC 指数过滤"""
        combinations = [
            [1, 2, 3, 4, 5, 6],  # AC 很低（规则）
            [1, 5, 12, 18, 25, 30],  # AC 正常
            [3, 7, 15, 22, 28, 33]   # AC 正常
        ]
        
        filtered = recommender.filter_by_ac(combinations, min_ac=4, max_ac=10)
        # 至少应该有 2 个组合符合（后两个）
        assert len(filtered) >= 2


class TestLotteryStrategyCompatibility:
    """兼容旧版本的接口测试"""
    
    @pytest.fixture
    def strategy(self, sample_data):
        """创建策略实例"""
        return LotteryStrategy(sample_data)
    
    def test_analyze_hot_cold(self, strategy):
        """测试冷热号分析（旧接口）"""
        hot, cold = strategy.analyze_hot_cold('red', recent_n=5)
        assert isinstance(hot, list)
        assert isinstance(cold, list)
        assert len(hot) > 0
        assert len(cold) > 0
    
    def test_analyze_omission(self, strategy):
        """测试遗漏分析（旧接口）"""
        omission = strategy.analyze_omission('red')
        assert isinstance(omission, dict)
        assert len(omission) == 33
    
    def test_get_omission_top(self, strategy):
        """测试高遗漏号码（旧接口）"""
        top = strategy.get_omission_top('red', top_n=10)
        assert isinstance(top, list)
        assert len(top) == 10
    
    def test_recommend_balls(self, strategy):
        """测试号码推荐（旧接口）"""
        result = strategy.recommend_balls()
        assert isinstance(result, dict)
        assert 'red_candidates' in result
        assert 'blue_candidates' in result
        assert len(result['red_candidates']) > 0
        assert len(result['blue_candidates']) > 0
    
    def test_generate_combinations(self, strategy):
        """测试组合生成（旧接口）"""
        red_candidates = list(range(1, 13))
        blue_candidates = [9, 11, 14]
        
        combos = strategy.generate_combinations(red_candidates, blue_candidates, n_combinations=5)
        assert len(combos) == 5
        assert all('red' in combo and 'blue' in combo for combo in combos)
        assert all(len(combo['red']) == 6 for combo in combos)
    
    def test_smart_filter(self, strategy):
        """测试智能过滤（旧接口）"""
        combinations = [
            {'red': [1, 5, 12, 18, 25, 30], 'blue': 9},
            {'red': [10, 15, 20, 25, 30, 33], 'blue': 11}
        ]
        
        filtered = strategy.smart_filter(combinations, sum_range=(90, 120), ac_range=(4, 10))
        assert isinstance(filtered, list)
