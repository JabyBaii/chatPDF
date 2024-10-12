#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 定义端口
BACKEND_PORT=8000
FRONTEND_PORT=8501

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="LINUX"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="MAC"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="WINDOWS"
else
    OS="UNKNOWN"
fi

# 定义函数来打印带颜色的消息
print_message() {
    echo -e "${YELLOW}$1${NC}"
}

# 定义函数来检查端口并获取进程信息
check_port_and_get_process() {
    local port=$1
    if [[ "$OS" == "WINDOWS" ]]; then
        local pid=$(netstat -ano | findstr ":$port " | findstr "LISTENING" | awk '{print $5}')
        if [[ ! -z "$pid" ]]; then
            local process_name=$(tasklist | findstr $pid | awk '{print $1}')
            echo -e "${RED}错误: 端口 $port 已被占用。${NC}"
            echo "PID: $pid"
            echo "进程名: $process_name"
            echo "要终止此进程，请运行: taskkill /F /PID $pid"
            echo "或者强制kill进程：taskkill /F /IM $process_name"
            return 0
        fi
    elif [[ "$OS" == "LINUX" ]] || [[ "$OS" == "MAC" ]]; then
        local pid=$(lsof -ti :$port)
        if [[ ! -z "$pid" ]]; then
            local process_name=$(ps -p $pid -o comm=)
            echo -e "${RED}错误: 端口 $port 已被占用。${NC}"
            echo "PID: $pid"
            echo "进程名: $process_name"
            echo "要终止此进程，请运行: kill $pid"
            return 0
        fi
    else
        echo "不支持的操作系统"
        exit 1
    fi
    return 1
}

# 检查是否安装了必要的工具
if [[ "$OS" == "WINDOWS" ]]; then
    command -v python >/dev/null 2>&1 || { echo >&2 "需要 python 但未安装。退出。"; exit 1; }
else
    command -v python3 >/dev/null 2>&1 || { echo >&2 "需要 python3 但未安装。退出。"; exit 1; }
fi
command -v streamlit >/dev/null 2>&1 || { echo >&2 "需要 streamlit 但未安装。退出。"; exit 1; }

# 检查端口
print_message "检查端口..."
if check_port_and_get_process $BACKEND_PORT; then
    exit 1
fi
if check_port_and_get_process $FRONTEND_PORT; then
    exit 1
fi

# 启动后端
print_message "正在启动chroma服务器..."
if [[ "$OS" == "WINDOWS" ]]; then
    chroma run --path ./chroma_db &
else
    chroma run --path ./chroma_db &
fi
BACKEND_PID=$!

# 等待chroma服务器启动
sleep 5

# 检查chroma服务器是否启动成功
if ps -p $BACKEND_PID > /dev/null
then
   echo "chroma服务器启动成功，PID: $BACKEND_PID"
else
   echo "chroma服务器启动失败"
   exit 1
fi

# 启动前端
print_message "正在启动chroma客户端..."
if [[ "$OS" == "WINDOWS" ]]; then
    streamlit run .\chatPDF-ui.py &
else
    streamlit run ./chatPDF-ui.py &
fi
FRONTEND_PID=$!

# 等待chroma客户端启动
sleep 5

# 检查chroma客户端是否启动成功
if ps -p $FRONTEND_PID > /dev/null
then
   echo "chroma客户端启动成功，PID: $FRONTEND_PID"
else
   echo "chroma客户端启动失败"
   kill $BACKEND_PID
   exit 1
fi

print_message "所有服务已启动。"
echo -e "${GREEN}后端运行在 http://localhost:$BACKEND_PORT${NC}"
echo -e "${GREEN}前端运行在 http://localhost:$FRONTEND_PORT${NC}"

# 等待用户输入来停止服务
read -p "按任意键停止所有服务..."

# 停止服务
print_message "正在停止服务..."
if [[ "$OS" == "WINDOWS" ]]; then
    taskkill //PID $BACKEND_PID //F > /dev/null 2>&1
    taskkill //PID $FRONTEND_PID //F > /dev/null 2>&1
else
    kill $BACKEND_PID
    kill $FRONTEND_PID
fi

print_message "所有服务已停止。"