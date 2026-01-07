# 墨宝 (Mobo)

通过 VLM 识别老师发布的作业照片，自动生成可管理的作业清单，解决频繁查看微信群作业照片的痛点。

## 功能特点

- 📸 **图片上传识别** - 支持批量上传作业照片，自动 VLM 识别
- 📝 **作业清单管理** - 自动解析作业内容，支持手动编辑
- ✅ **状态跟踪** - todo / doing / done 三种状态，记录完成时间
- 🎨 **科目分类** - 支持多科目管理，带颜色标识
- 📊 **数据统计** - 每日完成率、用时分析

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv（推荐）
uv sync

```

### 2. 初始化项目

```bash
# 初始化数据库
uv run init

# 创建家庭和孩子（首次运行必须）
uv run python -m backend.scripts.add_user --family "家庭名" --child "孩子名"
```

### 3. 启动服务

```bash
# 启动服务器
uv run serve

# 开发模式（自动重载）
uv run serve --reload
```

其他脚本：

```bash
uv run python -m backend.scripts.test_ocr PATH
uv run python -m backend.scripts.test_vlm <图片路径>...
```

## 生产部署

生产环境部署请参阅 [部署指南](docs/deploy.md)。

```bash
git clone <repo-url> homework-keeper
cd homework-keeper
sudo ./scripts/deploy.sh
```

运行后会显示交互式菜单，可选择执行单个步骤或全部部署。

## 项目结构

```
homework-keeper/
├── backend/
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置文件
│   ├── database.py             # 数据库连接管理
│   ├── models.py               # SQLAlchemy 数据模型
│   ├── schemas.py              # Pydantic 数据验证模型
│   ├── services/
│   │   ├── llm_service.py      # 文本解析（规则/LLM）
│   │   └── homework_service.py # 作业批次管理业务
│   └── api/routes/             # API 路由
├── frontend/
│   ├── index.html              # 主页面
│   ├── css/styles.css          # 样式
│   └── js/
│       ├── api.js              # API 调用封装
│       └── app.js              # 主应用逻辑
├── data/
│   ├── database.db             # SQLite 数据库
│   └── uploads/                # 上传图片存储
└── pyproject.toml              # 项目配置
```

## 使用说明

### 添加作业

1. 点击右上角「+ 添加作业」按钮
2. 选择或拖拽作业照片
3. 等待 VLM 识别完成
4. 确认/编辑作业清单
5. 设置截止时间（可选）
6. 点击「确认」保存

### 管理作业

- **开始** - 点击「开始」按钮将状态改为进行中
- **完成** - 点击「完成」按钮标记作业已完成
- **删除** - 点击删除图标移除作业项
- **筛选** - 顶部筛选栏可按状态筛选作业

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy
- **前端**: 原生 JavaScript + HTML + Tailwind CSS
- **数据库**: SQLite
