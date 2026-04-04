# -*- coding: utf-8 -*-
"""
兼容性配置模块
为旧代码提供 config 导入支持，所有变量从 config_new 派生
Author: BigCat
"""
import os
from config_new import (
    model_args as _flat_model_args,
    name_path,
    data_file_name,
    ball_name,
    PROXY_CONFIG,
    config
)

# ============================================================
# 基础兼容变量
# ============================================================

# 模型保存根目录
model_path = os.path.join(config.data_dir, "models")

# 预测关键节点文件名
pred_key_name = "pred_key.json"

# 模型检查点文件扩展名
extension = "ckpt"

# ============================================================
# model_args 完整嵌套结构（按彩票类型）
# 旧代码期望 model_args[lottery_type]["model_args"][...]
#       和 model_args[lottery_type]["train_args"][...]
#       和 model_args[lottery_type]["path"]["red"/"blue"]
# ============================================================

_model_args = {
    "ssq": {
        "model_args": {
            "batch_size": 64,
            "red_n_class": 34,
            "blue_n_class": 17,
            "sequence_len": 6,
            "red_sequence_len": 6,
            "blue_sequence_len": 1,
            "windows_size": 10,
            "red_embedding_size": 64,
            "red_hidden_size": 128,
            "red_layer_size": 2,
            "red_epochs": 50,
            "blue_embedding_size": 32,
            "blue_hidden_size": 64,
            "blue_layer_size": 2,
            "blue_epochs": 50,
        },
        "train_args": {
            "red_learning_rate": 0.001,
            "red_beta1": 0.9,
            "red_beta2": 0.999,
            "red_epsilon": 1e-8,
            "blue_learning_rate": 0.001,
            "blue_beta1": 0.9,
            "blue_beta2": 0.999,
            "blue_epsilon": 1e-8,
        },
        "path": {
            "red": os.path.join(model_path, "ssq", "red"),
            "blue": os.path.join(model_path, "ssq", "blue"),
        }
    },
    "dlt": {
        "model_args": {
            "batch_size": 64,
            "red_n_class": 36,
            "blue_n_class": 13,
            "sequence_len": 5,
            "red_sequence_len": 5,
            "blue_sequence_len": 2,
            "windows_size": 10,
            "red_embedding_size": 64,
            "red_hidden_size": 128,
            "red_layer_size": 2,
            "red_epochs": 50,
            "blue_embedding_size": 32,
            "blue_hidden_size": 64,
            "blue_layer_size": 2,
            "blue_epochs": 50,
        },
        "train_args": {
            "red_learning_rate": 0.001,
            "red_beta1": 0.9,
            "red_beta2": 0.999,
            "red_epsilon": 1e-8,
            "blue_learning_rate": 0.001,
            "blue_beta1": 0.9,
            "blue_beta2": 0.999,
            "blue_epsilon": 1e-8,
        },
        "path": {
            "red": os.path.join(model_path, "dlt", "red"),
            "blue": os.path.join(model_path, "dlt", "blue"),
        }
    },
    "qlc": {
        "model_args": {
            "batch_size": 64,
            "red_n_class": 31,
            "blue_n_class": 31,
            "sequence_len": 7,
            "red_sequence_len": 7,
            "blue_sequence_len": 1,
            "windows_size": 10,
            "red_embedding_size": 64,
            "red_hidden_size": 128,
            "red_layer_size": 2,
            "red_epochs": 50,
            "blue_embedding_size": 32,
            "blue_hidden_size": 64,
            "blue_layer_size": 2,
            "blue_epochs": 50,
        },
        "train_args": {
            "red_learning_rate": 0.001,
            "red_beta1": 0.9,
            "red_beta2": 0.999,
            "red_epsilon": 1e-8,
            "blue_learning_rate": 0.001,
            "blue_beta1": 0.9,
            "blue_beta2": 0.999,
            "blue_epsilon": 1e-8,
        },
        "path": {
            "red": os.path.join(model_path, "qlc", "red"),
            "blue": os.path.join(model_path, "qlc", "blue"),
        }
    },
    "fc3d": {
        "model_args": {
            "batch_size": 64,
            "red_n_class": 10,
            "blue_n_class": 10,
            "sequence_len": 3,
            "red_sequence_len": 3,
            "blue_sequence_len": 1,
            "windows_size": 10,
            "red_embedding_size": 32,
            "red_hidden_size": 64,
            "red_layer_size": 2,
            "red_epochs": 50,
            "blue_embedding_size": 32,
            "blue_hidden_size": 64,
            "blue_layer_size": 2,
            "blue_epochs": 50,
        },
        "train_args": {
            "red_learning_rate": 0.001,
            "red_beta1": 0.9,
            "red_beta2": 0.999,
            "red_epsilon": 1e-8,
            "blue_learning_rate": 0.001,
            "blue_beta1": 0.9,
            "blue_beta2": 0.999,
            "blue_epsilon": 1e-8,
        },
        "path": {
            "red": os.path.join(model_path, "fc3d", "red"),
            "blue": os.path.join(model_path, "fc3d", "blue"),
        }
    },
    "pl3": {
        "model_args": {
            "batch_size": 64,
            "red_n_class": 10,
            "blue_n_class": 10,
            "sequence_len": 3,
            "red_sequence_len": 3,
            "blue_sequence_len": 1,
            "windows_size": 10,
            "red_embedding_size": 32,
            "red_hidden_size": 64,
            "red_layer_size": 2,
            "red_epochs": 50,
            "blue_embedding_size": 32,
            "blue_hidden_size": 64,
            "blue_layer_size": 2,
            "blue_epochs": 50,
        },
        "train_args": {
            "red_learning_rate": 0.001,
            "red_beta1": 0.9,
            "red_beta2": 0.999,
            "red_epsilon": 1e-8,
            "blue_learning_rate": 0.001,
            "blue_beta1": 0.9,
            "blue_beta2": 0.999,
            "blue_epsilon": 1e-8,
        },
        "path": {
            "red": os.path.join(model_path, "pl3", "red"),
            "blue": os.path.join(model_path, "pl3", "blue"),
        }
    },
    "pl5": {
        "model_args": {
            "batch_size": 64,
            "red_n_class": 10,
            "blue_n_class": 10,
            "sequence_len": 5,
            "red_sequence_len": 5,
            "blue_sequence_len": 1,
            "windows_size": 10,
            "red_embedding_size": 32,
            "red_hidden_size": 64,
            "red_layer_size": 2,
            "red_epochs": 50,
            "blue_embedding_size": 32,
            "blue_hidden_size": 64,
            "blue_layer_size": 2,
            "blue_epochs": 50,
        },
        "train_args": {
            "red_learning_rate": 0.001,
            "red_beta1": 0.9,
            "red_beta2": 0.999,
            "red_epsilon": 1e-8,
            "blue_learning_rate": 0.001,
            "blue_beta1": 0.9,
            "blue_beta2": 0.999,
            "blue_epsilon": 1e-8,
        },
        "path": {
            "red": os.path.join(model_path, "pl5", "red"),
            "blue": os.path.join(model_path, "pl5", "blue"),
        }
    },
    "qxc": {
        "model_args": {
            "batch_size": 64,
            "red_n_class": 10,
            "blue_n_class": 10,
            "sequence_len": 6,
            "red_sequence_len": 6,
            "blue_sequence_len": 1,
            "windows_size": 10,
            "red_embedding_size": 32,
            "red_hidden_size": 64,
            "red_layer_size": 2,
            "red_epochs": 50,
            "blue_embedding_size": 32,
            "blue_hidden_size": 64,
            "blue_layer_size": 2,
            "blue_epochs": 50,
        },
        "train_args": {
            "red_learning_rate": 0.001,
            "red_beta1": 0.9,
            "red_beta2": 0.999,
            "red_epsilon": 1e-8,
            "blue_learning_rate": 0.001,
            "blue_beta1": 0.9,
            "blue_beta2": 0.999,
            "blue_epsilon": 1e-8,
        },
        "path": {
            "red": os.path.join(model_path, "qxc", "red"),
            "blue": os.path.join(model_path, "qxc", "blue"),
        }
    },
    "kl8": {
        "model_args": {
            "batch_size": 64,
            "red_n_class": 81,
            "blue_n_class": 81,
            "sequence_len": 20,
            "red_sequence_len": 20,
            "blue_sequence_len": 1,
            "windows_size": 10,
            "red_embedding_size": 128,
            "red_hidden_size": 256,
            "red_layer_size": 2,
            "red_epochs": 50,
            "blue_embedding_size": 64,
            "blue_hidden_size": 128,
            "blue_layer_size": 2,
            "blue_epochs": 50,
        },
        "train_args": {
            "red_learning_rate": 0.001,
            "red_beta1": 0.9,
            "red_beta2": 0.999,
            "red_epsilon": 1e-8,
            "blue_learning_rate": 0.001,
            "blue_beta1": 0.9,
            "blue_beta2": 0.999,
            "blue_epsilon": 1e-8,
        },
        "path": {
            "red": os.path.join(model_path, "kl8", "red"),
            "blue": os.path.join(model_path, "kl8", "blue"),
        }
    }
}

# 覆盖 config_new 中的扁平 model_args，提供完整嵌套结构
model_args = _model_args

# 确保模型目录存在
os.makedirs(model_path, exist_ok=True)
for lottery_type in model_args:
    os.makedirs(model_args[lottery_type]["path"]["red"], exist_ok=True)
    os.makedirs(model_args[lottery_type]["path"]["blue"], exist_ok=True)
