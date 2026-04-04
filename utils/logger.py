# -*- coding: utf-8 -*-
"""
兼容层：历史代码使用 `from utils.logger import log, setup_logger`。
基于 loguru，避免重复实现 logging 配置。
"""
import sys
from loguru import logger

log = logger


def setup_logger(level: str = "INFO") -> None:
    """配置控制台输出；可重复调用以刷新级别。"""
    logger.remove()
    logger.add(
        sys.stderr,
        level=level.upper(),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
    )
