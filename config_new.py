# -*- coding: utf-8 -*-
"""
统一的配置管理模块
Author: BigCat
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class ProxyConfig:
    """代理配置"""
    enabled: bool = False
    proxies: Dict[str, str] = field(default_factory=dict)
    rotation: bool = False


@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str = "sqlite:///data/lottery.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class UIConfig:
    """UI配置"""
    theme: str = "dark"
    font_family: Optional[str] = None
    font_size: int = 12
    window_width: int = 1200
    window_height: int = 800


@dataclass
class AppConfig:
    """应用主配置"""
    debug: bool = False
    log_level: str = "INFO"
    max_retries: int = 3
    timeout: int = 30
    data_dir: str = "data"
    output_dir: str = "outputs"
    
    # 子配置
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ui: UIConfig = field(default_factory=UIConfig)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config.yaml"
        self.config = AppConfig()
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                import yaml
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                self._update_config_from_dict(data)
            except ImportError:
                logger.warning("PyYAML未安装，使用默认配置")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        else:
            logger.info("配置文件不存在，使用默认配置")
    
    def _update_config_from_dict(self, data: Dict[str, Any]):
        """从字典更新配置"""
        if not data:
            return
            
        # 更新主配置
        for key, value in data.items():
            if hasattr(self.config, key) and not isinstance(value, dict):
                setattr(self.config, key, value)
        
        # 更新子配置
        if 'proxy' in data:
            self._update_proxy_config(data['proxy'])
        if 'database' in data:
            self._update_database_config(data['database'])
        if 'ui' in data:
            self._update_ui_config(data['ui'])
    
    def _update_proxy_config(self, data: Dict[str, Any]):
        """更新代理配置"""
        for key, value in data.items():
            if hasattr(self.config.proxy, key):
                setattr(self.config.proxy, key, value)
    
    def _update_database_config(self, data: Dict[str, Any]):
        """更新数据库配置"""
        for key, value in data.items():
            if hasattr(self.config.database, key):
                setattr(self.config.database, key, value)
    
    def _update_ui_config(self, data: Dict[str, Any]):
        """更新UI配置"""
        for key, value in data.items():
            if hasattr(self.config.ui, key):
                setattr(self.config.ui, key, value)
    
    def save_config(self):
        """保存配置到文件"""
        try:
            import yaml
            config_dict = {
                'debug': self.config.debug,
                'log_level': self.config.log_level,
                'max_retries': self.config.max_retries,
                'timeout': self.config.timeout,
                'data_dir': self.config.data_dir,
                'output_dir': self.config.output_dir,
                'proxy': {
                    'enabled': self.config.proxy.enabled,
                    'proxies': self.config.proxy.proxies,
                    'rotation': self.config.proxy.rotation
                },
                'database': {
                    'url': self.config.database.url,
                    'echo': self.config.database.echo,
                    'pool_size': self.config.database.pool_size,
                    'max_overflow': self.config.database.max_overflow
                },
                'ui': {
                    'theme': self.config.ui.theme,
                    'font_family': self.config.ui.font_family,
                    'font_size': self.config.ui.font_size,
                    'window_width': self.config.ui.window_width,
                    'window_height': self.config.ui.window_height
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"配置已保存到 {self.config_file}")
        except ImportError:
            logger.warning("PyYAML未安装，无法保存配置")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def get_config(self) -> AppConfig:
        """获取配置对象"""
        return self.config
    
    def get_env_config(self) -> Dict[str, Any]:
        """获取环境变量配置"""
        env_config = {}
        
        # 从环境变量读取配置
        env_mapping = {
            'LOTTERY_DEBUG': ('debug', bool),
            'LOTTERY_LOG_LEVEL': ('log_level', str),
            'LOTTERY_MAX_RETRIES': ('max_retries', int),
            'LOTTERY_TIMEOUT': ('timeout', int),
            'LOTTERY_DATA_DIR': ('data_dir', str),
            'LOTTERY_OUTPUT_DIR': ('output_dir', str),
            'LOTTERY_PROXY_ENABLED': ('proxy.enabled', bool),
            'LOTTERY_DB_URL': ('database.url', str),
        }
        
        for env_var, (config_key, value_type) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if value_type == bool:
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type == int:
                        value = int(value)
                    env_config[config_key] = value
                except ValueError:
                    logger.warning(f"环境变量 {env_var} 的值 {value} 无法转换为 {value_type}")
        
        return env_config


# 全局配置实例
config_manager = ConfigManager()
config = config_manager.get_config()


# 兼容性配置 - 保持向后兼容
ball_name = [
    ("红球", "red"),
    ("蓝球", "blue")
]

data_file_name = "data.csv"

name_path = {
    "ssq": {"name": "双色球", "path": "data/ssq/"},
    "dlt": {"name": "大乐透", "path": "data/dlt/"},
    "qlc": {"name": "七乐彩", "path": "data/qlc/"},
    "fc3d": {"name": "福彩3D", "path": "data/fc3d/"},
    "kl8": {"name": "快乐8", "path": "data/kl8/"},
    "pl3": {"name": "排列3", "path": "data/pl3/"},
    "pl5": {"name": "排列5", "path": "data/pl5/"},
    "qxc": {"name": "七星彩", "path": "data/qxc/"},
}

# 代理配置
PROXY_CONFIG = {
    'enabled': config.proxy.enabled,
    'proxies': config.proxy.proxies,
    'rotation': config.proxy.rotation
}

# 模型参数
model_args = {
    'n_estimators': 100,
    'max_depth': 10,
    'random_state': 42,
    'test_size': 0.2,
    'validation_split': 0.2
}


def get_data_path(lottery_type: str) -> str:
    """获取彩票数据路径"""
    if lottery_type not in name_path:
        raise ValueError(f"不支持的彩票类型: {lottery_type}")
    return name_path[lottery_type]["path"]


def ensure_data_dirs():
    """确保数据目录存在"""
    for lottery_info in name_path.values():
        Path(lottery_info["path"]).mkdir(parents=True, exist_ok=True)
    
    Path(config.data_dir).mkdir(parents=True, exist_ok=True)
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)


# 初始化时创建目录
ensure_data_dirs()
