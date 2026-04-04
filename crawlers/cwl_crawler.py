# -*- coding: utf-8 -*-
"""
中国福彩官网爬虫
"""
import pandas as pd
from typing import Dict, Any
from .base_crawler import BaseCrawler
from loguru import logger


class CwlCrawler(BaseCrawler):
    """中国福彩官网爬虫"""

    def __init__(self):
        super().__init__(
            name="cwl",
            base_url="http://www.cwl.gov.cn"
        )

    def fetch_data(
        self,
        lottery_type: str,
        issue_count: int = 100
    ) -> pd.DataFrame:
        """
        从福彩官网获取数据

        Args:
            lottery_type: 彩种类型 (ssq/qlc/fc3d)
            issue_count: 获取期数

        Returns:
            DataFrame
        """
        url = "http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        api_name = "3d" if lottery_type == "fc3d" else lottery_type

        params = {
            "name": api_name,
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
                blue_str = item.get("blue")

                if lottery_type in ["ssq", "qlc"]:
                    reds = red_str.split(",")
                    for i, r_num in enumerate(reds):
                        row[f'红球_{i+1}'] = r_num
                    row['蓝球'] = blue_str
                elif lottery_type == "fc3d":
                    reds = red_str.split(",")
                    for i, r_num in enumerate(reds):
                        # 福彩3D 0-9 映射为 1-10 以兼容模型
                        row[f'红球_{i+1}'] = str(int(r_num) + 1)
                    row['蓝球'] = "1"  # 假蓝球

                data.append(row)

            df = pd.DataFrame(data)
            df = self._validate_dataframe(df, lottery_type)
            df = self._standardize_output(df, lottery_type)

            logger.info(f"福彩官网爬虫成功: {lottery_type}, 共 {len(df)} 期")
            return df

        except requests.exceptions.RequestException as e:
            logger.error(f"福彩官网爬取失败: {e}")
            raise
        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            raise
