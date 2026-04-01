# -*- coding:utf-8 -*-
"""
日志配置模块
"""
import sys
from loguru import logger


def setup_logger(log_file=None, level="INFO"):
    """
    配置日志
    
    Args:
        log_file: 日志文件路径，None 表示仅输出到控制台
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        配置后的 logger 实例
    """
    # 移除默认的处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 添加文件输出（如果指定了文件）
    if log_file:
        logger.add(
            log_file,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="7 days",
            compression="zip"
        )
    
    return logger


# 创建全局 logger 实例
log = setup_logger()
