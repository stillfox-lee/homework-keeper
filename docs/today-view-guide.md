# 今日作业/详情页面使用指南

## 概述

今日作业页面 (`today.js`) 展示单个批次的详细信息，包括大图预览、截止时间倒计时和作业列表。

## 文件结构

```
frontend/
├── js/
│   └── today.js          # 今日作业页面逻辑
├── css/
│   └── today.css         # 今日作业页面样式
└── templates/
    └── today.html        # HTML 模板（可选）
```

## 功能特性

### 1. 顶部导航
- **返回按钮**：点击返回到批次列表（作业本）
- **批次名称**：显示批次名称和截止日期

### 2. 大图区域
- **横向滚动**：支持左右滑动浏览图片
- **图片分类**：
  - 作业图片（homework）显示在前，带橙色"作业"标签
  - 参考图片（reference）显示在后，带灰色"参考"标签
- **点击放大**：点击图片打开全屏查看器

### 3. Deadline 倒计时
- **未超时**：显示"距离截止还有 XX 小时 XX 分钟"
  - 绿色背景：时间充裕（>6小时）
  - 橙色背景：临近截止（<6小时）
  - 红色背景+脉冲动画：紧急（<1小时）
- **已超时**：显示"已超过截止时间 XX 小时 XX 分钟"（红色背景）
- **自动更新**：每分钟自动刷新倒计时

### 4. 作业列表
- **未完成作业**：显示在上部
  - todo 状态：灰色图标 + "开始做"按钮
  - doing 状态：橙色图标 + "完成"按钮 + 已用时
- **已完成作业**：显示在下部，带分隔线
  - done 状态：绿色图标 + "已完成"标签 + 耗时

## API 接口

### 已实现的 API 方法

```javascript
// 获取批次详情
api.getBatch(batchId)

// 获取批次作业项（新增）
api.getBatchItems(batchId, params = {})
// params: { status: 'todo' | 'doing' | 'done' } (可选)

// 获取批次图片
api.getBatchImages(batchId)

// 更新作业项状态
api.updateItemStatus(itemId, status)
```

## 使用方法

### 1. 导航到今日作业页面

```javascript
// 从批次列表点击某个批次
navigateToToday(batchId);

// 示例：在批次卡片点击事件中
document.querySelector('.batch-card').addEventListener('click', (e) => {
    const batchId = parseInt(e.currentTarget.dataset.id);
    navigateToToday(batchId);
});
```

### 2. 返回批次列表

```javascript
// 点击返回按钮
navigateToRegistry();
```

### 3. 视图生命周期

```javascript
// 初始化视图
todayView.init(batchId);

// 重新加载数据
todayView.reload();

// 销毁视图（清理定时器等）
todayView.destroy();
```

## 数据结构

### todayView.data

```javascript
{
    batch: {
        id: number,
        name: string,
        status: 'draft' | 'active' | 'completed',
        deadline_at: string | null,  // ISO 8601 格式
        created_at: string,
        updated_at: string,
    },
    items: [
        {
            id: number,
            subject: {
                id: number,
                name: string,
                color: string,
            },
            text: string,
            key_concept: string | null,
            status: 'todo' | 'doing' | 'done',
            started_at: string | null,
            finished_at: string | null,
        }
    ],
    images: [
        {
            id: number,
            file_path: string,  // 已包含 /uploads/ 前缀
            file_name: string,
            image_type: 'homework' | 'reference',
            sort_order: number,
        }
    ]
}
```

## 工具函数

### formatDeadlineDetail(deadlineAt)

格式化详细的倒计时信息。

**参数：**
- `deadlineAt`: ISO 8601 格式的截止时间字符串

**返回：**
```javascript
{
    text: string,              // 倒计时文本
    containerClass: string,    // 容器背景色类名
    iconClass: string,         // 图标颜色类名
    textClass: string,         // 文字颜色类名
}
```

**示例：**
```javascript
const info = formatDeadlineDetail('2026-01-05T12:00:00');
// {
//     text: "距离截止还有 5 小时 30 分钟",
//     containerClass: "bg-emerald-50",
//     iconClass: "text-emerald-500",
//     textClass: "text-emerald-600",
// }
```

## 样式定制

### CSS 变量

今日作业页面使用以下 CSS 类：

- `.today-header`: 顶部导航容器
- `.today-back-btn`: 返回按钮
- `.today-image-item`: 图片项
- `.today-item`: 作业卡片
- `.today-action-btn`: 操作按钮

### 响应式断点

- **移动端**（默认）：< 640px
- **平板**：≥ 640px
- **桌面**：≥ 1024px

## 事件处理

### 作业项状态更新

```javascript
// 点击"开始做"按钮
todayView.handleStatusUpdate(itemId, 'doing');

// 点击"完成"按钮
todayView.handleStatusUpdate(itemId, 'done');
```

### 完成批次

当所有作业都完成时，会显示完成祝贺弹窗（复用 `completionModal`）。

## 注意事项

1. **图片排序**：homework 类型图片始终在 reference 图片之前
2. **定时器清理**：离开视图时需要调用 `todayView.destroy()` 清理倒计时定时器
3. **错误处理**：API 调用失败时会显示 Toast 提示
4. **状态同步**：更新作业状态后会重新加载整个批次数据

## 扩展功能

### 添加筛选功能

```javascript
// 在 today.js 中添加
filterItems(status) {
    if (status === 'all') {
        return this.data.items;
    }
    return this.data.items.filter(item => item.status === status);
}
```

### 添加搜索功能

```javascript
// 在 today.js 中添加
searchItems(keyword) {
    if (!keyword) return this.data.items;
    return this.data.items.filter(item =>
        item.text.includes(keyword) ||
        item.subject.name.includes(keyword)
    );
}
```

## 测试

### 手动测试步骤

1. 启动后端服务器
2. 访问 http://localhost:8000
3. 创建一个新批次（或使用现有批次）
4. 在批次列表中点击某个批次
5. 验证以下功能：
   - 大图区域显示正确
   - 倒计时准确
   - 作业列表完整
   - 状态更新正常
   - 返回按钮工作正常

## 调试

### 控制台日志

```javascript
// 在 today.js 中添加调试日志
console.log('[TodayView] Batch ID:', this.batchId);
console.log('[TodayView] Data:', this.data);
```

### 常见问题

1. **图片不显示**：检查 `file_path` 是否包含 `/uploads/` 前缀
2. **倒计时不更新**：确认定时器已正确启动
3. **状态更新失败**：检查 API 响应和错误处理

## 未来改进

- [ ] 添加下拉刷新功能
- [ ] 支持作业项拖拽排序
- [ ] 添加作业备注功能
- [ ] 支持批量操作（一键全部开始/完成）
- [ ] 添加学习统计数据（每日完成率、平均用时等）
