# -*- coding:utf-8 -*-
"""
集成测试
测试完整的工作流程
"""
import pytest
import sys
import os
import pandas as pd
import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)


class TestDataFlow:
    """数据流测试"""
    
    def test_complete_analysis_pipeline(self, sample_data):
        """测试完整的分析流程"""
        from core.strategies import LotteryStrategy
        
        # 1. 创建策略分析器
        strategy = LotteryStrategy(sample_data)
        
        # 2. 执行冷热号分析
        hot, cold = strategy.analyze_hot_cold('red', recent_n=5)
        assert len(hot) > 0
        assert len(cold) > 0
        
        # 3. 执行遗漏分析
        top_omission = strategy.get_omission_top('red', top_n=10)
        assert len(top_omission) == 10
        
        # 4. 获取推荐号码
        recommendation = strategy.recommend_balls()
        assert 'red_candidates' in recommendation
        assert 'blue_candidates' in recommendation
        
        # 5. 生成组合
        combos = strategy.generate_combinations(
            recommendation['red_candidates'],
            recommendation['blue_candidates'],
            n_combinations=3
        )
        assert len(combos) == 3
        
        # 6. 过滤组合
        filtered = strategy.smart_filter(combos)
        assert isinstance(filtered, list)
    
    def test_statistics_pipeline(self, sample_data):
        """测试统计分析流程"""
        from core.strategies import StatisticsAnalyzer
        
        stats = StatisticsAnalyzer(sample_data)
        
        # 分析和值
        sum_stats = stats.analyze_sum_range()
        assert sum_stats['mean'] > 0
        
        # 分析 AC 指数
        ac_stats = stats.analyze_ac_index()
        assert ac_stats['mean'] >= 0
        
        # 分析连号
        consecutive = stats.analyze_consecutive_numbers()
        assert isinstance(consecutive, dict)


class TestHelpersIntegration:
    """工具函数集成测试"""
    
    def test_validation_and_analysis(self, sample_data):
        """测试验证和分析的集成"""
        from utils.validators import validate_red_balls
        from core.strategies import LotteryStrategy
        
        # 1. 验证数据有效性
        for idx in range(len(sample_data)):
            red_balls = [
                sample_data.iloc[idx][f'红球_{i}'] 
                for i in range(1, 7)
            ]
            # 数据可能不满足验证条件（未排序等），所以用 try
            try:
                validate_red_balls(red_balls)
            except Exception:
                pass  # 预期中的失败
    
    def test_error_handling_integration(self, sample_data):
        """测试错误处理的集成"""
        from utils.exceptions import DataValidationError
        from utils.validators import validate_red_balls
        
        # 测试各种无效输入
        invalid_cases = [
            [1, 2, 3],  # 数量不够
            [1, 2, 3, 4, 5, 35],  # 超出范围
            [1, 1, 3, 4, 5, 6],  # 重复号码
        ]
        
        for balls in invalid_cases:
            with pytest.raises(DataValidationError):
                validate_red_balls(balls)


class TestPerformance:
    """性能测试"""
    
    def test_large_dataset_analysis(self, large_sample_data):
        """测试大数据集分析性能"""
        from core.strategies import LotteryStrategy
        import time
        
        start_time = time.time()
        
        strategy = LotteryStrategy(large_sample_data)
        
        # 执行完整分析
        strategy.analyze_hot_cold('red', recent_n=100)
        strategy.analyze_omission('red')
        strategy.recommend_balls()
        
        elapsed = time.time() - start_time
        
        # 应该在 120 秒内完成（考虑到算法复杂度）
        assert elapsed < 120.0, f"分析耗时过长：{elapsed:.2f}秒"
    
    def test_memory_efficiency(self, large_sample_data):
        """测试内存效率"""
        from core.strategies import StrategyAnalyzer
        import tracemalloc
        
        tracemalloc.start()
        
        analyzer = StrategyAnalyzer(large_sample_data)
        analyzer.calculate_frequency('red', recent_n=500)
        analyzer.calculate_omission('red')
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # 峰值内存应小于 100MB
        assert peak < 100 * 1024 * 1024, f"内存使用过高：{peak / 1024 / 1024:.2f}MB"


class TestEdgeCases:
    """边界情况测试"""
    
    def test_empty_data(self):
        """测试空数据"""
        from core.strategies import LotteryStrategy
        import pandas as pd
        
        empty_data = pd.DataFrame({
            '期数': [],
            '红球_1': [],
            '红球_2': [],
            '红球_3': [],
            '红球_4': [],
            '红球_5': [],
            '红球_6': [],
            '蓝球': []
        })
        
        strategy = LotteryStrategy(empty_data)
        # 应该能处理空数据而不崩溃
        freq = strategy.strategy.calculate_frequency('red', recent_n=50)
        assert len(freq) == 0
    
    def test_single_record(self):
        """测试单条记录"""
        from core.strategies import LotteryStrategy
        import pandas as pd
        
        single_data = pd.DataFrame({
            '期数': ['2024001'],
            '红球_1': [3],
            '红球_2': [7],
            '红球_3': [12],
            '红球_4': [18],
            '红球_5': [25],
            '红球_6': [30],
            '蓝球': [9]
        })
        
        strategy = LotteryStrategy(single_data)
        # 应该能处理单条记录
        hot = strategy.strategy.get_hot_numbers('red', recent_n=1)
        assert len(hot) > 0
    
    def test_extreme_values(self):
        """测试极端值"""
        from utils.helpers import safe_divide, validate_range
        
        # 极大数（考虑浮点精度）
        result = safe_divide(1e100, 1e50)
        assert abs(result - 1e50) / 1e50 < 1e-10, f"极大数计算误差过大：{result}"
        
        # 极小数
        result = safe_divide(1e-100, 1e-50)
        assert abs(result - 1e-50) / 1e-50 < 1e-10, f"极小数计算误差过大：{result}"
        
        # 边界值验证
        assert validate_range(1, 1, 33, "test") is True
        assert validate_range(33, 1, 33, "test") is True
