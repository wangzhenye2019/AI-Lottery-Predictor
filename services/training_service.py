# -*- coding: utf-8 -*-
"""
训练服务模块
支持多轮训练、模型版本管理、超参数调优
"""
import os
import json
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
import numpy as np
from loguru import logger
from database import get_db_manager
from config import model_args, model_path
from modeling import LstmWithCRFModel, SignalLstmModel, tf
from utils.logger import log


class TrainingService:
    """训练服务类"""

    def __init__(self, lottery_type: str = "ssq", use_db: bool = True):
        """
        初始化训练服务

        Args:
            lottery_type: 彩种类型
            use_db: 是否使用数据库记录
        """
        self.lottery_type = lottery_type
        self.use_db = use_db
        self.db = get_db_manager() if use_db else None
        self.model_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def prepare_training_data(
        self,
        data: pd.DataFrame,
        sequence_len: int,
        window_size: int
    ) -> tuple:
        """
        准备训练数据

        Args:
            data: 历史数据
            sequence_len: 序列长度
            window_size: 窗口大小

        Returns:
            (X_train, y_train, X_val, y_val)
        """
        from sklearn.model_selection import train_test_split

        # 提取特征和标签
        red_cols = [col for col in data.columns if '红球' in col]
        blue_col = '蓝球' if '蓝球' in data.columns else None

        # 构建序列数据
        X_list = []
        y_red_list = []
        y_blue_list = []

        for i in range(window_size, len(data)):
            # 输入窗口
            window = data.iloc[i-window_size:i]
            features = window[red_cols].astype(int).values.flatten()

            if blue_col:
                blue_features = window[blue_col].astype(int).values
                features = np.concatenate([features, blue_features])

            X_list.append(features)

            # 标签（下一期）
            next_row = data.iloc[i]
            y_red = [int(next_row[col]) - 1 for col in red_cols]  # 0-based
            y_red_list.append(y_red)

            if blue_col:
                y_blue = int(next_row[blue_col]) - 1  # 0-based
                y_blue_list.append(y_blue)

        X = np.array(X_list, dtype=np.int32)
        y_red = np.array(y_red_list, dtype=np.int32)
        y_blue = np.array(y_blue_list, dtype=np.int32) if y_blue_list else None

        # 划分训练集和验证集
        if len(X) > 10:
            X_train, X_val, y_red_train, y_red_val = train_test_split(
                X, y_red, test_size=0.2, random_state=42
            )
            if y_blue is not None:
                _, _, y_blue_train, y_blue_val = train_test_split(
                    X, y_blue, test_size=0.2, random_state=42
                )
            else:
                y_blue_train = y_blue_val = None
        else:
            X_train, X_val = X, X
            y_red_train, y_red_val = y_red, y_red
            y_blue_train, y_blue_val = y_blue, y_blue

        logger.info(f"数据准备完成: 训练集 {len(X_train)} 条, 验证集 {len(X_val)} 条")
        return (X_train, y_red_train, y_blue_train,
                X_val, y_red_val, y_blue_val)

    def train_lstm_model(
        self,
        data: pd.DataFrame,
        model_type: str = 'red',  # 'red' or 'blue'
        hyperparams: Optional[Dict[str, Any]] = None,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        训练 LSTM 模型

        Args:
            data: 历史数据
            model_type: 模型类型
            hyperparams: 超参数
            save_path: 保存路径

        Returns:
            训练结果字典
        """
        logger.info(f"开始训练 {self.lottery_type} {model_type} 模型...")

        m_args = model_args[self.lottery_type]['model_args']
        train_args = model_args[self.lottery_type]['train_args']

        # 合并超参数
        if hyperparams:
            m_args.update(hyperparams)

        # 准备数据
        sequence_len = m_args['sequence_len'] if model_type == 'red' else m_args.get('blue_sequence_len', 2)
        window_size = m_args['windows_size']

        X_train, y_red_train, y_blue_train, X_val, y_red_val, y_blue_val = \
            self.prepare_training_data(data, sequence_len, window_size)

        y_train = y_red_train if model_type == 'red' else y_blue_train
        y_val = y_red_val if model_type == 'red' else y_blue_val

        if y_train is None:
            raise ValueError(f"模型类型 {model_type} 无可用标签")

        # 构建模型
        tf.compat.v1.reset_default_graph()

        if model_type == 'red':
            if self.lottery_type in ['ssq', 'qlc']:
                model = LstmWithCRFModel(
                    batch_size=m_args['batch_size'],
                    n_class=m_args['red_n_class'],
                    ball_num=sequence_len,
                    w_size=window_size,
                    embedding_size=m_args['red_embedding_size'],
                    words_size=m_args['red_n_class'],
                    hidden_size=m_args['red_hidden_size'],
                    layer_size=m_args['red_layer_size']
                )
            else:
                model = LstmWithCRFModel(
                    batch_size=m_args['batch_size'],
                    n_class=m_args['red_n_class'],
                    ball_num=sequence_len,
                    w_size=window_size,
                    embedding_size=m_args['red_embedding_size'],
                    words_size=m_args['red_n_class'],
                    hidden_size=m_args['red_hidden_size'],
                    layer_size=m_args['red_layer_size']
                )
        else:  # blue
            if self.lottery_type in ['ssq', 'qlc']:
                model = SignalLstmModel(
                    batch_size=m_args['batch_size'],
                    n_class=m_args['blue_n_class'],
                    w_size=window_size,
                    embedding_size=m_args['blue_embedding_size'],
                    hidden_size=m_args['blue_hidden_size'],
                    outputs_size=m_args['blue_n_class'],
                    layer_size=m_args['blue_layer_size']
                )
            else:
                model = LstmWithCRFModel(
                    batch_size=m_args['batch_size'],
                    n_class=m_args['blue_n_class'],
                    ball_num=sequence_len,
                    w_size=window_size,
                    embedding_size=m_args['blue_embedding_size'],
                    words_size=m_args['blue_n_class'],
                    hidden_size=m_args['blue_hidden_size'],
                    layer_size=m_args['blue_layer_size']
                )

        # 训练配置
        sess_config = tf.compat.v1.ConfigProto(
            intra_op_parallelism_threads=4,
            inter_op_parallelism_threads=4,
            allow_soft_placement=True
        )

        with tf.compat.v1.Session(config=sess_config) as sess:
            saver = tf.compat.v1.train.Saver()

            # 初始化变量
            sess.run(tf.compat.v1.global_variables_initializer())

            # 训练循环
            epochs = m_args[f'{model_type}_epochs']
            batch_size = m_args['batch_size']

            train_losses = []
            val_losses = []

            start_time = time.time()

            for epoch in range(epochs):
                # 打乱数据
                indices = np.random.permutation(len(X_train))
                X_train_shuffled = X_train[indices]
                y_train_shuffled = y_train[indices]

                # Mini-batch 训练
                epoch_loss = 0
                n_batches = 0

                for i in range(0, len(X_train_shuffled), batch_size):
                    batch_X = X_train_shuffled[i:i+batch_size]
                    batch_y = y_train_shuffled[i:i+batch_size]

                    # 构建 feed_dict
                    feed_dict = {
                        "inputs:0": batch_X,
                        "labels:0": batch_y,
                        "sequence_length:0": np.array([sequence_len] * len(batch_X)),
                        "dropout_keep_prob:0": 1.0 - train_args.get(f'{model_type}_dropout', 0.3)
                    }

                    # 运行训练步骤
                    loss, _ = sess.run(
                        [model.loss, model.train_op],
                        feed_dict=feed_dict
                    )
                    epoch_loss += loss
                    n_batches += 1

                avg_loss = epoch_loss / n_batches
                train_losses.append(avg_loss)

                # 验证
                if len(X_val) > 0:
                    val_feed = {
                        "inputs:0": X_val,
                        "labels:0": y_val,
                        "sequence_length:0": np.array([sequence_len] * len(X_val)),
                        "dropout_keep_prob:0": 1.0
                    }
                    val_loss = sess.run(model.loss, feed_dict=val_feed)
                    val_losses.append(val_loss)

                    logger.info(f"  Epoch {epoch+1}/{epochs}: train_loss={avg_loss:.4f}, val_loss={val_loss:.4f}")
                else:
                    logger.info(f"  Epoch {epoch+1}/{epochs}: train_loss={avg_loss:.4f}")

            duration = time.time() - start_time

            # 保存模型
            if save_path is None:
                save_path = os.path.join(model_path, self.lottery_type, f'{model_type}_ball_model')

            os.makedirs(save_path, exist_ok=True)
            model_path_full = os.path.join(save_path, f'{model_type}_ball_model.ckpt')
            saver.save(sess, model_path_full)

            logger.info(f"模型已保存到: {model_path_full}")

        # 记录训练信息
        result = {
            'lottery_type': self.lottery_type,
            'model_type': model_type,
            'model_version': self.model_version,
            'epochs': epochs,
            'final_train_loss': float(train_losses[-1]) if train_losses else None,
            'final_val_loss': float(val_losses[-1]) if val_losses else None,
            'duration_seconds': int(duration),
            'samples': len(X_train),
            'model_path': model_path_full
        }

        # 保存到数据库
        if self.use_db and self.db:
            try:
                # 获取完整训练记录
                training_record = self.db.save_training_record(
                    lottery_type=self.lottery_type,
                    model_version=self.model_version,
                    training_data_range={
                        'start_index': 0,
                        'end_index': len(data),
                        'total_records': len(data)
                    },
                    hyperparameters={**m_args, **train_args},
                    metrics={
                        'train_losses': train_losses,
                        'val_losses': val_losses,
                        'final_train_loss': result['final_train_loss'],
                        'final_val_loss': result['final_val_loss']
                    },
                    model_path=model_path_full,
                    training_samples=len(X_train),
                    validation_samples=len(X_val),
                    duration_seconds=result['duration_seconds']
                )
                logger.info(f"训练记录已保存到数据库，ID: {training_record.id}")
            except Exception as e:
                logger.warning(f"保存训练记录失败: {e}")

        logger.info(f"{self.lottery_type} {model_type} 模型训练完成，耗时 {duration:.2f} 秒")
        return result

    def train_all_models(
        self,
        data: pd.DataFrame,
        hyperparams: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        训练所有模型（红球+蓝球）

        Args:
            data: 历史数据
            hyperparams: 超参数

        Returns:
            训练结果字典
        """
        logger.info(f"开始训练 {self.lottery_type} 全部模型...")

        results = {}

        # 训练红球模型
        try:
            red_result = self.train_lstm_model(
                data=data,
                model_type='red',
                hyperparams=hyperparams
            )
            results['red'] = red_result
        except Exception as e:
            logger.error(f"红球模型训练失败: {e}")
            results['red'] = {'error': str(e)}

        # 训练蓝球模型
        try:
            blue_result = self.train_lstm_model(
                data=data,
                model_type='blue',
                hyperparams=hyperparams
            )
            results['blue'] = blue_result
        except Exception as e:
            logger.error(f"蓝球模型训练失败: {e}")
            results['blue'] = {'error': str(e)}

        logger.info(f"{self.lottery_type} 全部模型训练完成")
        return results

    def multi_round_training(
        self,
        data: pd.DataFrame,
        n_rounds: int = 3,
        round_data_ratio: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        多轮训练：使用不同数据子集训练多个模型版本

        Args:
            data: 完整历史数据
            n_rounds: 训练轮数
            round_data_ratio: 每轮使用的数据比例（滚动窗口）

        Returns:
            训练结果列表
        """
        logger.info(f"开始多轮训练: {n_rounds} 轮")

        results = []
        total_len = len(data)

        for round_idx in range(n_rounds):
            logger.info(f"=== 第 {round_idx + 1}/{n_rounds} 轮训练 ===")

            # 计算数据范围（滑动窗口）
            start_idx = int(round_idx * (1 - round_data_ratio) * total_len)
            end_idx = min(start_idx + int(total_len * round_data_ratio), total_len)

            round_data = data.iloc[start_idx:end_idx].reset_index(drop=True)

            logger.info(f"数据范围: {start_idx} - {end_idx} (共 {len(round_data)} 条)")

            # 训练
            round_result = self.train_all_models(round_data)
            round_result['round'] = round_idx + 1
            round_result['data_range'] = {'start': start_idx, 'end': end_idx}
            results.append(round_result)

        logger.info("多轮训练完成")
        return results


def get_training_service(lottery_type: str = "ssq", use_db: bool = True) -> TrainingService:
    """获取训练服务实例"""
    return TrainingService(lottery_type, use_db)
