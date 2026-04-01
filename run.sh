#!/bin/bash
# 一键运行脚本 (适用于 Linux/macOS)

# 设置颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}   双色球/大乐透 AI 预测系统一键脚本   ${NC}"
echo -e "${BLUE}=======================================${NC}"

# 选择玩法
read -p "请选择玩法 (ssq/dlt) [默认: ssq]: " GAME_NAME
GAME_NAME=${GAME_NAME:-ssq}

echo -e "\n${GREEN}[1/4] 正在获取最新数据...${NC}"
python get_data.py --name $GAME_NAME

echo -e "\n${GREEN}[2/4] 正在进行模型训练...${NC}"
python run_train_model_optimized.py --name $GAME_NAME --use_early_stopping

echo -e "\n${GREEN}[3/4] 正在进行统计分析...${NC}"
python analyzer.py --name $GAME_NAME --plot --report

echo -e "\n${GREEN}[4/4] 正在生成预测结果...${NC}"
read -p "请选择预测策略 (hybrid/model_only/strategy_only) [默认: hybrid]: " STRATEGY
STRATEGY=${STRATEGY:-hybrid}

python run_predict_enhanced.py --name $GAME_NAME --strategy $STRATEGY --n_combinations 5

echo -e "\n${BLUE}=======================================${NC}"
echo -e "${GREEN}             流程执行完毕!             ${NC}"
echo -e "${BLUE}=======================================${NC}"
