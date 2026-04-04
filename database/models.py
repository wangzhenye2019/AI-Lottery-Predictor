# -*- coding: utf-8 -*-
"""
数据库模型定义
使用 SQLAlchemy ORM
"""
from datetime import datetime
from typing import List, Optional
import pandas as pd
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Boolean,
    Float, JSON, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import model_path

Base = declarative_base()


class LotteryDraw(Base):
    """历史开奖记录表"""
    __tablename__ = 'lottery_draws'

    id = Column(Integer, primary_key=True)
    lottery_type = Column(String(10), nullable=False, comment='彩种: ssq/dlt/qlc/fc3d')
    issue_number = Column(String(20), nullable=False, comment='期号')
    draw_date = Column(Date, nullable=False, comment='开奖日期')
    red_balls = Column(JSON, nullable=False, comment='红球数组')
    blue_ball = Column(JSON, nullable=True, comment='蓝球(双色球为整数，大乐透为数组)')
    created_at = Column(DateTime, default=datetime.now, comment='记录创建时间')

    # 索引 - 使用组合唯一索引
    __table_args__ = (
        Index('idx_draws_type_issue', 'lottery_type', 'issue_number', unique=True),
        Index('idx_draw_date', 'draw_date'),
        Index('idx_draws_type_date', 'lottery_type', 'draw_date'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'lottery_type': self.lottery_type,
            'issue_number': self.issue_number,
            'draw_date': self.draw_date.isoformat() if self.draw_date else None,
            'red_balls': self.red_balls,
            'blue_ball': self.blue_ball,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dataframe_row(cls, row, lottery_type: str):
        """从DataFrame行创建对象"""
        # 提取红球列
        red_cols = [col for col in row.index if '红球' in col]
        red_balls = [int(row[col]) for col in sorted(red_cols)]

        # 提取蓝球
        blue_ball = int(row.get('蓝球', 0)) if '蓝球' in row else None

        return cls(
            lottery_type=lottery_type,
            issue_number=str(row['期数']),
            draw_date=pd.to_datetime(row['日期']).date() if '日期' in row else datetime.now().date(),
            red_balls=red_balls,
            blue_ball=blue_ball
        )


class Prediction(Base):
    """预测记录表"""
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True)
    lottery_draw_id = Column(Integer, nullable=False, comment='关联的开奖记录ID')
    lottery_type = Column(String(10), nullable=False, comment='彩种')
    issue_number = Column(String(20), nullable=False, comment='预测期号')
    predicted_red = Column(JSON, nullable=False, comment='预测红球')
    predicted_blue = Column(Integer, nullable=True, comment='预测蓝球')
    strategy_used = Column(String(50), nullable=False, comment='使用的策略')
    confidence_score = Column(Float, nullable=True, comment='置信度分数')
    model_version = Column(String(50), nullable=True, comment='模型版本')
    actual_red = Column(JSON, nullable=True, comment='实际开奖红球')
    actual_blue = Column(Integer, nullable=True, comment='实际开奖蓝球')
    is_hit = Column(Boolean, nullable=True, comment='是否命中')
    hit_count = Column(Integer, nullable=True, comment='命中红球数量')
    created_at = Column(DateTime, default=datetime.now, comment='预测时间')

    __table_args__ = (
        Index('idx_predictions_type_issue', 'lottery_type', 'issue_number'),
        Index('idx_predictions_created_at', 'created_at'),
        Index('idx_predictions_is_hit', 'is_hit'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'lottery_draw_id': self.lottery_draw_id,
            'lottery_type': self.lottery_type,
            'issue_number': self.issue_number,
            'predicted_red': self.predicted_red,
            'predicted_blue': self.predicted_blue,
            'strategy_used': self.strategy_used,
            'confidence_score': self.confidence_score,
            'model_version': self.model_version,
            'actual_red': self.actual_red,
            'actual_blue': self.actual_blue,
            'is_hit': self.is_hit,
            'hit_count': self.hit_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def calculate_hit(self):
        """计算命中情况"""
        if self.actual_red and self.predicted_red:
            hit_red = len(set(self.predicted_red) & set(self.actual_red))
            self.hit_count = hit_red
            # 双色球6红全中才算命中，大乐透5红全中
            required = 6 if self.lottery_type == 'ssq' else 5
            self.is_hit = (hit_red >= required)
            return self.is_hit, hit_red
        return None, 0


class ModelTraining(Base):
    """模型训练记录表"""
    __tablename__ = 'model_training'

    id = Column(Integer, primary_key=True)
    lottery_type = Column(String(10), nullable=False, comment='彩种')
    model_version = Column(String(50), nullable=False, comment='模型版本')
    training_data_range = Column(JSON, nullable=False, comment='训练数据范围')
    hyperparameters = Column(JSON, nullable=False, comment='超参数')
    metrics = Column(JSON, nullable=False, comment='训练指标')
    model_path = Column(String(500), nullable=False, comment='模型文件路径')
    training_samples = Column(Integer, nullable=True, comment='训练样本数')
    validation_samples = Column(Integer, nullable=True, comment='验证样本数')
    trained_at = Column(DateTime, default=datetime.now, comment='训练时间')
    duration_seconds = Column(Integer, nullable=True, comment='训练耗时(秒)')

    __table_args__ = (
        Index('idx_lottery_type_version', 'lottery_type', 'model_version'),
        Index('idx_trained_at', 'trained_at'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'lottery_type': self.lottery_type,
            'model_version': self.model_version,
            'training_data_range': self.training_data_range,
            'hyperparameters': self.hyperparameters,
            'metrics': self.metrics,
            'model_path': self.model_path,
            'training_samples': self.training_samples,
            'validation_samples': self.validation_samples,
            'trained_at': self.trained_at.isoformat() if self.trained_at else None,
            'duration_seconds': self.duration_seconds
        }
