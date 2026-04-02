# -*- coding: utf-8 -*-
"""
Author: BigCat
"""
import os

ball_name = [
    ("红球", "red"),
    ("蓝球", "blue")
]

data_file_name = "data.csv"

name_path = {
    "ssq": {
        "name": "双色球",
        "path": "data/ssq/"
    },
    "dlt": {
        "name": "大乐透",
        "path": "data/dlt/"
    },
    "qlc": {
        "name": "七乐彩",
        "path": "data/qlc/"
    },
    "fc3d": {
        "name": "福彩3D",
        "path": "data/fc3d/"
    }
}

model_path = os.path.join(os.getcwd(), "model")

model_args = {
    "ssq": {
        "model_args": {
            "windows_size": 5,  # 增加窗口大小，捕捉更多历史模式
            "batch_size": 64,   # 改为 64，支持批量数据训练，极大提升速度
            "sequence_len": 6,
            "red_n_class": 33,  # 红球类别数（1-33）
            "red_epochs": 50,   # 增加训练轮数
            "red_embedding_size": 64,  # 增加嵌入维度
            "red_hidden_size": 128,    # 增加隐藏层维度
            "red_layer_size": 2,       # 增加 LSTM 层数
            "blue_n_class": 16,
            "blue_epochs": 50,
            "blue_embedding_size": 64,
            "blue_hidden_size": 128,
            "blue_layer_size": 2
        },
        "train_args": {
            "red_learning_rate": 0.0005,  # 降低学习率
            "red_beta1": 0.9,
            "red_beta2": 0.999,
            "red_epsilon": 1e-08,
            "red_dropout": 0.3,           # 添加 dropout 防止过拟合
            "blue_learning_rate": 0.0005,
            "blue_beta1": 0.9,
            "blue_beta2": 0.999,
            "blue_epsilon": 1e-08,
            "blue_dropout": 0.3
        },
        "strategy_args": {
            "hot_recent_n": 50,           # 冷热号分析最近期数
            "hot_weight": 0.35,           # 热号权重
            "cold_weight": 0.25,          # 冷号权重
            "omission_weight": 0.25,      # 遗漏权重
            "probability_weight": 0.15,   # 概率权重
            "sum_range_min": 90,          # 和值范围最小值
            "sum_range_max": 120,         # 和值范围最大值
            "ac_range_min": 4,            # AC 指数最小值
            "ac_range_max": 10            # AC 指数最大值
        },
        "path": {
            "red": os.path.join(model_path, "ssq", "red_ball_model"),
            "blue": os.path.join(model_path, "ssq", "blue_ball_model")
        }
    },
    "dlt": {
        "model_args": {
            "windows_size": 3,
            "batch_size": 64,
            "red_sequence_len": 5,
            "red_n_class": 35,
            "red_epochs": 1,
            "red_embedding_size": 32,
            "red_hidden_size": 32,
            "red_layer_size": 1,
            "blue_sequence_len": 2,
            "blue_n_class": 12,
            "blue_epochs": 1,
            "blue_embedding_size": 32,
            "blue_hidden_size": 32,
            "blue_layer_size": 1
        },
        "train_args": {
            "red_learning_rate": 0.001,
            "red_beta1": 0.9,
            "red_beta2": 0.999,
            "red_epsilon": 1e-08,
            "blue_learning_rate": 0.001,
            "blue_beta1": 0.9,
            "blue_beta2": 0.999,
            "blue_epsilon": 1e-08
        },
        "path": {
            "red": os.path.join(model_path, "dlt", "red_ball_model"),
            "blue": os.path.join(model_path, "dlt", "blue_ball_model")
        }
    },
    "qlc": {
        "model_args": {
            "windows_size": 5,
            "batch_size": 64,
            "sequence_len": 7,  # 7 red
            "red_n_class": 30,  # 红球类别数（1-30）
            "red_epochs": 50,
            "red_embedding_size": 64,
            "red_hidden_size": 128,
            "red_layer_size": 2,
            "blue_n_class": 30,
            "blue_epochs": 50,
            "blue_embedding_size": 64,
            "blue_hidden_size": 128,
            "blue_layer_size": 2
        },
        "train_args": {
            "red_learning_rate": 0.0005,
            "red_beta1": 0.9,
            "red_beta2": 0.999,
            "red_epsilon": 1e-08,
            "red_dropout": 0.3,
            "blue_learning_rate": 0.0005,
            "blue_beta1": 0.9,
            "blue_beta2": 0.999,
            "blue_epsilon": 1e-08,
            "blue_dropout": 0.3
        },
        "strategy_args": {
            "hot_recent_n": 50,
            "hot_weight": 0.35,
            "cold_weight": 0.25,
            "omission_weight": 0.25,
            "probability_weight": 0.15,
            "sum_range_min": 70,
            "sum_range_max": 140,
            "ac_range_min": 4,
            "ac_range_max": 10
        },
        "path": {
            "red": os.path.join(model_path, "qlc", "red_ball_model"),
            "blue": os.path.join(model_path, "qlc", "blue_ball_model")
        }
    },
    "fc3d": {
        "model_args": {
            "windows_size": 3,
            "batch_size": 64,
            "red_sequence_len": 3,
            "red_n_class": 10,
            "red_epochs": 20,
            "red_embedding_size": 32,
            "red_hidden_size": 32,
            "red_layer_size": 1,
            "blue_sequence_len": 1,
            "blue_n_class": 2,
            "blue_epochs": 1,
            "blue_embedding_size": 8,
            "blue_hidden_size": 8,
            "blue_layer_size": 1
        },
        "train_args": {
            "red_learning_rate": 0.001,
            "red_beta1": 0.9,
            "red_beta2": 0.999,
            "red_epsilon": 1e-08,
            "red_dropout": 0.3,
            "blue_learning_rate": 0.001,
            "blue_beta1": 0.9,
            "blue_beta2": 0.999,
            "blue_epsilon": 1e-08,
            "blue_dropout": 0.3
        },
        "strategy_args": {
            "hot_recent_n": 50,
            "hot_weight": 0.35,
            "cold_weight": 0.25,
            "omission_weight": 0.25,
            "probability_weight": 0.15,
            "sum_range_min": 0,
            "sum_range_max": 27,
            "ac_range_min": 0,
            "ac_range_max": 3
        },
        "path": {
            "red": os.path.join(model_path, "fc3d", "red_ball_model"),
            "blue": os.path.join(model_path, "fc3d", "blue_ball_model")
        }
    }
}

# 模型名
pred_key_name = "key_name.json"
red_ball_model_name = "red_ball_model"
blue_ball_model_name = "blue_ball_model"
extension = "ckpt"
