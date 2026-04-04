# -*- coding: utf-8 -*-
"""
数据访问层 - 统一数据管理
Author: BigCat
"""
import os
import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from config_new import config
from utils.exceptions_new import DataError, handle_exceptions
from utils.logger_new import get_logger, log_performance

logger = get_logger(__name__)

Base = declarative_base()


class LotteryDraw(Base):
    """彩票开奖记录表"""
    __tablename__ = 'lottery_draws'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lottery_type = Column(String(10), nullable=False, index=True)  # 彩票类型
    issue = Column(String(20), nullable=False)  # 期号
    draw_date = Column(DateTime, nullable=False)  # 开奖日期
    numbers = Column(Text, nullable=False)  # 开奖号码JSON
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class PredictionResult(Base):
    """预测结果表"""
    __tablename__ = 'prediction_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lottery_type = Column(String(10), nullable=False, index=True)
    strategy_name = Column(String(50), nullable=False)
    issue = Column(String(20), nullable=False)
    predicted_numbers = Column(Text, nullable=False)  # 预测号码JSON
    confidence_score = Column(Float, nullable=True)  # 置信度
    created_at = Column(DateTime, default=datetime.now)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = create_engine(
            config.database.url,
            echo=config.database.echo,
            pool_size=config.database.pool_size,
            max_overflow=config.database.max_overflow
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库初始化完成")
        except SQLAlchemyError as e:
            logger.error(f"数据库初始化失败: {e}")
            raise DataError(f"数据库初始化失败: {e}")
    
    @contextmanager
    def get_session(self):
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise DataError(f"数据库操作失败: {e}")
        finally:
            session.close()
    
    @log_performance
    def save_lottery_draw(self, lottery_type: str, issue: str, draw_date: datetime, numbers: List[int]) -> bool:
        """保存开奖记录"""
        import json
        
        try:
            with self.get_session() as session:
                # 检查是否已存在
                existing = session.query(LotteryDraw).filter_by(
                    lottery_type=lottery_type, issue=issue
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.draw_date = draw_date
                    existing.numbers = json.dumps(numbers)
                    existing.updated_at = datetime.now()
                else:
                    # 创建新记录
                    draw = LotteryDraw(
                        lottery_type=lottery_type,
                        issue=issue,
                        draw_date=draw_date,
                        numbers=json.dumps(numbers)
                    )
                    session.add(draw)
                
                logger.info(f"保存开奖记录: {lottery_type} {issue}")
                return True
        except Exception as e:
            logger.error(f"保存开奖记录失败: {e}")
            return False
    
    @log_performance
    def get_lottery_draws(self, lottery_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取开奖记录"""
        import json
        
        try:
            with self.get_session() as session:
                draws = session.query(LotteryDraw).filter_by(
                    lottery_type=lottery_type
                ).order_by(LotteryDraw.draw_date.desc()).limit(limit).all()
                
                result = []
                for draw in draws:
                    result.append({
                        'issue': draw.issue,
                        'draw_date': draw.draw_date,
                        'numbers': json.loads(draw.numbers)
                    })
                
                return result
        except Exception as e:
            logger.error(f"获取开奖记录失败: {e}")
            return []
    
    @log_performance
    def save_prediction_result(self, lottery_type: str, strategy_name: str, issue: str, 
                             predicted_numbers: List[int], confidence_score: float = None) -> bool:
        """保存预测结果"""
        import json
        
        try:
            with self.get_session() as session:
                prediction = PredictionResult(
                    lottery_type=lottery_type,
                    strategy_name=strategy_name,
                    issue=issue,
                    predicted_numbers=json.dumps(predicted_numbers),
                    confidence_score=confidence_score
                )
                session.add(prediction)
                
                logger.info(f"保存预测结果: {lottery_type} {strategy_name} {issue}")
                return True
        except Exception as e:
            logger.error(f"保存预测结果失败: {e}")
            return False
    
    @log_performance
    def get_prediction_results(self, lottery_type: str, strategy_name: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取预测结果"""
        import json
        
        try:
            with self.get_session() as session:
                query = session.query(PredictionResult).filter_by(lottery_type=lottery_type)
                
                if strategy_name:
                    query = query.filter_by(strategy_name=strategy_name)
                
                results = query.order_by(PredictionResult.created_at.desc()).limit(limit).all()
                
                return [{
                    'strategy_name': result.strategy_name,
                    'issue': result.issue,
                    'predicted_numbers': json.loads(result.predicted_numbers),
                    'confidence_score': result.confidence_score,
                    'created_at': result.created_at
                } for result in results]
        except Exception as e:
            logger.error(f"获取预测结果失败: {e}")
            return []


class CSVDataManager:
    """CSV数据管理器 - 兼容原有CSV格式"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or config.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    @log_performance
    def save_to_csv(self, data: pd.DataFrame, lottery_type: str, filename: str = None) -> bool:
        """保存数据到CSV"""
        try:
            if filename is None:
                filename = f"{lottery_type}_data.csv"
            
            filepath = self.data_dir / lottery_type / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            data.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"CSV数据已保存: {filepath}")
            return True
        except Exception as e:
            logger.error(f"保存CSV数据失败: {e}")
            return False
    
    @log_performance
    def load_from_csv(self, lottery_type: str, filename: str = None) -> Optional[pd.DataFrame]:
        """从CSV加载数据"""
        try:
            if filename is None:
                filename = f"{lottery_type}_data.csv"
            
            filepath = self.data_dir / lottery_type / filename
            
            if not filepath.exists():
                logger.warning(f"CSV文件不存在: {filepath}")
                return None
            
            data = pd.read_csv(filepath, encoding='utf-8')
            logger.info(f"CSV数据已加载: {filepath}")
            return data
        except Exception as e:
            logger.error(f"加载CSV数据失败: {e}")
            return None
    
    @log_performance
    def append_to_csv(self, data: pd.DataFrame, lottery_type: str, filename: str = None) -> bool:
        """追加数据到CSV"""
        try:
            existing_data = self.load_from_csv(lottery_type, filename)
            
            if existing_data is not None:
                # 合并数据，去重
                combined_data = pd.concat([existing_data, data], ignore_index=True)
                combined_data = combined_data.drop_duplicates()
            else:
                combined_data = data
            
            return self.save_to_csv(combined_data, lottery_type, filename)
        except Exception as e:
            logger.error(f"追加CSV数据失败: {e}")
            return False


class DataManager:
    """统一数据管理器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.csv_manager = CSVDataManager()
    
    @log_performance
    def import_csv_to_database(self, lottery_type: str, csv_file: str = None) -> bool:
        """将CSV数据导入数据库"""
        try:
            data = self.csv_manager.load_from_csv(lottery_type, csv_file)
            if data is None or data.empty:
                logger.warning("没有数据可导入")
                return False
            
            success_count = 0
            for _, row in data.iterrows():
                # 假设CSV格式包含期号、开奖日期、号码等字段
                issue = str(row.get('issue', ''))
                draw_date = pd.to_datetime(row.get('draw_date', datetime.now()))
                
                # 提取号码 - 需要根据实际CSV格式调整
                numbers = []
                for col in data.columns:
                    if '红球' in col or '蓝球' in col or '号码' in col:
                        if pd.notna(row[col]):
                            numbers.append(int(row[col]))
                
                if numbers and issue:
                    if self.db_manager.save_lottery_draw(lottery_type, issue, draw_date, numbers):
                        success_count += 1
            
            logger.info(f"成功导入 {success_count} 条记录到数据库")
            return success_count > 0
        except Exception as e:
            logger.error(f"导入CSV到数据库失败: {e}")
            return False
    
    @log_performance
    def export_database_to_csv(self, lottery_type: str, csv_file: str = None) -> bool:
        """将数据库数据导出为CSV"""
        try:
            draws = self.db_manager.get_lottery_draws(lottery_type, limit=10000)
            
            if not draws:
                logger.warning("没有数据可导出")
                return False
            
            # 转换为DataFrame
            data_rows = []
            for draw in draws:
                row = {
                    'issue': draw['issue'],
                    'draw_date': draw['draw_date']
                }
                
                # 根据号码数量分配列
                numbers = draw['numbers']
                for i, num in enumerate(numbers):
                    if i < 6:  # 前6个作为红球
                        row[f'红球{i+1}'] = num
                    else:  # 后面的作为蓝球
                        row[f'蓝球{i-5}'] = num
                
                data_rows.append(row)
            
            df = pd.DataFrame(data_rows)
            return self.csv_manager.save_to_csv(df, lottery_type, csv_file)
        except Exception as e:
            logger.error(f"导出数据库到CSV失败: {e}")
            return False


# 全局数据管理器实例
data_manager = DataManager()
