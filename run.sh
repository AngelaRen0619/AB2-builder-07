#!/bin/bash

# 检查虚拟环境
if [ -d "./path/to/venv" ]; then
  echo "激活虚拟环境..."
  source ./path/to/venv/bin/activate
  echo "虚拟环境已激活"
else
  echo "警告: 未找到虚拟环境 ./path/to/venv"
  echo "尝试使用系统 Python..."
fi

# 检查依赖
echo "检查依赖..."
python3 -c "import sys; print(f'Python 版本: {sys.version}')"
python3 -c "import importlib.util; print(f'strands: {importlib.util.find_spec(\"strands\") is not None}')"
python3 -c "import importlib.util; print(f'boto3: {importlib.util.find_spec(\"boto3\") is not None}')"

# 安装缺失的依赖
if ! python3 -c "import strands" 2>/dev/null; then
  echo "未找到 strands 包，尝试安装..."
  pip install strands-agents strands-agents-tools
fi

# Run the agent with proper UTF-8 encoding
echo "设置 UTF-8 编码..."
export PYTHONIOENCODING=utf-8
echo "启动应用程序..."
python3 fix_encoding.py

# 如果激活了虚拟环境，则退出
if [ -d "./path/to/venv" ]; then
  echo "退出虚拟环境..."
  deactivate
fi

echo "程序已退出"
