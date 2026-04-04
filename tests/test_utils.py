# -*- coding:utf-8 -*-
"""
工具模块单元测试
"""
import pytest
import sys
import os

# 添加项目根目录 predict_Lottery_ticket
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from utils.exceptions import (
    LotteryException, DataFetchError, DataValidationError,
    ModelLoadError, PredictionError
)
from utils.helpers import (
    ensure_dir, safe_divide, format_number, validate_range,
    join_path, file_exists, read_file_lines, write_to_file
)
from utils.validators import (
    validate_lottery_number, validate_red_balls, validate_blue_balls,
    validate_data_frame
)


class TestExceptions:
    """异常类测试"""
    
    def test_data_fetch_error(self):
        """测试数据获取异常"""
        error = DataFetchError(source="test_url")
        assert "test_url" in str(error)
        assert error.source == "test_url"
    
    def test_data_validation_error(self):
        """测试数据验证异常"""
        error = DataValidationError(field="test_field")
        assert "test_field" in str(error)
        assert error.field == "test_field"
    
    def test_prediction_error(self):
        """测试预测异常"""
        error = PredictionError(ball_type="red")
        assert "red" in str(error)
        assert error.ball_type == "red"


class TestHelpers:
    """辅助函数测试"""
    
    def test_safe_divide_normal(self):
        """测试正常除法"""
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 4) == 2.5
    
    def test_safe_divide_by_zero(self):
        """测试除零保护"""
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, default=-1) == -1
    
    def test_format_number(self):
        """测试数字格式化"""
        assert format_number(3.14159) == "3.14"
        assert format_number(3.14159, decimals=3) == "3.142"
        assert format_number(100) == "100.00"
    
    def test_validate_range_valid(self):
        """测试范围验证（有效）"""
        assert validate_range(50, 1, 100, "百分比") is True
        assert validate_range(5, 1, 33, "红球") is True
    
    def test_validate_range_invalid(self):
        """测试范围验证（无效）"""
        with pytest.raises(ValueError):
            validate_range(150, 1, 100, "百分比")
        with pytest.raises(ValueError):
            validate_range(0, 1, 33, "红球")
    
    def test_ensure_dir(self, tmp_path):
        """测试目录创建"""
        new_dir = tmp_path / "test_dir" / "nested"
        ensure_dir(str(new_dir))
        assert new_dir.exists()
        assert new_dir.is_dir()
    
    def test_join_path(self):
        """测试路径拼接"""
        path = join_path("home", "user", "test")
        assert "home" in path
        assert "user" in path
        assert "test" in path
    
    def test_file_operations(self, tmp_path):
        """测试文件操作"""
        test_file = tmp_path / "test.txt"
        content = "测试内容\n第二行"
        
        # 写入文件
        write_to_file(content, str(test_file))
        assert file_exists(str(test_file))
        
        # 读取文件
        lines = read_file_lines(str(test_file))
        assert len(lines) == 2
        assert "测试内容" in lines[0]


class TestValidators:
    """验证工具测试"""
    
    def test_validate_lottery_number_red_valid(self):
        """测试红球验证（有效）"""
        assert validate_lottery_number(5, "red") is True
        assert validate_lottery_number(33, "red") is True
    
    def test_validate_lottery_number_red_invalid(self):
        """测试红球验证（无效）"""
        with pytest.raises(DataValidationError):
            validate_lottery_number(0, "red")
        with pytest.raises(DataValidationError):
            validate_lottery_number(34, "red")
    
    def test_validate_lottery_number_blue_valid(self):
        """测试蓝球验证（有效）"""
        assert validate_lottery_number(9, "blue") is True
        assert validate_lottery_number(16, "blue") is True
    
    def test_validate_lottery_number_blue_invalid(self):
        """测试蓝球验证（无效）"""
        with pytest.raises(DataValidationError):
            validate_lottery_number(0, "blue")
        with pytest.raises(DataValidationError):
            validate_lottery_number(17, "blue")
    
    def test_validate_red_balls_valid(self):
        """测试红球组合验证（有效）"""
        balls = [1, 5, 12, 18, 25, 30]
        assert validate_red_balls(balls) is True
    
    def test_validate_red_balls_invalid_count(self):
        """测试红球组合验证（数量错误）"""
        with pytest.raises(DataValidationError):
            validate_red_balls([1, 5, 12])  # 只有 3 个
    
    def test_validate_red_balls_invalid_duplicate(self):
        """测试红球组合验证（重复号码）"""
        with pytest.raises(DataValidationError):
            validate_red_balls([1, 5, 5, 18, 25, 30])  # 5 重复
    
    def test_validate_red_balls_invalid_unsorted(self):
        """测试红球组合验证（未排序）"""
        with pytest.raises(DataValidationError):
            validate_red_balls([5, 1, 12, 18, 25, 30])  # 未排序
    
    def test_validate_blue_balls_ssq(self):
        """测试双色球蓝球验证"""
        assert validate_blue_balls([9], play_type="ssq") is True
        
        with pytest.raises(DataValidationError):
            validate_blue_balls([9, 11], play_type="ssq")  # 双色球只要 1 个
    
    def test_validate_blue_balls_dlt(self):
        """测试大乐透蓝球验证"""
        assert validate_blue_balls([5, 11], play_type="dlt") is True
        
        with pytest.raises(DataValidationError):
            validate_blue_balls([5], play_type="dlt")  # 大乐透要 2 个
    
    def test_validate_data_frame(self, sample_data):
        """测试 DataFrame 验证"""
        required = ['期数', '红球_1', '红球_2', '蓝球']
        assert validate_data_frame(sample_data, required) is True
        
        invalid_required = ['期数', '不存在的列']
        with pytest.raises(DataValidationError):
            validate_data_frame(sample_data, invalid_required)
