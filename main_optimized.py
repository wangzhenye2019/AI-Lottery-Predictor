#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化后的主入口 - AI智能彩票预测系统
整合配置管理、错误处理和用户体验优化
Author: BigCat
"""
import sys
import os
import threading
import traceback
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger

# ========================================================================
# 统一配置管理
# ========================================================================

@dataclass
class AppConfig:
    """应用配置类"""
    # 基础配置
    debug: bool = False
    log_level: str = "INFO"
    data_dir: str = "data"
    output_dir: str = "outputs"

    # UI配置
    theme: str = "light"
    window_width: int = 1200
    window_height: int = 800
    min_width: int = 1000
    min_height: int = 700

    # 预测配置
    default_lottery_type: str = "ssq"
    default_strategy: str = "XGBoost梯度提升"

    # 试用配置
    trial_limit: int = 10

    def __post_init__(self):
        """初始化后创建必要目录"""
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


class ConfigManager:
    """配置管理器 - 单例模式"""
    _instance: Optional['ConfigManager'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config = AppConfig()
        self._load_env_config()
        self._setup_logging()
        self._initialized = True
        logger.info("配置管理器初始化完成")

    def _load_env_config(self):
        """从环境变量加载配置"""
        env_mapping = {
            'LOTTERY_DEBUG': ('debug', lambda x: x.lower() in ('true', '1', 'yes')),
            'LOTTERY_LOG_LEVEL': ('log_level', str),
            'LOTTERY_DATA_DIR': ('data_dir', str),
            'LOTTERY_THEME': ('theme', str),
        }

        for env_var, (attr, converter) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    setattr(self.config, attr, converter(value))
                    logger.debug(f"从环境变量加载配置: {env_var}={value}")
                except Exception as e:
                    logger.warning(f"环境变量 {env_var} 解析失败: {e}")

    def _setup_logging(self):
        """配置日志系统"""
        logger.remove()

        # 控制台输出
        logger.add(
            sys.stderr,
            level=self.config.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )

        # 文件输出
        log_dir = Path(self.config.data_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_dir / "lottery_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="30 days",
            encoding="utf-8",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}"
        )

    def get_config(self) -> AppConfig:
        """获取配置对象"""
        return self.config


# 全局配置实例
config_manager = ConfigManager()
app_config = config_manager.get_config()


# ========================================================================
# 应用生命周期管理
# ========================================================================

class AppLifecycle:
    """应用生命周期管理器"""

    def __init__(self):
        self.initialized = False
        self._cleanup_callbacks: list = []
        self._startup_callbacks: list = []

    def on_startup(self, callback: Callable):
        """注册启动回调"""
        self._startup_callbacks.append(callback)
        return callback

    def on_cleanup(self, callback: Callable):
        """注册清理回调"""
        self._cleanup_callbacks.append(callback)
        return callback

    def startup(self):
        """应用启动"""
        logger.info("=" * 50)
        logger.info("🚀 AI智能彩票预测系统启动")
        logger.info("=" * 50)

        try:
            # 检查GPU可用性
            self._check_gpu()

            # 检查数据目录
            self._check_data_dirs()

            # 执行启动回调
            for callback in self._startup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"启动回调执行失败: {e}")

            self.initialized = True
            logger.info("✅ 应用初始化完成")

        except Exception as e:
            logger.error(f"❌ 应用启动失败: {e}")
            raise

    def cleanup(self):
        """应用清理"""
        logger.info("🧹 应用清理中...")

        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"清理回调执行失败: {e}")

        logger.info("✅ 应用已安全关闭")

    def _check_gpu(self):
        """检查GPU可用性"""
        try:
            import tensorflow as tf
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                logger.info(f"✅ GPU可用: {len(gpus)}个设备")
                for gpu in gpus:
                    logger.info(f"   - {gpu}")
            else:
                logger.warning("⚠️ 未检测到GPU，将使用CPU进行计算")
        except ImportError:
            logger.warning("⚠️ TensorFlow未安装")
        except Exception as e:
            logger.warning(f"⚠️ GPU检查失败: {e}")

    def _check_data_dirs(self):
        """检查数据目录"""
        required_dirs = [
            app_config.data_dir,
            app_config.output_dir,
            f"{app_config.data_dir}/models",
            f"{app_config.data_dir}/logs",
        ]

        for dir_path in required_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 检查目录: {dir_path}")


# ========================================================================
# 错误处理装饰器
# ========================================================================

def handle_errors(context: str = "", reraise: bool = False):
    """错误处理装饰器工厂"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"[{context}] {func.__name__} 执行失败: {e}"
                logger.error(error_msg)
                logger.debug(traceback.format_exc())

                if reraise:
                    raise
                return None
        return wrapper
    return decorator


@contextmanager
def error_boundary(context: str, on_error: Optional[Callable] = None):
    """错误边界上下文管理器"""
    try:
        yield
    except Exception as e:
        error_msg = f"[{context}] 发生错误: {e}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())

        if on_error:
            on_error(e)


# ========================================================================
# 主程序入口
# ========================================================================

def create_main_app():
    """创建主应用实例（懒加载）"""
    try:
        from commercial_main import CommercialLotteryApp
        return CommercialLotteryApp()
    except ImportError as e:
        logger.error(f"无法导入主应用: {e}")
        raise


@handle_errors(context="主程序", reraise=True)
def main():
    """主程序入口"""
    # 初始化生命周期管理器
    lifecycle = AppLifecycle()

    # 注册清理回调
    @lifecycle.on_cleanup
    def cleanup_logging():
        logger.info("📝 日志系统关闭")

    # 启动应用
    lifecycle.startup()

    try:
        # 创建并运行主应用
        app = create_main_app()

        # 注册应用清理
        @lifecycle.on_cleanup
        def cleanup_app():
            if hasattr(app, 'cleanup'):
                app.cleanup()

        # 运行主循环
        app.root.mainloop()

    except KeyboardInterrupt:
        logger.info("⛔ 用户中断")
    except Exception as e:
        logger.critical(f"💥 程序异常: {e}")
        logger.debug(traceback.format_exc())
        raise
    finally:
        lifecycle.cleanup()


if __name__ == "__main__":
    main()
