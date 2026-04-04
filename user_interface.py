# -*- coding: utf-8 -*-
"""
改进的错误处理和用户提示模块
Author: BigCat
"""
import sys
import traceback
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from functools import wraps
from loguru import logger

# 使用统一的配置和工具模块
try:
    from config_new import config
except ImportError:
    from config import config

from utils.exceptions import (
    LotteryException as LotteryError,
    DataFetchError as DataError,
    PredictionError
)

# 兼容网络错误和验证错误
class NetworkError(LotteryError):
    """网络错误"""
    pass

class ValidationError(LotteryError):
    """验证错误"""
    pass

# 使用loguru作为日志记录器
logger = logger


class UserFriendlyError(Exception):
    """用户友好的错误类"""
    
    def __init__(self, message: str, error_code: str = None, 
                 suggestions: List[str] = None, technical_details: str = None):
        self.message = message
        self.error_code = error_code
        self.suggestions = suggestions or []
        self.technical_details = technical_details
        super().__init__(message)


class ErrorMessageFormatter:
    """错误信息格式化器"""
    
    @staticmethod
    def format_error(error: Exception, context: str = "") -> Dict[str, Any]:
        """格式化错误信息"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'message': str(error),
            'context': context,
            'user_message': '',
            'suggestions': [],
            'technical_details': '',
            'severity': 'error'
        }
        
        # 根据错误类型生成用户友好的信息
        if isinstance(error, UserFriendlyError):
            error_info['user_message'] = error.message
            error_info['suggestions'] = error.suggestions
            error_info['technical_details'] = error.technical_details or str(error)
            error_info['error_code'] = error.error_code
        
        elif isinstance(error, NetworkError):
            error_info['user_message'] = "网络连接出现问题，请检查网络设置"
            error_info['suggestions'] = [
                "检查网络连接是否正常",
                "确认代理设置是否正确",
                "稍后重试操作",
                "联系技术支持"
            ]
            error_info['technical_details'] = str(error)
            error_info['severity'] = 'warning'
        
        elif isinstance(error, DataError):
            error_info['user_message'] = "数据处理出现问题，请检查数据格式"
            error_info['suggestions'] = [
                "确认数据格式是否正确",
                "检查数据是否完整",
                "重新获取数据",
                "查看数据格式说明"
            ]
            error_info['technical_details'] = str(error)
            error_info['severity'] = 'warning'
        
        elif isinstance(error, ValidationError):
            error_info['user_message'] = "输入数据验证失败，请检查输入参数"
            error_info['suggestions'] = [
                "检查输入参数格式",
                "确认参数范围是否正确",
                "参考输入示例",
                "查看参数说明"
            ]
            error_info['technical_details'] = str(error)
        
        elif isinstance(error, FileNotFoundError):
            error_info['user_message'] = "文件未找到，请确认文件路径"
            error_info['suggestions'] = [
                "检查文件路径是否正确",
                "确认文件是否存在",
                "检查文件权限",
                "重新选择文件"
            ]
            error_info['technical_details'] = str(error)
        
        elif isinstance(error, PermissionError):
            error_info['user_message'] = "权限不足，请检查文件或目录权限"
            error_info['suggestions'] = [
                "以管理员身份运行",
                "检查文件权限设置",
                "更换保存路径",
                "联系系统管理员"
            ]
            error_info['technical_details'] = str(error)
        
        elif isinstance(error, MemoryError):
            error_info['user_message'] = "内存不足，请释放内存后重试"
            error_info['suggestions'] = [
                "关闭其他应用程序",
                "减少数据量",
                "重启应用程序",
                "增加系统内存"
            ]
            error_info['technical_details'] = str(error)
            error_info['severity'] = 'critical'
        
        elif isinstance(error, TimeoutError):
            error_info['user_message'] = "操作超时，请稍后重试"
            error_info['suggestions'] = [
                "稍后重试操作",
                "检查网络连接",
                "减少数据量",
                "联系技术支持"
            ]
            error_info['technical_details'] = str(error)
            error_info['severity'] = 'warning'
        
        else:
            # 未知错误
            error_info['user_message'] = "系统出现未知错误，请联系技术支持"
            error_info['suggestions'] = [
                "重启应用程序",
                "检查系统资源",
                "联系技术支持",
                "查看错误日志"
            ]
            error_info['technical_details'] = f"{type(error).__name__}: {str(error)}"
        
        return error_info


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.formatter = ErrorMessageFormatter()
        self.error_callbacks = {}
        self.error_history = []
    
    def register_callback(self, error_type: type, callback: Callable):
        """注册错误回调"""
        self.error_callbacks[error_type] = callback
    
    def handle_error(self, error: Exception, context: str = "", 
                    show_to_user: bool = True) -> Dict[str, Any]:
        """处理错误"""
        # 格式化错误信息
        error_info = self.formatter.format_error(error, context)
        
        # 记录错误
        self._log_error(error_info)
        
        # 保存到历史记录
        self.error_history.append(error_info)
        
        # 调用回调
        error_type = type(error)
        if error_type in self.error_callbacks:
            try:
                self.error_callbacks[error_type](error_info)
            except Exception as callback_error:
                logger.error(f"错误回调执行失败: {callback_error}")
        
        # 显示给用户
        if show_to_user:
            self._show_error_to_user(error_info)
        
        return error_info
    
    def _log_error(self, error_info: Dict[str, Any]):
        """记录错误日志"""
        log_level_map = {
            'critical': logger.critical,
            'error': logger.error,
            'warning': logger.warning,
            'info': logger.info
        }
        log_func = log_level_map.get(error_info.get('severity', 'error'), logger.error)

        log_message = f"[{error_info.get('error_code') or 'UNKNOWN'}] {error_info.get('user_message', '')}"

        if error_info.get('context'):
            log_message += f" (上下文: {error_info['context']})"

        log_func(log_message)

        if getattr(config, 'debug', False) and error_info.get('technical_details'):
            logger.debug(f"技术详情: {error_info['technical_details']}")
    
    def _show_error_to_user(self, error_info: Dict[str, Any]):
        """显示错误给用户"""
        # 这里可以根据不同的UI框架实现
        # 目前提供基本的控制台输出
        print(f"\n❌ {error_info['user_message']}")
        
        if error_info['suggestions']:
            print("💡 建议解决方案:")
            for i, suggestion in enumerate(error_info['suggestions'], 1):
                print(f"   {i}. {suggestion}")
        
        if getattr(config, 'debug', False) and error_info.get('technical_details'):
            print(f"🔧 技术详情: {error_info['technical_details']}")
        
        print()
    
    def get_error_summary(self, limit: int = 10) -> Dict[str, Any]:
        """获取错误摘要"""
        recent_errors = self.error_history[-limit:]
        
        if not recent_errors:
            return {
                'total_errors': 0,
                'recent_errors': [],
                'error_types': {},
                'severity_distribution': {}
            }
        
        # 统计错误类型
        error_types = {}
        severity_dist = {'critical': 0, 'error': 0, 'warning': 0, 'info': 0}
        
        for error in recent_errors:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
            severity_dist[error['severity']] += 1
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors': recent_errors,
            'error_types': error_types,
            'severity_distribution': severity_dist
        }


class UserNotifier:
    """用户通知器"""
    
    def __init__(self):
        self.notifications = []
    
    def show_info(self, message: str, title: str = "信息", duration: int = 3000):
        """显示信息通知"""
        notification = {
            'type': 'info',
            'title': title,
            'message': message,
            'timestamp': datetime.now(),
            'duration': duration
        }
        self.notifications.append(notification)
        self._display_notification(notification)
    
    def show_success(self, message: str, title: str = "成功", duration: int = 3000):
        """显示成功通知"""
        notification = {
            'type': 'success',
            'title': title,
            'message': message,
            'timestamp': datetime.now(),
            'duration': duration
        }
        self.notifications.append(notification)
        self._display_notification(notification)
    
    def show_warning(self, message: str, title: str = "警告", duration: int = 5000):
        """显示警告通知"""
        notification = {
            'type': 'warning',
            'title': title,
            'message': message,
            'timestamp': datetime.now(),
            'duration': duration
        }
        self.notifications.append(notification)
        self._display_notification(notification)
    
    def show_error(self, message: str, title: str = "错误", duration: int = 0):
        """显示错误通知"""
        notification = {
            'type': 'error',
            'title': title,
            'message': message,
            'timestamp': datetime.now(),
            'duration': duration  # 错误通知默认不自动消失
        }
        self.notifications.append(notification)
        self._display_notification(notification)
    
    def _display_notification(self, notification: Dict[str, Any]):
        """显示通知"""
        icons = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        }
        
        icon = icons.get(notification['type'], '📢')
        print(f"{icon} {notification['title']}: {notification['message']}")
    
    def get_recent_notifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的通知"""
        return self.notifications[-limit:]


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total_steps: int, description: str = ""):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = datetime.now()
        self.notifier = UserNotifier()
    
    def update(self, step: int = 1, message: str = ""):
        """更新进度"""
        self.current_step += step
        progress_percent = (self.current_step / self.total_steps) * 100
        
        if message:
            full_message = f"{self.description} - {message}"
        else:
            full_message = self.description
        
        progress_msg = f"进度: {self.current_step}/{self.total_steps} ({progress_percent:.1f}%)"
        
        if self.current_step >= self.total_steps:
            elapsed = datetime.now() - self.start_time
            self.notifier.show_success(f"{full_message} - 完成! 耗时: {elapsed.total_seconds():.2f}秒")
        else:
            print(f"⏳ {progress_msg} - {message}")
    
    def finish(self, message: str = "操作完成"):
        """完成进度"""
        self.current_step = self.total_steps
        elapsed = datetime.now() - self.start_time
        self.notifier.show_success(f"{self.description} - {message} (耗时: {elapsed.total_seconds():.2f}秒)")


# 全局实例
error_handler = ErrorHandler()
user_notifier = UserNotifier()


def handle_user_error(error: Exception, context: str = "", show_to_user: bool = True) -> Dict[str, Any]:
    """处理用户错误的便捷函数"""
    return error_handler.handle_error(error, context, show_to_user)


def user_friendly_error_handler(func):
    """用户友好的错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_info = handle_user_error(e, f"函数 {func.__name__} 执行")
            # 根据错误严重程度决定是否重新抛出
            if error_info['severity'] == 'critical':
                raise
            return None
    return wrapper


def show_progress(total_steps: int, description: str = "") -> ProgressTracker:
    """显示进度条的便捷函数"""
    return ProgressTracker(total_steps, description)


def show_info(message: str, title: str = "信息"):
    """显示信息通知的便捷函数"""
    user_notifier.show_info(message, title)


def show_success(message: str, title: str = "成功"):
    """显示成功通知的便捷函数"""
    user_notifier.show_success(message, title)


def show_warning(message: str, title: str = "警告"):
    """显示警告通知的便捷函数"""
    user_notifier.show_warning(message, title)


def show_error(message: str, title: str = "错误"):
    """显示错误通知的便捷函数"""
    user_notifier.show_error(message, title)


class UserFriendlyExceptions:
    """用户友好异常类集合"""
    
    class DataLoadError(UserFriendlyError):
        def __init__(self, message: str = "数据加载失败"):
            super().__init__(
                message=message,
                error_code="DATA_LOAD_001",
                suggestions=[
                    "检查网络连接",
                    "确认数据源地址正确",
                    "稍后重试",
                    "更换数据源"
                ]
            )
    
    class ModelTrainingError(UserFriendlyError):
        def __init__(self, message: str = "模型训练失败"):
            super().__init__(
                message=message,
                error_code="MODEL_TRAIN_001",
                suggestions=[
                    "检查训练数据是否充足",
                    "确认数据格式正确",
                    "调整模型参数",
                    "减少数据量后重试"
                ]
            )
    
    class PredictionError(UserFriendlyError):
        def __init__(self, message: str = "预测失败"):
            super().__init__(
                message=message,
                error_code="PREDICTION_001",
                suggestions=[
                    "检查模型是否已训练",
                    "确认输入数据格式",
                    "重新训练模型",
                    "使用其他预测策略"
                ]
            )
    
    class FileOperationError(UserFriendlyError):
        def __init__(self, message: str = "文件操作失败"):
            super().__init__(
                message=message,
                error_code="FILE_OP_001",
                suggestions=[
                    "检查文件路径是否正确",
                    "确认文件权限",
                    "检查磁盘空间",
                    "更换保存路径"
                ]
            )


if __name__ == "__main__":
    # 测试错误处理和用户提示
    print("=== 测试错误处理和用户提示 ===")
    
    # 测试不同类型的错误
    test_errors = [
        NetworkError("网络连接超时"),
        DataError("数据格式错误"),
        ValidationError("参数验证失败"),
        FileNotFoundError("文件不存在"),
        UserFriendlyExceptions.DataLoadError(),
        Exception("未知错误")
    ]
    
    for error in test_errors:
        print(f"\n测试错误: {type(error).__name__}")
        handle_user_error(error, "测试上下文")
    
    # 测试用户通知
    show_info("这是一条信息通知")
    show_success("操作成功完成")
    show_warning("请注意检查输入参数")
    show_error("发生了一个错误")
    
    # 测试进度跟踪
    progress = show_progress(5, "数据处理")
    for i in range(5):
        progress.update(1, f"处理第{i+1}步")
    
    # 测试装饰器
    @user_friendly_error_handler
    def test_function():
        raise ValueError("测试函数中的错误")
    
    print("\n测试装饰器:")
    result = test_function()
    print(f"函数返回结果: {result}")
    
    print("\n=== 测试完成 ===")
