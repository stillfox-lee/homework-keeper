# 作业登记簿集成指南

## 快速集成步骤

### 1. 更新 index.html

在 `<head>` 中添加 CSS：
```html
<link rel="stylesheet" href="/frontend/css/registry.css">
```

在 `</body>` 前添加 JS：
```html
<script src="/frontend/js/registry.js"></script>
```

### 2. 更新导航按钮

在 `index.html` 中，找到作业本按钮：
```html
<button id="batchesBtn" class="px-3 py-1.5 text-sm bg-stone-100 text-stone-600 rounded-xl hover:bg-stone-200 transition-all duration-250">
    作业本
</button>
```

修改为使用登记簿视图：
```javascript
// 在 app.js 的 bindEvents 中
document.getElementById('batchesBtn').addEventListener('click', () => {
    // 使用新的登记簿视图
    if (window.router) {
        router.navigate('registry');
    } else {
        // Fallback
        window.location.href = '/frontend/registry-test.html';
    }
});
```

### 3. 注册视图到路由系统

在 `views.js` 中添加：

```javascript
/**
 * 作业登记簿视图
 */
const registryView = new View('registry', {
    selectors: {
        navBtn: '#backBtn',
        container: '#registryView',
        grid: '#registryGrid',
        empty: '#registryEmpty',
    },
    onEnter: () => {
        // 初始化登记簿
        if (window.registryView) {
            window.registryView.init();
        }
    },
    onExit: () => {
        // 清理
        if (window.registryView) {
            window.registryView.destroy();
        }
    }
});

// 注册到路由
router.registerView('registry', registryView);
```

### 4. 添加 HTML 容器

在 `index.html` 的 `<main>` 区域添加：

```html
<!-- 作业登记簿视图 (默认隐藏) -->
<div id="registryView" class="hidden">
    <!-- 书本网格 -->
    <div id="registryGrid">
        <!-- 动态生成 -->
    </div>

    <!-- 空状态 -->
    <div id="registryEmpty" class="hidden text-center py-12 text-stone-400">
        <svg class="mx-auto h-16 w-16 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <p class="text-stone-500">还没有作业本</p>
        <p class="text-stone-400 text-sm mt-1">点击 + 按钮添加第一个作业本</p>
    </div>
</div>
```

### 5. 更新 CSS Grid 容器宽度

在 `registry.css` 中，需要为网格容器添加最大宽度约束：

```css
/* 在 #registryGrid 规则中添加 */
#registryGrid {
    display: grid;
    gap: 1.5rem;
    padding: 1rem 0;
    max-width: 1200px;  /* 添加这行 */
    margin: 0 auto;     /* 添加这行 */
    /* 响应式列数由 JS 动态设置 */
    transition: all 0.3s ease;
}
```

### 6. 测试

启动开发服务器：
```bash
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

访问：
- 主应用集成版：`http://localhost:8000/`
- 独立测试页：`http://localhost:8000/frontend/registry-test.html`

## 依赖检查清单

- [x] `api.js` - 提供 `getBatches()` 接口
- [x] `app.js` - 提供 `openUploadModal()` 和 `restoreDraft()` 函数
- [x] `views.js` - 路由系统
- [x] `utils.js` - 工具函数（如需要）

## 功能验证

### 基础功能
- [ ] 页面加载显示书本网格
- [ ] 空状态显示提示和 + 按钮
- [ ] 点击书本跳转到今日作业
- [ ] 点击 + 打开新建编辑器

### 响应式
- [ ] PC (≥1024px): 4列网格
- [ ] 平板 (768-1023px): 3列网格
- [ ] 移动 (<768px): 2列网格

### 交互
- [ ] hover 时书上浮 3D 效果
- [ ] PC hover 显示编辑按钮
- [ ] 移动端长按显示编辑菜单
- [ ] 滚动到底部自动加载更多

### 样式
- [ ] 书脊渐变效果
- [ ] 书页条纹效果
- [ ] 进度条颜色根据状态变化
- [ ] 截止时间智能显示（今天/明天/周几）

## 常见问题

### Q: 书本不显示？
A: 检查 `api.getBatches()` 是否返回数据，检查浏览器控制台是否有错误。

### Q: 点击书本没反应？
A: 确认 `navigateToToday()` 函数已定义，检查批次 ID 是否正确传递。

### Q: 编辑按钮不显示？
A: PC 端需要 hover 才显示，移动端使用长按（800ms）。

### Q: 响应式列数不正确？
A: 检查 `getResponsiveConfig()` 函数和 `updateGridColumns()` 是否被正确调用。

### Q: 滚动加载不触发？
A: 检查 `hasMore` 状态和滚动容器高度，确保页面内容超过一屏。

## 下一步优化

1. **搜索功能**: 添加搜索框过滤作业本
2. **排序选项**: 按时间/状态/进度排序
3. **批量操作**: 批量删除/归档作业本
4. **书签收藏**: 标记常用作业本
5. **分组视图**: 按日期/科目分组展示
6. **主题切换**: 支持不同颜色主题
