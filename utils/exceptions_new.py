# -*- coding: utf-8 -*-
"""
统一的异常处理模块
Author: BigCat
"""
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type, Union
from loguru import logger


class LotteryError(Exception):
    """彩票系统基础异常"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class DataError(LotteryError):
    """数据相关异常"""
    pass


class NetworkError(LotteryError):
    """网络相关异常"""
    pass


class ValidationError(LotteryError):
    """验证相关异常"""
    pass


class ConfigError(LotteryError):
    """配置相关异常"""
    pass


class StrategyError(LotteryError):
    """策略相关异常"""
    pass


class UIError(LotteryError):
    """UI相关异常"""
    pass


def handle_exceptions(
    exceptions: Union[Type[Exception], tuple] = Exception,
    default_return: Any = None,
    log_level: str = "ERROR",
    reraise: bool = False
):
    """
    异常处理装饰器
    
    Args:
        exceptions: 要捕获的异常类型
        default_return: 异常时的默认返回值
        log_level: 日志级别
        reraise: 是否重新抛出异常
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                # 记录日志
                log_msg = f"函数 {func.__name__} 执行失败: {str(e)}"
                if log_level.upper() == "DEBUG":
                    logger.debug(log_msg)
                elif log_level.upper() == "INFO":
                    logger.info(log_msg)
                elif log_level.upper() == "WARNING":
                    logger.warning(log_msg)
                elif log_level.upper() == "ERROR":
                    logger.error(log_msg)
                else:
                    logger.critical(log_msg)
                
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, default_return: Any = None, **kwargs) -> Any:
    """
    安全执行函数
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        default_return: 异常时的默认返回值
        **kwargs: 关键字参数
        
    Returns:
        函数执行结果或默认返回值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"安全执行函数 {func.__name__} 失败: {str(e)}")
        return default_return


class ExceptionHandler:
    """异常处理器"""
    
    def __init__(self):
        self.handlers = {}
    
    def register_handler(self, exception_type: Type[Exception], handler: Callable):
        """注册异常处理器"""
        self.handlers[exception_type] = handler
    
    def handle_exception(self, exception: Exception) -> Any:
        """处理异常"""
        exception_type = type(exception)
        if exception_type in self.handlers:
            return self.handlers[exception_type](exception)
        
        # 查找父类处理器
        for exc_type, handler in self.handlers.items():
            if issubclass(exception_type, exc_type):
                return handler(exception)
        
        # 默认处理
        logger.error(f"未处理的异常: {type(exception).__name__}: {str(exception)}")
        return None


# 全局异常处理器
global_exception_handler = ExceptionHandler()

# 注册默认处理器
def handle_network_error(exception: NetworkError) -> str:
    """处理网络错误"""
    return f"网络错误: {exception.message}"

def handle_data_error(exception: DataError) -> str:
    """处理数据错误"""
    return f"数据错误: {exception.message}"

def handle_validation_error(exception: ValidationError) -> str:
    """处理验证错误"""
    return f"验证错误: {exception.message}"

global_exception_handler.register_handler(NetworkError, handle_network_error)
global_exception_handler.register_handler(DataError, handle_data_error)
global_exception_handler.register_handler(ValidationError, handle_validation_error)


def setup_global_exception_handler():
    """设置全局异常处理器"""
    import sys
    
    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical(
            "未捕获的异常",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_unhandled_exception


# 初始化全局异常处理器
setup_global_exception_handler()
