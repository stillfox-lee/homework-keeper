# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在此代码库中工作的指导。

## 项目概述

作业管家是一个全栈作业管理系统，通过 OCR (PaddleOCR) 识别老师发布的作业照片，自动生成可管理的任务清单。应用解决了频繁查看微信群作业照片的痛点。

**技术栈：**
- 后端：Python 3.11+ with FastAPI, SQLAlchemy ORM, SQLite
- 前端：原生 JavaScript, HTML5, Tailwind CSS
- OCR：PaddleOCR（中文文本识别）
- 包管理器：UV（现代 Python 包管理器）

## 常用命令

```bash
# 安装依赖
uv sync

# 初始化数据库并下载 OCR 模型（仅首次运行）
uv run init

# 启动开发服务器
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 或使用直接脚本方式初始化
uv run python -m backend.scripts.init
```

应用访问地址：http://localhost:8000

## 架构说明

### 后端结构

- **`backend/main.py`** - FastAPI 应用入口，CORS 配置，静态文件服务
- **`backend/database.py`** - SQLAlchemy 连接管理，Session 创建
- **`backend/models.py`** - 数据模型：Family, Child, Subject, HomeworkBatch, BatchImage, HomeworkItem
- **`backend/schemas.py`** - Pydantic 请求/响应验证模型
- **`backend/config.py`** - 基于 Pydantic Settings 的环境配置
- **`backend/api/deps.py`** - 通过 access token 进行家庭认证的依赖注入

**路由** (`backend/api/routes/`):
- `family.py` - 家庭和成员管理，token 生成
- `upload.py` - 多图上传，通过 `ocr_service.py` 进行 OCR 处理
- `batch.py` - 作业批次 CRUD，草稿 → 进行中 → 已完成 工作流
- `items.py` - 单个作业项管理，状态转换 (todo/doing/done)
- `subject.py` - 科目管理，预定义科目和颜色
- `analytics.py` - 完成统计和用时分析

**服务** (`backend/services/`):
- `ocr_service.py` - PaddleOCR 封装（单例模式），中文文本识别
- `llm_service.py` - 文本解析提取科目/知识点（当前为规则解析，计划集成 LLM）
- `homework_service.py` - 批次管理业务逻辑

### 前端结构

- **`frontend/index.html`** - 主 SPA 界面，使用 Tailwind CSS
- **`frontend/js/api.js`** - 集中式 API 客户端封装（基于 fetch）
- **`frontend/js/app.js`** - 应用逻辑，弹窗处理，DOM 操作
- **`frontend/css/styles.css`** - 自定义样式

### 数据模型

核心实体：
- **Family** - 支持多家庭，通过 access token 共享访问
- **Child** - 家庭成员/孩子档案
- **Subject** - 预定义科目（语文、数学、英语等）带颜色标识
- **HomeworkBatch** - 将相关作业项分组，支持草稿/进行中/已完成状态
- **BatchImage** - 与批次关联的图片（原始上传）
- **HomeworkItem** - 单个作业任务，有 todo/doing/done 状态和时间戳

### 核心工作流

1. **上传 → OCR → 解析**：用户上传照片，PaddleOCR 提取文本，规则解析器识别科目和知识点
2. **批次创建**：图片归组为一个批次（草稿 → 进行中），从 OCR 文本解析出作业项
3. **作业项状态流转**：todo → doing → done，记录开始/完成时间戳
4. **家庭共享**：通过 access token 让家庭成员查看同一份作业清单

## 开发注意事项

- 当前未配置测试框架
- 未配置代码检查/格式化工具
- 前端使用原生 JS（无框架），直接操作 DOM
- OCR 模型（~100MB）在首次初始化时下载
- 数据库文件 (`data/database.db`) 已被 gitignore
- 上传图片存储在 `data/uploads/`
- CORS 已开启用于开发
- 静态文件由 FastAPI 从 `frontend/` 目录提供服务
