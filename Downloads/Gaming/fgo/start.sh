#!/bin/bash
# FGO 自动刷本脚本启动器

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}FGO 自动刷本脚本 v2.0${NC}"
echo -e "${BLUE}================================${NC}"

# 检查虚拟环境
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${YELLOW}⚠️  虚拟环境不存在，正在创建...${NC}"
    python3 -m venv "$PROJECT_DIR/venv"
    echo -e "${GREEN}✅ 虚拟环境创建完成${NC}"
fi

# 激活虚拟环境
echo -e "${BLUE}📦 激活虚拟环境...${NC}"
source "$PROJECT_DIR/venv/bin/activate"

# 检查依赖
echo -e "${BLUE}🔍 检查依赖...${NC}"
python3 -m pip install -q opencv-python numpy Pillow 2>/dev/null

# 进入项目目录
cd "$PROJECT_DIR"

# 解析命令行参数
SCRIPT_MODE=""
DEVICE=""
COUNT=""
STRATEGY="round_robin"
DEBUG_FLAG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode|--script-mode)
            SCRIPT_MODE="--script-mode $2"
            shift 2
            ;;
        --device)
            DEVICE="--device $2"
            shift 2
            ;;
        --count)
            COUNT="--count $2"
            shift 2
            ;;
        --strategy|--card-strategy)
            STRATEGY="$2"
            shift 2
            ;;
        --debug)
            DEBUG_FLAG="--debug"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# 构建命令
CMD="python fgo.py"
[ -n "$SCRIPT_MODE" ] && CMD="$CMD $SCRIPT_MODE"
[ -n "$DEVICE" ] && CMD="$CMD $DEVICE"
[ -n "$COUNT" ] && CMD="$CMD $COUNT"
CMD="$CMD --card-strategy $STRATEGY"
[ -n "$DEBUG_FLAG" ] && CMD="$CMD $DEBUG_FLAG"

echo ""
echo -e "${GREEN}🚀 启动命令:${NC}"
echo -e "${YELLOW}$CMD${NC}"
echo ""

# 执行
$CMD
