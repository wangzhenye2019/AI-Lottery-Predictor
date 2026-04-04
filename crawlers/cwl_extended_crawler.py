# -*- coding: utf-8 -*-
"""
福彩扩展爬虫 - 支持快乐8
"""
import pandas as pd
from typing import Dict, Any
from .base_crawler import BaseCrawler
from loguru import logger


class CwlExtendedCrawler(BaseCrawler):
    """福彩扩展爬虫（支持快乐8等）"""

    def __init__(self):
        super().__init__(
            name="cwl_extended",
            base_url="http://www.cwl.gov.cn"
        )

    def fetch_data(
        self,
        lottery_type: str,
        issue_count: int = 100
    ) -> pd.DataFrame:
        """
        从福彩官网获取数据（扩展支持）

        Args:
            lottery_type: 彩种类型 (kl8)
            issue_count: 获取期数

        Returns:
            DataFrame
        """
        url = "http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # 快乐8的API名称
        api_name_map = {
            "kl8": "kl8"
        }

        if lottery_type not in api_name_map:
            logger.warning(f"福彩扩展爬虫不支持 {lottery_type}")
            return pd.DataFrame()

        params = {
            "name": api_name_map[lottery_type],
            "issueCount": issue_count
        }

        try:
            response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data_json = response.json()

            if "result" not in data_json:
                logger.error(f"未找到数据: {data_json}")
                return pd.DataFrame()

            data = []
            results = data_json["result"]

            for item in results:
                row = {}
                row['期数'] = item.get("code")
                row['日期'] = item.get("date")
                red_str = item.get("red")
                # 快乐8没有蓝球，但为了兼容模型，我们创建一个假蓝球
                # 快乐8从1-80中选20个号码

                if lottery_type == "kl8":
                    reds = red_str.split(",")
                    # 快乐8有20个红球
                    for i in range(20):
                        if i < len(reds):
                            row[f'红球_{i+1}'] = reds[i]
                        else:
                            row[f'红球_{i+1}'] = ""
                    # 假蓝球（快乐8没有蓝球）
                    row['蓝球'] = "1"

                data.append(row)

            df = pd.DataFrame(data)
            df = self._validate_dataframe(df, lottery_type)
            df = self._standardize_output(df, lottery_type)

            logger.info(f"福彩扩展爬虫成功: {lottery_type}, 共 {len(df)} 期")
            return df

        except requests.exceptions.RequestException as e:
            logger.error(f"福彩扩展爬取失败: {e}")
            raise
        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            raise
