# -*- coding: utf-8 -*-
"""
增强爬虫模块
支持多源数据、增量更新、容错处理
"""
from .base_crawler import BaseCrawler
from .cwl_crawler import CwlCrawler
from .cwl_extended_crawler import CwlExtendedCrawler
from .fivehundred_crawler import FiveHundredCrawler
from .sports_lottery_crawler import SportsLotteryCrawler
# 网易爬虫需要 aiohttp 依赖，暂未安装
# from .netease_crawler import NeteaseCrawler
from .crawler_manager import CrawlerManager

__all__ = [
    'BaseCrawler',
    'CwlCrawler',
    'CwlExtendedCrawler',
    'FiveHundredCrawler',
    'SportsLotteryCrawler',
    # 'NeteaseCrawler',  # 需要 aiohttp
    'CrawlerManager'
]
