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
    
    def __init__(self, name: str = "ssq"):
        """
        初始化预测服务
        
        Args:
            name: 玩法名称 (ssq/dlt)
        """
        self.name = name
        self.red_sess = None
        self.blue_sess = None
        self.red_graph = None
        self.blue_graph = None
        self.pred_key_d = None
    
    def load_models(self) -> None:
        """加载红球和蓝球模型"""
        try:
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
            # 加载红球模型
            self.red_graph = tf.compat.v1.Graph()
            with self.red_graph.as_default():
                if self.name in ["ssq", "qlc"]:
                    LstmWithCRFModel(
                        batch_size=m_args["model_args"]["batch_size"],
                        n_class=m_args["model_args"]["red_n_class"],
                        ball_num=m_args["model_args"]["sequence_len"],
                        w_size=m_args["model_args"]["windows_size"],
                        embedding_size=m_args["model_args"]["red_embedding_size"],
                        words_size=m_args["model_args"]["red_n_class"],
                        hidden_size=m_args["model_args"]["red_hidden_size"],
                        layer_size=m_args["model_args"]["red_layer_size"]
                    )
                else:
                    LstmWithCRFModel(
                        batch_size=m_args["model_args"]["batch_size"],
                        n_class=m_args["model_args"]["red_n_class"],
                        ball_num=m_args["model_args"]["red_sequence_len"],
                        w_size=m_args["model_args"]["windows_size"],
                        embedding_size=m_args["model_args"]["red_embedding_size"],
                        words_size=m_args["model_args"]["red_n_class"],
                        hidden_size=m_args["model_args"]["red_hidden_size"],
                        layer_size=m_args["model_args"]["red_layer_size"]
                    )
                red_saver = tf.compat.v1.train.Saver()
            self.red_sess = tf.compat.v1.Session(graph=self.red_graph, config=sess_config)
            red_saver.restore(
                self.red_sess, 
                os.path.join(m_args["path"]["red"], "red_ball_model.ckpt")
            )
            log.info("已加载红球模型")
            
            # 加载蓝球模型
            self.blue_graph = tf.compat.v1.Graph()
            with self.blue_graph.as_default():
                if self.name in ["ssq", "qlc"]:
                    SignalLstmModel(
                        batch_size=m_args["model_args"]["batch_size"],
                        n_class=m_args["model_args"]["blue_n_class"],
                        w_size=m_args["model_args"]["windows_size"],
                        embedding_size=m_args["model_args"]["blue_embedding_size"],
                        hidden_size=m_args["model_args"]["blue_hidden_size"],
                        outputs_size=m_args["model_args"]["blue_n_class"],
                        layer_size=m_args["model_args"]["blue_layer_size"]
                    )
                else:
                    LstmWithCRFModel(
                        batch_size=m_args["model_args"]["batch_size"],
                        n_class=m_args["model_args"]["blue_n_class"],
                        ball_num=m_args["model_args"]["blue_sequence_len"],
                        w_size=m_args["model_args"]["windows_size"],
                        embedding_size=m_args["model_args"]["blue_embedding_size"],
                        words_size=m_args["model_args"]["blue_n_class"],
                        hidden_size=m_args["model_args"]["blue_hidden_size"],
                        layer_size=m_args["model_args"]["blue_layer_size"]
                    )
                blue_saver = tf.compat.v1.train.Saver()
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
        predict_features: np.ndarray
    ) -> Dict[str, Union[List[int], int]]:
        """
        获取最终预测结果（简化版）
        
        Args:
            predict_features: 预测特征数据
        
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
            
            return {
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
            
            return {
                'red': sorted([int(res) + 1 for res in red_pred]),
                'blue': sorted([int(res) + 1 for res in blue_pred])
            }
