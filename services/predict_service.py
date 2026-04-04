# -*- coding:utf-8 -*-
"""
预测服务模块
统一处理所有预测相关逻辑，消除代码重复
"""
import json
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Optional, Union
from config import model_args, pred_key_name, model_path, ball_name, name_path
from modeling import LstmWithCRFModel, SignalLstmModel, tf
from utils.exceptions import ModelLoadError, PredictionError
from utils.logger import log
from utils.runtime_config import get_runtime_tuning

_RUNTIME_LOGGED = False


class PredictService:
    """预测服务类"""
    
    def __init__(self, name: str = "ssq", use_db: bool = True):
        """
        初始化预测服务
        
        Args:
            name: 玩法名称 (ssq/dlt)
            use_db: 是否使用数据库记录预测结果
        """
        self.name = name
        self.use_db = use_db
        self.red_sess = None
        self.blue_sess = None
        self.red_graph = None
        self.blue_graph = None
        self.pred_key_d = None
        self.db = None
        self.current_prediction = None
    
    def load_models(self) -> None:
        """加载红球和蓝球模型"""
        try:
            # 初始化数据库连接
            if self.use_db:
                from database import get_db_manager
                self.db = get_db_manager()

            m_args = model_args[self.name]
            global _RUNTIME_LOGGED
            tuning = get_runtime_tuning()
            if not _RUNTIME_LOGGED:
                mem_str = f"{tuning.mem_available_gb:.1f}GB" if tuning.mem_available_gb is not None else "未知"
                log.info(
                    f"系统资源: CPU={tuning.cpu_logical}, 可用内存={mem_str}, "
                    f"推理并行={tuning.parallel_predict}, TF线程={tuning.tf_intra_threads}/{tuning.tf_inter_threads}"
                )
                _RUNTIME_LOGGED = True
            sess_config = tf.compat.v1.ConfigProto(
                intra_op_parallelism_threads=tuning.tf_intra_threads,
                inter_op_parallelism_threads=tuning.tf_inter_threads,
                allow_soft_placement=True,
            )
            # 加载红球模型（使用 import_meta_graph 确保图结构完全一致）
            self.red_graph = tf.compat.v1.Graph()
            with self.red_graph.as_default():
                # 直接加载训练时保存的 meta graph
                red_meta_path = os.path.join(m_args["path"]["red"], "red_ball_model.ckpt.meta")
                red_saver = tf.compat.v1.train.import_meta_graph(red_meta_path)
            self.red_sess = tf.compat.v1.Session(graph=self.red_graph, config=sess_config)
            red_saver.restore(
                self.red_sess,
                os.path.join(m_args["path"]["red"], "red_ball_model.ckpt")
            )
            log.info("已加载红球模型")

            # 加载蓝球模型（使用 import_meta_graph 确保图结构完全一致）
            self.blue_graph = tf.compat.v1.Graph()
            with self.blue_graph.as_default():
                # 直接加载训练时保存的 meta graph
                blue_meta_path = os.path.join(m_args["path"]["blue"], "blue_ball_model.ckpt.meta")
                blue_saver = tf.compat.v1.train.import_meta_graph(blue_meta_path)
            self.blue_sess = tf.compat.v1.Session(graph=self.blue_graph, config=sess_config)
            blue_saver.restore(
                self.blue_sess,
                os.path.join(m_args["path"]["blue"], "blue_ball_model.ckpt")
            )
            log.info("已加载蓝球模型")

            # 加载关键节点名
            with open(os.path.join(model_path, self.name, pred_key_name)) as f:
                self.pred_key_d = json.load(f)

        except Exception as e:
            raise ModelLoadError(f"模型加载失败：{str(e)}", model_name=f"{self.name}_model")
    
    def close(self) -> None:
        """关闭会话，释放资源"""
        if self.red_sess:
            self.red_sess.close()
        if self.blue_sess:
            self.blue_sess.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        self.load_models()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def predict_red_balls(
        self, 
        predict_features: np.ndarray, 
        sequence_len: int, 
        windows_size: int
    ) -> Tuple[List[int], List[str]]:
        """
        红球预测
        
        Args:
            predict_features: 预测特征数据
            sequence_len: 序列长度
            windows_size: 窗口大小
        
        Returns:
            (预测结果列表，号码名称列表)
        """
        try:
            name_list = [(ball_name[0], i + 1) for i in range(sequence_len)]
            data = predict_features[
                ["{}_{}".format(name[0], i) for name, i in name_list]
            ].values.astype(int) - 1
            
            with self.red_graph.as_default():
                reverse_sequence = tf.compat.v1.get_default_graph().get_tensor_by_name(
                    self.pred_key_d[ball_name[0][0]]
                )
                pred = self.red_sess.run(
                    reverse_sequence,
                    feed_dict={
                        "inputs:0": data.reshape(1, windows_size, sequence_len),
                        "sequence_length:0": np.array([sequence_len] * 1)
                    }
                )
            
            return pred[0].tolist(), name_list
            
        except Exception as e:
            raise PredictionError(f"红球预测失败：{str(e)}", ball_type="red")
    
    def predict_blue_balls(
        self,
        predict_features: np.ndarray,
        sequence_len: int,
        windows_size: int,
        ball_count: int = 1
    ) -> Union[List[int], Tuple[List[int], List[str]]]:
        """
        蓝球预测
        
        Args:
            predict_features: 预测特征数据
            sequence_len: 序列长度
            windows_size: 窗口大小
            ball_count: 蓝球数量 (ssq=1, dlt=2)
        
        Returns:
            预测结果
        """
        try:
            if ball_count == 1:  # 双色球
                data = predict_features[[ball_name[1][0]]].values.astype(int) - 1
                
                with self.blue_graph.as_default():
                    softmax = tf.compat.v1.get_default_graph().get_tensor_by_name(
                        self.pred_key_d[ball_name[1][0]]
                    )
                    pred = self.blue_sess.run(
                        softmax,
                        feed_dict={"inputs:0": data.reshape(1, windows_size)}
                    )
                return pred.tolist()
            else:  # 大乐透
                name_list = [(ball_name[1], i + 1) for i in range(sequence_len)]
                if self.name == "fc3d":
                    blue_columns = ["蓝球"]
                else:
                    # pl3/pl5/fc3d: 蓝球列名
                    if sequence_len == 1:
                        blue_columns = [ball_name[1][0]]  # 直接使用 "蓝球"
                    else:
                        blue_columns = [
                            f"{x[0]}_{i+1}" 
                            for x in ball_name[1:] 
                            for i in range(sequence_len)
                        ]
                data = predict_features[blue_columns].values.astype(int) - 1
                
                with self.blue_graph.as_default():
                    reverse_sequence = tf.compat.v1.get_default_graph().get_tensor_by_name(
                        self.pred_key_d[ball_name[1][0]]
                    )
                    pred = self.blue_sess.run(
                        reverse_sequence,
                        feed_dict={
                            "inputs:0": data.reshape(1, windows_size, sequence_len),
                            "sequence_length:0": np.array([sequence_len] * 1)
                        }
                    )
                return pred[0].tolist(), name_list
                
        except Exception as e:
            raise PredictionError(f"蓝球预测失败：{str(e)}", ball_type="blue")
    
    def get_final_prediction(
        self,
        predict_features: np.ndarray,
        issue_number: Optional[str] = None,
        strategy_name: str = "model_only",
        confidence_score: Optional[float] = None
    ) -> Dict[str, Union[List[int], int]]:
        """
        获取最终预测结果（简化版）

        Args:
            predict_features: 预测特征数据
            issue_number: 期号（用于记录）
            strategy_name: 策略名称
            confidence_score: 置信度分数

        Returns:
            预测结果字典 {'red': [...], 'blue': ...}
        """
        m_args = model_args[self.name]["model_args"]
        tuning = get_runtime_tuning()

        if self.name in ["ssq", "qlc"]:
            if tuning.parallel_predict:
                with ThreadPoolExecutor(max_workers=2) as ex:
                    f_red = ex.submit(self.predict_red_balls, predict_features, m_args["sequence_len"], m_args["windows_size"])
                    f_blue = ex.submit(self.predict_blue_balls, predict_features, 0, m_args["windows_size"], 1)
                    red_pred, red_name_list = f_red.result()
                    blue_pred = f_blue.result()
            else:
                red_pred, red_name_list = self.predict_red_balls(
                    predict_features,
                    m_args["sequence_len"],
                    m_args["windows_size"]
                )
                blue_pred = self.predict_blue_balls(
                    predict_features,
                    0,
                    m_args["windows_size"],
                    ball_count=1
                )

            result = {
                'red': sorted([int(res) + 1 for res in red_pred]),
                'blue': int(blue_pred[0]) + 1
            }
        else:
            if tuning.parallel_predict:
                with ThreadPoolExecutor(max_workers=2) as ex:
                    f_red = ex.submit(self.predict_red_balls, predict_features, m_args["red_sequence_len"], m_args["windows_size"])
                    f_blue = ex.submit(self.predict_blue_balls, predict_features, m_args["blue_sequence_len"], m_args["windows_size"], 2)
                    red_pred, red_name_list = f_red.result()
                    blue_pred, blue_name_list = f_blue.result()
            else:
                red_pred, red_name_list = self.predict_red_balls(
                    predict_features,
                    m_args["red_sequence_len"],
                    m_args["windows_size"]
                )
                blue_pred, blue_name_list = self.predict_blue_balls(
                    predict_features,
                    m_args["blue_sequence_len"],
                    m_args["windows_size"],
                    ball_count=2
                )

            result = {
                'red': sorted([int(res) + 1 for res in red_pred]),
                'blue': sorted([int(res) + 1 for res in blue_pred])
            }

        # 保存预测记录到数据库
        if self.use_db and issue_number and self.db:
            try:
                lottery_draw = self.db.get_latest_draw(self.name)
                lottery_draw_id = lottery_draw.id if lottery_draw else None

                prediction = self.db.save_prediction(
                    lottery_type=self.name,
                    issue_number=issue_number,
                    predicted_red=result['red'],
                    predicted_blue=result.get('blue'),
                    strategy_used=strategy_name,
                    confidence_score=confidence_score,
                    model_version="v2.0",
                    lottery_draw_id=lottery_draw_id
                )
                self.current_prediction = prediction
                log.info(f"预测记录已保存到数据库，ID: {prediction.id}")
            except Exception as e:
                log.warning(f"保存预测记录失败: {e}")

        return result

    def record_actual_result(
        self,
        issue_number: str,
        actual_red: List[int],
        actual_blue: Optional[int]
    ) -> bool:
        """
        记录实际开奖结果并计算命中

        Args:
            issue_number: 期号
            actual_red: 实际红球
            actual_blue: 实际蓝球

        Returns:
            是否成功更新
        """
        if not self.use_db or not self.db:
            return False

        try:
            # 查找对应的预测记录
            predictions = self.db.get_predictions(
                lottery_type=self.name,
                limit=100
            )
            target = None
            for p in predictions:
                if p.issue_number == issue_number and p.is_hit is None:
                    target = p
                    break

            if target:
                success = self.db.update_prediction_result(
                    prediction_id=target.id,
                    actual_red=actual_red,
                    actual_blue=actual_blue
                )
                if success:
                    log.info(f"期号 {issue_number} 预测结果已更新，命中: {target.is_hit}, 命中红球数: {target.hit_count}")
                return success
            else:
                log.warning(f"未找到期号 {issue_number} 的预测记录")
                return False
        except Exception as e:
            log.error(f"记录实际结果失败: {e}")
            return False
