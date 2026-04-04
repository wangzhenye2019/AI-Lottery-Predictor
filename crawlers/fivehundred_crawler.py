# -*- coding: utf-8 -*-
"""
500.com 爬虫
"""
import pandas as pd
from typing import Dict, Any
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler
from loguru import logger


class FiveHundredCrawler(BaseCrawler):
    """500.com 爬虫"""

    def __init__(self):
        super().__init__(
            name="500",
            base_url="https://datachart.500.com"
        )

    def fetch_data(
        self,
        lottery_type: str,
        issue_count: int = 100
    ) -> pd.DataFrame:
        """
        从 500.com 获取数据

        Args:
            lottery_type: 彩种类型 (ssq/dlt)
            issue_count: 获取期数

        Returns:
            DataFrame
        """
        # 500.com URL 格式
        url_map = {
            'ssq': f"{self.base_url}/ssq/history/",
            'dlt': f"{self.base_url}/dlt/history/"
        }

        if lottery_type not in url_map:
            raise ValueError(f"不支持的彩种: {lottery_type}")

        url = url_map[lottery_type]
        path = "newinc/history.php?start={}&end="

        try:
            # 获取最新期号
            current_num = self._get_current_number(url)

            # 计算起始期号（简单估算）
            start_num = max(1, current_num - issue_count + 1)

            full_url = f"{url}{path.format(start_num)}{current_num}"

            response = self.session.get(full_url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'gb2312'

            soup = BeautifulSoup(response.text, 'lxml')
            tdata = soup.find("tbody", attrs={"id": "tdata"})

            if not tdata:
                logger.error("未找到数据表格")
                return pd.DataFrame()

            trs = tdata.find_all("tr")
            data = []

            for tr in trs:
                tds = tr.find_all("td")
                if not tds or len(tds) < 8:
                    continue

                item = {}

                if lottery_type == "ssq":
                    item['期数'] = tds[0].get_text().strip()
                    for i in range(6):
                        item[f'红球_{i+1}'] = tds[i+1].get_text().strip()
                    item['蓝球'] = tds[7].get_text().strip()
                elif lottery_type == "dlt":
                    item['期数'] = tds[0].get_text().strip()
                    for i in range(5):
                        item[f'红球_{i+1}'] = tds[i+1].get_text().strip()
                    for j in range(2):
                        item[f'蓝球_{j+1}'] = tds[6+j].get_text().strip()
                    # 合并蓝球为单个字段
                    item['蓝球'] = item.get('蓝球_1', '') + ' ' + item.get('蓝球_2', '')

                data.append(item)

            df = pd.DataFrame(data)
            df = self._validate_dataframe(df, lottery_type)
            df = self._standardize_output(df, lottery_type)

            logger.info(f"500.com 爬虫成功: {lottery_type}, 共 {len(df)} 期")
            return df

        except requests.exceptions.RequestException as e:
            logger.error(f"500.com 爬取失败: {e}")
            raise
        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            raise

    def _get_current_number(self, url: str) -> int:
        """获取最新一期期号"""
        try:
            response = self.session.get(f"{url}history.shtml", timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'gb2312'
            soup = BeautifulSoup(response.text, 'lxml')
            input_elem = soup.find("div", class_="wrap_datachart").find("input", id="end")
            if input_elem:
                return int(input_elem["value"])
            return 2024001  # 默认值
        except Exception as e:
            logger.warning(f"获取最新期号失败: {e}")
            return 2024001
