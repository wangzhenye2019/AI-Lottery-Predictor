# 🚀 AI Lottery Predictor (双色球 / 大乐透 AI 预测系统)

基于深度学习 (LSTM + CRF) 与统计学策略混合架构的中国福利彩票双色球、大乐透智能预测系统。该系统不仅通过神经网络学习历史中奖号码的隐含模式，还融合了热冷号、遗漏值、和值、AC值等多维度的专业统计策略，并且结合历史频率权重进行最终的概率采样，以期在统计学层面上最大化中奖概率。

---

## ✨ 核心特性

1. **深度学习驱动**：采用两层 LSTM 结合 CRF 的序列模型结构，并支持小批量 (Mini-Batch) 并行训练，速度飞快（几十秒内即可跑完所有历史数据）。
2. **混合智能策略**：支持 `model_only` (纯模型)、`strategy_only` (纯策略) 以及 `hybrid` (模型与策略交叉验证) 三种模式预测，并在抽样时引入了中奖概率加权算法。
3. **自动化数据获取**：内置自动化网络爬虫，随时同步 500 彩票网的最新一期历史开奖数据。
4. **多平台无缝兼容**：代码经过跨平台重构，支持 Windows / Linux / macOS。
5. **图形化界面 (GUI)**：为 Windows 用户提供了友好的 Tkinter 可视化界面，无需记忆任何代码命令，一键点击即可完成获取数据、训练和预测。
6. **Docker 容器化**：原生支持 `docker-compose`，实现环境完全隔离的一键式自动化部署。

---

## 📦 下载开箱即用的版本

如果您是普通用户，不想配置复杂的 Python 环境，您可以直接从 **[Releases](https://github.com/wangzhenye2019/AI-Lottery-Predictor/releases)** 页面下载我们打包好的压缩包。

下载并解压后，您可以直接双击运行：
- **lottery-predictor-gui.exe**：带有可视化窗口的图形界面版本（推荐）。
- **lottery-predictor-cli.exe**：终端命令行版本。

---

## 🛠️ 源码本地部署与运行

如果你是开发者，希望自己调整参数或进行二次开发，请参考以下指南：

### 1. 环境准备
推荐使用 Python 3.10+。首先安装依赖：
```bash
git clone https://github.com/wangzhenye2019/AI-Lottery-Predictor.git
cd AI-Lottery-Predictor
pip install -r requirements.txt
```

### 2. 命令行一键执行 (CLI)
使用自带的 `main.py` 入口脚本，带进度条展示：
```bash
# 默认执行双色球预测（若需训练加上 --train 参数）
python main.py --name ssq --train

# 执行大乐透预测
python main.py --name dlt --train
```

### 3. 图形界面运行 (GUI)
如果你在本地配置了环境，也可以直接启动带界面的版本：
```bash
python gui_main.py
```

### 4. Docker 一键部署
如果您安装了 Docker 和 Docker-Compose，只需要执行：
```bash
docker-compose up --build
```
系统将自动完成所有构建、数据拉取、模型训练和预测任务，并将产生的数据和模型文件通过挂载卷 (Volume) 持久化保存到您的本地。

---

## 📖 更多文档

更详细的跨平台部署指南和常见问题解答，请参阅：
- [DEPLOYMENT.md](./DEPLOYMENT.md) - 多平台部署指南

---

## ⚠️ 免责声明 (Disclaimer)

**彩票本质上是一个独立随机事件，没有任何算法能够 100% 预测出下一期的开奖号码。** 
本项目仅作为深度学习和统计分析的**学术研究与技术探讨**，**切勿作为实际购彩的绝对指导**！请理性购彩，量力而行，不要沉迷。

作者不对因使用本程序产生的任何直接或间接损失负责。
