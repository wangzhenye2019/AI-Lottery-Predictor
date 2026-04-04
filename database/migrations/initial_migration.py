# -*- coding: utf-8 -*-
"""
初始数据迁移脚本
将现有 CSV 数据迁移到数据库
"""
import os
import sys
import pandas as pd
from pathlib import Path
from loguru import logger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_db


def migrate_all_data(data_dir: str = None):
    """
    迁移所有彩种数据

    Args:
        data_dir: 数据目录路径，默认使用 config 中的路径
    """
    if data_dir is None:
        from config import name_path
        data_dir = os.path.join(project_root, 'data')

    logger.info(f"开始数据迁移，源目录: {data_dir}")

    # 初始化数据库
    db = init_db()

    # 迁移各彩种
    lottery_types = ['ssq', 'dlt', 'qlc', 'fc3d']
    stats = {}

    for lottery_type in lottery_types:
        csv_path = os.path.join(data_dir, lottery_type, 'data.csv')
        if not os.path.exists(csv_path):
            logger.warning(f"文件不存在，跳过: {csv_path}")
            continue

        try:
            df = pd.read_csv(csv_path)
            count = db.upsert_lottery_draws(df, lottery_type)
            stats[lottery_type] = {
                'total_rows': len(df),
                'inserted': count,
                'file': csv_path
            }
            logger.info(f"{lottery_type}: 共 {len(df)} 行，新增 {count} 条")
        except Exception as e:
            logger.error(f"迁移 {lottery_type} 失败: {e}")
            stats[lottery_type] = {'error': str(e)}

    # 输出统计
    logger.info("=== 数据迁移完成 ===")
    for lt, info in stats.items():
        if 'error' in info:
            logger.error(f"{lt}: {info['error']}")
        else:
            logger.info(f"{lt}: {info['inserted']}/{info['total_rows']} 条记录")

    return stats


def verify_migration():
    """验证迁移结果"""
    db = get_db_manager()

    logger.info("=== 验证迁移结果 ===")
    for lottery_type in ['ssq', 'dlt', 'qlc', 'fc3d']:
        count = db.count_draws(lottery_type)
        logger.info(f"{lottery_type}: 数据库中有 {count} 条记录")

        # 查询最新一期
        latest = db.get_latest_draw(lottery_type)
        if latest:
            logger.info(f"  最新期号: {latest.issue_number}, 日期: {latest.draw_date}")
        else:
            logger.warning(f"  未找到记录")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='数据迁移工具')
    parser.add_argument('--data-dir', help='数据目录路径')
    parser.add_argument('--verify', action='store_true', help='仅验证，不迁移')
    parser.add_argument('--reset', action='store_true', help='清空数据库后重新迁移')

    args = parser.parse_args()

    if args.verify:
        verify_migration()
    else:
        if args.reset:
            # 删除数据库文件（仅 SQLite）
            db_file = os.path.join(project_root, 'data', 'lottery.db')
            if os.path.exists(db_file):
                os.remove(db_file)
                logger.info(f"已删除数据库文件: {db_file}")

        stats = migrate_all_data(args.data_dir)
        verify_migration()

        # 返回退出码
        sys.exit(0 if all('error' not in s for s in stats.values()) else 1)
