# -*- coding:utf-8 -*-
"""
Author: BigCat
"""
import warnings
import argparse
import requests
import pandas as pd
import os
from bs4 import BeautifulSoup
from loguru import logger
from config import name_path, data_file_name

# 抑制 SSL 警告（不影响功能）
warnings.filterwarnings('ignore', message='.*InsecureRequestWarning.*')
requests.packages.urllib3.disable_warnings()


def get_url(name):
    """
    :param name: 玩法名称
    :return:
    """
    url = "https://datachart.500.com/{}/history/".format(name)
    path = "newinc/history.php?start={}&end="
    return url, path


def spider_cwl(name, issue_count=3000):
    """ 从中国福彩官网爬取数据 (支持 ssq, qlc, fc3d) """
    url = "http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    api_name = "3d" if name == "fc3d" else name
    params = {"name": api_name, "issueCount": issue_count}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        data_json = r.json()
        if "result" not in data_json:
            logger.error(f"未找到数据: {data_json}")
            return pd.DataFrame()
            
        data = []
        results = data_json["result"]
        for item in results:
            row = dict()
            row[u"期数"] = item.get("code")
            red_str = item.get("red")
            blue_str = item.get("blue")
            
            if name in ["ssq", "qlc"]:
                reds = red_str.split(",")
                for i, r_num in enumerate(reds):
                    row[u"红球_{}".format(i+1)] = r_num
                row[u"蓝球"] = blue_str
            elif name == "fc3d":
                # fc3d 没有蓝球，只有3个红球数字（百十个）
                reds = red_str.split(",")
                for i, r_num in enumerate(reds):
                    row[u"红球_{}".format(i+1)] = str(int(r_num) + 1) # 为了兼容模型，0-9映射为1-10
                row[u"蓝球"] = "1" # 假蓝球，避免修改大量架构代码
            data.append(row)
            
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        logger.error(f"爬取福彩数据失败: {e}")
        raise


def get_current_number(name):
    """ 获取最新一期数字
    :return: int
    """
    url, _ = get_url(name)
    try:
        r = requests.get("{}{}".format(url, "history.shtml"), verify=False, timeout=15)
        r.raise_for_status()
        r.encoding = "gb2312"
        soup = BeautifulSoup(r.text, "lxml")
        current_num = soup.find("div", class_="wrap_datachart").find("input", id="end")["value"]
        return current_num
    except requests.exceptions.RequestException as e:
        logger.error(f"获取最新一期数字失败: {e}")
        raise
    except Exception as e:
        logger.error(f"解析最新一期数字失败: {e}")
        raise


def spider(name, start, end, mode):
    """ 爬取历史数据
    :param name 玩法
    :param start 开始一期
    :param end 最近一期
    :param mode 模式，train：训练模式，predict：预测模式（训练模式会保持文件）
    :return:
    """
    url, path = get_url(name)
    url = "{}{}{}".format(url, path.format(start), end)
    try:
        r = requests.get(url=url, verify=False, timeout=15)
        r.raise_for_status()
        r.encoding = "gb2312"
        soup = BeautifulSoup(r.text, "lxml")
        tdata = soup.find("tbody", attrs={"id": "tdata"})
        if not tdata:
            logger.error("未找到数据表格，请检查网络或网站结构。")
            return pd.DataFrame()
            
        trs = tdata.find_all("tr")
        data = []
        for tr in trs:
            item = dict()
            tds = tr.find_all("td")
            if not tds or len(tds) < 8:
                continue
                
            if name == "ssq":
                item[u"期数"] = tds[0].get_text().strip()
                for i in range(6):
                    item[u"红球_{}".format(i+1)] = tds[i+1].get_text().strip()
                item[u"蓝球"] = tds[7].get_text().strip()
                data.append(item)
            elif name == "dlt":
                item[u"期数"] = tds[0].get_text().strip()
                for i in range(5):
                    item[u"红球_{}".format(i+1)] = tds[i+1].get_text().strip()
                for j in range(2):
                    item[u"蓝球_{}".format(j+1)] = tds[6+j].get_text().strip()
                data.append(item)
            else:
                logger.warning("抱歉，没有找到数据源！")
                break

        if mode == "train":
            df = pd.DataFrame(data)
            output_path = os.path.join(name_path[name]["path"], data_file_name)
            df.to_csv(output_path, encoding="utf-8", index=False)
            return df
        elif mode == "predict":
            return pd.DataFrame(data)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"爬取数据失败: {e}")
        raise


def run(name):
    """
    :param name: 玩法名称
    :return:
    """
    try:
        save_dir = name_path[name]["path"]
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        logger.info("正在获取【{}】数据。。。".format(name_path[name]["name"]))
        
        if name in ["ssq", "qlc", "fc3d"]:
            # 优先使用官方 API，速度极快
            df = spider_cwl(name, 5000)
            if df.empty:
                logger.error("通过官方接口未获取到数据！")
                return
            
            output_path = os.path.join(save_dir, data_file_name)
            df.to_csv(output_path, encoding="utf-8", index=False)
            logger.info("【{}】最新一期期号：{}".format(name_path[name]["name"], df.iloc[0]["期数"]))
            data = df
        else:
            current_number = get_current_number(name)
            logger.info("【{}】最新一期期号：{}".format(name_path[name]["name"], current_number))
            data = spider(name, 1, current_number, "train")
        
        file_path = os.path.join(save_dir, data_file_name)
        if os.path.exists(file_path):
            logger.info("【{}】数据准备就绪，共{}期, 下一步可训练模型...".format(name_path[name]["name"], len(data)))
        else:
            logger.error("数据文件不存在！爬取可能失败。")
            
    except Exception as e:
        logger.error(f"执行失败: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default="ssq", type=str, help="选择爬取数据: 双色球/大乐透")
    args = parser.parse_args()
    
    if not args.name:
        logger.error("玩法名称不能为空！")
    else:
        run(name=args.name)
