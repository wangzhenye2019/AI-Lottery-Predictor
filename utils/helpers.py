# -*- coding:utf-8 -*-
"""
辅助函数模块
"""
import os
from pathlib import Path
from typing import Union


def ensure_dir(dir_path: Union[str, Path]) -> None:
    """
    确保目录存在，不存在则创建
    
    Args:
        dir_path: 目录路径
    """
    path = Path(dir_path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    安全除法，避免除零错误
    
    Args:
        a: 被除数
        b: 除数
        default: 除零时的默认返回值
    
    Returns:
        除法结果或默认值
    """
    return a / b if b != 0 else default


def format_number(num: float, decimals: int = 2) -> str:
    """
    格式化数字显示
    
    Args:
        num: 要格式化的数字
        decimals: 小数位数
    
    Returns:
        格式化后的字符串
    """
    return f"{num:.{decimals}f}"


def validate_range(value: int, min_val: int, max_val: int, name: str = "值") -> bool:
    """
    验证值是否在范围内
    
    Args:
        value: 要验证的值
        min_val: 最小值
        max_val: 最大值
        name: 值的名称（用于错误提示）
    
    Returns:
        是否在范围内
    
    Raises:
        ValueError: 超出范围时抛出
    """
    if not (min_val <= value <= max_val):
        raise ValueError(f"{name}必须在 {min_val}-{max_val} 之间，当前值：{value}")
    return True


def get_project_root() -> Path:
    """
    获取项目根目录
    
    Returns:
        项目根目录的 Path 对象
    """
    return Path(__file__).parent.parent


def join_path(*args) -> str:
    """
    安全的跨平台路径拼接
    
    Args:
        *args: 路径片段
    
    Returns:
        拼接后的完整路径
    """
    return str(Path(*args))


def file_exists(file_path: str) -> bool:
    """
    检查文件是否存在
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件是否存在
    """
    return Path(file_path).exists()


def read_file_lines(file_path: str, encoding: str = 'utf-8') -> list:
    """
    读取文件所有行
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
    
    Returns:
        包含所有行的列表
    """
    with open(file_path, 'r', encoding=encoding) as f:
        return f.readlines()


def write_to_file(content: str, file_path: str, encoding: str = 'utf-8') -> None:
    """
    写入内容到文件
    
    Args:
        content: 要写入的内容
        file_path: 文件路径
        encoding: 文件编码
    """
    ensure_dir(Path(file_path).parent)
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(content)
