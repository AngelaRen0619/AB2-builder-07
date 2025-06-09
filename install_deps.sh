#!/bin/bash

# 创建日志目录
mkdir -p logs
LOG_FILE="logs/install_$(date +%Y%m%d_%H%M%S).log"
echo "安装开始时间: $(date)" > $LOG_FILE

# 检查Python版本
echo "检查Python版本..." | tee -a $LOG_FILE
python3 --version | tee -a $LOG_FILE

# 安装依赖
echo "安装strands-agents和strands-agents-tools..." | tee -a $LOG_FILE
pip install strands-agents strands-agents-tools boto3 | tee -a $LOG_FILE

# 验证安装
echo "验证安装..." | tee -a $LOG_FILE
python3 -c "import importlib.util; print('strands:', importlib.util.find_spec('strands') is not None); print('strands_tools:', importlib.util.find_spec('strands_tools') is not None); print('boto3:', importlib.util.find_spec('boto3') is not None)" | tee -a $LOG_FILE

echo "安装完成时间: $(date)" | tee -a $LOG_FILE
echo "安装日志已保存到 $LOG_FILE"
