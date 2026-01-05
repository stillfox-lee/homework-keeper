/**
 * 作业登记簿页面逻辑
 * MPA 版本 - 书本网格展示
 */

// 全局状态（与 app.js、editor.js 保持兼容）
// 注意：不声明 const state，避免与 editor.js 重复声明
// 直接使用 window.state 或通过 var 创建别名
if (!window.state) {
    window.state = {
        subjects: [],
    };
}
var state = window.state;  // 使用 var 允许重复声明

// 状态数据
const registryState = {
    batches: [],
    page: 0,
    hasMore: true,
    loading: false,
    itemsPerPage: 4,
};

// 响应式配置
function getResponsiveConfig() {
    const width = window.innerWidth;
    if (width >= 1024) return { cols: 4, initial: 7, scrollLoad: 4 };
    if (width >= 768) return { cols: 3, initial: 5, scrollLoad: 3 };
    return { cols: 2, initial: 3, scrollLoad: 2 };
}

/**
 * 加载作业登记簿页面
 */
async function loadRegistryPage() {
    // 重置状态
    registryState.batches = [];
    registryState.page = 0;
    registryState.hasMore = true;
    registryState.loading = false;

    // 加载数据
    await loadInitialData();

    // 绑定事件
    bindEvents();
}

/**
 * 初始加载数据
 */
async function loadInitialData() {
    if (registryState.loading) return;

    registryState.loading = true;

    try {
        // 先加载科目列表
        if (!state.subjects || state.subjects.length === 0) {
            state.subjects = await api.getSubjects();
        }

        // 再加载批次数据
        const config = getResponsiveConfig();
        const batches = await api.getBatches({
            limit: config.initial,
            offset: 0,
        });

        registryState.batches = batches;
        registryState.page = 1;
        registryState.hasMore = batches.length >= config.initial;

        render();
    } catch (error) {
        console.error('[RegistryPage] 加载失败:', error);
    } finally {
        registryState.loading = false;
    }
}

/**
 * 加载更多
 */
async function loadMore() {
    if (registryState.loading || !registryState.hasMore) return;

    registryState.loading = true;

    try {
        const config = getResponsiveConfig();
        const offset = registryState.batches.length;

        const batches = await api.getBatches({
            limit: config.scrollLoad,
            offset: offset,
        });

        registryState.batches.push(...batches);
        registryState.page += 1;
        registryState.hasMore = batches.length >= config.scrollLoad;

        render();
    } catch (error) {
        console.error('[RegistryPage] 加载更多失败:', error);
    } finally {
        registryState.loading = false;
    }
}

/**
 * 渲染页面
 */
function render() {
    const grid = document.getElementById('batchesGrid');
    const emptyState = document.getElementById('emptyState');

    if (!grid) return;

    const config = getResponsiveConfig();
    grid.style.gridTemplateColumns = `repeat(${config.cols}, 1fr)`;

    // 空状态
    if (registryState.batches.length === 0) {
        grid.innerHTML = createAddCardHTML();
        emptyState?.classList.remove('hidden');
        return;
    }

    emptyState?.classList.add('hidden');

    // 渲染书本卡片 + 添加按钮
    grid.innerHTML = registryState.batches.map(batch => createBookCardHTML(batch)).join('') +
                      createAddCardHTML();
}

/**
 * 创建书本卡片 HTML
 */
function createBookCardHTML(batch) {
    const progress = calculateProgress(batch);
    const statusColor = getStatusColor(batch.status);
    const statusBadge = getStatusBadge(batch.status);
    const deadlineText = formatDeadline(batch.deadline_at);

    return `
        <div class="book-card book-card-${batch.status}" data-batch-id="${batch.id}">
            <a href="/today.html?id=${batch.id}" class="book-link">
                <div class="book-spine" style="background: linear-gradient(90deg, ${statusColor.dark} 0%, ${statusColor.light} 100%);"></div>
                <div class="book-pages"></div>
                <div class="book-content">
                    <div class="book-title">${escapeHtml(batch.name)}</div>
                    ${statusBadge}
                    <div class="book-progress">
                        <span class="progress-text">${progress.completed}/${progress.total}</span>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: ${progress.percent}%; background: ${statusColor.main};"></div>
                        </div>
                    </div>
                    <div class="book-deadline">
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>${deadlineText}</span>
                    </div>
                </div>
            </a>
            <button class="book-edit-btn" data-batch-id="${batch.id}" aria-label="编辑作业">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
                <span>编辑</span>
            </button>
        </div>
    `;
}

/**
 * 创建添加卡片 HTML
 */
function createAddCardHTML() {
    return `
        <div id="addCard" class="book-card book-card-add">
            <div class="add-content">
                <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                <span>添加作业</span>
            </div>
        </div>
    `;
}

/**
 * 计算进度
 */
function calculateProgress(batch) {
    const items = batch.items || [];
    const total = items.length;
    const completed = items.filter(item => item.status === 'done').length;
    const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
    return { total, completed, percent };
}

/**
 * 获取状态徽章
 */
function getStatusBadge(status) {
    const badges = {
        draft: '<span class="book-badge book-badge-draft">草稿</span>',
        active: '<span class="book-badge book-badge-active">进行中</span>',
        completed: '<span class="book-badge book-badge-completed">已完成</span>',
    };
    return badges[status] || badges.active;
}

/**
 * 获取状态颜色
 */
function getStatusColor(status) {
    const colors = {
        draft: { main: '#9CA3AF', light: '#D1D5DB', dark: '#6B7280' },
        active: { main: '#F59E0B', light: '#FDE68A', dark: '#D97706' },
        completed: { main: '#34D399', light: '#6EE7B7', dark: '#059669' },
    };
    return colors[status] || colors.active;
}

/**
 * 格式化截止时间
 * 注意：deadlineAt 是 UTC 时间，需要基于 UTC 日期进行比较
 */
function formatDeadline(deadlineAt) {
    if (!deadlineAt) return '未设置';

    const deadline = new Date(deadlineAt);

    // 使用 UTC 日期进行比较（避免时区转换导致的日期跳变）
    // 例如：UTC 2026-01-06 23:59:00 存储的是 1月6日，不应因转本地时区变成 1月7日
    const today = new Date();
    const todayUtc = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
    const deadlineUtc = Date.UTC(deadline.getUTCFullYear(), deadline.getUTCMonth(), deadline.getUTCDate());

    const diffTime = deadlineUtc - todayUtc;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return '今天';
    if (diffDays === 1) return '明天';
    if (diffDays === -1) return '昨天';
    if (diffDays < -1) return `${Math.abs(diffDays)}天前`;

    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const weekday = weekdays[deadline.getUTCDay()];

    if (diffDays <= 7) return weekday;
    return `${deadline.getUTCMonth() + 1}/${deadline.getUTCDate()}`;
}

/**
 * 转义 HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 绑定事件
 */
function bindEvents() {
    const grid = document.getElementById('batchesGrid');
    if (!grid) return;

    // 点击添加卡片 - 打开编辑器（新建模式）
    const addCardHandler = () => {
        handleNewBatch();
    };
    document.getElementById('addCard')?.addEventListener('click', addCardHandler);

    // 编辑按钮点击（事件委托）
    grid.addEventListener('click', (e) => {
        const editBtn = e.target.closest('.book-edit-btn');
        if (editBtn) {
            e.preventDefault();
            e.stopPropagation();
            const batchId = editBtn.dataset.batchId;
            handleEditBatch(batchId);
        }
    });

    // 移动端长按支持
    setupLongPress(grid);

    // 滚动加载
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        if (scrollTimeout) clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(checkScrollAndLoad, 100);
    });

    // 窗口大小变化
    let resizeTimeout;
    window.addEventListener('resize', () => {
        if (resizeTimeout) clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            const config = getResponsiveConfig();
            if (grid) {
                grid.style.gridTemplateColumns = `repeat(${config.cols}, 1fr)`;
            }
        }, 200);
    });
}

/**
 * 处理编辑作业
 */
function handleEditBatch(batchId) {
    // 跳转到编辑器页面（编辑模式）
    window.location.href = `/editor.html?mode=edit&id=${batchId}`;
}

/**
 * 处理新建作业
 */
function handleNewBatch() {
    // 跳转到编辑器页面（新建模式）
    window.location.href = '/editor.html?mode=new';
}

/**
 * 设置移动端长按支持
 */
function setupLongPress(grid) {
    const LONG_PRESS_DURATION = 500; // 长按时间阈值（毫秒）
    const longPressTimers = new Map();

    // 使用事件委托处理所有书本卡片的长按
    grid.addEventListener('touchstart', (e) => {
        const card = e.target.closest('.book-card');
        if (!card || card.classList.contains('book-card-add')) return;

        longPressTimers.set(card, setTimeout(() => {
            card.classList.add('long-press');
            // 触觉反馈（如果设备支持）
            if (navigator.vibrate) {
                navigator.vibrate(50);
            }
        }, LONG_PRESS_DURATION));
    });

    grid.addEventListener('touchend', (e) => {
        const card = e.target.closest('.book-card');
        if (!card) return;

        const timer = longPressTimers.get(card);
        if (timer) {
            clearTimeout(timer);
            longPressTimers.delete(card);
        }

        // 如果是长按状态，移除类（延迟一下让用户看到效果）
        if (card.classList.contains('long-press')) {
            setTimeout(() => {
                card.classList.remove('long-press');
            }, 2000);
        }
    });

    grid.addEventListener('touchmove', (e) => {
        const card = e.target.closest('.book-card');
        if (!card) return;

        // 手指移动时取消长按
        const timer = longPressTimers.get(card);
        if (timer) {
            clearTimeout(timer);
            longPressTimers.delete(card);
        }
    });

    grid.addEventListener('touchcancel', (e) => {
        const card = e.target.closest('.book-card');
        if (!card) return;

        const timer = longPressTimers.get(card);
        if (timer) {
            clearTimeout(timer);
            longPressTimers.delete(card);
        }
    });
}

/**
 * 检查滚动并加载更多
 */
function checkScrollAndLoad() {
    if (registryState.loading || !registryState.hasMore) return;

    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;

    if (scrollTop + windowHeight >= documentHeight - 200) {
        loadMore();
    }
}
