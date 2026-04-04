# -*- coding: utf-8 -*-
"""
彩票业务异常定义（与 validators、services、tests 约定一致）
"""
from typing import Optional


class LotteryException(Exception):
    """彩票系统基础异常"""
    pass


class DataFetchError(LotteryException):
    """数据拉取失败"""

    def __init__(self, message: str = "", *, source: Optional[str] = None):
        self.source = source
        if not message and source is not None:
            message = f"数据获取失败: {source}"
        elif not message:
            message = "数据获取失败"
        super().__init__(message)


class DataValidationError(LotteryException):
    """数据或参数校验失败"""

    def __init__(self, message: str = "", *, field: Optional[str] = None):
        self.field = field
        if not message and field is not None:
            message = f"数据验证失败: {field}"
        elif not message:
            message = "数据验证失败"
        super().__init__(message)


class ModelLoadError(LotteryException):
    """模型加载失败"""

    def __init__(self, message: str = "", *, model_name: Optional[str] = None):
        self.model_name = model_name
        if not message:
            message = "模型加载失败"
        super().__init__(message)


class PredictionError(LotteryException):
    """预测过程失败"""

    def __init__(self, message: str = "", *, ball_type: Optional[str] = None):
        self.ball_type = ball_type
        if not message and ball_type is not None:
            message = f"预测失败: {ball_type}"
        elif not message:
            message = "预测失败"
        super().__init__(message)


class TrainingError(LotteryException):
    """训练过程失败"""
    pass
