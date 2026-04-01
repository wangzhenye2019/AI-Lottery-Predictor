# 跨平台部署指南

本项目经过优化，已完全支持 **Windows**、**Linux**、**macOS** 以及 **Docker** 容器化环境部署。

---

## 🖥️ 1. Windows 环境部署

Windows 环境提供了方便的批处理脚本（`.bat`）和 PowerShell 脚本（`.ps1`）。

### 环境要求
- Windows 10/11
- Python 3.7+ (推荐 3.10+)

### 快速开始
1. **安装依赖**：
   双击运行 `install.ps1` 或者在命令行执行：
   ```cmd
   pip install -r requirements.txt
   ```

2. **一键执行完整流程**：
   双击运行 `predict_cmd.bat`。该脚本会自动执行：获取数据 -> 优化训练模型 -> 生成图表 -> 混合预测。

3. **修复环境问题**：
   如果遇到依赖冲突，可以双击 `check_env.bat` 进行自动修复。

---

## 🍎 2. Linux / macOS 环境部署

对于 Unix-like 系统，我们提供了 Shell 脚本进行一键式管理。代码内部的路径已使用 `os.path.join` 优化，完美兼容 Linux 目录结构。

### 环境要求
- Ubuntu/CentOS/Debian 或 macOS
- Python 3.7+

### 快速开始
1. **安装依赖**：
   打开终端，执行以下命令：
   ```bash
   # 如果需要，先创建虚拟环境
   python3 -m venv venv
   source venv/bin/activate
   
   # 安装依赖
   pip install -r requirements.txt
   ```

2. **赋予脚本执行权限**：
   ```bash
   chmod +x run.sh
   ```

3. **一键运行**：
   ```bash
   ./run.sh
   ```
   脚本会引导你选择玩法（双色球/大乐透）和预测策略，并按顺序自动执行数据爬取、模型训练、图表分析和结果预测。

---

## 🐳 3. Docker 环境部署 (推荐)

如果你不想在宿主机上配置 Python 环境，使用 Docker 是最干净、最简单的选择。

### 环境要求
- Docker Engine
- Docker Compose (通常随 Docker Desktop 安装)

### 快速开始

1. **直接通过 Docker Compose 运行 (一键搞定)**：
   在项目根目录下，执行：
   ```bash
   docker-compose up --build
   ```
   此命令会自动构建镜像，并执行完整流程（获取数据、训练模型、生成分析报告、进行预测）。
   运行产生的数据文件（`data/`）、模型文件（`model/`）和分析图表（`analysis_output/`）会通过数据卷挂载直接保存在你的宿主机项目目录中。

2. **自定义 Docker 运行 (按需执行)**：
   如果你想手动进入容器或执行特定脚本：
   
   构建镜像：
   ```bash
   docker build -t lottery-predictor .
   ```
   
   交互式运行容器：
   ```bash
   docker run -it --rm -v $(pwd)/data:/app/data -v $(pwd)/model:/app/model lottery-predictor /bin/bash
   ```
   
   在容器内，你可以像在普通 Linux 系统一样运行命令：
   ```bash
   python get_data.py --name ssq
   python run_train_model_optimized.py --name ssq
   python run_predict_enhanced.py --name ssq --strategy hybrid
   ```

---

## 🛠️ 常见问题 (FAQ)

### 1. 模型训练速度太慢？
在最新版本中，我们已经优化了 `config.py` 中的 `batch_size`（从 1 改为了 64），并在 `train_service.py` 中实现了小批量梯度下降。
训练速度已经从几十分钟缩短到了**几秒至一分钟**内。如果你依然觉得慢，请确保使用了最新代码，并运行 `run_train_model_optimized.py`。

### 2. 爬虫获取数据失败？
我们已为 `get_data.py` 增加了网络超时 (`timeout=15`) 和重试机制。如果依然失败，请检查：
- 你的网络是否能够正常访问 `500.com`。
- 如果在 Docker 中，请确保 Docker 容器配置了正确的 DNS。

### 3. Linux/macOS 下路径报错？
代码中的路径拼接已经全部替换为 `os.path.join()`。如果遇到路径找不到的问题，请确保在项目**根目录**下执行脚本（例如：`python get_data.py` 而不是 `cd scripts && python train.py`）。
