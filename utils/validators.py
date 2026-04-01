# -*- coding:utf-8 -*-
"""
验证工具模块
"""
from typing import List, Optional
from utils.exceptions import DataValidationError


def validate_lottery_number(number: int, ball_type: str = "red") -> bool:
    """
    验证彩票号码是否有效
    
    Args:
        number: 要验证的号码
        ball_type: 球类型 (red/blue)
    
    Returns:
        是否有效
    
    Raises:
        DataValidationError: 无效号码
    """
    if ball_type == "red":
        if not (1 <= number <= 33):
            raise DataValidationError(f"红球号码必须在 1-33 之间", field=f"red_ball={number}")
    elif ball_type == "blue":
        if not (1 <= number <= 16):
            raise DataValidationError(f"蓝球号码必须在 1-16 之间", field=f"blue_ball={number}")
    else:
        raise DataValidationError(f"未知的球类型：{ball_type}", field="ball_type")
    
    return True


def validate_red_balls(numbers: List[int]) -> bool:
    """
    验证红球组合是否有效
    
    Args:
        numbers: 红球号码列表
    
    Returns:
        是否有效
    
    Raises:
        DataValidationError: 无效组合
    """
    if len(numbers) != 6:
        raise DataValidationError(f"红球必须是 6 个", field=f"count={len(numbers)}")
    
    for num in numbers:
        validate_lottery_number(num, "red")
    
    # 检查是否有重复
    if len(numbers) != len(set(numbers)):
        raise DataValidationError("红球号码不能重复", field="duplicate_numbers")
    
    # 检查是否按顺序排列
    if numbers != sorted(numbers):
        raise DataValidationError("红球号码必须按从小到大排序", field="not_sorted")
    
    return True


def validate_blue_balls(numbers: List[int], play_type: str = "ssq") -> bool:
    """
    验证蓝球组合是否有效
    
    Args:
        numbers: 蓝球号码列表
        play_type: 玩法类型 (ssq/dlt)
    
    Returns:
        是否有效
    
    Raises:
        DataValidationError: 无效组合
    """
    if play_type == "ssq":
        expected_count = 1
        max_num = 16
    elif play_type == "dlt":
        expected_count = 2
        max_num = 12
    else:
        raise DataValidationError(f"未知的玩法类型：{play_type}", field="play_type")
    
    if len(numbers) != expected_count:
        raise DataValidationError(f"{play_type}蓝球必须是{expected_count}个", field=f"count={len(numbers)}")
    
    for num in numbers:
        if not (1 <= num <= max_num):
            raise DataValidationError(f"蓝球号码必须在 1-{max_num} 之间", field=f"blue_ball={num}")
    
    return True


def validate_data_frame(df, required_columns: List[str]) -> bool:
    """
    验证 DataFrame 是否包含必需的列
    
    Args:
        df: pandas DataFrame
        required_columns: 必需的列名列表
    
    Returns:
        是否有效
    
    Raises:
        DataValidationError: 缺少必需列
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise DataValidationError(
            f"数据缺少必需的列：{missing_columns}",
            field="missing_columns"
        )
    return True


def validate_file_path(file_path: str, must_exist: bool = True) -> bool:
    """
    验证文件路径是否有效
    
    Args:
        file_path: 文件路径
        must_exist: 文件是否必须存在
    
    Returns:
        是否有效
    
    Raises:
        DataValidationError: 路径无效
    """
    from pathlib import Path
    path = Path(file_path)
    
    if must_exist and not path.exists():
        raise DataValidationError(f"文件不存在", field=file_path)
    
    if not must_exist:
        # 检查父目录是否存在
        parent = path.parent
        if not parent.exists():
            raise DataValidationError(f"父目录不存在", field=str(parent))
    
    return True
