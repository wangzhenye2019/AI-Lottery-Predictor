# -*- coding:utf-8 -*-
"""
自定义异常类
"""


class LotteryException(Exception):
    """彩票系统基础异常类"""
    pass


class DataFetchError(LotteryException):
    """数据获取失败异常"""
    def __init__(self, message="数据获取失败", source=None):
        self.source = source
        super().__init__(f"{message}: {source}" if source else message)


class DataValidationError(LotteryException):
    """数据验证失败异常"""
    def __init__(self, message="数据验证失败", field=None):
        self.field = field
        super().__init__(f"{message}: {field}" if field else message)


class ModelLoadError(LotteryException):
    """模型加载失败异常"""
    def __init__(self, message="模型加载失败", model_name=None):
        self.model_name = model_name
        super().__init__(f"{message}: {model_name}" if model_name else message)


class ModelSaveError(LotteryException):
    """模型保存失败异常"""
    def __init__(self, message="模型保存失败", model_name=None):
        self.model_name = model_name
        super().__init__(f"{message}: {model_name}" if model_name else message)


class TrainingError(LotteryException):
    """训练失败异常"""
    def __init__(self, message="训练失败", stage=None):
        self.stage = stage
        super().__init__(f"{message} - 阶段：{stage}" if stage else message)


class PredictionError(LotteryException):
    """预测失败异常"""
    def __init__(self, message="预测失败", ball_type=None):
        self.ball_type = ball_type
        super().__init__(f"{message} - 类型：{ball_type}" if ball_type else message)


class StrategyError(LotteryException):
    """策略分析失败异常"""
    def __init__(self, message="策略分析失败", strategy_name=None):
        self.strategy_name = strategy_name
        super().__init__(f"{message} - 策略：{strategy_name}" if strategy_name else message)


class ConfigError(LotteryException):
    """配置错误异常"""
    def __init__(self, message="配置错误", config_key=None):
        self.config_key = config_key
        super().__init__(f"{message}: {config_key}" if config_key else message)


class FileError(LotteryException):
    """文件操作失败异常"""
    def __init__(self, message="文件操作失败", file_path=None):
        self.file_path = file_path
        super().__init__(f"{message}: {file_path}" if file_path else message)
