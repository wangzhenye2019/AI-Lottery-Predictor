# -*- coding: utf-8 -*-
"""
体彩爬虫 - 支持排列3/5、七星彩
"""
import requests
import pandas as pd
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler
from loguru import logger


class SportsLotteryCrawler(BaseCrawler):
    """体彩爬虫（支持排列3/5、七星彩）"""

    def __init__(self, proxies: Optional[Dict[str, str]] = None):
        """
        初始化体彩爬虫
        
        Args:
            proxies: 代理配置，格式：{'http': '...', 'https': '...'}
        """
        super().__init__(
            name="sports_lottery",
            base_url="https://datachart.500.com",
            proxies=proxies
        )

    def fetch_data(
        self,
        lottery_type: str,
        issue_count: int = 100
    ) -> pd.DataFrame:
        """
        从500.com获取体彩数据

        Args:
            lottery_type: 彩种类型 (pl3/pl5/qxc)
            issue_count: 获取期数（iframe页面默认显示最近30期，如需更多需翻页）

        Returns:
            DataFrame
        """
        # 500.com URL 格式
        url_map = {
            'pl3': f"{self.base_url}/pls/history/",  # 排列3
            'pl5': f"{self.base_url}/plw/history/",  # 排列5
            'qxc': f"{self.base_url}/qxc/history/"   # 七星彩
        }

        if lottery_type not in url_map:
            logger.warning(f"体彩爬虫不支持 {lottery_type}")
            return pd.DataFrame()

        base_url = url_map[lottery_type]

        try:
            # 1. 获取主页面，解析 iframe URL
            response = self.session.get(f"{base_url}history.shtml", timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'gb2312'
            soup = BeautifulSoup(response.text, 'lxml')
            
            iframe = soup.find("iframe", id="chart")
            if not iframe or not iframe.get("src"):
                logger.error("未找到数据 iframe")
                return pd.DataFrame()
            
            iframe_src = iframe["src"]
            if iframe_src.startswith("http"):
                data_url = iframe_src
            else:
                data_url = base_url + iframe_src.lstrip('/')
            
            logger.info(f"数据URL: {data_url}")

            # 2. 获取 iframe 页面（包含数据表格）
            response2 = self.session.get(data_url, timeout=self.timeout)
            response2.raise_for_status()
            response2.encoding = 'gb2312'
            soup2 = BeautifulSoup(response2.text, 'lxml')
            
            # 3. 查找数据表格
            tdata = soup2.find("table", attrs={"id": "tablelist"})
            if not tdata:
                logger.error("未找到数据表格")
                return pd.DataFrame()

            trs = tdata.find_all("tr")
            data = []

            for tr in trs:
                tds = tr.find_all("td")
                if not tds:
                    continue
                
                # 根据彩种判断最少列数
                min_cols = 8 if lottery_type == "pl3" else 5
                if len(tds) < min_cols:
                    continue
                
                # 跳过奖金行（仅排列3有，第二行 td[0]="注数"）
                period_text = tds[0].get_text().strip()
                if period_text in ["注数", "期号"]:
                    continue
                
                item = {}

                if lottery_type == "pl3":
                    # 排列3：期号 + 3个号码（空格分隔）
                    item['期数'] = period_text
                    numbers = tds[1].get_text().strip().split()
                    for i in range(min(3, len(numbers))):
                        item[f'红球_{i+1}'] = numbers[i]
                    item['蓝球'] = "1"

                elif lottery_type == "pl5":
                    # 排列5：期号 + 5个号码（空格分隔）
                    item['期数'] = period_text
                    numbers = tds[1].get_text().strip().split()
                    for i in range(min(5, len(numbers))):
                        item[f'红球_{i+1}'] = numbers[i]
                    item['蓝球'] = "1"

                elif lottery_type == "qxc":
                    # 七星彩：期号 + 7个号码（空格分隔）
                    item['期数'] = period_text
                    numbers = tds[1].get_text().strip().split()
                    for i in range(min(7, len(numbers))):
                        item[f'红球_{i+1}'] = numbers[i]
                    item['蓝球'] = "1"

                data.append(item)

            df = pd.DataFrame(data)
            df = self._validate_dataframe(df, lottery_type)
            df = self._standardize_output(df, lottery_type)

            logger.info(f"体彩爬虫成功: {lottery_type}, 共 {len(df)} 期")
            return df

        except requests.exceptions.RequestException as e:
            logger.error(f"体彩爬取失败: {e}")
            raise
        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            raise

    def _get_current_number(self, url: str) -> int:
        """获取最新一期期号"""
        try:
            # 1. 获取主页面
            response = self.session.get(f"{url}history.shtml", timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'gb2312'
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 2. 查找 iframe
            iframe = soup.find("iframe", id="chart")
            if iframe and iframe.get("src"):
                iframe_src = iframe["src"]
                if iframe_src.startswith("http"):
                    iframe_url = iframe_src
                else:
                    iframe_url = url + iframe_src.lstrip('/')
                
                # 3. 获取 iframe 页面提取期号
                response2 = self.session.get(iframe_url, timeout=self.timeout)
                response2.raise_for_status()
                response2.encoding = 'gb2312'
                soup2 = BeautifulSoup(response2.text, 'lxml')
                input_elem = soup2.find("div", class_="wrap_datachart").find("input", id="end")
                if input_elem and input_elem.get("value"):
                    return int(input_elem["value"])
            
            # 降级：尝试旧方法
            input_elem = soup.find("div", class_="wrap_datachart")
            if input_elem:
                end_input = input_elem.find("input", id="end")
                if end_input and end_input.get("value"):
                    return int(end_input["value"])
            
            return 2024001  # 默认值
        except Exception as e:
            logger.warning(f"获取最新期号失败: {e}")
            return 2024001
