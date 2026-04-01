# -*- coding:utf-8 -*-
"""
pytest 配置文件
"""
import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_data():
    """创建示例数据"""
    data = {
        '期数': ['2024001', '2024002', '2024003', '2024004', '2024005'],
        '红球_1': [3, 5, 7, 9, 11],
        '红球_2': [7, 9, 12, 15, 18],
        '红球_3': [12, 15, 18, 21, 24],
        '红球_4': [18, 21, 24, 27, 30],
        '红球_5': [25, 28, 30, 32, 33],
        '红球_6': [30, 33, 33, 33, 33],
        '蓝球': [9, 11, 5, 14, 16]
    }
    return pd.DataFrame(data)


@pytest.fixture
def large_sample_data():
    """创建大数据集（用于性能测试）"""
    np.random.seed(42)
    n_records = 1000
    
    data = {
        '期数': [f'2024{i:03d}' for i in range(1, n_records + 1)],
        '红球_1': np.random.randint(1, 34, n_records),
        '红球_2': np.random.randint(1, 34, n_records),
        '红球_3': np.random.randint(1, 34, n_records),
        '红球_4': np.random.randint(1, 34, n_records),
        '红球_5': np.random.randint(1, 34, n_records),
        '红球_6': np.random.randint(1, 34, n_records),
        '蓝球': np.random.randint(1, 17, n_records)
    }
    return pd.DataFrame(data)


@pytest.fixture(scope="session")
def test_output_dir(tmp_path_factory):
    """创建测试输出目录"""
    return tmp_path_factory.mktemp("output")
