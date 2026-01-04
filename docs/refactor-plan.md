# 墨宝前端重构计划

## 概述

基于 `docs/ui-v1.md` 全新设计前端 UI，不受旧代码约束。

### 导航逻辑

```
┌─────────────────────────────────────┐
│                                     │
│   今日作业 ←[返回]→ 作业登记簿       │
│      ↑              │               │
│      └──────────────┘               │
│    (点击书本卡片)                   │
│                                     │
│  hover/长按 → 编辑器                │
│                                     │
└─────────────────────────────────────┘
```

### 页面结构

| 页面 | 说明 |
|------|------|
| 今日作业 | 首页 = 作业详情，显示批次详情、大图、作业列表 |
| 作业登记簿 | 书本网格，显示所有批次 |
| 编辑器 | 全屏弹窗，新建/编辑作业 |

---

## 并行任务拆分

按技术独立性拆分为 **5 个并行任务**，每个任务修改独立的代码文件，可独立开发测试。

### 任务 1: 基础设施 - 路由和状态管理

**负责人**: 待定
**优先级**: P0（其他任务依赖）
**文件**: `frontend/js/app.js`

**工作内容**:
1. 重构状态管理
2. 实现 hash 路由
3. 实现视图切换逻辑
4. 提供状态更新接口

**状态结构**:
```javascript
const state = {
    currentView: 'today',           // 'today' | 'registry'
    currentBatchId: null,
    todayData: { batch: null, items: [], images: [] },
    registryData: { batches: [], page: 0, hasMore: true, loading: false },
    editorData: { open: false, mode: 'new', batchId: null, images: [], items: [], deadlineAt: null },
};
```

**路由规则**:
| 路由 | 动作 |
|------|------|
| `#/` 或 `#/today/{batchId}` | 显示今日作业 |
| `#/registry` | 显示作业登记簿 |
| `#/editor/new` | 打开新建编辑器 |
| `#/editor/{id}` | 打开编辑编辑器 |

**验收**:
- [ ] hash 路由正确解析
- [ ] 状态更新后视图正确切换
- [ ] 提供其他模块调用的接口

---

### 任务 2: 作业登记簿页面

**负责人**: 待定
**优先级**: P1
**文件**: `frontend/css/styles.css`, `frontend/js/views.js` (registryView), `frontend/js/renderers.js` (书本卡片)

**工作内容**:

1. **CSS 样式** (`styles.css`):
   - 拟物化书本卡片样式（书脊、书页、3D 效果）
   - 响应式网格（PC 4列、平板 3列、移动 2列）
   - hover 编辑按钮（PC）
   - 空状态样式

2. **视图逻辑** (`views.js` 新增 `registryView`):
   - 初始加载（填满一屏减一格）
   - 滚动加载更多
   - 点击书本跳转

3. **渲染函数** (`renderers.js`):
   - `createBookCardHTML(batch)` - 书本卡片
   - `createAddCardHTML()` - 添加按钮
   - `createRegistryEmptyHTML()` - 空状态

**响应式配置**:
| 屏幕 | 列数 | 初始加载 | 滚动加载 |
|------|------|----------|----------|
| PC ≥1024px | 4 | 7个 | 4个 |
| 平板 768-1023px | 3 | 5个 | 3个 |
| 移动 <768px | 2 | 3个 | 2个 |

**验收**:
- [ ] 书本拟物化样式正确
- [ ] 响应式网格正确
- [ ] 滚动加载正常
- [ ] 点击书本跳转今日作业

---

### 任务 3: 今日作业/详情页面

**负责人**: 待定
**优先级**: P1
**文件**: `frontend/css/styles.css`, `frontend/js/views.js` (todayView), `frontend/js/renderers.js` (作业列表)

**工作内容**:

1. **CSS 样式** (`styles.css`):
   - 大图滑动区域样式
   - 作业列表样式
   - deadline 倒计时样式
   - 返回按钮样式

2. **视图逻辑** (`views.js` 新增 `todayView`):
   - 加载批次详情
   - 加载作业项和图片
   - 返回按钮跳转
   - 作业状态操作

3. **渲染函数** (`renderers.js`):
   - `createTodayHeaderHTML(batch)` - 页面头部
   - `createImageStripHTML(images)` - 图片滑动条
   - `createHomeworkItemHTML(item)` - 作业项
   - `createDeadlineHTML(deadline)` - 倒计时

**验收**:
- [ ] 大图可左右滑动
- [ ] homework 类型图片在最左侧
- [ ] deadline 倒计时正确（超时显示"已超时"）
- [ ] 已完成作业在最下面
- [ ] 返回按钮跳转登记簿

---

### 任务 4: 编辑器弹窗

**负责人**: 待定
**优先级**: P1
**文件**: `frontend/css/styles.css`, `frontend/js/views.js` (editorView), `frontend/js/renderers.js` (编辑器组件)

**工作内容**:

1. **CSS 样式** (`styles.css`):
   - 全屏弹窗样式
   - 图片缩略图列表
   - 作业编辑表单
   - 图片上传弹窗

2. **视图逻辑** (`views.js` 新增 `editorView`):
   - 打开/关闭弹窗
   - 图片列表管理
   - 作业项编辑
   - deadline 设置
   - 保存逻辑

3. **渲染函数** (`renderers.js`):
   - `createEditorImageListHTML(images)` - 图片列表
   - `createEditorItemListHTML(items)` - 作业编辑列表
   - `createUploadModalHTML()` - 上传弹窗

**验收**:
- [ ] 点击「+」打开新建弹窗
- [ ] hover/长按书本打开编辑弹窗
- [ ] 图片列表横向滚动，+ 始终可见
- [ ] 保存后返回登记簿

---

### 任务 5: HTML 结构重写

**负责人**: 待定
**优先级**: P1（依赖任务 2-4 的样式类名）
**文件**: `frontend/index.html`

**工作内容**:

1. 移除所有旧视图容器
2. 创建新视图容器:
   ```html
   <div id="todayView" class="view hidden">...</div>
   <div id="registryView" class="view hidden">...</div>
   <div id="editorView" class="modal hidden">...</div>
   <div id="uploadModal" class="modal hidden">...</div>
   ```

3. 确保容器结构与任务 2-4 的渲染函数匹配

**验收**:
- [ ] HTML 结构正确
- [ ] 与各任务的渲染函数匹配
- [ ] 页面可正常渲染

---

### 任务 6: 工具函数扩展

**负责人**: 待定
**优先级**: P2
**文件**: `frontend/js/utils.js`

**工作内容**:

1. 分页配置:
   ```javascript
   const PAGINATION = {
       getConfig() {
           const w = window.innerWidth;
           if (w >= 1024) return { cols: 4, initial: 7, pageSize: 4 };
           if (w >= 768)  return { cols: 3, initial: 5, pageSize: 3 };
           return { cols: 2, initial: 3, pageSize: 2 };
       }
   };
   ```

2. 滚动加载工具:
   ```javascript
   function createInfiniteScroll(callback, threshold = 100) { ... }
   ```

3. 倒计时格式化:
   ```javascript
   function formatDeadlineCountdown(deadlineAt) { ... }
   ```

4. 长按检测:
   ```javascript
   function createLongPress(element, callback, duration = 500) { ... }
   ```

**验收**:
- [ ] 分页配置正确
- [ ] 滚动加载正常触发
- [ ] 倒计时格式化正确

---

## 依赖关系

```
任务1 (路由状态)
   ↓
任务2 (登记簿) ←┐
任务3 (今日)   ├→ 任务5 (HTML)
任务4 (编辑器) ←┘
                 ↑
任务6 (工具函数) ─┴─ 支持
```

**建议顺序**:
1. 任务 1 先完成（基础设施）
2. 任务 2、3、4 并行开发
3. 任务 5 在 2-4 期间或之后完成
4. 任务 6 可随时进行

---

## API 使用

所有任务共享 `frontend/js/api.js`，**无需修改**。

| API | 用途 |
|-----|------|
| `api.getBatches({status, limit, offset})` | 任务2：获取批次列表 |
| `api.getBatch(batchId)` | 任务2、3：获取批次详情 |
| `api.getBatchItems(batchId, {status})` | 任务3：获取作业项 |
| `api.getBatchImages(batchId)` | 任务3、4：获取图片 |
| `api.createDraftBatch(files)` | 任务4：上传图片 |
| `api.confirmDraftBatch(batchId, data)` | 任务4：确认保存 |
| `api.updateItemStatus(itemId, status)` | 任务3：更新作业状态 |
| `api.updateBatchDeadline(batchId, deadlineAt)` | 任务4：更新截止时间 |

---

## 总体验收标准

### 今日作业页面
- [ ] 首页自动加载最近的 active 批次
- [ ] 显示批次名称和截止日期
- [ ] 大图区域可左右滑动（homework 类型在最左侧）
- [ ] deadline 倒计时正确显示（超时显示"已超时 XX 小时"）
- [ ] 未完成作业在上，已完成作业在下
- [ ] 点击「返回」跳转到作业登记簿

### 作业登记簿页面
- [ ] 显示拟物化书本网格
- [ ] 响应式：PC 4列、平板 3列、移动 2列
- [ ] 初始加载填满一屏减一格，「+」在最后一行末尾
- [ ] 滚动到底部自动加载更多
- [ ] 空状态显示「还没有作业，点击添加作业」
- [ ] 点击书本卡片跳转到今日作业
- [ ] PC 端 hover 显示编辑按钮
- [ ] 移动端长按显示编辑菜单

### 编辑器弹窗
- [ ] 点击「+」打开新建作业弹窗
- [ ] 图片列表横向滚动，+ 按钮始终可见
- [ ] 点击 + 打开图片上传弹窗
- [ ] 作业列表可编辑、删除
- [ ] 可设置 deadline
- [ ] 保存后返回作业登记簿
