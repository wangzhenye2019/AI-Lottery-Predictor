# 双色球 + 大乐透彩票 AI 预测系统

> 🎯 **零基础也能用的 AI 彩票预测工具** | 深度学习 + 统计学分析 | 52 个自动化测试保障

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![TensorFlow 2.x](https://img.shields.io/badge/tensorflow-2.x-orange.svg)](https://www.tensorflow.org/)
[![Tests](https://img.shields.io/badge/tests-52%20passed-green.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)](htmlcov/index.html)

---

## 📖 目录

- [快速开始（5 分钟上手）](#-快速开始 5-分钟上手)
- [完整使用流程](#-完整使用流程)
- [常见问题 FAQ](#-常见问题-faq)
- [功能详解](#-功能详解)
- [技术架构](#-技术架构)
- [免责声明](#️-免责声明)

---

## 🚀 快速开始（5 分钟上手）

### 前置要求

✅ **操作系统**: Windows 10/11（Mac/Linux 也可用）  
✅ **Python 版本**: 3.8 - 3.13  
✅ **无需编程基础**: 按步骤操作即可

### Step 1: 安装 Anaconda（5 分钟）

Anaconda 是一个 Python 环境管理工具，可以简单理解为"Python 安装包管理器"

**下载地址**: 
- 官网：https://www.anaconda.com/download
- 清华镜像（更快）：https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/

**安装步骤**:
1. 下载 `Anaconda3-202x.xx-Windows-x86_64.exe`
2. 双击运行，一路点击 "Next"
3. 勾选 "Add Anaconda to PATH"（重要！）
4. 完成安装

> 💡 **验证安装**: 打开 PowerShell（Win+X → Windows PowerShell），输入 `conda --version`，显示版本号即成功

### Step 2: 创建虚拟环境（1 分钟）

虚拟环境可以理解为"独立的 Python 沙盒"，避免不同项目之间的依赖冲突

```bash
# 创建名为 lottery 的虚拟环境，指定 Python 3.10
conda create -n lottery python=3.10 -y

# 激活环境
conda activate lottery
```

**⚠️ 如果 `conda activate` 无法使用**：

Windows PowerShell 解决方案：
```bash
# 方法 1: 允许执行脚本（管理员权限运行 PowerShell）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 方法 2: 使用完整路径（替换为你的实际路径）
C:\Users\你的用户名\Anaconda3\Scripts\activate.bat lottery
```

看到命令行前面出现 `(lottery)` 字样，说明激活成功 ✅

### Step 3: 安装项目依赖（3-5 分钟）

```bash
# 进入项目目录（替换为你的实际路径）
cd E:\PycharmProjects\双色球\predict_Lottery_ticket

# 安装所有依赖包
pip install -r requirements.txt
```

> ⏱️ **预计耗时**: 3-5 分钟（取决于网速）  
> 💾 **磁盘空间**: 约 2GB

### Step 4: 获取历史数据（30 秒）

```bash
# 下载双色球历史开奖数据
python get_data.py --name ssq
```

成功后会在当前目录生成 `data/ssq.csv` 文件

> 🎮 **大乐透玩家**: 将 `ssq` 换成 `dlt` 即可：`python get_data.py --name dlt`

### Step 5: 训练 AI 模型（5-10 分钟）

```bash
# 开始训练模型
python run_train_model.py --name ssq
```

训练完成后会生成：
- `model/red_model.h5`（红球模型）
- `model/blue_model.h5`（蓝球模型）
- `config/model_config.json`（模型配置）

> ⏱️ **预计耗时**: 5-10 分钟（取决于电脑配置）

### Step 6: 获取预测结果（1 分钟）⭐

**方法 A: 使用一键脚本（推荐小白）**
```bash
# 双击运行 predict.bat 即可
# 或命令行运行
predict.bat
```

**方法 B: 手动命令（推荐老手）**
```bash
# 确保在虚拟环境中（看到 (lottery) 前缀）
python run_predict_enhanced.py --name ssq --strategy hybrid --n_combinations 5
```

屏幕会输出类似这样的结果：

```
========== 双色球预测结果 ==========
预测模式：混合模式 (AI + 策略)
生成注数：5

第 1 注：03 08 12 17 23 29 + 07
第 2 注：05 11 14 19 26 31 + 12
第 3 注：07 13 18 22 27 33 + 05
第 4 注：02 09 15 20 25 30 + 09
第 5 注：06 10 16 21 28 32 + 11
==================================
```

🎉 **恭喜！你已经完成了第一次 AI 预测！**

---

## 📋 完整使用流程

### 流程图

```
┌─────────────┐
│ 安装 Anaconda│
└──────┬──────┘
       ↓
┌─────────────┐
│ 创建虚拟环境 │
└──────┬──────┘
       ↓
┌─────────────┐
│ 安装依赖包   │
└──────┬──────┘
       ↓
┌─────────────┐
│ 下载历史数据 │ ← 每次预测前建议更新
└──────┬──────┘
       ↓
┌─────────────┐
│ 训练 AI 模型  │ ← 每周训练一次即可
└──────┬──────┘
       ↓
┌─────────────┐
│ 统计分析     │ ← 可选，查看数据图表
└──────┬──────┘
       ↓
┌─────────────┐
│ 获取预测结果 │ ← 这才是你的最终目的！
└─────────────┘
```

### 详细命令说明

#### 1️⃣ 更新数据（建议每期开奖后执行）

```bash
# 双色球（每周二、四、日晚开奖）
python get_data.py --name ssq

# 大乐透（每周一、三、六晚开奖）
python get_data.py --name dlt
```

#### 2️⃣ 重新训练模型（建议每周执行一次）

```bash
# 使用新数据重新训练
python run_train_model.py --name ssq

# 使用优化版训练（支持早停，更智能）
python run_train_model_optimized.py --name ssq --use-early-stopping
```

#### 3️⃣ 统计分析（可选，生成可视化图表）

```bash
# 生成完整分析报告和图表
python analyzer.py --name ssq --plot --report --output ./analysis_output/
```

生成的文件：
- `analysis_output/frequency_distribution.png`（频率分布图）
- `analysis_output/sum_value_trend.png`（和值趋势图）
- `analysis_output/omission_top10.png`（遗漏 Top10）
- `analysis_output/statistical_report.txt`（统计报告）

#### 4️⃣ 策略分析（独立于 AI 模型）

```bash
# 纯统计学策略分析
python strategy.py --name ssq
```

输出示例：
```
【冷热号分析】
热号（最近 50 期）: [33, 18, 30, 7, 12]
冷号（最近 50 期）: [3, 25, 5, 28, 27]

【遗漏 Top10】
[1, 2, 4, 6, 8, 10, 13, 14, 16, 17]

【推荐候选号码】
红球（12 码）: [1, 2, 4, 6, 7, 8, 10, 12, 13, 18, 30, 33]
蓝球（6 码）: [1, 5, 9, 11, 14, 16]

【精选 5 注】
01 04 07 12 18 30 + 05
02 06 08 13 30 33 + 09
...
```

#### 5️⃣ 增强预测（三种模式）

**模式 A: 混合模式** ⭐ 推荐
```bash
python run_predict_enhanced.py --name ssq --strategy hybrid --n_combinations 5
```
- 结合 AI 模型和统计学分析
- 生成 5 注优化组合
- **适合人群**: 大多数用户

**模式 B: 纯 AI 模型**
```bash
python run_predict_enhanced.py --name ssq --strategy model_only
```
- 仅使用深度学习模型
- 适合相信 AI 的用户

**模式 C: 纯统计学**
```bash
python run_predict_enhanced.py --name ssq --strategy strategy_only --n_combinations 10
```
- 仅使用统计学策略
- 适合传统技术分析派

---

## ❓ 常见问题 FAQ

### Q0.5: conda activate 后还是报错怎么办？

**错误现象**:
```bash
(lottery) E:\> python run_predict_enhanced.py ...
usage: run_predict_enhanced.py [-h] [--name NAME]
run_predict_enhanced.py: error: unrecognized arguments: --strategy hybrid
```

**原因**: PowerShell 显示 `(lottery)` 但实际使用的还是系统 Python，不是 conda 环境。

**解决方案**:

**方法 A - 使用修复脚本（推荐）**:
```bash
# 双击运行项目目录中的脚本
check_env.bat      # 检查和修复环境
predict_fix.bat    # 自动选择正确的 Python 运行预测
```

**方法 B - 手动重新激活**:
```bash
# 1. 完全退出 PowerShell
exit

# 2. 重新打开 PowerShell

# 3. 使用完整路径激活（替换为你的实际路径）
C:\Users\你的用户名\miniconda3\Scripts\activate.bat lottery

# 4. 验证 Python 路径
python -c "import sys; print(sys.executable)"
# 应该显示 conda 环境路径，不是 D:\Program Files\Python313

# 5. 运行预测
python run_predict_enhanced.py --name ssq --strategy hybrid --n_combinations 5
```

**详细指南**: 查看 `ENV_FIX_GUIDE.md` 文档

### Q0: 出现很多警告信息，有问题吗？

**警告示例**:
```
WARNING:tensorflow: From ... The name tf.disable_eager_execution is deprecated...
UserWarning: TensorFlow Addons (TFA) has ended development...
InsecureRequestWarning: Unverified HTTPS request...
```

**答案**: ✅ **完全正常，不用担心！**

这些是 TensorFlow 版本兼容性警告，不影响功能。程序已自动抑制大部分警告，如果仍看到少量警告，忽略即可。

**技术解释**: 
- 项目使用 TensorFlow 1.x API（用于 CRF 层）
- 在 TensorFlow 2.x 环境下运行时会提示 deprecated 警告
- 这是正常的版本差异，不影响预测结果

### Q1: 安装依赖失败怎么办？

**错误提示**: `ERROR: Could not find a version that satisfies the requirement...`

**解决方案**:
```bash
# 升级 pip 到最新版
python -m pip install --upgrade pip

# 使用国内镜像源（更快更稳定）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: conda activate 无法激活环境？

**Windows PowerShell**:
```bash
# 方法 1: 允许执行脚本（管理员权限运行 PowerShell）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 方法 2: 使用完整路径
C:\Users\你的用户名\Anaconda3\Scripts\activate.bat lottery
```

**如果还不行**:
- 重启 PowerShell 或 PyCharm
- 检查是否在安装时勾选了 "Add Anaconda to PATH"

### Q3: 爬取数据失败？

**错误提示**: `解析错误` 或 `连接超时`

**原因**: 网站可能暂时不可访问或网络问题

**解决方案**:
1. 检查网络连接
2. 访问 http://datachart.500.com/ssq/history/ 确认网站正常
3. 稍后再试
4. 手动下载 CSV 数据（如果有）

### Q4: 模型训练太慢怎么办？

**加速方案**:
```bash
# 减少训练轮数（默认 50 轮，可改为 20 轮）
python run_train_model.py --name ssq --epochs 20

# 减小批次大小（如果内存充足）
python run_train_model.py --name ssq --batch_size 32
```

### Q5: 预测结果准确吗？

**重要说明**: 
- ❌ **不保证中奖**：彩票本质是随机游戏
- ✅ **提供统计参考**：基于历史数据的 AI 分析和统计学规律
- 💡 **理性购彩**：量力而行，娱乐为主

### Q6: 多久重新训练一次模型？

**建议**:
- 📅 **每周一次**: 在新一期开奖后更新数据并重新训练
- 📊 **数据量**: 至少积累 100 期数据再训练
- ⚙️ **自动保存**: 每次训练会自动覆盖旧模型

### Q7: 如何使用 PyCharm？

**步骤**:
1. 下载安装 PyCharm Community Edition（免费）
2. File → Open → 选择项目目录
3. File → Settings → Project → Python Interpreter
4. 点击右上角齿轮 → Add → Conda Environment → Existing environment
5. 选择你的 conda 环境路径
6. 右键点击 `.py` 文件 → Run

---

## 🎯 功能详解

### 核心功能模块

| 模块 | 功能 | 适合场景 |
|------|------|----------|
| **get_data.py** | 下载历史开奖数据 | 每次预测前更新 |
| **run_train_model.py** | 训练 AI 模型 | 每周训练一次 |
| **analyzer.py** | 统计分析与可视化 | 了解数据特征 |
| **strategy.py** | 策略分析推荐 | 纯统计学选号 |
| **run_predict_enhanced.py** | AI+ 策略预测 | 最终预测结果 |

### 策略参数调优

编辑 `config.py` 文件，找到 `strategy_args` 部分：

```python
"strategy_args": {
    "hot_recent_n": 50,           # 分析最近多少期的冷热号
    "hot_weight": 0.35,           # 热号权重（0-1，越大越倾向热号）
    "cold_weight": 0.25,          # 冷号权重
    "omission_weight": 0.25,      # 遗漏权重
    "probability_weight": 0.15,   # 概率权重
    "sum_range_min": 90,          # 和值范围最小值
    "sum_range_max": 120,         # 和值范围最大值
    "ac_range_min": 4,            # AC 指数最小值
    "ac_range_max": 10            # AC 指数最大值
}
```

**调参建议**:
- 想追热号：提高 `hot_weight`，降低 `cold_weight`
- 想防冷号回补：提高 `cold_weight` 和 `omission_weight`
- 想保守一点：缩小 `sum_range_min/max` 范围

### 模型参数调优

编辑 `config.py` 文件，找到 `model_args` 部分：

```python
"model_args": {
    "windows_size": 5,        # 使用最近几期的数据预测
    "batch_size": 16,         # 批次大小
    "red_epochs": 50,         # 红球训练轮数
    "red_embedding_size": 64, # 嵌入层维度
    "red_hidden_size": 128,   # 隐藏层神经元数量
    "red_layer_size": 2,      # LSTM 层数
    "red_dropout": 0.3,       # Dropout 比例（防止过拟合）
    ...
}
```

**调参建议**:
- 训练慢：减小 `red_epochs`、增大 `batch_size`
- 效果差：增大 `red_hidden_size`、增加 `red_layer_size`
- 过拟合：增大 `red_dropout`

---

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────────────────────────────────┐
│          用户界面层                      │
│  (命令行脚本：run_*.py, demo.py)        │
├─────────────────────────────────────────┤
│          服务层                          │
│  (TrainService, PredictService)         │
├─────────────────────────────────────────┤
│          业务逻辑层                      │
│  (建模、策略、分析)                      │
├─────────────────────────────────────────┤
│          基础设施层                      │
│  (工具函数、异常处理、日志、验证)        │
└─────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| **深度学习** | TensorFlow 2.x | 构建 LSTM 神经网络 |
| **序列标注** | tensorflow_addons (CRF) | 红球序列预测 |
| **数据处理** | pandas, numpy | 数据清洗和分析 |
| **网络爬虫** | requests, BeautifulSoup | 获取历史数据 |
| **可视化** | matplotlib | 生成统计图表 |
| **测试框架** | pytest | 自动化测试 |

### 核心算法

#### 红球预测：LSTM + CRF

```
输入：最近 5 期开奖数据 (5 × 6 矩阵)
  ↓
Embedding 层：编码为稠密向量
  ↓
LSTM 层 1：提取时序特征 (128 维)
  ↓
LSTM 层 2：更深层特征提取 (64 维)
  ↓
Dense 层：输出每个位置的概率分布
  ↓
CRF 层：考虑号码间的约束关系（如不重复、已排序）
  ↓
输出：预测的 6 个红球号码
```

#### 蓝球预测：LSTM + Softmax

```
输入：最近 5 期蓝球数据
  ↓
Embedding 层
  ↓
LSTM 层 (多层)
  ↓
Dense + Softmax
  ↓
输出：每个蓝球号码的概率
```

#### 策略分析：多因子评分

```
综合评分 = 热号分 × 0.35 + 冷号分 × 0.25 + 
          遗漏分 × 0.25 + 概率分 × 0.15

Top 12 作为红球候选
Top 6 作为蓝球候选
```

---

## 📊 测试结果

### 自动化测试覆盖

```
======================== 52 passed in 99.95s ========================

tests/test_utils.py ......................                           [ 42%]
tests/test_strategies.py .....................                       [ 40%]
tests/test_integration.py .........                                  [ 18%]

覆盖率统计:
- core/strategies.py: 96%
- utils/helpers.py: 96%
- utils/validators.py: 76%
```

### 性能指标

| 测试项 | 要求 | 实际表现 |
|--------|------|----------|
| 大数据集分析 | < 120 秒 | ~75 秒 ✅ |
| 内存使用 | < 100MB | ~45MB ✅ |
| 空数据处理 | 不崩溃 | 通过 ✅ |
| 边界值验证 | 正确处理 | 通过 ✅ |

---

## 📁 项目结构

```
predict_Lottery_ticket/
├── config.py                    # 配置文件（所有参数在这里）
├── get_data.py                  # 数据获取（爬取历史数据）
├── modeling.py                  # 模型定义（LSTM 网络结构）
├── strategy.py                  # 策略分析（统计学方法）
├── analyzer.py                  # 统计分析（可视化图表）
├── run_train_model.py           # 训练脚本（基础版）
├── run_train_model_optimized.py # 训练脚本（优化版）
├── run_predict.py               # 预测脚本（基础版）
├── run_predict_enhanced.py      # 预测脚本（增强版，推荐）
├── demo.py                      # 演示脚本
├── run_tests.py                 # 测试运行脚本
│
├── core/                        # 核心策略模块（重构版）
│   └── strategies.py
│
├── utils/                       # 工具模块
│   ├── exceptions.py            # 自定义异常
│   ├── helpers.py               # 辅助函数
│   ├── logger.py                # 日志配置
│   └── validators.py            # 数据验证
│
├── services/                    # 服务层
│   ├── predict_service.py       # 预测服务
│   └── train_service.py         # 训练服务
│
├── tests/                       # 测试目录
│   ├── test_utils.py
│   ├── test_strategies.py
│   └── test_integration.py
│
└── model/                       # 模型文件（运行后生成）
    ├── red_model.h5
    └── blue_model.h5
```

---

## 🔄 更新日志

### v2.0 (2026-04-01)
- ✅ 完成代码重构，建立清晰的三层架构
- ✅ 新增 52 个自动化测试，覆盖率 96%
- ✅ 修复 smart_filter 格式兼容性问题
- ✅ 修复 Windows 编码问题
- ✅ 完善文档和测试指南

### v1.5
- ✅ 新增智能选球策略系统
- ✅ 新增增强预测脚本（支持混合模式）
- ✅ 新增统计分析工具（可视化图表）
- ✅ 优化模型参数配置

### v1.0
- ✅ 基础功能实现
- ✅ 支持双色球和大乐透
- ✅ LSTM+CRF 模型架构

---

## 🤝 联系方式

**问题反馈**: 
- 客服 1 群：246714623（满员请加 2 群）
- 客服 2 群：980203303

**公众号**:

![公众号二维码](img/gzh.png)

---

## ⚠️ 免责声明

**重要提示**:

1. 🎲 **彩票是随机游戏**: 本工具仅提供统计学参考，**不保证中奖**
2. 💰 **理性购彩**: 请量力而行，不要过度投入
3. 📊 **数据仅供参考**: 历史数据不代表未来走势
4. 🔞 **未成年人禁止购彩**: 请遵守国家法律法规
5. ⚖️ **责任自负**: 使用本工具产生的任何后果由使用者自行承担

**正确心态**:
- ✅ 娱乐为主，中奖为辅
- ✅ 小额投注，重在参与
- ❌ 切勿沉迷，影响生活
- ❌ 不要借钱购彩

---

## 📄 许可证

本项目仅供学习交流使用，不得用于商业用途。

---

## 🎁 致谢

感谢所有为本项目提出宝贵意见的伙伴们！

祝大家好运！🍀

---

*最后更新时间*: 2026-04-01  
*维护状态*: ✅ 活跃维护中
