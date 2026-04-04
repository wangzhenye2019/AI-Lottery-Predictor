#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用状态管理器 - 管理全局状态和用户交互
Author: BigCat
"""
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import threading
from loguru import logger


class AppStatus(Enum):
    """应用状态枚举"""
    IDLE = auto()           # 空闲
    INITIALIZING = auto()   # 初始化中
    LOADING_DATA = auto()   # 加载数据中
    TRAINING = auto()       # 训练中
    PREDICTING = auto()     # 预测中
    ANALYZING = auto()      # 分析中
    EXPORTING = auto()      # 导出中
    ERROR = auto()          # 错误状态


@dataclass
class PredictionResult:
    """预测结果数据类"""
    red_balls: List[int] = field(default_factory=list)
    blue_balls: List[int] = field(default_factory=list)
    confidence: float = 0.0
    strategy: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    issue_number: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'red_balls': self.red_balls,
            'blue_balls': self.blue_balls,
            'confidence': self.confidence,
            'strategy': self.strategy,
            'timestamp': self.timestamp.isoformat(),
            'issue_number': self.issue_number
        }


class AppStateManager:
    """
    应用状态管理器 - 单例模式
    管理全局状态、用户操作历史和通知
    """
    _instance: Optional['AppStateManager'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'AppStateManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._status = AppStatus.IDLE
        self._status_callbacks: List[Callable[[AppStatus], None]] = []
        self._progress_callbacks: List[Callable[[float, str], None]] = []
        self._notification_callbacks: List[Callable[[str, str, str], None]] = []

        # 当前状态数据
        self.current_lottery_type: str = "ssq"
        self.current_strategy: str = "XGBoost梯度提升"
        self.last_prediction: Optional[PredictionResult] = None
        self.prediction_history: List[PredictionResult] = []

        # 性能统计
        self._operation_stats: Dict[str, Dict[str, Any]] = {}

        self._initialized = True
        logger.debug("AppStateManager 初始化完成")

    @property
    def status(self) -> AppStatus:
        """获取当前状态"""
        return self._status

    @status.setter
    def status(self, new_status: AppStatus):
        """设置状态并触发回调"""
        if self._status != new_status:
            old_status = self._status
            self._status = new_status
            logger.debug(f"状态变更: {old_status.name} -> {new_status.name}")

            # 触发回调
            for callback in self._status_callbacks:
                try:
                    callback(new_status)
                except Exception as e:
                    logger.error(f"状态回调执行失败: {e}")

    def on_status_change(self, callback: Callable[[AppStatus], None]):
        """注册状态变更回调"""
        self._status_callbacks.append(callback)
        return callback

    def on_progress_update(self, callback: Callable[[float, str], None]):
        """注册进度更新回调"""
        self._progress_callbacks.append(callback)
        return callback

    def on_notification(self, callback: Callable[[str, str, str], None]):
        """注册通知回调"""
        self._notification_callbacks.append(callback)
        return callback

    def update_progress(self, progress: float, message: str = ""):
        """更新进度"""
        progress = max(0.0, min(1.0, progress))
        for callback in self._progress_callbacks:
            try:
                callback(progress, message)
            except Exception as e:
                logger.error(f"进度回调执行失败: {e}")

    def notify(self, message: str, title: str = "通知", level: str = "info"):
        """发送通知"""
        logger.info(f"[{level}] {title}: {message}")
        for callback in self._notification_callbacks:
            try:
                callback(message, title, level)
            except Exception as e:
                logger.error(f"通知回调执行失败: {e}")

    def notify_success(self, message: str, title: str = "成功"):
        """发送成功通知"""
        self.notify(message, title, "success")

    def notify_warning(self, message: str, title: str = "警告"):
        """发送警告通知"""
        self.notify(message, title, "warning")

    def notify_error(self, message: str, title: str = "错误"):
        """发送错误通知"""
        self.notify(message, title, "error")

    def record_prediction(self, result: PredictionResult):
        """记录预测结果"""
        self.last_prediction = result
        self.prediction_history.append(result)

        # 限制历史记录数量
        if len(self.prediction_history) > 100:
            self.prediction_history = self.prediction_history[-100:]

        logger.info(f"预测结果已记录: {result.to_dict()}")

    def get_prediction_history(self, limit: int = 10) -> List[PredictionResult]:
        """获取预测历史"""
        return self.prediction_history[-limit:]

    def record_operation_time(self, operation: str, duration_ms: float):
        """记录操作耗时"""
        if operation not in self._operation_stats:
            self._operation_stats[operation] = {
                'count': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf')
            }

        stats = self._operation_stats[operation]
        stats['count'] += 1
        stats['total_time'] += duration_ms
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['max_time'] = max(stats['max_time'], duration_ms)
        stats['min_time'] = min(stats['min_time'], duration_ms)

    def get_operation_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取操作统计"""
        return self._operation_stats.copy()

    def is_busy(self) -> bool:
        """检查是否正在处理中"""
        return self._status in [
            AppStatus.INITIALIZING,
            AppStatus.LOADING_DATA,
            AppStatus.TRAINING,
            AppStatus.PREDICTING,
            AppStatus.ANALYZING,
            AppStatus.EXPORTING
        ]

    def can_start_operation(self) -> bool:
        """检查是否可以开始新操作"""
        return self._status == AppStatus.IDLE

    def reset(self):
        """重置状态"""
        self._status = AppStatus.IDLE
        self.current_lottery_type = "ssq"
        self.current_strategy = "XGBoost梯度提升"
        logger.debug("AppStateManager 已重置")


# 全局状态管理器实例
app_state = AppStateManager()


class OperationContext:
    """操作上下文管理器 - 用于简化状态管理"""

    def __init__(self, operation_name: str, status: AppStatus,
                 progress_callback: Optional[Callable] = None):
        self.operation_name = operation_name
        self.status = status
        self.progress_callback = progress_callback
        self.start_time: Optional[datetime] = None

    def __enter__(self):
        """进入上下文"""
        if not app_state.can_start_operation():
            raise RuntimeError(f"无法开始操作 '{self.operation_name}': 当前状态为 {app_state.status.name}")

        self.start_time = datetime.now()
        app_state.status = self.status
        logger.info(f"开始操作: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        duration = (datetime.now() - self.start_time).total_seconds() * 1000

        if exc_type is None:
            app_state.status = AppStatus.IDLE
            app_state.record_operation_time(self.operation_name, duration)
            logger.info(f"操作完成: {self.operation_name} (耗时: {duration:.2f}ms)")
        else:
            app_state.status = AppStatus.ERROR
            logger.error(f"操作失败: {self.operation_name} (耗时: {duration:.2f}ms) - {exc_val}")

        return False  # 不抑制异常

    def update_progress(self, progress: float, message: str = ""):
        """更新进度"""
        app_state.update_progress(progress, message)
        if self.progress_callback:
            self.progress_callback(progress, message)


# 便捷函数
def with_operation(operation_name: str, status: AppStatus):
    """操作装饰器工厂"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with OperationContext(operation_name, status):
                return func(*args, **kwargs)
        return wrapper
    return decorator
