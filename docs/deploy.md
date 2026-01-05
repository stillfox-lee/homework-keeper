# 部署指南

本文档介绍如何将墨宝部署到生产服务器。

## 部署架构

```
Internet → Nginx (反向代理) → systemd → Uvicorn (FastAPI) → SQLite + 上传文件
```

## 系统要求

- **操作系统**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- **Python**: 3.11+ (脚本会自动安装)
- **Nginx**: 已安装
- **systemd**: 已安装 (大多数 Linux 发行版默认包含)

## 快速部署

### 1. 克隆代码

```bash
git clone <repo-url> homework-keeper
cd homework-keeper
```

### 2. 环境检测（可选）

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh --check
```

这会检测服务器环境是否满足要求，不执行安装。

### 3. 执行部署

```bash
sudo ./scripts/deploy.sh
```

部署脚本会：
- 检测并安装 Python 3.11+ (使用 uv)
- 安装 uv 包管理器
- 生成 `.env` 配置文件（交互式输入 API Key）
- 安装 Python 依赖
- 初始化数据库
- 配置 systemd 服务
- 配置 Nginx
- 启动服务

## 配置说明

### 环境变量

部署时会生成 `.env` 文件，包含以下配置：

```bash
# 应用配置
APP_NAME=墨宝
DEBUG=false                       # 生产环境设为 false
DATABASE_URL=sqlite:///./data/database.db
UPLOAD_DIR=./data/uploads
MAX_UPLOAD_SIZE=10485760          # 10MB

# CORS 配置（逗号分隔）
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# VLM 配置（智谱 AI）
ZHIPU_API_KEY=your-api-key-here   # 需要替换为实际 Key
VLM_MODEL=glm-4.6v-flash
VLM_TIMEOUT=60
VLM_MAX_RETRIES=3
```

### systemd 服务

服务文件位于 `/etc/systemd/system/mobo.service`：

```ini
[Unit]
Description=Mobo Homework Keeper
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/homework-keeper
Environment="PATH=/root/.local/bin:/usr/bin"
ExecStart=/root/.local/bin/uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Nginx 配置

配置文件位于 `/etc/nginx/sites-available/mobo`：

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    location /frontend/ {
        alias /path/to/homework-keeper/frontend/;
        expires 7d;
    }

    location /uploads/ {
        alias /path/to/homework-keeper/data/uploads/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }
}
```

## 服务管理

### systemd 命令

```bash
systemctl status mobo            # 查看状态
systemctl start mobo             # 启动
systemctl stop mobo              # 停止
systemctl restart mobo           # 重启
systemctl enable mobo            # 开机自启
systemctl disable mobo           # 禁用开机自启
```

### 查看日志

```bash
journalctl -u mobo -f            # 实时查看日志
journalctl -u mobo -n 100        # 查看最近 100 行
journalctl -u mobo --since today # 查看今天的日志
```

### 更新部署

当代码更新后：

```bash
cd homework-keeper
git pull
uv sync                          # 更新依赖
systemctl restart mobo           # 重启服务
```

## 目录结构

部署后的目录结构：

```
homework-keeper/                 # 项目根目录
├── backend/                     # 后端代码
├── frontend/                    # 前端代码
├── scripts/
│   └── deploy.sh                # 部署脚本
├── pyproject.toml               # 依赖配置
├── .env                         # 环境变量（自动生成）
└── data/                        # 数据目录（自动创建）
    ├── database.db              # SQLite 数据库
    └── uploads/                 # 上传文件
```

## 故障排查

### 服务无法启动

```bash
# 查看服务状态
systemctl status mobo

# 查看详细日志
journalctl -u mobo -n 50 --no-pager
```

### Nginx 502 错误

```bash
# 检查后端服务是否运行
systemctl status mobo

# 检查端口占用
netstat -tlnp | grep 8000

# 测试 Nginx 配置
nginx -t
```

### 数据库问题

```bash
# 重新初始化数据库
cd /path/to/homework-keeper
uv run init
```

## 数据备份

### 备份数据库

```bash
cp /path/to/homework-keeper/data/database.db /backup/mobo-$(date +%Y%m%d).db
```

### 备份上传文件

```bash
tar -czf /backup/mobo-uploads-$(date +%Y%m%d).tar.gz /path/to/homework-keeper/data/uploads/
```

### 定时备份（crontab）

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点备份
0 2 * * * cp /path/to/homework-keeper/data/database.db /backup/mobo-$(date +\%Y\%m\%d).db
```

## 脚本参数

```bash
./scripts/deploy.sh --check      # 仅检测环境
./scripts/deploy.sh              # 完整部署
./scripts/deploy.sh --force      # 强制重新安装依赖
./scripts/deploy.sh --help       # 显示帮助
```
