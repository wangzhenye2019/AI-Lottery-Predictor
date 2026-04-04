# -*- coding: utf-8 -*-
"""
性能监控和优化模块
Author: BigCat
"""
import time
import psutil
import threading
from typing import Dict, Any, Optional, Callable
from functools import wraps
from collections import defaultdict, deque
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from utils.logger_new import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time: float
    memory_usage: float
    cpu_usage: float
    call_count: int = 1
    avg_time: float = field(init=False)
    
    def __post_init__(self):
        self.avg_time = self.execution_time


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.call_counts: Dict[str, int] = defaultdict(int)
        self.start_times: Dict[str, float] = {}
        self.lock = threading.Lock()
    
    def start_timing(self, name: str):
        """开始计时"""
        with self.lock:
            self.start_times[name] = time.time()
    
    def end_timing(self, name: str) -> float:
        """结束计时"""
        end_time = time.time()
        with self.lock:
            if name in self.start_times:
                execution_time = end_time - self.start_times[name]
                del self.start_times[name]
                
                # 记录系统资源使用情况
                process = psutil.Process()
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                cpu_usage = process.cpu_percent()
                
                # 创建性能指标
                metrics = PerformanceMetrics(
                    execution_time=execution_time,
                    memory_usage=memory_usage,
                    cpu_usage=cpu_usage
                )
                
                self.metrics[name].append(metrics)
                self.call_counts[name] += 1
                
                return execution_time
        return 0.0
    
    def get_metrics(self, name: str) -> Optional[Dict[str, Any]]:
        """获取性能指标"""
        with self.lock:
            if name not in self.metrics or not self.metrics[name]:
                return None
            
            metrics_list = list(self.metrics[name])
            latest = metrics_list[-1]
            
            # 计算统计信息
            execution_times = [m.execution_time for m in metrics_list]
            memory_usages = [m.memory_usage for m in metrics_list]
            cpu_usages = [m.cpu_usage for m in metrics_list]
            
            return {
                'name': name,
                'call_count': self.call_counts[name],
                'latest': {
                    'execution_time': latest.execution_time,
                    'memory_usage': latest.memory_usage,
                    'cpu_usage': latest.cpu_usage,
                },
                'statistics': {
                    'avg_execution_time': sum(execution_times) / len(execution_times),
                    'min_execution_time': min(execution_times),
                    'max_execution_time': max(execution_times),
                    'avg_memory_usage': sum(memory_usages) / len(memory_usages),
                    'max_memory_usage': max(memory_usages),
                    'avg_cpu_usage': sum(cpu_usages) / len(cpu_usages),
                    'max_cpu_usage': max(cpu_usages),
                }
            }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有性能指标"""
        with self.lock:
            return {name: self.get_metrics(name) for name in self.metrics.keys()}
    
    def clear_metrics(self, name: str = None):
        """清除性能指标"""
        with self.lock:
            if name:
                if name in self.metrics:
                    self.metrics[name].clear()
                if name in self.call_counts:
                    del self.call_counts[name]
            else:
                self.metrics.clear()
                self.call_counts.clear()
                self.start_times.clear()


# 全局性能监控器
performance_monitor = PerformanceMonitor()


def monitor_performance(name: str = None):
    """性能监控装饰器"""
    def decorator(func: Callable) -> Callable:
        func_name = name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            performance_monitor.start_timing(func_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = performance_monitor.end_timing(func_name)
                if execution_time > 1.0:  # 超过1秒记录警告
                    logger.warning(f"函数 {func_name} 执行时间过长: {execution_time:.3f}s")
        return wrapper
    return decorator


def monitor_async_performance(name: str = None):
    """异步性能监控装饰器"""
    def decorator(func: Callable) -> Callable:
        func_name = name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            performance_monitor.start_timing(func_name)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                execution_time = performance_monitor.end_timing(func_name)
                if execution_time > 1.0:
                    logger.warning(f"异步函数 {func_name} 执行时间过长: {execution_time:.3f}s")
        return wrapper
    return decorator


class MemoryProfiler:
    """内存分析器"""
    
    def __init__(self):
        self.snapshots = []
    
    def take_snapshot(self, name: str = None):
        """拍摄内存快照"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        snapshot = {
            'name': name or datetime.now().isoformat(),
            'timestamp': datetime.now(),
            'rss': memory_info.rss,  # 物理内存
            'vms': memory_info.vms,  # 虚拟内存
            'percent': process.memory_percent(),
        }
        
        self.snapshots.append(snapshot)
        logger.debug(f"内存快照: {snapshot['name']} - RSS: {snapshot['rss']/1024/1024:.2f}MB")
        
        return snapshot
    
    def get_memory_trend(self) -> Dict[str, Any]:
        """获取内存趋势"""
        if len(self.snapshots) < 2:
            return {}
        
        first = self.snapshots[0]
        latest = self.snapshots[-1]
        
        rss_diff = latest['rss'] - first['rss']
        percent_diff = latest['percent'] - first['percent']
        
        return {
            'initial_rss': first['rss'] / 1024 / 1024,  # MB
            'current_rss': latest['rss'] / 1024 / 1024,  # MB
            'rss_diff': rss_diff / 1024 / 1024,  # MB
            'initial_percent': first['percent'],
            'current_percent': latest['percent'],
            'percent_diff': percent_diff,
            'snapshots_count': len(self.snapshots),
        }
    
    def clear_snapshots(self):
        """清除快照"""
        self.snapshots.clear()


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.monitoring = False
        self.thread = None
        self.data = deque(maxlen=3600)  # 1小时的数据
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("资源监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("资源监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 收集系统资源信息
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                data_point = {
                    'timestamp': datetime.now(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used': memory.used / 1024 / 1024 / 1024,  # GB
                    'memory_total': memory.total / 1024 / 1024 / 1024,  # GB
                    'disk_percent': disk.percent,
                    'disk_used': disk.used / 1024 / 1024 / 1024,  # GB
                    'disk_total': disk.total / 1024 / 1024 / 1024,  # GB
                }
                
                self.data.append(data_point)
                
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"资源监控错误: {e}")
                time.sleep(self.interval)
    
    def get_current_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        if not self.data:
            return {}
        
        latest = self.data[-1]
        return {
            'cpu_percent': latest['cpu_percent'],
            'memory_percent': latest['memory_percent'],
            'memory_used_gb': latest['memory_used'],
            'disk_percent': latest['disk_percent'],
            'disk_used_gb': latest['disk_used'],
            'timestamp': latest['timestamp'],
        }
    
    def get_resource_history(self, minutes: int = 10) -> Dict[str, list]:
        """获取资源历史"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        filtered_data = [
            point for point in self.data 
            if point['timestamp'] >= cutoff_time
        ]
        
        if not filtered_data:
            return {}
        
        return {
            'timestamps': [point['timestamp'] for point in filtered_data],
            'cpu_percent': [point['cpu_percent'] for point in filtered_data],
            'memory_percent': [point['memory_percent'] for point in filtered_data],
            'disk_percent': [point['disk_percent'] for point in filtered_data],
        }


# 全局资源监控器
resource_monitor = ResourceMonitor()


class OptimizationSuggestions:
    """优化建议"""
    
    @staticmethod
    def analyze_performance(metrics: Dict[str, Any]) -> list:
        """分析性能并提供建议"""
        suggestions = []
        
        if not metrics:
            return suggestions
        
        # 分析执行时间
        stats = metrics.get('statistics', {})
        avg_time = stats.get('avg_execution_time', 0)
        max_time = stats.get('max_execution_time', 0)
        
        if avg_time > 2.0:
            suggestions.append(f"平均执行时间过长 ({avg_time:.3f}s)，建议优化算法逻辑")
        
        if max_time > 5.0:
            suggestions.append(f"最大执行时间过长 ({max_time:.3f}s)，建议检查是否有阻塞操作")
        
        # 分析内存使用
        avg_memory = stats.get('avg_memory_usage', 0)
        max_memory = stats.get('max_memory_usage', 0)
        
        if avg_memory > 500:  # 500MB
            suggestions.append(f"平均内存使用较高 ({avg_memory:.2f}MB)，建议检查内存泄漏")
        
        if max_memory > 1000:  # 1GB
            suggestions.append(f"峰值内存使用过高 ({max_memory:.2f}MB)，建议优化数据结构")
        
        # 分析调用次数
        call_count = metrics.get('call_count', 0)
        if call_count > 1000 and avg_time > 0.1:
            suggestions.append(f"频繁调用 ({call_count}次) 且耗时较长，建议添加缓存")
        
        return suggestions
    
    @staticmethod
    def analyze_system_resources(status: Dict[str, Any]) -> list:
        """分析系统资源并提供建议"""
        suggestions = []
        
        if not status:
            return suggestions
        
        cpu_percent = status.get('cpu_percent', 0)
        memory_percent = status.get('memory_percent', 0)
        disk_percent = status.get('disk_percent', 0)
        
        if cpu_percent > 80:
            suggestions.append(f"CPU使用率过高 ({cpu_percent:.1f}%)，建议检查CPU密集型操作")
        
        if memory_percent > 80:
            suggestions.append(f"内存使用率过高 ({memory_percent:.1f}%)，建议释放不必要的内存")
        
        if disk_percent > 90:
            suggestions.append(f"磁盘使用率过高 ({disk_percent:.1f}%)，建议清理临时文件")
        
        return suggestions


# 全局实例
memory_profiler = MemoryProfiler()
optimization_suggestions = OptimizationSuggestions()


def start_performance_monitoring():
    """启动性能监控"""
    resource_monitor.start_monitoring()
    logger.info("性能监控系统已启动")


def stop_performance_monitoring():
    """停止性能监控"""
    resource_monitor.stop_monitoring()
    logger.info("性能监控系统已停止")


def get_performance_report() -> Dict[str, Any]:
    """获取性能报告"""
    return {
        'function_metrics': performance_monitor.get_all_metrics(),
        'memory_trend': memory_profiler.get_memory_trend(),
        'system_status': resource_monitor.get_current_status(),
        'resource_history': resource_monitor.get_resource_history(),
    }
