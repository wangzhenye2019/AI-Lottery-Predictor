# 双色球项目 - 一键安装脚本
# 使用方法：右键 → 使用 PowerShell 运行

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "       双色球 AI 预测 - 一键安装脚本" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 conda
Write-Host "[1/4] 检查 conda..." -ForegroundColor Yellow
try {
    $condaVersion = conda --version 2>&1
    Write-Host "[成功] conda 已安装：$condaVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未找到 conda！" -ForegroundColor Red
    Write-Host "请先安装 Miniconda: https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/"
    pause
    exit 1
}

# 检查环境
Write-Host ""
Write-Host "[2/4] 检查 lottery 环境..." -ForegroundColor Yellow
$envs = conda env list | Select-String "lottery"
if ($envs) {
    Write-Host "[信息] lottery 环境已存在" -ForegroundColor Green
} else {
    Write-Host "[操作] 创建 lottery 环境 (Python 3.10)..." -ForegroundColor Yellow
    conda create -n lottery python=3.10 -y
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] 环境创建失败！" -ForegroundColor Red
        pause
        exit 1
    }
    Write-Host "[成功] 环境创建完成！" -ForegroundColor Green
}

# 激活环境
Write-Host ""
Write-Host "[3/4] 激活 environment..." -ForegroundColor Yellow
conda activate lottery

# 验证 Python
Write-Host ""
Write-Host "[4/4] 验证 Python..." -ForegroundColor Yellow
$pythonPath = python -c "import sys; print(sys.executable)"
Write-Host "[信息] 使用 Python: $pythonPath" -ForegroundColor Green

# 安装依赖
Write-Host ""
Write-Host "正在安装依赖包（约 3-5 分钟）..." -ForegroundColor Yellow
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 依赖安装失败！" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "              安装完成！" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 训练模型：python run_train_model.py --name ssq" -ForegroundColor White
Write-Host "2. 获取预测：python run_predict_enhanced.py --name ssq --strategy hybrid --n_combinations 5" -ForegroundColor White
Write-Host ""
Write-Host "或双击运行：" -ForegroundColor Yellow
Write-Host "- train.bat - 训练模型" -ForegroundColor White
Write-Host "- predict.bat - 获取预测" -ForegroundColor White
Write-Host ""
pause
