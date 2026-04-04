# -*- coding: utf-8 -*-
"""
爬虫管理器
协调多个数据源，实现增量更新和容错
"""
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from .base_crawler import BaseCrawler
from .cwl_crawler import CwlCrawler
from .cwl_extended_crawler import CwlExtendedCrawler
from .fivehundred_crawler import FiveHundredCrawler
from .sports_lottery_crawler import SportsLotteryCrawler
# from .netease_crawler import NeteaseCrawler  # 需要 aiohttp
from database import get_db_manager


class CrawlerManager:
    """爬虫管理器"""

    def __init__(self, use_db: bool = True):
        """
        初始化爬虫管理器

        Args:
            use_db: 是否使用数据库
        """
        self.use_db = use_db
        self.db = get_db_manager() if use_db else None
        self.crawlers: Dict[str, BaseCrawler] = {}
        self._register_crawlers()

    def _register_crawlers(self):
        """注册所有爬虫"""
        from config import PROXY_CONFIG
        
        # 准备代理配置
        proxies = PROXY_CONFIG.get('proxies', {}) if PROXY_CONFIG.get('enabled', False) else None
        
        crawlers = {
            'cwl': CwlCrawler,
            'cwl_extended': CwlExtendedCrawler,
            '500': FiveHundredCrawler,
            'sports': SportsLotteryCrawler,
            'netease': NeteaseCrawler
        }

        for name, cls in crawlers.items():
            try:
                # 为需要代理的爬虫传递代理参数
                if name == 'sports' and proxies:
                    crawler = cls(proxies=proxies)
                else:
                    crawler = cls()
                self.crawlers[name] = crawler
                logger.debug(f"注册爬虫: {name}")
            except Exception as e:
                logger.warning(f"爬虫 {name} 注册失败: {e}")

    def fetch_from_all(
        self,
        lottery_type: str,
        issue_count: int = 100,
        sources: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        从所有可用数据源获取数据并合并

        Args:
            lottery_type: 彩种类型
            issue_count: 获取期数
            sources: 指定数据源列表，None 表示全部

        Returns:
            合并后的 DataFrame
        """
        all_data = []
        sources_to_use = sources or list(self.crawlers.keys())

        # 定义每个爬虫支持的彩种
        crawler_support = {
            'cwl': ['ssq', 'qlc', 'fc3d'],
            'cwl_extended': ['kl8'],
            '500': ['ssq', 'dlt'],
            'sports': ['pl3', 'pl5', 'qxc'],
            'netease': ['ssq', 'dlt']  # 暂未实现
        }

        for source in sources_to_use:
            if source not in self.crawlers:
                logger.warning(f"爬虫 {source} 不存在，跳过")
                continue

            # 检查该爬虫是否支持当前彩种
            supported = crawler_support.get(source, [])
            if supported and lottery_type not in supported:
                logger.debug(f"爬虫 {source} 不支持 {lottery_type}，跳过")
                continue

            crawler = self.crawlers[source]
            try:
                logger.info(f"从 {source} 获取 {lottery_type} 数据...")
                df = crawler.fetch_data(lottery_type, issue_count)
                if not df.empty:
                    # 添加数据源标记
                    df['data_source'] = source
                    all_data.append(df)
                    logger.info(f"  {source}: {len(df)} 条记录")
                else:
                    logger.warning(f"  {source}: 无数据")
            except Exception as e:
                logger.error(f"  {source} 获取失败: {e}")
                continue

        if not all_data:
            logger.error("所有数据源均失败")
            return pd.DataFrame()

        # 合并数据
        combined_df = pd.concat(all_data, ignore_index=True)

        # 去重（按期号）
        if '期数' in combined_df.columns:
            combined_df = combined_df.drop_duplicates(subset=['期数'], keep='first')
            logger.info(f"去重后共 {len(combined_df)} 条记录")

        return combined_df

    def incremental_update(
        self,
        lottery_type: str,
        days_back: int = 7
    ) -> int:
        """
        增量更新：只获取最近N天的数据

        Args:
            lottery_type: 彩种类型
            days_back: 回溯天数

        Returns:
            新增记录数
        """
        logger.info(f"开始增量更新 {lottery_type}，回溯 {days_back} 天")

        # 从数据库获取最新期号
        if self.use_db and self.db:
            latest_draw = self.db.get_latest_draw(lottery_type)
            if latest_draw:
                logger.info(f"数据库最新期号: {latest_draw.issue_number}")
                # 这里可以计算需要获取的期号范围
                # 简化：直接获取最近N天数据
            else:
                logger.info("数据库为空，将全量获取")
        else:
            logger.warning("未启用数据库，无法判断增量")

        # 获取数据
        df = self.fetch_from_all(lottery_type, issue_count=100)

        if df.empty:
            return 0

        # 保存到数据库
        if self.use_db and self.db:
            inserted = self.db.upsert_lottery_draws(df, lottery_type)
            logger.info(f"增量更新完成，新增 {inserted} 条记录")
            return inserted
        else:
            # 保存到 CSV
            from config import name_path
            import os
            save_dir = name_path[lottery_type]["path"]
            os.makedirs(save_dir, exist_ok=True)
            csv_path = os.path.join(save_dir, "data.csv")
            df.to_csv(csv_path, encoding="utf-8", index=False)
            logger.info(f"数据已保存到 {csv_path}")
            return len(df)

    def full_sync(
        self,
        lottery_type: str,
        issue_count: int = 3000
    ) -> int:
        """
        全量同步：获取指定期数的历史数据

        Args:
            lottery_type: 彩种类型
            issue_count: 总期数

        Returns:
            总记录数
        """
        logger.info(f"开始全量同步 {lottery_type}，目标 {issue_count} 期")

        df = self.fetch_from_all(lottery_type, issue_count)

        if df.empty:
            return 0

        # 保存到数据库
        if self.use_db and self.db:
            # 先清空该彩种数据（可选）
            # self.db.clear_lottery_draws(lottery_type)
            inserted = self.db.upsert_lottery_draws(df, lottery_type)
            logger.info(f"全量同步完成，共 {inserted} 条记录")
            return inserted
        else:
            # 保存到 CSV
            from config import name_path
            import os
            save_dir = name_path[lottery_type]["path"]
            os.makedirs(save_dir, exist_ok=True)
            csv_path = os.path.join(save_dir, "data.csv")
            df.to_csv(csv_path, encoding="utf-8", index=False)
            logger.info(f"数据已保存到 {csv_path}")
            return len(df)

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            'database': 'unknown',
            'crawlers': {},
            'timestamp': datetime.now().isoformat()
        }

        # 检查数据库
        if self.use_db and self.db:
            try:
                count = self.db.count_draws('ssq')
                status['database'] = f'connected (ssq records: {count})'
            except Exception as e:
                status['database'] = f'error: {e}'
        else:
            status['database'] = 'disabled'

        # 检查爬虫
        for name, crawler in self.crawlers.items():
            try:
                # 简单测试请求
                test_url = f"{crawler.base_url}/"
                response = crawler.session.head(test_url, timeout=5)
                status['crawlers'][name] = f'ok (status: {response.status_code})'
            except Exception as e:
                status['crawlers'][name] = f'error: {e}'

        return status

    def close(self):
        """关闭所有爬虫会话"""
        for crawler in self.crawlers.values():
            crawler.close()
        logger.info("所有爬虫已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_crawler_manager() -> CrawlerManager:
    """获取爬虫管理器实例"""
    return CrawlerManager()
