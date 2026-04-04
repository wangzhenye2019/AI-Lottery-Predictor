# -*- coding: utf-8 -*-
"""
数据同步服务
负责启动时检查并更新开奖数据、管理模型训练状态
"""
import os
import re
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from database import get_db_manager
from config import data_file_name, name_path


class DataSyncService:
    """数据同步服务"""

    def __init__(self):
        self.db = get_db_manager()

    def check_and_update(self, game_key: str, max_fetch: int = 50) -> Dict[str, Any]:
        """
        检查并更新开奖数据

        Returns:
            {
                'updated': bool,       # 是否有新数据
                'local_count': int,     # 本地记录数
                'local_latest': str,   # 本地最新期号
                'remote_latest': str,   # 远程最新期号
                'new_count': int,      # 新增记录数
                'message': str         # 说明信息
            }
        """
        result = {
            'updated': False,
            'local_count': 0,
            'local_latest': '',
            'remote_latest': '',
            'new_count': 0,
            'message': ''
        }

        try:
            # 1. 获取本地最新记录
            local_draws = self.db.get_lottery_draws_dict(game_key, limit=1)
            if local_draws:
                result['local_latest'] = local_draws[0]['issue_number']
                result['local_count'] = self.db.count_draws(game_key)
                logger.info(f"[{game_key}] 本地最新期号: {result['local_latest']}, 共 {result['local_count']} 条")

            # 2. 检查是否需要从远程更新
            # 注意：期号格式可能不一致（旧格式如9154，新格式如2026036）
            # 简化为：如果本地数据量足够（>3000条），认为不需要更新
            if result['local_count'] > 3000:
                result['message'] = f"数据已足够 ({result['local_count']}条)"
                logger.info(f"[{game_key}] 数据量充足，跳过远程检查")
            else:
                # 数据量不足，尝试从远程获取
                remote_latest = self._fetch_remote_latest(game_key)
                if remote_latest:
                    result['remote_latest'] = remote_latest

                    # 比较期号（使用标准化比较）
                    if self._need_update(result['local_latest'], remote_latest):
                        logger.info(f"[{game_key}] 检测到新数据: 本地 {result['local_latest']} -> 远程 {remote_latest}")
                        new_count = self._sync_from_remote(game_key, max_fetch)
                        result['updated'] = True
                        result['new_count'] = new_count
                        result['message'] = f"已更新 {new_count} 条数据"
                    else:
                        result['message'] = "数据已是最新"
                else:
                    result['message'] = "无法获取远程数据"

        except Exception as e:
            logger.error(f"[{game_key}] 数据检查失败: {e}")
            result['message'] = f"检查失败: {e}"

        return result

    def _fetch_remote_latest(self, game_key: str) -> Optional[str]:
        """获取远程最新期号"""
        try:
            if game_key in ['ssq', 'qlc', 'fc3d']:
                from get_data import spider_cwl
                df = spider_cwl(game_key, 1)
                if df is not None and len(df) > 0:
                    return str(df.iloc[0].get('期数', ''))
            elif game_key == 'dlt':
                from utils.zhcw_client import fetch_draw_list
                items = fetch_draw_list(game_key, page_num=1, page_size=1)
                if items:
                    return items[0].issue
        except Exception as e:
            logger.warning(f"获取远程数据失败: {e}")
        return None

    def _need_update(self, local_latest: str, remote_latest: str) -> bool:
        """判断是否需要更新"""
        try:
            local_num = int(local_latest)
            remote_num = int(remote_latest)
            return remote_num > local_num
        except:
            return local_latest != remote_latest

    def _sync_from_remote(self, game_key: str, max_fetch: int) -> int:
        """从远程同步数据到数据库"""
        try:
            # 1. 爬取数据
            if game_key in ['ssq', 'qlc', 'fc3d']:
                from get_data import spider_cwl
                df = spider_cwl(game_key, max_fetch)
            elif game_key == 'dlt':
                from utils.zhcw_client import fetch_draw_list, DrawItem
                items = fetch_draw_list(game_key, page_num=1, page_size=max_fetch)
                df = self._convert_draw_items(items)
            else:
                return 0

            if df is None or len(df) == 0:
                return 0

            # 2. 保存到数据库
            count = self.db.upsert_lottery_draws(df, game_key)
            logger.info(f"[{game_key}] 同步完成，新增 {count} 条")
            return count

        except Exception as e:
            logger.error(f"[{game_key}] 同步失败: {e}")
            return 0

    def _convert_draw_items(self, items) -> pd.DataFrame:
        """将 DrawItem 列表转换为 DataFrame"""
        data = []
        for item in items:
            # 解析日期，处理各种格式
            date_str = ''
            if hasattr(item, 'open_time'):
                date_str = item.open_time.strftime('%Y-%m-%d')
            elif hasattr(item, 'date'):
                date_str = self._parse_date(item.date)

            data.append({
                '期数': item.issue,
                '日期': date_str,
                '红球1': item.reds[0] if len(item.reds) > 0 else 0,
                '红球2': item.reds[1] if len(item.reds) > 1 else 0,
                '红球3': item.reds[2] if len(item.reds) > 2 else 0,
                '红球4': item.reds[3] if len(item.reds) > 3 else 0,
                '红球5': item.reds[4] if len(item.reds) > 4 else 0,
                '红球6': item.reds[5] if len(item.reds) > 5 else 0,
                '蓝球': item.blue if hasattr(item, 'blue') else 0,
            })
        return pd.DataFrame(data)

    def _parse_date(self, date_str: str) -> str:
        """解析各种日期格式"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')

        # 尝试解析中文日期格式如 "2026-04-02(四)"
        match = re.match(r'(\d{4}-\d{2}-\d{2})', date_str)
        if match:
            return match.group(1)

        try:
            # 尝试标准解析
            dt = pd.to_datetime(date_str)
            return dt.strftime('%Y-%m-%d')
        except:
            return date_str

    def get_latest_issue(self, game_key: str) -> Tuple[Optional[str], Optional[str]]:
        """获取本地最新期号和日期"""
        try:
            draws = self.db.get_lottery_draws_dict(game_key, limit=1)
            if draws:
                return draws[0]['issue_number'], str(draws[0]['draw_date'])
        except:
            pass
        return None, None

    def load_dataframe(self, game_key: str) -> Optional[pd.DataFrame]:
        """从数据库加载数据并转换为DataFrame"""
        try:
            draws = self.db.get_lottery_draws_dict(game_key, limit=10000)
            if not draws:
                return None

            data = []
            for draw in draws:
                row = {
                    '期数': draw['issue_number'],
                    '日期': str(draw['draw_date']),
                }
                # 红球 - 同时添加两种格式以兼容不同模块
                red_balls = draw['red_balls'] or []
                for i, ball in enumerate(red_balls):
                    row[f'红球_{i+1}'] = ball  # 红球_1 格式
                    row[f'红球{i+1}'] = ball   # 红球1 格式
                # 蓝球 - 同时添加两种格式
                blue_val = draw['blue_ball']
                if isinstance(blue_val, list):
                    row['蓝球'] = blue_val
                elif blue_val:
                    row['蓝球'] = int(blue_val)
                else:
                    row['蓝球'] = 0
                
                data.append(row)

            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"加载DataFrame失败: {e}")
            return None


class ModelCheckService:
    """模型检查服务 - 检查是否需要训练"""

    def __init__(self):
        self.db = get_db_manager()

    def check_needs_training(self, game_key: str) -> Dict[str, Any]:
        """
        检查模型是否需要训练

        Returns:
            {
                'needs_training': bool,
                'reason': str,
                'last_trained': str 或 None,
                'data_count': int,
                'data_latest': str,
                'model_exists': bool
            }
        """
        result = {
            'needs_training': False,
            'reason': '',
            'last_trained': None,
            'data_count': 0,
            'data_latest': '',
            'model_exists': False
        }

        try:
            # 1. 检查数据量
            data_count = self.db.count_draws(game_key)
            result['data_count'] = data_count

            if data_count < 100:
                result['needs_training'] = True
                result['reason'] = f"数据量不足: 仅 {data_count} 条 (需要至少100条)"
                return result

            # 2. 检查最新数据期号
            latest_draws = self.db.get_lottery_draws_dict(game_key, limit=1)
            if latest_draws:
                result['data_latest'] = latest_draws[0]['issue_number']

            # 3. 检查模型文件是否存在
            from config import model_path
            model_dir = os.path.join(model_path, game_key)
            red_model = os.path.join(model_dir, "red_ball_model")
            blue_model = os.path.join(model_dir, "blue_ball_model")

            result['model_exists'] = (
                os.path.exists(red_model + ".ckpt.index") or
                os.path.exists(red_model + ".index")
            )

            # 4. 检查最后训练时间
            trainings = self.db.get_training_records(game_key, limit=1)
            if trainings:
                result['last_trained'] = trainings[0].trained_at.strftime('%Y-%m-%d %H:%M')

            # 5. 判断是否需要训练
            if not result['model_exists']:
                result['needs_training'] = True
                result['reason'] = "模型文件不存在，需要训练"
            elif result['last_trained'] is None:
                result['needs_training'] = True
                result['reason'] = "无训练记录，需要训练"
            else:
                # 检查数据是否比模型新
                try:
                    if latest_draws:
                        data_issue = int(latest_draws[0]['issue_number'])
                        # 假设训练数据用了最近500期
                        if data_issue > 2020000:  # 简化判断
                            result['needs_training'] = True
                            result['reason'] = "有新增数据，建议重新训练"
                        else:
                            result['reason'] = f"模型已训练 ({result['last_trained']})，数据无重大更新"
                except:
                    result['reason'] = "模型状态正常"

        except Exception as e:
            logger.error(f"模型检查失败: {e}")
            result['reason'] = f"检查失败: {e}"

        return result


def sync_game_data(game_key: str, max_fetch: int = 50) -> Dict[str, Any]:
    """同步彩种数据的便捷函数"""
    service = DataSyncService()
    return service.check_and_update(game_key, max_fetch)


def check_model_status(game_key: str) -> Dict[str, Any]:
    """检查模型状态的便捷函数"""
    service = ModelCheckService()
    return service.check_needs_training(game_key)
