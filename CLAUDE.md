# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在此代码库中工作的指导。

## 项目概述

墨宝 (Mobo) 是一个全栈作业管理系统，通过 VLM 识别老师发布的作业照片，自动生成可管理的任务清单。应用解决了频繁查看微信群作业照片的痛点。

**技术栈：**

- 后端：Python 3.11+ with FastAPI, SQLAlchemy ORM, SQLite
- 前端：原生 JavaScript, HTML5, Tailwind CSS
- 包管理器：UV（现代 Python 包管理器）

## 常用命令

```bash
# 安装依赖
uv sync

# 初始化数据库（仅首次运行）
uv run init

# 启动开发服务器
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 或使用直接脚本方式初始化
uv run python -m backend.scripts.init
```

应用访问地址：<http://localhost:8000>

## 架构说明

### 后端结构

- **`backend/main.py`** - FastAPI 应用入口，CORS 配置，静态文件服务
- **`backend/database.py`** - SQLAlchemy 连接管理，Session 创建
- **`backend/models.py`** - 数据模型：Family, Child, Subject, HomeworkBatch, BatchImage, HomeworkItem
- **`backend/schemas.py`** - Pydantic 请求/响应验证模型
- **`backend/config.py`** - 基于 Pydantic Settings 的环境配置
- **`backend/api/deps.py`** - 通过 access token 进行家庭认证的依赖注入

**服务** (`backend/services/`):

- `llm_service.py` - 文本解析提取科目/知识点（当前为规则解析，计划集成 LLM）
- `homework_service.py` - 批次管理业务逻辑

### 前端结构（MPA 多页面应用）

```
frontend/
├── index.html          # 首页（重定向到最近批次）
├── today.html          # 今日作业详情页
├── registry.html       # 作业登记簿页面
├── css/
│   ├── common.css      # 公共样式
│   ├── today.css       # 今日作业样式
│   └── registry.css    # 登记簿样式
└── js/
    ├── api.js          # API 封装
    ├── utils.js        # 工具函数
    ├── today.js        # 今日作业逻辑
    └── registry.js     # 登记簿逻辑
```

**页面导航：**
- `/` → 自动跳转到最近的 active 批次
- `/today.html?id=1` → 批次详情页
- `/registry.html` → 作业登记簿

**脚本加载顺序（重要）：**
各页面的脚本应按以下顺序加载，确保依赖正确：
1. `api.js` - API 调用封装
2. `utils.js` - 工具函数（包括 Toast 组件）
3. 业务逻辑模块（如 `editor.js`、`today.js` 等）
4. 页面初始化脚本

**新增页面步骤：**
1. 在 `frontend/` 创建新的 HTML 文件
2. 在 `backend/main.py` 添加对应路由：
   ```python
   @app.get("/newpage.html")
   async def newpage():
       return FileResponse("frontend/newpage.html")
   ```

### 前端页面设计

- 主要目标用户是 k12 学生，所以界面用语应该保持易懂亲切，特别是小学生词汇量有限。

### 数据模型

核心实体：

- **Family** - 支持多家庭，通过 access token 共享访问
- **Child** - 家庭成员/孩子档案
- **Subject** - 预定义科目（语文、数学、英语等）带颜色标识
- **HomeworkBatch** - 将相关作业项分组，支持草稿/进行中/已完成状态
- **BatchImage** - 与批次关联的图片（原始上传）
- **HomeworkItem** - 单个作业任务，有 todo/doing/done 状态和时间戳

### 核心工作流

1. **批次创建**：图片归组为一个批次（草稿 → 进行中），从 VLM 文本解析出作业项
2. **作业项状态流转**：todo → doing → done，记录开始/完成时间戳
3. **家庭共享**：通过 access token 让家庭成员查看同一份作业清单

## 开发注意事项

### 前端组件化规范

**通用组件规则：**
- 通用组件定义在 `frontend/js/utils.js` 中
- 通用组件必须导出到 `window` 对象，供其他模块使用
- 禁止在业务模块中重复定义通用组件

**Toast 组件使用规范：**
- 统一使用 `utils.js` 中的 `showToast(message, duration)` 函数
- Toast 仅用于显示操作结果（成功/失败/错误）
- **禁止**使用 Toast 显示"加载中"、"正在处理"等过程性提示
- 各页面 HTML 需包含 Toast 元素：`<div id="toast" class="toast hidden"></div>`

**全局状态管理：**
- 使用 `window.state` 管理全局状态（如科目列表）
- 多个模块共享状态时，使用 `var state = window.state` 允许重复声明
- 避免使用 `const/let` 声明可能被多个模块引用的全局变量

**避免重复定义：**
- 检查现有模块是否已定义所需函数/变量
- 使用 `if (typeof window.fnName !== 'function')` 检查函数是否存在
- 使用 `var` 而非 `const/let` 声明可能重复的全局变量

### 通用开发规范

- 当前未配置测试框架
- 未配置代码检查/格式化工具

### 时区处理原则（重要）

**统一使用 UTC 时间存储：**

所有数据库时间字段统一使用 UTC 时间存储，确保时区一致性。

| 层级 | 处理方式 |
|------|----------|
| **数据库存储** | 全部使用 UTC 时间 |
| **代码获取时间** | 使用 `datetime.utcnow()` 而非 `datetime.now()` |
| **业务逻辑** | 判断工作日/节假日时转换为本地时间（Asia/Shanghai） |
| **API 返回** | 返回 UTC 时间的 ISO 格式字符串 |
| **前端显示** | 浏览器自动将 ISO 时间转换为本地时区显示 |

**代码规范：**
```python
# ✅ 正确：获取 UTC 时间
now = datetime.utcnow()

# ❌ 错误：获取本地时间（会导致时区混乱）
now = datetime.now()
```

**特殊情况：**
- `generate_batch_name()` - 需要本地日期显示，转为本地时区后获取月/日
- `calculate_deadline()` - 需要基于本地日期判断工作日，内部处理时区转换

**依赖：**
- `pytz` - 用于时区转换（如 `Asia/Shanghai`）
