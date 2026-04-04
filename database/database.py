# -*- coding: utf-8 -*-
"""
数据库管理器
支持 SQLite（开发）和 PostgreSQL（生产）
"""
import os
from datetime import datetime
import pandas as pd
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from loguru import logger
from .models import Base, LotteryDraw, Prediction, ModelTraining


class DatabaseManager:
    """数据库管理器单例"""

    _instance: Optional['DatabaseManager'] = None

    def __new__(cls, db_url: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_url: Optional[str] = None):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.db_url = db_url or self._get_default_db_url()
        self.engine = None
        self.SessionLocal = None
        self._connect()

    def _get_default_db_url(self) -> str:
        """获取默认数据库连接URL"""
        # 优先使用环境变量
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            return db_url

        # 开发环境使用 SQLite
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(base_dir, 'data', 'lottery.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return f'sqlite:///{db_path}'

    def _connect(self):
        """连接数据库"""
        try:
            self.engine = create_engine(
                self.db_url,
                echo=os.getenv('SQL_ECHO', 'false').lower() == 'true',
                pool_pre_ping=True,
                connect_args={"check_same_thread": False} if self.db_url.startswith('sqlite') else {}
            )

            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            # 创建表（如果不存在）
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"数据库连接成功: {self.db_url}")

        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    @contextmanager
    def get_session(self) -> Session:
        """获取数据库会话（上下文管理器）"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")

    # ========== 历史开奖记录操作 ==========

    def upsert_lottery_draws(self, data: pd.DataFrame, lottery_type: str) -> int:
        """
        批量插入或更新历史开奖记录

        Args:
            data: 包含历史数据的DataFrame
            lottery_type: 彩种类型

        Returns:
            插入/更新的记录数
        """
        from .models import LotteryDraw

        count = 0
        with self.get_session() as session:
            for _, row in data.iterrows():
                # 检查是否已存在
                issue = str(row['期数'])
                existing = session.query(LotteryDraw).filter_by(
                    lottery_type=lottery_type,
                    issue_number=issue
                ).first()

                if existing:
                    # 更新现有记录
                    existing.draw_date = pd.to_datetime(row['日期']).date() if '日期' in row else existing.draw_date
                    # 更新红球和蓝球
                    red_cols = [col for col in row.index if '红球' in col]
                    existing.red_balls = [int(row[col]) for col in sorted(red_cols)]
                    if '蓝球' in row:
                        # 蓝球可能是整数(双色球)或列表(大乐透)
                        blue_val = row['蓝球']
                        if isinstance(blue_val, list):
                            existing.blue_ball = blue_val
                        else:
                            existing.blue_ball = int(blue_val) if blue_val else None
                else:
                    # 创建新记录
                    red_cols = [col for col in row.index if '红球' in col]
                    red_balls = [int(row[col]) for col in sorted(red_cols)]
                    blue_val = row.get('蓝球')
                    if isinstance(blue_val, list):
                        blue_ball = blue_val
                    else:
                        blue_ball = int(blue_val) if blue_val else None

                    draw = LotteryDraw(
                        lottery_type=lottery_type,
                        issue_number=issue,
                        draw_date=pd.to_datetime(row['日期']).date() if '日期' in row else datetime.now().date(),
                        red_balls=red_balls,
                        blue_ball=blue_ball
                    )
                    session.add(draw)
                    count += 1

        logger.info(f"彩票类型 {lottery_type}: 新增 {count} 条记录")
        return count

    def get_lottery_draws(
        self,
        lottery_type: str,
        limit: Optional[int] = None,
        start_issue: Optional[str] = None,
        end_issue: Optional[str] = None
    ) -> List[LotteryDraw]:
        """
        查询历史开奖记录

        Args:
            lottery_type: 彩种类型
            limit: 限制返回数量
            start_issue: 起始期号
            end_issue: 结束期号

        Returns:
            LotteryDraw 对象列表
        """
        from .models import LotteryDraw

        with self.get_session() as session:
            query = session.query(LotteryDraw).filter_by(lottery_type=lottery_type)

            if start_issue or end_issue:
                if start_issue:
                    query = query.filter(LotteryDraw.issue_number >= start_issue)
                if end_issue:
                    query = query.filter(LotteryDraw.issue_number <= end_issue)
            else:
                query = query.order_by(LotteryDraw.issue_number.desc())

            if limit:
                query = query.limit(limit)

            return query.all()

    def get_lottery_draws_dict(
        self,
        lottery_type: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        查询历史开奖记录（返回字典列表，避免SQLAlchemy session问题）
        """
        from .models import LotteryDraw

        with self.get_session() as session:
            query = session.query(LotteryDraw).filter_by(lottery_type=lottery_type)
            query = query.order_by(LotteryDraw.issue_number.desc())
            if limit:
                query = query.limit(limit)

            results = []
            for draw in query.all():
                results.append({
                    'id': draw.id,
                    'lottery_type': draw.lottery_type,
                    'issue_number': draw.issue_number,
                    'draw_date': draw.draw_date,
                    'red_balls': draw.red_balls,
                    'blue_ball': draw.blue_ball,
                })
            return results

    def get_latest_draw(self, lottery_type: str) -> Optional[LotteryDraw]:
        """获取最新一期开奖记录"""
        draws = self.get_lottery_draws(lottery_type, limit=1)
        return draws[0] if draws else None

    def count_draws(self, lottery_type: str) -> int:
        """统计指定彩种的记录数"""
        from .models import LotteryDraw

        with self.get_session() as session:
            return session.query(LotteryDraw).filter_by(lottery_type=lottery_type).count()

    # ========== 预测记录操作 ==========

    def save_prediction(
        self,
        lottery_type: str,
        issue_number: str,
        predicted_red: List[int],
        predicted_blue: Optional[int],
        strategy_used: str,
        confidence_score: Optional[float] = None,
        model_version: Optional[str] = None,
        lottery_draw_id: Optional[int] = None
    ) -> Prediction:
        """
        保存预测记录

        Args:
            lottery_draw_id: 关联的开奖记录ID（如果已知）

        Returns:
            Prediction 对象
        """
        with self.get_session() as session:
            prediction = Prediction(
                lottery_draw_id=lottery_draw_id,
                lottery_type=lottery_type,
                issue_number=issue_number,
                predicted_red=predicted_red,
                predicted_blue=predicted_blue,
                strategy_used=strategy_used,
                confidence_score=confidence_score,
                model_version=model_version
            )
            session.add(prediction)
            session.flush()  # 获取 ID
            return prediction

    def update_prediction_result(
        self,
        prediction_id: int,
        actual_red: List[int],
        actual_blue: Optional[int]
    ) -> bool:
        """更新预测结果（实际开奖号码）"""
        with self.get_session() as session:
            prediction = session.query(Prediction).get(prediction_id)
            if not prediction:
                return False

            prediction.actual_red = actual_red
            prediction.actual_blue = actual_blue
            prediction.calculate_hit()
            return True

    def get_predictions(
        self,
        lottery_type: Optional[str] = None,
        strategy: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Prediction]:
        """查询预测记录"""
        with self.get_session() as session:
            query = session.query(Prediction)

            if lottery_type:
                query = query.filter_by(lottery_type=lottery_type)
            if strategy:
                query = query.filter_by(strategy_used=strategy)

            query = query.order_by(Prediction.created_at.desc())
            if limit:
                query = query.limit(limit)

            return query.all()

    def get_hit_rate(self, lottery_type: str, strategy: Optional[str] = None) -> Dict[str, Any]:
        """计算命中率统计"""
        with self.get_session() as session:
            query = session.query(Prediction).filter_by(lottery_type=lottery_type)

            if strategy:
                query = query.filter_by(strategy_used=strategy)

            predictions = query.all()

            total = len(predictions)
            if total == 0:
                return {'total': 0, 'hit_count': 0, 'hit_rate': 0.0}

            hit_count = sum(1 for p in predictions if p.is_hit)
            hit_rate = hit_count / total

            # 计算平均命中红球数
            avg_hit = sum(p.hit_count or 0 for p in predictions) / total

            return {
                'total': total,
                'hit_count': hit_count,
                'hit_rate': round(hit_rate, 4),
                'avg_hit_red': round(avg_hit, 2)
            }

    # ========== 模型训练记录操作 ==========

    def save_training_record(
        self,
        lottery_type: str,
        model_version: str,
        training_data_range: Dict[str, Any],
        hyperparameters: Dict[str, Any],
        metrics: Dict[str, Any],
        model_path: str,
        training_samples: int,
        validation_samples: int,
        duration_seconds: int
    ) -> ModelTraining:
        """保存模型训练记录"""
        with self.get_session() as session:
            record = ModelTraining(
                lottery_type=lottery_type,
                model_version=model_version,
                training_data_range=training_data_range,
                hyperparameters=hyperparameters,
                metrics=metrics,
                model_path=model_path,
                training_samples=training_samples,
                validation_samples=validation_samples,
                duration_seconds=duration_seconds
            )
            session.add(record)
            session.flush()
            return record

    def get_latest_training(self, lottery_type: str) -> Optional[ModelTraining]:
        """获取最新训练记录"""
        with self.get_session() as session:
            return session.query(ModelTraining)\
                .filter_by(lottery_type=lottery_type)\
                .order_by(ModelTraining.trained_at.desc())\
                .first()

    def get_training_records(self, lottery_type: str, limit: int = 10) -> List[ModelTraining]:
        """获取训练记录列表"""
        from .models import ModelTraining
        with self.get_session() as session:
            return session.query(ModelTraining)\
                .filter_by(lottery_type=lottery_type)\
                .order_by(ModelTraining.trained_at.desc())\
                .limit(limit)\
                .all()

    # ========== 工具方法 ==========

    def migrate_from_csv(self, data_dir: str) -> Dict[str, int]:
        """
        从 CSV 文件迁移历史数据到数据库

        Args:
            data_dir: 数据目录（包含 ssq/dlt/qlc/fc3d 子目录）

        Returns:
            各彩种迁移的记录数统计
        """
        import pandas as pd
        from .models import LotteryDraw

        stats = {}
        for lottery_type in ['ssq', 'dlt', 'qlc', 'fc3d']:
            csv_path = os.path.join(data_dir, lottery_type, 'data.csv')
            if not os.path.exists(csv_path):
                logger.warning(f"文件不存在: {csv_path}")
                continue

            df = pd.read_csv(csv_path)
            count = self.upsert_lottery_draws(df, lottery_type)
            stats[lottery_type] = count

        logger.info(f"数据迁移完成: {stats}")
        return stats

    def backup_database(self, backup_path: str) -> bool:
        """备份数据库（仅 SQLite）"""
        if not self.db_url.startswith('sqlite'):
            logger.warning("备份功能仅支持 SQLite")
            return False

        import shutil
        db_file = self.db_url.replace('sqlite:///', '')
        if os.path.exists(db_file):
            shutil.copy2(db_file, backup_path)
            logger.info(f"数据库已备份到: {backup_path}")
            return True
        return False


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def init_db(db_url: Optional[str] = None) -> DatabaseManager:
    """初始化数据库"""
    global _db_manager
    _db_manager = DatabaseManager(db_url)
    return _db_manager
