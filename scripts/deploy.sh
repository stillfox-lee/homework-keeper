#!/bin/bash
# 墨宝 (Mobo) 交互式部署脚本

set -e

# ============================================================================
# 配置变量
# ============================================================================
APP_NAME="mobo"
# Nginx 配置路径（根据系统类型自动检测）
NGINX_SITE=""
NGINX_STYLE=""
SYSTEMD_SERVICE="/etc/systemd/system/mobo.service"

# 部署配置（全局变量）
DOMAIN=""       # 主域名 (如 example.com)
SUB_PATH=""     # 子路径 (如 /mobo)

# 颜色输出
color_ok="\\033[1;32m"
color_error="\\033[1;31m"
color_info="\\033[1;34m"
color_warn="\\033[1;33m"
color_dim="\\033[2;37m"
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

    if [[ -f "$script_dir/pyproject.toml" ]] || [[ -d "$script_dir/.git" ]]; then
        echo "$script_dir"
    else
        local parent_dir="$(dirname "$script_dir")"
        while [[ "$parent_dir" != "/" ]]; do
            if [[ -f "$parent_dir/pyproject.toml" ]] || [[ -d "$parent_dir/.git" ]]; then
                echo "$parent_dir"
                return
            fi
            parent_dir="$(dirname "$parent_dir")"
        done
        echo "$script_dir"
    fi
}

# 检测步骤状态
check_step_status() {
    local step="$1"
    local project_root="$2"

    case "$step" in
        deps)
            if command_exists uv && command_exists python3; then
                echo -e "${color_ok}✓${color_reset}"
            else
                echo -e "${color_dim}○${color_reset}"
            fi
            ;;
        env)
            if [[ -f "$project_root/.env" ]]; then
                echo -e "${color_ok}✓${color_reset}"
            else
                echo -e "${color_dim}○${color_reset}"
            fi
            ;;
        install)
            if [[ -d "$project_root/.venv" ]]; then
                echo -e "${color_ok}✓${color_reset}"
            else
                echo -e "${color_dim}○${color_reset}"
            fi
            ;;
        frontend)
            if [[ -f "$project_root/frontend/js/config.js" ]]; then
                echo -e "${color_ok}✓${color_reset}"
            else
                echo -e "${color_dim}○${color_reset}"
            fi
            ;;
        init)
            if [[ -f "$project_root/data/database.db" ]]; then
                echo -e "${color_ok}✓${color_reset}"
            else
                echo -e "${color_dim}○${color_reset}"
            fi
            ;;
        systemd)
            if [[ -f "$SYSTEMD_SERVICE" ]]; then
                echo -e "${color_ok}✓${color_reset}"
            else
                echo -e "${color_dim}○${color_reset}"
            fi
            ;;
        nginx)
            if [[ -f "$NGINX_SITE" ]]; then
                echo -e "${color_ok}✓${color_reset}"
            else
                echo -e "${color_dim}○${color_reset}"
            fi
            ;;
        running)
            if systemctl is-active --quiet mobo 2>/dev/null; then
                echo -e "${color_ok}✓${color_reset}"
            else
                echo -e "${color_dim}○${color_reset}"
            fi
            ;;
        *)
            echo -e "${color_dim}○${color_reset}"
            ;;
    esac
}

# 询问用户
prompt_continue() {
    local message="$1"
    local default="${2:-n}"

    if [[ "$default" == "y" ]]; then
        read -p "$message [Y/n]: " -n 1 -r
        echo
        [[ ! $REPLY =~ ^[Nn]$ ]]
    else
        read -p "$message [y/N]: " -n 1 -r
        echo
        [[ $REPLY =~ ^[Yy]$ ]]
    fi
}

# 询问错误处理
prompt_error() {
    local step="$1"
    while true; do
        read -p "重试(r) / 跳过(s) / 退出(q): " -n 1 -r
        echo
        case $REPLY in
            [Rr]*) return 0 ;;  # 重试
            [Ss]*) return 1 ;;  # 跳过
            [Qq]*) exit 1 ;;    # 退出
            *) echo "请输入 r, s 或 q" ;;
        esac
    done
}

# ============================================================================
# 步骤函数
# ============================================================================

step_check_environment() {
    echo -e "${color_info}=== 检测环境 ===${color_reset}"

    if command_exists python3; then
        python_version=$(python3 --version | awk '{print $2}')
        echo -e "Python3:      ${color_ok}✓${color_reset} $python_version"
    else
        echo -e "Python3:      ${color_error}✗${color_reset} 未安装"
    fi

    if command_exists uv; then
        uv_version=$(uv --version | awk '{print $2}')
        echo -e "uv:           ${color_ok}✓${color_reset} $uv_version"
    else
        echo -e "uv:           ${color_error}✗${color_reset} 未安装"
    fi

    if command_exists nginx; then
        nginx_version=$(nginx -v 2>&1 | grep -oP 'nginx/\K[0-9.]+' || echo "installed")
        echo -e "Nginx:        ${color_ok}✓${color_reset} $nginx_version"
    else
        echo -e "Nginx:        ${color_error}✗${color_reset} 未安装"
    fi

    if command_exists systemctl; then
        echo -e "systemd:      ${color_ok}✓${color_reset} $(systemctl --version | head -n1)"
    else
        echo -e "systemd:      ${color_error}✗${color_reset} 未安装"
    fi

    echo
}

step_install_dependencies() {
    echo -e "${color_info}=== 安装依赖 (uv, Python) ===${color_reset}"

    if ! command_exists uv; then
        echo -e "${color_warn}正在安装 uv...${color_reset}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        echo -e "${color_ok}uv 安装完成${color_reset}"
    else
        echo -e "${color_ok}uv 已安装${color_reset}"
    fi

    need_python=false
    if ! command_exists python3; then
        need_python=true
    else
        if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
            need_python=true
        fi
    fi

    if $need_python; then
        echo -e "${color_warn}正在使用 uv 安装 Python 3.11+...${color_reset}"
        uv python install 3.11
        echo -e "${color_ok}Python 安装完成${color_reset}"
    else
        echo -e "${color_ok}Python 3.11+ 已安装${color_reset}"
    fi

    echo
}

step_generate_env() {
    local project_root="$1"

    echo -e "${color_info}=== 生成 .env 配置文件 ===${color_reset}"

    if [[ -f "$project_root/.env" ]]; then
        echo -e "${color_warn}.env 文件已存在${color_reset}"
        if ! prompt_continue "是否重新生成?"; then
            # 从现有 .env 读取 DOMAIN 和 SUB_PATH
            if [[ -f "$project_root/.env" ]]; then
                DOMAIN=$(grep "^DOMAIN=" "$project_root/.env" | cut -d'=' -f2)
                SUB_PATH=$(grep "^SUB_PATH=" "$project_root/.env" | cut -d'=' -f2)
            fi
            echo
            return 0
        fi
    fi

    # 复制模板
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

# CORS 配置
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# VLM 配置（智谱 AI）
ZHIPU_API_KEY=your-api-key-here
VLM_MODEL=glm-4.6v-flash
VLM_TIMEOUT=60
VLM_MAX_RETRIES=3

# 访问配置
DOMAIN=
SUB_PATH=
EOF
    fi

    echo
    echo -e "${color_info}---- 访问配置 ----${color_reset}"

    # 输入域名
    read -p "请输入主域名 (如 example.com): " input_domain
    if [[ -n "$input_domain" ]]; then
        DOMAIN="$input_domain"
        # 更新 .env 中的 DOMAIN
        if grep -q "^DOMAIN=" "$project_root/.env"; then
            sed -i "s/^DOMAIN=.*/DOMAIN=$DOMAIN/" "$project_root/.env"
        else
            echo "DOMAIN=$DOMAIN" >> "$project_root/.env"
        fi
        echo -e "${color_ok}域名: $DOMAIN${color_reset}"
    else
        DOMAIN="localhost"
        echo "DOMAIN=localhost" >> "$project_root/.env"
        echo -e "${color_warn}使用默认域名: localhost${color_reset}"
    fi

    # 输入子路径
    while true; do
        read -p "请输入子路径 (如 mobo，不要带 /，留空使用根路径): " input_path
        if [[ -z "$input_path" ]]; then
            SUB_PATH=""
            break
        fi
        # 确保不以 / 开头
        input_path="${input_path#/}"
        # 拒绝单斜杠或空值
        if [[ "$input_path" == "/" ]] || [[ -z "$input_path" ]]; then
            echo -e "${color_error}错误: 子路径不能是单斜杠${color_reset}"
            continue
        fi
        SUB_PATH="/$input_path"
        break
    done

    if [[ -n "$SUB_PATH" ]]; then
        if grep -q "^SUB_PATH=" "$project_root/.env"; then
            sed -i "s|^SUB_PATH=.*|SUB_PATH=$SUB_PATH/|" "$project_root/.env"
        else
            echo "SUB_PATH=$SUB_PATH" >> "$project_root/.env"
        fi
        echo -e "${color_ok}子路径: $SUB_PATH${color_reset}"
    else
        echo "SUB_PATH=" >> "$project_root/.env"
        echo -e "${color_info}使用根路径部署${color_reset}"
    fi

    # 更新 CORS_ORIGINS
    if [[ -n "$DOMAIN" && "$DOMAIN" != "localhost" ]]; then
        cors_value="http://$DOMAIN,https://$DOMAIN"
        if [[ -n "$SUB_PATH" ]]; then
            cors_value="http://$DOMAIN$SUB_PATH,https://$DOMAIN$SUB_PATH"
        fi
        if grep -q "^CORS_ORIGINS=" "$project_root/.env"; then
            sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=$cors_value|" "$project_root/.env"
        fi
        echo -e "${color_ok}CORS 配置: $cors_value${color_reset}"
    fi

    echo
    echo -e "${color_info}---- API 配置 ----${color_reset}"

    # 输入 API Key
    read -p "请输入智谱 API Key (留空跳过): " api_key
    if [[ -n "$api_key" ]]; then
        sed -i "s/^ZHIPU_API_KEY=.*/ZHIPU_API_KEY=$api_key/" "$project_root/.env"
        echo -e "${color_ok}API Key 已保存${color_reset}"
    else
        echo -e "${color_warn}未设置 API Key，VLM 功能将不可用${color_reset}"
    fi

    echo
    echo -e "${color_ok}配置摘要:${color_reset}"
    echo -e "  访问地址: ${color_info}http://$DOMAIN$SUB_PATH/${color_reset}"
    echo -e "${color_ok}.env 文件生成完成${color_reset}"
    echo
}

step_install_python_deps() {
    local project_root="$1"

    echo -e "${color_info}=== 安装 Python 依赖 (uv sync) ===${color_reset}"
    cd "$project_root"
    uv sync
    echo -e "${color_ok}Python 依赖安装完成${color_reset}"
    echo
}

step_generate_frontend_config() {
    local project_root="$1"

    echo -e "${color_info}=== 生成前端配置文件 ===${color_reset}"

    # 读取 .env 配置
    if [[ ! -f "$project_root/.env" ]]; then
        echo -e "${color_error}.env 文件不存在，请先生成配置文件${color_reset}"
        return 1
    fi

    # 读取 DOMAIN 和 SUB_PATH
    local domain=$(grep "^DOMAIN=" "$project_root/.env" | cut -d'=' -f2)
    local sub_path=$(grep "^SUB_PATH=" "$project_root/.env" | cut -d'=' -f2)

    if [[ -z "$domain" ]]; then
        echo -e "${color_error}DOMAIN 未配置${color_reset}"
        return 1
    fi

    # 判断协议（www 开头用 https）
    local protocol="http"
    if [[ "$domain" == www.* ]]; then
        protocol="https"
    fi

    # 移除 sub_path 末尾的 /（如果有）
    sub_path="${sub_path%/}"

    local api_base="${protocol}://${domain}${sub_path}"

    # 生成 config.js
    cat > "$project_root/frontend/js/config.js" << EOF
/**
 * 前端配置文件（由 deploy.sh 自动生成，请勿手动修改）
 */
window.API_BASE = '$api_base';
EOF

    echo -e "${color_ok}API_BASE: $api_base${color_reset}"
    echo -e "${color_ok}配置文件生成完成${color_reset}"
    echo
}

step_init_database() {
    local project_root="$1"

    echo -e "${color_info}=== 初始化数据库 ===${color_reset}"
    cd "$project_root"
    uv run init
    echo -e "${color_ok}数据库初始化完成${color_reset}"
    echo
}

step_configure_systemd() {
    local project_root="$1"

    echo -e "${color_info}=== 配置 systemd 服务 ===${color_reset}"

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
    echo -e "${color_ok}systemd 服务配置完成${color_reset}"
    echo
}

# ============================================================================
# Nginx 配置相关
# ============================================================================

# 检测 Nginx 冲突
check_nginx_conflicts() {
    local domain="$1"
    local sub_path="$2"

    echo -e "${color_info}检测 Nginx 配置冲突...${color_reset}"

    local conflicts=0

    # 检测端口 80 和相同 server_name 的配置
    local existing_configs=$(grep -l "listen 80" /etc/nginx/sites-enabled/* 2>/dev/null || true)
    if [[ -n "$existing_configs" ]]; then
        while IFS= read -r conf_file; do
            # 检查是否有相同的 server_name
            if grep -q "server_name.*$domain" "$conf_file" 2>/dev/null; then
                echo -e "  ${color_warn}!${color_reset} 发现相同域名配置: $conf_file"
                conflicts=$((conflicts + 1))
            fi
        done <<< "$existing_configs"
    fi

    # 检测 location 冲突
    if [[ -n "$sub_path" ]]; then
        local location_conflicts=$(grep -r "location $sub_path" /etc/nginx/sites-enabled/ 2>/dev/null || true)
        if [[ -n "$location_conflicts" ]]; then
            echo -e "  ${color_warn}!${color_reset} 路径冲突: $sub_path 已被使用"
            conflicts=$((conflicts + 1))
        fi
    fi

    if [[ $conflicts -eq 0 ]]; then
        echo -e "  ${color_ok}✓${color_reset} 无冲突"
        return 0
    fi

    # 有冲突，提供替代路径选项
    if [[ -n "$sub_path" ]]; then
        echo
        echo -e "${color_warn}请选择替代子路径（必须包含 'mobo'）:${color_reset}"
        echo "  1) ${sub_path}-app"
        echo "  2) ${sub_path}-homework"
        echo "  3) homework${sub_path}"
        echo "  4) 自定义"

        while true; do
            read -p "请选择 [1-4]: " -n 1 -r choice
            echo
            case $choice in
                1)
                    SUB_PATH="${sub_path}-app"
                    break
                    ;;
                2)
                    SUB_PATH="${sub_path}-homework"
                    break
                    ;;
                3)
                    # 移除开头的 / 再拼接
                    SUB_PATH="/homework${sub_path#/}"
                    break
                    ;;
                4)
                    read -p "请输入子路径（如 mobo-app）: " custom_path
                    if [[ "$custom_path" =~ mobo ]]; then
                        SUB_PATH="/${custom_path#/}"
                        break
                    else
                        echo -e "${color_error}子路径必须包含 'mobo'${color_reset}"
                    fi
                    ;;
                *)
                    echo "无效选择"
                    ;;
            esac
        done

        echo -e "${color_ok}使用子路径: $SUB_PATH${color_reset}"

        # 更新 .env 文件中的 SUB_PATH
        local project_root="$(get_project_root)"
        if [[ -f "$project_root/.env" ]]; then
            sed -i "s|^SUB_PATH=.*|SUB_PATH=$SUB_PATH|" "$project_root/.env"
        fi
    fi

    return 0
}

step_configure_nginx() {
    local project_root="$1"

    echo -e "${color_info}=== 配置 Nginx ===${color_reset}"

    # 检测 Nginx 配置方式
    if [[ -d "/etc/nginx/sites-available" ]]; then
        NGINX_STYLE="debian"
        NGINX_SITE="/etc/nginx/sites-available/mobo"
        NGINX_ENABLED="/etc/nginx/sites-enabled/mobo"
        echo -e "${color_info}检测到 Debian/Ubuntu 风格 Nginx 配置${color_reset}"
    elif [[ -d "/etc/nginx/conf.d" ]]; then
        NGINX_STYLE="rhel"
        NGINX_SITE="/etc/nginx/conf.d/mobo.conf"
        NGINX_ENABLED=""
        echo -e "${color_info}检测到 CentOS/RHEL 风格 Nginx 配置${color_reset}"
    else
        echo -e "${color_error}无法检测 Nginx 配置目录${color_reset}"
        echo -e "请确认 Nginx 已正确安装"
        return 1
    fi

    # 从 .env 读取配置（如果全局变量为空）
    if [[ -z "$DOMAIN" || -z "$SUB_PATH" ]]; then
        if [[ -f "$project_root/.env" ]]; then
            [[ -z "$DOMAIN" ]] && DOMAIN=$(grep "^DOMAIN=" "$project_root/.env" | cut -d'=' -f2)
            [[ -z "$SUB_PATH" ]] && SUB_PATH=$(grep "^SUB_PATH=" "$project_root/.env" | cut -d'=' -f2)
        fi
    fi

    # 检测冲突（只有在子路径模式下才检测）
    if [[ -n "$SUB_PATH" ]]; then
        check_nginx_conflicts "$DOMAIN" "$SUB_PATH"
        # 重新读取可能被修改的 SUB_PATH
        SUB_PATH=$(grep "^SUB_PATH=" "$project_root/.env" | cut -d'=' -f2)
    fi

    # 生成 Nginx 配置
    if [[ -z "$DOMAIN" ]]; then
        DOMAIN="_"  # 默认匹配所有域名
    fi

    if [[ -z "$SUB_PATH" ]]; then
        # 根路径部署
        cat > "$NGINX_SITE" << EOF
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 10M;

    location /frontend/ {
        alias $project_root/frontend/;
        try_files \$uri \$uri/ /frontend/index.html;
    }

    location /uploads/ {
        alias $project_root/data/uploads/;
    }

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
    else
        # 子路径部署 - 使用 rewrite 去掉前缀后代理到后端
        cat > "$NGINX_SITE" << EOF
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 10M;

    # 子路径 - 所有请求都通过 rewrite 去掉前缀
    # /mobo/api/xxx → /api/xxx
    # /mobo/today.html → /today.html
    location $SUB_PATH/ {
        rewrite ^$SUB_PATH/(.*) /\$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }

    # 子路径根（处理不以 / 结尾的请求）
    location $SUB_PATH {
        rewrite ^$SUB_PATH\$ $SUB_PATH/ permanent;
    }
}
EOF
    fi

    # 启用站点（仅 Debian 风格需要符号链接）
    if [[ "$NGINX_STYLE" == "debian" ]]; then
        if [[ ! -L "$NGINX_ENABLED" ]]; then
            ln -sf "$NGINX_SITE" "$NGINX_ENABLED"
            echo -e "${color_info}创建符号链接: $NGINX_ENABLED${color_reset}"
        fi
    fi
    # RHEL 风格不需要符号链接，配置文件直接在 conf.d/ 中生效

    # 测试配置
    if nginx -t 2>&1 | grep -q "successful"; then
        systemctl reload nginx
        echo -e "${color_ok}Nginx 配置完成${color_reset}"
    else
        echo -e "${color_error}Nginx 配置测试失败${color_reset}"
        return 1
    fi

    echo
}

step_start_service() {
    echo -e "${color_info}=== 启动服务 ===${color_reset}"
    systemctl restart mobo

    if systemctl is-active --quiet mobo; then
        echo -e "${color_ok}服务已启动${color_reset}"
        echo
        show_completion_info
    else
        echo -e "${color_error}服务启动失败${color_reset}"
        echo "查看日志: journalctl -u mobo -n 50"
        return 1
    fi
}

# ============================================================================
# 显示函数
# ============================================================================

show_menu() {
    local project_root="$1"

    clear
    echo -e "${color_info}╔════════════════════════════════════════╗${color_reset}"
    echo -e "${color_info}║         墨宝 (Mobo) 部署脚本          ║${color_reset}"
    echo -e "${color_info}╚════════════════════════════════════════╝${color_reset}"
    echo
    echo -e "${color_info}项目路径:${color_reset} $project_root"
    echo
    echo "步骤状态:"
    echo "  1) 检测环境                    $(check_step_status check "$project_root")"
    echo "  2) 安装依赖 (uv, Python)       $(check_step_status deps "$project_root")"
    echo "  3) 生成 .env 配置文件          $(check_step_status env "$project_root")"
    echo "  4) 安装 Python 依赖            $(check_step_status install "$project_root")"
    echo "  5) 生成前端配置文件            $(check_step_status frontend "$project_root")"
    echo "  6) 初始化数据库                $(check_step_status init "$project_root")"
    echo "  7) 配置 systemd 服务           $(check_step_status systemd "$project_root")"
    echo "  8) 配置 Nginx                  $(check_step_status nginx "$project_root")"
    echo "  9) 启动服务                    $(check_step_status running "$project_root")"
    echo
    echo "操作:"
    echo "  1-9) 执行对应步骤"
    echo "  a)   全部部署 (按顺序执行)"
    echo "  0)   退出"
    echo
}

show_completion_info() {
    echo -e "${color_ok}========================================${color_reset}"
    echo -e "${color_ok}     部署完成！${color_reset}"
    echo -e "${color_ok}========================================${color_reset}"
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
# 执行函数
# ============================================================================

execute_step() {
    local step="$1"
    local project_root="$2"

    case "$step" in
        1) step_check_environment ;;
        2) step_install_dependencies ;;
        3) step_generate_env "$project_root" ;;
        4) step_install_python_deps "$project_root" ;;
        5) step_generate_frontend_config "$project_root" ;;
        6) step_init_database "$project_root" ;;
        7) step_configure_systemd "$project_root" ;;
        8) step_configure_nginx "$project_root" ;;
        9) step_start_service ;;
    esac
}

run_all_steps() {
    local project_root="$1"

    for step in {1..9}; do
        show_menu "$project_root"
        echo -e "${color_info}正在执行步骤 $step...${color_reset}"
        echo

        if ! execute_step "$step" "$project_root"; then
            if prompt_error "$step"; then
                continue  # 重试
            else
                break     # 跳过
            fi
        fi

        if [[ $step -lt 9 ]]; then
            if ! prompt_continue "继续下一步?" "y"; then
                break
            fi
        fi
    done
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    # 检查 root 权限
    if [[ $EUID -ne 0 ]]; then
        echo -e "${color_error}错误: 此脚本需要 root 权限${color_reset}"
        echo "请使用: sudo $0"
        exit 1
    fi

    # 获取项目根目录
    PROJECT_ROOT="$(get_project_root)"

    # 主菜单循环
    while true; do
        show_menu "$PROJECT_ROOT"
        read -p "请选择 [0-9,a]: " -n 1 -r choice
        echo

        case "$choice" in
            [1-9])
                if ! execute_step "$choice" "$PROJECT_ROOT"; then
                    prompt_error "$choice" || continue
                fi
                read -p "按 Enter 继续..."
                ;;
            a|A)
                run_all_steps "$PROJECT_ROOT"
                read -p "按 Enter 返回菜单..."
                ;;
            0)
                echo "退出"
                exit 0
                ;;
            *)
                echo -e "${color_error}无效选择，请重试${color_reset}"
                sleep 1
                ;;
        esac
    done
}

main
