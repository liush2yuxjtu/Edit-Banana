#!/bin/bash
# Edit-Banana 启动脚本
# 用法: ./start.sh [backend|ui|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查虚拟环境
if [ -d "venv" ]; then
    echo -e "${GREEN}激活虚拟环境...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}警告: 未找到虚拟环境，使用系统 Python${NC}"
fi

# 检查必要目录
echo -e "${GREEN}检查目录结构...${NC}"
mkdir -p uploads outputs input models logs

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}警告: 未找到 .env 文件，创建示例配置...${NC}"
    cat > .env << 'EOF'
# Kimi API 配置 (主用)
ANTHROPIC_API_KEY=your_kimi_api_key_here
KIMI_BASE_URL=https://api.kimi.com/coding/
KIMI_MODEL=kimi-k2-5

# Azure OpenAI 配置 (备用)
AZURE_OPENAI_KEY=
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Mistral AI 配置 (备用)
MISTRAL_API_KEY=
MISTRAL_MODEL=mistral-large-latest

# OpenAI 配置 (备用)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4
EOF
    echo -e "${RED}请编辑 .env 文件配置您的 API Keys${NC}"
fi

# 启动后端
start_backend() {
    echo -e "${GREEN}启动 FastAPI 后端服务...${NC}"
    echo -e "${YELLOW}服务将运行在 http://localhost:8000${NC}"
    echo -e "${YELLOW}API 文档: http://localhost:8000/docs${NC}"
    python server_pa.py &
    BACKEND_PID=$!
    echo $BACKEND_PID > .backend.pid
    sleep 2
    echo -e "${GREEN}后端服务已启动 (PID: $BACKEND_PID)${NC}"
}

# 启动前端
start_ui() {
    echo -e "${GREEN}启动 Streamlit UI...${NC}"
    echo -e "${YELLOW}界面将运行在 http://localhost:8501${NC}"
    streamlit run streamlit_app.py &
    UI_PID=$!
    echo $UI_PID > .ui.pid
    sleep 2
    echo -e "${GREEN}UI 服务已启动 (PID: $UI_PID)${NC}"
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}停止服务...${NC}"
    if [ -f .backend.pid ]; then
        kill $(cat .backend.pid) 2>/dev/null || true
        rm .backend.pid
    fi
    if [ -f .ui.pid ]; then
        kill $(cat .ui.pid) 2>/dev/null || true
        rm .ui.pid
    fi
    echo -e "${GREEN}服务已停止${NC}"
}

# 测试服务
test_services() {
    echo -e "${GREEN}测试后端服务...${NC}"
    curl -s http://localhost:8000/api/v1/status | python -m json.tool || echo -e "${RED}后端服务未响应${NC}"
}

# 主逻辑
case "${1:-all}" in
    backend)
        start_backend
        ;;
    ui)
        start_ui
        ;;
    all)
        start_backend
        sleep 3
        start_ui
        echo -e "${GREEN}=================================${NC}"
        echo -e "${GREEN}所有服务已启动!${NC}"
        echo -e "${GREEN}后端: http://localhost:8000${NC}"
        echo -e "${GREEN}前端: http://localhost:8501${NC}"
        echo -e "${GREEN}=================================${NC}"
        echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
        wait
        ;;
    stop)
        stop_services
        ;;
    test)
        test_services
        ;;
    *)
        echo "用法: $0 [backend|ui|all|stop|test]"
        echo "  backend - 仅启动后端服务"
        echo "  ui      - 仅启动前端界面"
        echo "  all     - 启动所有服务 (默认)"
        echo "  stop    - 停止所有服务"
        echo "  test    - 测试服务状态"
        exit 1
        ;;
esac
