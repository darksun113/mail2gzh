#!/bin/bash

# Mail2GZH 启动脚本
# 作者: Mail2GZH Team
# 版本: 1.0.0

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Python 版本
check_python() {
    log_info "检查 Python 版本..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装，请先安装 Python 3.13.3+"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "当前 Python 版本: $python_version"
    
    # 检查 Python 版本是否满足要求（3.8+）
    major_version=$(echo $python_version | cut -d. -f1)
    minor_version=$(echo $python_version | cut -d. -f2)
    
    if [ "$major_version" -lt 3 ] || ([ "$major_version" -eq 3 ] && [ "$minor_version" -lt 8 ]); then
        log_error "需要 Python 3.8+，当前版本: $python_version"
        exit 1
    fi
    
    log_success "Python 版本检查通过"
}

# 检查虚拟环境
check_venv() {
    log_info "检查虚拟环境..."
    if [ ! -d "venv" ]; then
        log_warning "虚拟环境不存在，正在创建..."
        python3 -m venv venv
        log_success "虚拟环境创建完成"
    else
        log_success "虚拟环境已存在"
    fi
}

# 激活虚拟环境
activate_venv() {
    log_info "激活虚拟环境..."
    source venv/bin/activate
    log_success "虚拟环境已激活"
}

# 检查并安装依赖
install_dependencies() {
    log_info "检查项目依赖..."
    
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt 文件不存在"
        exit 1
    fi
    
    # 检查是否需要安装依赖
    if [ ! -f "venv/pyvenv.cfg" ] || [ requirements.txt -nt venv/pyvenv.cfg ]; then
        log_info "正在安装/更新依赖..."
        pip install --upgrade pip
        pip install -r requirements.txt
        log_success "依赖安装完成"
    else
        log_info "依赖已是最新版本"
    fi
}

# 检查环境变量文件
check_env() {
    log_info "检查环境变量配置..."
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            log_warning ".env 文件不存在，正在从 env.example 创建..."
            cp env.example .env
            log_warning "请编辑 .env 文件，填写必要的配置信息"
            log_warning "特别是数据库、Gmail API、OpenAI API 和微信公众号的配置"
        else
            log_error "env.example 文件不存在，无法创建 .env 文件"
            exit 1
        fi
    else
        log_success "环境变量文件已存在"
    fi
}

# 检查日志目录
check_logs() {
    log_info "检查日志目录..."
    if [ ! -d "logs" ]; then
        mkdir -p logs
        log_success "日志目录创建完成"
    else
        log_success "日志目录已存在"
    fi
}

# 启动服务
start_service() {
    log_info "启动 Mail2GZH 服务..."
    log_info "服务地址: http://localhost:8000"
    log_info "API 文档: http://localhost:8000/docs"
    log_info "按 Ctrl+C 停止服务"
    echo ""
    
    # 启动 uvicorn 服务
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
}

# 主函数
main() {
    echo "=========================================="
    echo "    Mail2GZH 邮件转发服务启动脚本"
    echo "=========================================="
    echo ""
    
    check_python
    check_venv
    activate_venv
    install_dependencies
    check_env
    check_logs
    
    echo ""
    log_success "所有检查完成，正在启动服务..."
    echo ""
    
    start_service
}

# 捕获中断信号
trap 'echo ""; log_info "正在停止服务..."; exit 0' INT

# 运行主函数
main "$@"
