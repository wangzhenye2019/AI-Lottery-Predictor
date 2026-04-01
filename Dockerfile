FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TF_CPP_MIN_LOG_LEVEL 2

# 替换 apt 源为国内镜像（提高构建速度，可选）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || true

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 使用国内源安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目代码
COPY . .

# 赋予执行权限
RUN chmod +x run.sh || true

# 默认命令（可被 docker-compose 覆盖）
CMD ["python", "run_predict_enhanced.py", "--name", "ssq", "--strategy", "hybrid"]
