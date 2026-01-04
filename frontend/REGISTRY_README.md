# 作业登记簿页面

## 文件说明

- **`frontend/js/registry.js`** - 作业登记簿逻辑模块
- **`frontend/css/registry.css`** - 作业登记簿样式（拟物化书本设计）

## 功能特性

### 1. 书本网格展示
- 拟物化书本设计（书脊 + 书页效果）
- 3D 悬停动画（hover 上浮 + 旋转）
- 状态颜色标识（草稿-灰、进行中-橙、已完成-绿）
- 进度显示（如 "3/5"）
- 截止时间智能显示（今天/明天/周几/具体日期）

### 2. 响应式布局

| 屏幕尺寸 | 列数 | 初始加载 | 滚动加载 |
|---------|------|---------|---------|
| PC ≥1024px | 4列 | 7个 | 4个 |
| 平板 768-1023px | 3列 | 5个 | 3个 |
| 移动 <768px | 2列 | 3个 | 2个 |

### 3. 交互功能

#### 点击书本
- 跳转到今日作业页面（批次详情）
- 调用 `navigateToToday(batchId)`

#### 点击 + 按钮
- 打开新建编辑器
- 调用 `navigateToEditor('new')`

#### 编辑功能
- **PC**: hover 时显示编辑按钮，点击打开编辑器
- **移动端**: 长按 800ms 显示编辑菜单

### 4. 滚动加载
- 距离底部 200px 时自动加载更多
- 防抖处理（100ms）
- 加载状态提示

### 5. 空状态
- 没有数据时显示提示图标
- 始终显示 "+" 添加按钮

## 使用方法

### 方式一：独立页面测试

访问测试页面：
```
http://localhost:8000/frontend/registry-test.html
```

### 方式二：集成到主应用

#### 1. 在 HTML 中引入 CSS 和 JS

在 `index.html` 的 `<head>` 中添加：
```html
<link rel="stylesheet" href="/frontend/css/registry.css">
```

在 `</body>` 前添加：
```html
<script src="/frontend/js/registry.js"></script>
```

#### 2. 添加 HTML 结构

```html
<!-- 在 main 区域添加 -->
<div id="registryGrid">
    <!-- 动态生成书本卡片 -->
</div>

<div id="registryEmpty" class="hidden text-center py-12 text-stone-400">
    <svg class="mx-auto h-16 w-16 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>
    <p class="text-stone-500">还没有作业本</p>
    <p class="text-stone-400 text-sm mt-1">点击 + 按钮添加第一个作业本</p>
</div>
```

#### 3. 初始化视图

```javascript
// 在路由系统中注册视图
const registryView = new View('registry', {
    selectors: {
        grid: '#registryGrid',
        empty: '#registryEmpty',
    },
    onEnter: () => {
        if (window.registryView) {
            window.registryView.init();
        }
    },
    onExit: () => {
        if (window.registryView) {
            window.registryView.destroy();
        }
    }
});

router.registerView('registry', registryView);
```

#### 4. 导航到登记簿

```javascript
router.navigate('registry');
```

## API 依赖

需要 `api.js` 提供以下接口：

- `api.getBatches({ limit, offset })` - 获取批次列表

## 全局依赖

依赖以下全局函数（从 `app.js` 导入）：

- `openUploadModal()` - 打开上传弹窗
- `restoreDraft(batchId)` - 恢复草稿
- `navigateToToday(batchId)` - 跳转到今日作业
- `navigateToEditor(batchId)` - 跳转到编辑器

## 样式定制

### CSS 变量

在 `styles.css` 中定义的变量会被自动使用：

- `--color-primary` - 主色调（琥珀橙）
- `--color-text-primary` - 主要文字颜色
- `--color-text-secondary` - 次要文字颜色
- `--color-text-muted` - 弱化文字颜色

### 状态颜色

在 `registry.css` 中定义了三种状态的颜色：

- **草稿 (draft)**: 灰色 `#9CA3AF`
- **进行中 (active)**: 橙色 `#F59E0B`
- **已完成 (completed)**: 绿色 `#34D399`

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 移动端优化

- 响应式网格（2列）
- 触摸反馈动画
- 长按编辑菜单
- 防止误触（800ms 长按）

## 性能优化

- 滚动事件防抖（100ms）
- 窗口 resize 防抖（200ms）
- 分页加载（按需加载）
- CSS 动画硬件加速

## 可访问性

- 减少动画模式支持（`prefers-reduced-motion`）
- 高对比度模式支持（`prefers-contrast`）
- 触摸设备优化（`@media (hover: none)`）
- 键盘导航支持
- ARIA 标签（编辑按钮）
