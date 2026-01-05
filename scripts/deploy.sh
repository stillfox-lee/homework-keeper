#!/bin/bash
set -e

# 墨宝 (Mobo) 部署脚本
# 支持的参数: --check (仅检测环境), --force (强制重新安装)

# ============================================================================
# 配置变量
# ============================================================================
APP_NAME="mobo"
NGINX_SITE="/etc/nginx/sites-available/mobo"
SYSTEMD_SERVICE="/etc/systemd/system/mobo.service"

# 颜色输出
color_ok="\\033[1;32m"
color_error="\\033[1;31m"
color_info="\\033[1;34m"
color_warn="\\033[1;33m"
color_reset="\\033[0m"

# ============================================================================
# 工具函数
# ============================================================================

# 检测命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 获取项目根目录
get_project_root() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # 通过 pyproject.toml 或 .git 确认是项目根目录
    if [[ -f "$script_dir/pyproject.toml" ]] || [[ -d "$script_dir/.git" ]]; then
        echo "$script_dir"
    else
        # 向上查找
        local parent_dir="$(dirname "$script_dir")"
        while [[ "$parent_dir" != "/" ]]; do
            if [[ -f "$parent_dir/pyproject.toml" ]] || [[ -d "$parent_dir/.git" ]]; then
                echo "$parent_dir"
                return
            fi
            parent_dir="$(dirname "$parent_dir")"
        done
        echo "$script_dir"  # 找不到则返回脚本所在目录
    fi
}

# ============================================================================
# 环境检测
# ============================================================================

check_environment() {
    echo -e "${color_info}=== 环境检测 ===${color_reset}"

    # Python 检测
    if command_exists python3; then
        python_version=$(python3 --version | awk '{print $2}')
        echo -e "Python3:      ${color_ok}✓${color_reset} $python_version"
    else
        echo -e "Python3:      ${color_error}✗${color_reset} 未安装"
    fi

    # uv 检测
    if command_exists uv; then
        uv_version=$(uv --version | awk '{print $2}')
        echo -e "uv:           ${color_ok}✓${color_reset} $uv_version"
    else
        echo -e "uv:           ${color_error}✗${color_reset} 未安装"
    fi

    # Nginx 检测
    if command_exists nginx; then
        nginx_version=$(nginx -v 2>&1 | grep -oP 'nginx/\K[0-9.]+' || echo "installed")
        echo -e "Nginx:        ${color_ok}✓${color_reset} $nginx_version"
    else
        echo -e "Nginx:        ${color_error}✗${color_reset} 未安装"
    fi

    # systemd 检测
    if command_exists systemctl; then
        echo -e "systemd:      ${color_ok}✓${color_reset} $(systemctl --version | head -n1)"
    else
        echo -e "systemd:      ${color_error}✗${color_reset} 未安装"
    fi

    echo
}

# ============================================================================
# 安装依赖
# ============================================================================

install_dependencies() {
    echo -e "${color_info}=== 安装依赖 ===${color_reset}"

    # uv（优先安装，因为可以管理 Python）
    if ! command_exists uv; then
        echo -e "${color_warn}正在安装 uv...${color_reset}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    else
        echo -e "${color_ok}uv 已安装${color_reset}"
    fi

    # Python 3.11+ (使用 uv 管理)
    need_python=false
    if ! command_exists python3; then
        need_python=true
    else
        # 检查版本是否 >= 3.11
        if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
            need_python=true
        fi
    fi

    if $need_python; then
        echo -e "${color_warn}正在使用 uv 安装 Python 3.11+...${color_reset}"
        uv python install 3.11
    else
        echo -e "${color_ok}Python 3.11+ 已安装${color_reset}"
    fi

    echo -e "${color_ok}依赖安装完成${color_reset}\\n"
}

# ============================================================================
# 生成 .env 文件
# ============================================================================

generate_env_file() {
    local project_root="$1"

    if [[ -f "$project_root/.env" ]]; then
        echo -e "${color_warn}.env 文件已存在${color_reset}"
        read -p "是否重新生成? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${color_ok}保留现有 .env 文件${color_reset}\\n"
            return
        fi
    fi

    echo -e "${color_info}=== 生成 .env 文件 ===${color_reset}"

    # 复制示例文件
    if [[ -f "$project_root/.env.example" ]]; then
        cp "$project_root/.env.example" "$project_root/.env"
    else
        cat > "$project_root/.env" << 'EOF'
# 应用配置
APP_NAME=墨宝
DEBUG=false
DATABASE_URL=sqlite:///./data/database.db
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE=10485760

# CORS 配置（逗号分隔）
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# VLM 配置（智谱 AI）
ZHIPU_API_KEY=your-api-key-here
VLM_MODEL=glm-4.6v-flash
VLM_TIMEOUT=60
VLM_MAX_RETRIES=3
EOF
    fi

    # 交互式输入 ZHIPU_API_KEY
    echo
    read -p "请输入智谱 API Key (留空跳过): " api_key
    if [[ -n "$api_key" ]]; then
        sed -i "s/^ZHIPU_API_KEY=.*/ZHIPU_API_KEY=$api_key/" "$project_root/.env"
        echo -e "${color_ok}API Key 已保存${color_reset}"
    else
        echo -e "${color_warn}未设置 API Key，VLM 功能将不可用${color_reset}"
    fi

    # 获取服务器 IP 用于 CORS 配置
    read -p "请输入服务器访问地址 (如 http://192.168.1.100，留空使用默认): " server_url
    if [[ -n "$server_url" ]]; then
        sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=$server_url,http://localhost:8000|" "$project_root/.env"
        echo -e "${color_ok}CORS 配置已更新${color_reset}"
    fi

    echo
}

# ============================================================================
# 配置 systemd 服务
# ============================================================================

configure_systemd() {
    local project_root="$1"

    echo -e "${color_info}=== 配置 systemd 服务 ===${color_reset}"

    # 检测 uv 路径
    local uv_path=$(command -v uv || echo "$HOME/.local/bin/uv")

    cat > "$SYSTEMD_SERVICE" << EOF
[Unit]
Description=Mobo Homework Keeper
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$project_root
Environment="PATH=$HOME/.local/bin:/usr/bin"
ExecStart=$uv_path run uvicorn backend.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable mobo
    echo -e "${color_ok}systemd 服务配置完成${color_reset}\\n"
}

# ============================================================================
# 配置 Nginx
# ============================================================================

configure_nginx() {
    local project_root="$1"

    echo -e "${color_info}=== 配置 Nginx ===${color_reset}"

    cat > "$NGINX_SITE" << EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    # 静态文件缓存
    location /frontend/ {
        alias $project_root/frontend/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # 上传文件
    location /uploads/ {
        alias $project_root/data/uploads/;
        expires 30d;
    }

    # API 代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }
}
EOF

    # 启用站点（如果尚未启用）
    if [[ ! -L "/etc/nginx/sites-enabled/mobo" ]]; then
        ln -sf "$NGINX_SITE" "/etc/nginx/sites-enabled/mobo"
    fi

    # 测试配置
    if nginx -t 2>&1 | grep -q "successful"; then
        systemctl reload nginx
        echo -e "${color_ok}Nginx 配置完成${color_reset}\\n"
    else
        echo -e "${color_error}Nginx 配置测试失败，请检查配置${color_reset}\\n"
        return 1
    fi
}

# ============================================================================
# 显示完成信息
# ============================================================================

show_completion_info() {
    local project_root="$1"

    echo -e "${color_ok}========================================${color_reset}"
    echo -e "${color_ok}     部署完成！${color_reset}"
    echo -e "${color_ok}========================================${color_reset}"
    echo
    echo -e "${color_info}项目路径:${color_reset} $project_root"
    echo -e "${color_info}数据目录:${color_reset} $project_root/data/"
    echo
    echo -e "${color_info}管理命令:${color_reset}"
    echo "  systemctl status mobo     # 查看状态"
    echo "  systemctl restart mobo    # 重启服务"
    echo "  systemctl stop mobo       # 停止服务"
    echo "  journalctl -u mobo -f     # 查看日志"
    echo
    echo -e "${color_info}访问地址:${color_reset} http://$(hostname -I | awk '{print $1}')/"
    echo
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    # 解析参数
    CHECK_ONLY=false
    FORCE_INSTALL=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --check)
                CHECK_ONLY=true
                shift
                ;;
            --force)
                FORCE_INSTALL=true
                shift
                ;;
            -h|--help)
                echo "用法: $0 [--check] [--force]"
                echo
                echo "选项:"
                echo "  --check    仅检测环境，不执行安装"
                echo "  --force    强制重新安装依赖"
                echo "  -h, --help 显示帮助信息"
                exit 0
                ;;
            *)
                echo "未知选项: $1"
                echo "使用 -h 或 --help 查看帮助"
                exit 1
                ;;
        esac
    done

    # 检查 root 权限
    if [[ $EUID -ne 0 ]]; then
        echo -e "${color_error}错误: 此脚本需要 root 权限${color_reset}"
        echo "请使用: sudo $0"
        exit 1
    fi

    # 获取项目根目录
    PROJECT_ROOT="$(get_project_root)"
    echo -e "${color_info}项目根目录: ${PROJECT_ROOT}${color_reset}\\n"

    # 环境检测
    check_environment

    if $CHECK_ONLY; then
        exit 0
    fi

    # 安装依赖
    install_dependencies

    # 生成 .env 文件
    generate_env_file "$PROJECT_ROOT"

    # 安装 Python 依赖
    echo -e "${color_info}=== 安装 Python 依赖 ===${color_reset}"
    cd "$PROJECT_ROOT"
    uv sync
    echo -e "${color_ok}Python 依赖安装完成${color_reset}\\n"

    # 初始化数据库
    echo -e "${color_info}=== 初始化数据库 ===${color_reset}"
    uv run init
    echo -e "${color_ok}数据库初始化完成${color_reset}\\n"

    # 配置 systemd 服务
    configure_systemd "$PROJECT_ROOT"

    # 配置 Nginx
    configure_nginx "$PROJECT_ROOT"

    # 启动服务
    echo -e "${color_info}=== 启动服务 ===${color_reset}"
    systemctl restart mobo
    echo -e "${color_ok}服务已启动${color_reset}\\n"

    # 显示完成信息
    show_completion_info "$PROJECT_ROOT"
}

# 执行主流程
main "$@"
