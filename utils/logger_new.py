# -*- coding: utf-8 -*-
"""
统一的日志管理模块
Author: BigCat
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from config_new import config


class LogManager:
    """日志管理器"""
    
    def __init__(self):
        self.log_dir = Path(config.data_dir) / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志"""
        # 移除默认处理器
        logger.remove()
        
        # 控制台输出
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level=config.log_level,
            colorize=True
        )
        
        # 文件输出 - 所有日志
        logger.add(
            self.log_dir / "lottery_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="00:00",
            retention="30 days",
            compression="zip",
            encoding="utf-8"
        )
        
        # 文件输出 - 错误日志
        logger.add(
            self.log_dir / "error_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="ERROR",
            rotation="00:00",
            retention="30 days",
            compression="zip",
            encoding="utf-8"
        )
        
        # 如果是调试模式，添加详细日志
        if config.debug:
            logger.add(
                self.log_dir / "debug_{time:YYYY-MM-DD}.log",
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
                level="TRACE",
                rotation="100 MB",
                retention="7 days",
                compression="zip",
                encoding="utf-8"
            )
    
    def get_logger(self, name: Optional[str] = None) -> Any:
        """获取日志记录器"""
        if name:
            return logger.bind(name=name)
        return logger
    
    def log_function_call(self, func_name: str, args: tuple = (), kwargs: dict = None):
        """记录函数调用"""
        kwargs = kwargs or {}
        logger.debug(f"调用函数 {func_name}, args={args}, kwargs={kwargs}")
    
    def log_function_result(self, func_name: str, result: Any = None, execution_time: float = None):
        """记录函数结果"""
        msg = f"函数 {func_name} 执行完成"
        if execution_time is not None:
            msg += f", 耗时: {execution_time:.3f}s"
        if result is not None:
            msg += f", 结果: {result}"
        logger.debug(msg)
    
    def log_error(self, error: Exception, context: str = ""):
        """记录错误"""
        msg = f"错误: {type(error).__name__}: {str(error)}"
        if context:
            msg = f"{context} - {msg}"
        logger.error(msg, exc_info=True)
    
    def log_network_request(self, method: str, url: str, status_code: int = None, response_time: float = None):
        """记录网络请求"""
        msg = f"网络请求: {method} {url}"
        if status_code:
            msg += f" - 状态码: {status_code}"
        if response_time:
            msg += f" - 响应时间: {response_time:.3f}s"
        logger.info(msg)
    
    def log_data_operation(self, operation: str, table: str, count: int = None, execution_time: float = None):
        """记录数据操作"""
        msg = f"数据操作: {operation} {table}"
        if count is not None:
            msg += f" - 影响行数: {count}"
        if execution_time is not None:
            msg += f" - 耗时: {execution_time:.3f}s"
        logger.info(msg)
    
    def log_strategy_execution(self, strategy_name: str, lottery_type: str, result_count: int = None, execution_time: float = None):
        """记录策略执行"""
        msg = f"策略执行: {strategy_name} - {lottery_type}"
        if result_count is not None:
            msg += f" - 结果数量: {result_count}"
        if execution_time is not None:
            msg += f" - 耗时: {execution_time:.3f}s"
        logger.info(msg)


# 全局日志管理器实例
log_manager = LogManager()

# 便捷函数
def get_logger(name: Optional[str] = None) -> Any:
    """获取日志记录器"""
    return log_manager.get_logger(name)


def setup_logging(level: str = None):
    """重新设置日志级别"""
    if level:
        config.log_level = level.upper()
    log_manager._setup_logger()


def log_performance(func):
    """性能日志装饰器"""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            log_manager.log_function_result(func.__name__, result, execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            log_manager.log_error(e, f"函数 {func.__name__} 执行失败 (耗时: {execution_time:.3f}s)")
            raise
    
    return wrapper


def log_method_calls(cls):
    """类方法调用日志装饰器"""
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and not attr_name.startswith('_'):
            setattr(cls, attr_name, log_performance(attr))
    return cls
