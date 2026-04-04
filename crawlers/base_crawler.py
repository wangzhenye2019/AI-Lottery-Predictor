# -*- coding: utf-8 -*-
"""
基础爬虫抽象类
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd
import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BaseCrawler(ABC):
    """爬虫基类"""

    def __init__(
        self,
        name: str,
        base_url: str,
        timeout: int = 15,
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None,
        proxies: Optional[Dict[str, str]] = None
    ):
        """
        初始化爬虫

        Args:
            name: 爬虫名称
            base_url: 基础URL
            timeout: 请求超时时间
            max_retries: 最大重试次数
            headers: 请求头
            proxies: 代理配置，格式：{'http': '...', 'https': '...'}
        """
        self.name = name
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.proxies = proxies

        self.session = self._create_session(headers)

    def _create_session(
        self,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Session:
        """创建带重试机制的会话"""
        session = requests.Session()

        # 设置默认请求头
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        if headers:
            default_headers.update(headers)

        session.headers.update(default_headers)

        # 配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 设置代理（如果提供）
        if self.proxies:
            session.proxies.update(self.proxies)

        return session

    @abstractmethod
    def fetch_data(
        self,
        lottery_type: str,
        issue_count: int = 100
    ) -> pd.DataFrame:
        """
        获取历史数据

        Args:
            lottery_type: 彩种类型
            issue_count: 获取期数

        Returns:
            DataFrame 包含历史开奖数据
        """
        pass

    def close(self):
        """关闭会话"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _validate_dataframe(
        self,
        df: pd.DataFrame,
        lottery_type: str
    ) -> pd.DataFrame:
        """
        验证和清洗数据

        Args:
            df: 原始数据
            lottery_type: 彩种类型

        Returns:
            清洗后的数据
        """
        required_columns = ['期数']

        # 检查必要列
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"缺少必要列: {col}")

        # 去重（按期号）
        df = df.drop_duplicates(subset=['期数'])

        # 按期号降序排序
        df = df.sort_values('期数', ascending=False)

        # 重置索引
        df = df.reset_index(drop=True)

        logger.info(f"数据验证完成: {len(df)} 条记录")
        return df

    def _standardize_output(
        self,
        df: pd.DataFrame,
        lottery_type: str
    ) -> pd.DataFrame:
        """
        标准化输出格式

        Args:
            df: 原始数据
            lottery_type: 彩种类型

        Returns:
            标准化后的数据
        """
        # 确保列名统一
        column_mapping = {
            '期数': '期数',
            '日期': '日期',
            '红球': '红球',
            '蓝球': '蓝球'
        }

        # 重命名列
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

        # 处理红球列
        red_cols = [col for col in df.columns if '红球' in col]
        if not red_cols and '红球' in df.columns:
            # 如果红球是逗号分隔的字符串，拆分为多列
            red_split = df['红球'].str.split(',', expand=True)
            for i in range(red_split.shape[1]):
                df[f'红球_{i+1}'] = red_split[i].astype(int)

        # 处理蓝球列
        if '蓝球' in df.columns and '蓝球' not in [col for col in df.columns if col == '蓝球']:
            # 如果蓝球是多列，合并
            blue_cols = [col for col in df.columns if '蓝球' in col and col != '蓝球']
            if blue_cols:
                df['蓝球'] = df[blue_cols[0]]

        return df
