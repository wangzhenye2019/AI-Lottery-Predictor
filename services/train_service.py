# -*- coding:utf-8 -*-
"""
训练服务模块
统一处理所有训练相关逻辑，消除代码重复
"""
import time
import json
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from typing import Dict, Tuple, Optional
from config import model_args, name_path, data_file_name, ball_name, model_path, pred_key_name, extension
from modeling import LstmWithCRFModel, SignalLstmModel
from utils.logger import log
from utils.exceptions import TrainingError, DataValidationError


class TrainService:
    """训练服务类"""
    
    def __init__(self, name: str = "ssq", train_test_split: float = 0.8):
        """
        初始化训练服务
        
        Args:
            name: 玩法名称 (ssq/dlt)
            train_test_split: 训练集占比
        """
        self.name = name
        self.train_test_split = train_test_split
        self.pred_key = {}
        
        if train_test_split < 0.5:
            raise DataValidationError(
                f"训练集采样比例小于 50%,训练终止",
                field=f"train_test_split={train_test_split}"
            )
    
    def create_data(self, data: pd.DataFrame, windows: int) -> Dict[str, Dict[str, np.ndarray]]:
        """
        创建训练数据
        
        Args:
            data: 数据集
            windows: 训练窗口大小
        
        Returns:
            训练数据字典
        """
        if not len(data):
            raise DataValidationError("数据为空，请执行 get_data.py 进行数据下载")
        
        # 丢弃第 0 列(期号)，保留所有红球和蓝球
        data = data.iloc[:, 1:].values
        log.info(f"训练集数据维度：{data.shape}")
        
        x_data, y_data = [], []
        for i in range(len(data) - windows - 1):
            sub_data = data[i:(i+windows+1), :]
            x_data.append(sub_data[1:])
            y_data.append(sub_data[0])
        
        cut_num = 6 if self.name == "ssq" else 5
        
        x_data = np.array(x_data)
        y_data = np.array(y_data)
        
        log.info(f"x_data original shape: {x_data.shape}")
        log.info(f"y_data original shape: {y_data.shape}")
        
        return {
            "red": {
                "x_data": x_data[:, :, :cut_num],
                "y_data": y_data[:, :cut_num]
            },
            "blue": {
                "x_data": x_data[:, :, cut_num:],
                "y_data": y_data[:, cut_num:]
            }
        }
    
    def create_train_test_data(self, windows: int) -> Tuple[Dict, Dict]:
        """
        划分训练集和测试集
        
        Args:
            windows: 窗口大小
        
        Returns:
            (训练数据，测试数据)
        """
        path = "{}{}".format(name_path[self.name]["path"], data_file_name)
        data = pd.read_csv(path)
        log.info(f"从路径读取数据：{path}")
        
        train_size = int(len(data) * self.train_test_split)
        train_data = self.create_data(data.iloc[:train_size], windows)
        test_data = self.create_data(data.iloc[train_size:], windows)
        
        log.info(
            f"训练集采样率 = {self.train_test_split}, "
            f"测试集采样率 = {round(1 - self.train_test_split, 2)}"
        )
        
        return train_data, test_data
    
    def train_red_ball(
        self,
        x_train: np.ndarray,
        y_train: np.ndarray,
        x_test: np.ndarray,
        y_test: np.ndarray,
        use_optimization: bool = False,
        patience: int = 10,
        use_lr_decay: bool = False,
        decay_rate: float = 0.95,
        save_best_only: bool = False
    ) -> None:
        """
        训练红球模型
        
        Args:
            x_train: 训练特征
            y_train: 训练标签
            x_test: 测试特征
            y_test: 测试标签
            use_optimization: 是否使用优化
            patience: 早停耐心值
            use_lr_decay: 是否使用学习率衰减
            decay_rate: 衰减率
            save_best_only: 是否仅保存最佳模型
        """
        m_args = model_args[self.name]
        
        # 数据预处理
        x_train = x_train - 1
        y_train = y_train - 1
        train_len = x_train.shape[0]
        log.info(f"训练特征维度：{x_train.shape}")
        log.info(f"训练标签维度：{y_train.shape}")
        
        x_test = x_test - 1
        y_test = y_test - 1
        test_len = x_test.shape[0]
        log.info(f"测试特征维度：{x_test.shape}")
        log.info(f"测试标签维度：{y_test.shape}")
        
        start_time = time.time()
        best_loss = float('inf')
        patience_counter = 0
        initial_lr = m_args["train_args"]["red_learning_rate"]
        
        with tf.compat.v1.Session() as sess:
            # 构建模型
            red_model = LstmWithCRFModel(
                batch_size=m_args["model_args"]["batch_size"],
                n_class=m_args["model_args"]["red_n_class"],
                ball_num=m_args["model_args"]["sequence_len"] if self.name == "ssq" 
                         else m_args["model_args"]["red_sequence_len"],
                w_size=m_args["model_args"]["windows_size"],
                embedding_size=m_args["model_args"]["red_embedding_size"],
                words_size=m_args["model_args"]["red_n_class"],
                hidden_size=m_args["model_args"]["red_hidden_size"],
                layer_size=m_args["model_args"]["red_layer_size"]
            )
            
            # 构建优化器
            if use_lr_decay:
                global_step = tf.Variable(0, trainable=False)
                learning_rate = tf.compat.v1.train.exponential_decay(
                    initial_lr, global_step, decay_steps=100,
                    decay_rate=decay_rate, staircase=True
                )
                optimizer = tf.compat.v1.train.AdamOptimizer(
                    learning_rate=learning_rate,
                    beta1=m_args["train_args"]["red_beta1"],
                    beta2=m_args["train_args"]["red_beta2"],
                    epsilon=m_args["train_args"]["red_epsilon"]
                )
                train_step = optimizer.minimize(red_model.loss, global_step=global_step)
            else:
                train_step = tf.compat.v1.train.AdamOptimizer(
                    learning_rate=initial_lr,
                    beta1=m_args["train_args"]["red_beta1"],
                    beta2=m_args["train_args"]["red_beta2"],
                    epsilon=m_args["train_args"]["red_epsilon"]
                ).minimize(red_model.loss)
            
            sess.run(tf.compat.v1.global_variables_initializer())
            saver = tf.compat.v1.train.Saver(max_to_keep=3)
            
            sequence_len = m_args["model_args"]["sequence_len"] if self.name == "ssq" \
                          else m_args["model_args"]["red_sequence_len"]
            
            # 训练循环
            epochs = m_args["model_args"]["red_epochs"]
            batch_size = m_args["model_args"]["batch_size"]
            for epoch in range(epochs):
                epoch_losses = []
                
                for i in range(0, train_len, batch_size):
                    batch_x = x_train[i:i+batch_size]
                    batch_y = y_train[i:i+batch_size]
                    actual_batch_size = batch_x.shape[0]
                    
                    _, loss_, pred = sess.run(
                        [train_step, red_model.loss, red_model.pred_sequence],
                        feed_dict={
                            "inputs:0": batch_x,
                            "tag_indices:0": batch_y,
                            "sequence_length:0": np.array([sequence_len] * actual_batch_size)
                        }
                    )
                    epoch_losses.append(loss_)
                    
                    if i == 0 or (i // batch_size) % 10 == 0:
                        pred_nums = pred[0] + 1
                        true_nums = batch_y[0] + 1
                        
                        # 检查是否完全匹配
                        is_exact_match = np.array_equal(np.sort(pred_nums), np.sort(true_nums))
                        match_str = " ✅ 完全正确" if is_exact_match else ""
                        
                        log.info(
                            f"Epoch {epoch}, Step {i}/{train_len}: "
                            f"loss={loss_:.4f}, "
                            f"true={true_nums}, "
                            f"pred={pred_nums}{match_str}"
                        )
                
                avg_loss = np.mean(epoch_losses)
                log.info(f"Epoch {epoch} 完成，平均 loss: {avg_loss:.4f}")
                
                # 早停检查
                if use_optimization:
                    if avg_loss < best_loss:
                        best_loss = avg_loss
                        patience_counter = 0
                        if save_best_only:
                            self._save_model(saver, sess, "red")
                            log.info("保存最佳红球模型")
                    else:
                        patience_counter += 1
                        log.info(f"早停计数器：{patience_counter}/{patience}")
                        if patience_counter >= patience:
                            log.info("触发早停，停止训练")
                            break
                
                # 保存模型
                if not (save_best_only and use_optimization):
                    self._save_model(saver, sess, "red")
            
            log.info(f"训练耗时：{time.time() - start_time:.2f}秒")
            self.pred_key[ball_name[0][0]] = red_model.pred_sequence.name
            
            # 确保保存模型
            if not (save_best_only and use_optimization):
                self._save_model(saver, sess, "red")
            
            # 模型评估
            self._evaluate_model(
                sess, red_model, x_test, y_test,
                test_len, sequence_len, ball_type="red"
            )
    
    def train_blue_ball(
        self,
        x_train: np.ndarray,
        y_train: np.ndarray,
        x_test: np.ndarray,
        y_test: np.ndarray,
        use_optimization: bool = False,
        patience: int = 10,
        use_lr_decay: bool = False,
        decay_rate: float = 0.95,
        save_best_only: bool = False
    ) -> None:
        """
        训练蓝球模型
        
        Args:
            x_train: 训练特征
            y_train: 训练标签
            x_test: 测试特征
            y_test: 测试标签
            use_optimization: 是否使用优化
            patience: 早停耐心值
            use_lr_decay: 是否使用学习率衰减
            decay_rate: 衰减率
            save_best_only: 是否仅保存最佳模型
        """
        m_args = model_args[self.name]
        
        # 数据预处理
        x_train = x_train - 1
        train_len = x_train.shape[0]
        
        if self.name == "ssq":
            # For blue ball SSQ, x_train has shape (batch_size, windows_size, 1) currently from create_data
            # Let's use reshape to safely flatten the last dimensions
            x_train = x_train.reshape((train_len, m_args["model_args"]["windows_size"]))
            # y_train originally shape is (train_len, 1), so flatten it first
            y_train = y_train.flatten()
            y_train = tf.keras.utils.to_categorical(
                y_train - 1, num_classes=m_args["model_args"]["blue_n_class"]
            )
        else:
            y_train = y_train - 1
        
        log.info(f"训练特征维度：{x_train.shape}")
        log.info(f"训练标签维度：{y_train.shape}")
        
        x_test = x_test - 1
        test_len = x_test.shape[0]
        
        if self.name == "ssq":
            x_test = x_test.reshape((test_len, m_args["model_args"]["windows_size"]))
            # y_test originally shape is (test_len, 1), so flatten it first
            y_test = y_test.flatten()
            y_test = tf.keras.utils.to_categorical(
                y_test - 1, num_classes=m_args["model_args"]["blue_n_class"]
            )
        else:
            y_test = y_test - 1
        
        log.info(f"测试特征维度：{x_test.shape}")
        log.info(f"测试标签维度：{y_test.shape}")
        
        start_time = time.time()
        best_loss = float('inf')
        patience_counter = 0
        initial_lr = m_args["train_args"]["blue_learning_rate"]
        
        with tf.compat.v1.Session() as sess:
            # 构建模型
            if self.name == "ssq":
                blue_model = SignalLstmModel(
                    batch_size=m_args["model_args"]["batch_size"],
                    n_class=m_args["model_args"]["blue_n_class"],
                    w_size=m_args["model_args"]["windows_size"],
                    embedding_size=m_args["model_args"]["blue_embedding_size"],
                    hidden_size=m_args["model_args"]["blue_hidden_size"],
                    outputs_size=m_args["model_args"]["blue_n_class"],
                    layer_size=m_args["model_args"]["blue_layer_size"]
                )
            else:
                blue_model = LstmWithCRFModel(
                    batch_size=m_args["model_args"]["batch_size"],
                    n_class=m_args["model_args"]["blue_n_class"],
                    ball_num=m_args["model_args"]["blue_sequence_len"],
                    w_size=m_args["model_args"]["windows_size"],
                    embedding_size=m_args["model_args"]["blue_embedding_size"],
                    words_size=m_args["model_args"]["blue_n_class"],
                    hidden_size=m_args["model_args"]["blue_hidden_size"],
                    layer_size=m_args["model_args"]["blue_layer_size"]
                )
            
            # 构建优化器
            if use_lr_decay:
                global_step = tf.Variable(0, trainable=False)
                learning_rate = tf.compat.v1.train.exponential_decay(
                    initial_lr, global_step, decay_steps=100,
                    decay_rate=decay_rate, staircase=True
                )
                optimizer = tf.compat.v1.train.AdamOptimizer(
                    learning_rate=learning_rate,
                    beta1=m_args["train_args"]["blue_beta1"],
                    beta2=m_args["train_args"]["blue_beta2"],
                    epsilon=m_args["train_args"]["blue_epsilon"]
                )
                train_step = optimizer.minimize(blue_model.loss, global_step=global_step)
            else:
                train_step = tf.compat.v1.train.AdamOptimizer(
                    learning_rate=initial_lr,
                    beta1=m_args["train_args"]["blue_beta1"],
                    beta2=m_args["train_args"]["blue_beta2"],
                    epsilon=m_args["train_args"]["blue_epsilon"]
                ).minimize(blue_model.loss)
            
            sess.run(tf.compat.v1.global_variables_initializer())
            saver = tf.compat.v1.train.Saver(max_to_keep=3)
            
            sequence_len = "" if self.name == "ssq" else m_args["model_args"]["blue_sequence_len"]
            
            # 训练循环
            epochs = m_args["model_args"]["blue_epochs"]
            batch_size = m_args["model_args"]["batch_size"]
            for epoch in range(epochs):
                epoch_losses = []
                
                for i in range(0, train_len, batch_size):
                    batch_x = x_train[i:i+batch_size]
                    batch_y = y_train[i:i+batch_size]
                    actual_batch_size = batch_x.shape[0]
                    
                    if self.name == "ssq":
                        _, loss_, pred = sess.run(
                            [train_step, blue_model.loss, blue_model.pred_label],
                            feed_dict={
                                "inputs:0": batch_x,
                                "tag_indices:0": batch_y
                            }
                        )
                        if i == 0 or (i // batch_size) % 10 == 0:
                            pred_nums = pred[0] + 1
                            true_nums = np.argmax(batch_y[0]) + 1
                            
                            is_exact_match = (pred_nums == true_nums)
                            match_str = " ✅ 完全正确" if is_exact_match else ""
                            
                            log.info(
                                f"Epoch {epoch}, Step {i}/{train_len}: "
                                f"loss={loss_:.4f}, "
                                f"true={true_nums}, "
                                f"pred={pred_nums}{match_str}"
                            )
                    else:
                        _, loss_, pred = sess.run(
                            [train_step, blue_model.loss, blue_model.pred_sequence],
                            feed_dict={
                                "inputs:0": batch_x,
                                "tag_indices:0": batch_y,
                                "sequence_length:0": np.array([sequence_len] * actual_batch_size)
                            }
                        )
                        if i == 0 or (i // batch_size) % 10 == 0:
                            pred_nums = pred[0] + 1
                            true_nums = batch_y[0] + 1
                            
                            is_exact_match = np.array_equal(np.sort(pred_nums), np.sort(true_nums))
                            match_str = " ✅ 完全正确" if is_exact_match else ""
                            
                            log.info(
                                f"Epoch {epoch}, Step {i}/{train_len}: "
                                f"loss={loss_:.4f}, "
                                f"true={true_nums}, "
                                f"pred={pred_nums}{match_str}"
                            )
                    
                    epoch_losses.append(loss_)
                
                avg_loss = np.mean(epoch_losses)
                log.info(f"Epoch {epoch} 完成，平均 loss: {avg_loss:.4f}")
                
                # 早停检查
                if use_optimization:
                    if avg_loss < best_loss:
                        best_loss = avg_loss
                        patience_counter = 0
                        if save_best_only:
                            self._save_model(saver, sess, "blue")
                            log.info("保存最佳蓝球模型")
                    else:
                        patience_counter += 1
                        log.info(f"早停计数器：{patience_counter}/{patience}")
                        if patience_counter >= patience:
                            log.info("触发早停，停止训练")
                            break
                
                if not (save_best_only and use_optimization):
                    self._save_model(saver, sess, "blue")
            
            log.info(f"训练耗时：{time.time() - start_time:.2f}秒")
            self.pred_key[ball_name[1][0]] = blue_model.pred_label.name if self.name == "ssq" \
                                             else blue_model.pred_sequence.name
            
            if not (save_best_only and use_optimization):
                self._save_model(saver, sess, "blue")
            
            # 模型评估
            self._evaluate_model(
                sess, blue_model, x_test, y_test,
                test_len, sequence_len, ball_type="blue"
            )
    
    def _save_model(
        self, 
        saver: tf.compat.v1.train.Saver, 
        sess: tf.compat.v1.Session, 
        ball_type: str
    ) -> None:
        """保存模型"""
        model_path_str = model_args[self.name]["path"][ball_type]
        model_name = f"{ball_type}_ball_model"
        save_path = os.path.join(model_path_str, f"{model_name}.{extension}")
        saver.save(sess, save_path, write_meta_graph=False)
        log.info(f"已保存{ball_type}球模型")
    
    def _evaluate_model(
        self,
        sess: tf.compat.v1.Session,
        model,
        x_test: np.ndarray,
        y_test: np.ndarray,
        test_len: int,
        sequence_len,
        ball_type: str
    ) -> None:
        """评估模型"""
        log.info(f"模型评估【{name_path[self.name]['name']}】...")
        
        eval_dict = {}
        all_true_count = 0
        
        for j in range(test_len):
            true = y_test[j:(j + 1), :]
            
            if self.name == "ssq" and ball_type == "blue":
                pred = sess.run(model.pred_label, feed_dict={"inputs:0": x_test[j:(j + 1), :]})
            else:
                pred = sess.run(
                    model.pred_sequence,
                    feed_dict={
                        "inputs:0": x_test[j:(j + 1), :, :],
                        "sequence_length:0": np.array([sequence_len] * 1) if sequence_len else None
                    }
                )
            
            count = np.sum(true == pred + 1)
            all_true_count += count
            
            if count in eval_dict:
                eval_dict[count] += 1
            else:
                eval_dict[count] = 1
        
        log.info(f"测试期数：{test_len}")
        for k, v in eval_dict.items():
            log.info(f"命中{k}个球，{v}期，占比：{round(v * 100 / test_len, 2)}%")
        
        if self.name == "ssq" and ball_type == "blue":
            accuracy = round(all_true_count * 100 / test_len, 2)
        else:
            accuracy = round(all_true_count * 100 / (test_len * sequence_len), 2)
        
        log.info(f"整体准确率：{accuracy}%")
    
    def save_pred_keys(self) -> None:
        """保存预测关键节点名"""
        key_path = "{}/{}/{}".format(model_path, self.name, pred_key_name)
        with open(key_path, "w") as f:
            json.dump(self.pred_key, f)
        log.info(f"已保存预测关键节点到：{key_path}")
    
    def train(
        self,
        use_optimization: bool = False,
        patience: int = 10,
        use_lr_decay: bool = False,
        decay_rate: float = 0.95,
        save_best_only: bool = False
    ) -> None:
        """
        完整训练流程
        
        Args:
            use_optimization: 是否使用优化（早停、学习率衰减）
            patience: 早停耐心值
            use_lr_decay: 是否使用学习率衰减
            decay_rate: 衰减率
            save_best_only: 是否仅保存最佳模型
        """
        log.info(f"正在创建【{name_path[self.name]['name']}】训练集和测试集...")
        
        windows = model_args[self.name]["model_args"]["windows_size"]
        train_data, test_data = self.create_train_test_data(windows)
        
        # 训练红球模型
        log.info(f"开始训练【{name_path[self.name]['name']}】红球模型...")
        self.train_red_ball(
            x_train=train_data["red"]["x_data"],
            y_train=train_data["red"]["y_data"],
            x_test=test_data["red"]["x_data"],
            y_test=test_data["red"]["y_data"],
            use_optimization=use_optimization,
            patience=patience,
            use_lr_decay=use_lr_decay,
            decay_rate=decay_rate,
            save_best_only=save_best_only
        )
        
        # 重置计算图
        tf.compat.v1.reset_default_graph()
        
        # 训练蓝球模型
        log.info(f"开始训练【{name_path[self.name]['name']}】蓝球模型...")
        log.info(f"蓝球训练数据 x_data shape: {train_data['blue']['x_data'].shape}")
        
        self.train_blue_ball(
            x_train=train_data["blue"]["x_data"],
            y_train=train_data["blue"]["y_data"],
            x_test=test_data["blue"]["x_data"],
            y_test=test_data["blue"]["y_data"],
            use_optimization=use_optimization,
            patience=patience,
            use_lr_decay=use_lr_decay,
            decay_rate=decay_rate,
            save_best_only=save_best_only
        )
        
        # 保存预测关键节点
        self.save_pred_keys()
        
        log.info("训练完成！")
