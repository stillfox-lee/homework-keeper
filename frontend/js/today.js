/**
 * 今日作业页面逻辑
 * MPA 版本 - 直接从 URL 参数获取 batchId
 */

// 状态数据
const todayState = {
    batch: null,
    items: [],
    images: [],
    currentImageIndex: 0,
    deadlineTimer: null,
};

/**
 * 加载今日作业页面
 * @param {number} batchId - 批次 ID（从 URL 参数获取）
 */
async function loadTodayPage(batchId) {
    try {
        // 并行加载批次详情、作业项、图片
        const [batch, items, images] = await Promise.all([
            api.getBatch(batchId),
            api.getBatchItems(batchId),
            api.getBatchImages(batchId),
        ]);

        todayState.batch = batch;
        todayState.items = items;
        todayState.images = images;

        render();
    } catch (error) {
        console.error('[TodayPage] 加载失败:', error);
        showToast('加载失败，请重试');
    }
}

/**
 * 渲染页面
 */
function render() {
    // 渲染批次名称
    const batchNameEl = document.getElementById('batchName');
    if (batchNameEl) {
        batchNameEl.textContent = todayState.batch?.name || '作业详情';
    }

    // 渲染图片
    renderImages();

    // 渲染倒计时
    renderDeadline();

    // 渲染作业列表
    renderItems();
}

/**
 * 渲染图片区域
 */
function renderImages() {
    const container = document.getElementById('imagesContainer');
    const list = document.getElementById('imagesList');

    if (!todayState.images || todayState.images.length === 0) {
        container?.classList.add('hidden');
        return;
    }

    container?.classList.remove('hidden');

    // 按 image_type 分组，homework 在前
    const homeworkImages = todayState.images
        .filter(img => img.image_type === 'homework')
        .sort((a, b) => a.sort_order - b.sort_order);
    const referenceImages = todayState.images
        .filter(img => img.image_type === 'reference')
        .sort((a, b) => a.sort_order - b.sort_order);

    const allImages = [...homeworkImages, ...referenceImages];

    list.innerHTML = allImages.map((img, index) => `
        <div class="image-item" onclick="openImageViewer(${index})">
            <img src="${img.file_path}" alt="${img.file_name}" class="image-thumb">
            <span class="image-badge ${img.image_type === 'homework' ? 'image-badge-homework' : 'image-badge-reference'}">
                ${img.image_type === 'homework' ? '作业' : '参考'}
            </span>
        </div>
    `).join('');
}

/**
 * 渲染倒计时
 */
function renderDeadline() {
    const container = document.getElementById('deadlineContainer');
    const deadlineAt = todayState.batch?.deadline_at;

    if (!deadlineAt) {
        container?.classList.add('hidden');
        return;
    }

    container?.classList.remove('hidden');

    const deadline = new Date(deadlineAt);
    const now = new Date();
    const diffMs = deadline - now;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    let text, className;

    if (diffMs < 0) {
        // 已逾期
        const overdueHours = Math.abs(diffHours);
        const overdueMinutes = Math.abs(diffMinutes);
        text = overdueHours > 0
            ? `已超时 ${overdueHours} 小时 ${overdueMinutes} 分钟`
            : `已超时 ${overdueMinutes} 分钟`;
        className = 'deadline-overdue';
    } else if (diffHours < 6) {
        // 临近截止
        text = diffHours > 0
            ? `距离截止还有 ${diffHours} 小时 ${diffMinutes} 分钟`
            : `距离截止还有 ${diffMinutes} 分钟`;
        className = diffHours > 0 ? 'deadline-soon' : 'deadline-urgent';
    } else {
        // 正常
        text = `距离截止还有 ${diffHours} 小时 ${diffMinutes} 分钟`;
        className = 'deadline-normal';
    }

    container.innerHTML = `
        <svg class="deadline-icon ${className}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="${className}">${text}</span>
    `;

    // 每分钟更新
    if (todayState.deadlineTimer) {
        clearInterval(todayState.deadlineTimer);
    }
    todayState.deadlineTimer = setInterval(renderDeadline, 60000);
}

/**
 * 渲染作业列表
 */
function renderItems() {
    const todoContainer = document.getElementById('todoItems');
    const doneContainer = document.getElementById('doneItems');
    const doneSection = document.getElementById('doneSection');

    // 分组
    const todoItems = todayState.items.filter(item => item.status !== 'done');
    const doneItems = todayState.items.filter(item => item.status === 'done');

    // 渲染未完成
    if (todoItems.length === 0) {
        todoContainer.innerHTML = '<p class="empty-hint">太棒了！所有作业都完成了 🎉</p>';
    } else {
        todoContainer.innerHTML = todoItems.map(item => createItemHTML(item)).join('');
    }

    // 渲染已完成
    if (doneItems.length === 0) {
        doneSection?.classList.add('hidden');
    } else {
        doneSection?.classList.remove('hidden');
        doneContainer.innerHTML = doneItems.map(item => createItemHTML(item)).join('');
    }

    // 绑定事件
    bindItemEvents();
}

/**
 * 创建作业项 HTML
 */
function createItemHTML(item) {
    const isDone = item.status === 'done';
    const isDoing = item.status === 'doing';

    const statusConfig = {
        'todo': { bg: 'bg-stone-100', icon: '📝' },
        'doing': { bg: 'bg-amber-100', icon: '🚀' },
        'done': { bg: 'bg-emerald-100', icon: '✅' },
    };
    const config = statusConfig[item.status] || statusConfig['todo'];

    // 操作按钮
    let actionButton = '';
    if (item.status === 'todo') {
        actionButton = `<button class="item-btn item-btn-primary" data-id="${item.id}" data-status="doing">开始做</button>`;
    } else if (item.status === 'doing') {
        actionButton = `<button class="item-btn item-btn-success" data-id="${item.id}" data-status="done">完成</button>`;
    } else {
        actionButton = `<span class="item-done">已完成</span>`;
    }

    return `
        <div class="item-card" data-id="${item.id}">
            <div class="item-icon ${config.bg}">${config.icon}</div>
            <div class="item-content">
                <div class="item-header">
                    <span class="item-subject" style="background-color: ${item.subject.color}20; color: ${item.subject.color}">
                        ${item.subject.name}
                    </span>
                    ${item.key_concept ? `<span class="item-concept">${item.key_concept}</span>` : ''}
                </div>
                <p class="item-text ${isDone ? 'item-text-done' : ''}">${item.text}</p>
                ${isDoing && item.started_at ? `<p class="item-time">已用时 ${formatDuration(item.started_at)}</p>` : ''}
                ${isDone && item.started_at && item.finished_at ? `<p class="item-time">耗时 ${formatDuration(item.started_at, item.finished_at)}</p>` : ''}
            </div>
            <div class="item-action">${actionButton}</div>
        </div>
    `;
}

/**
 * 绑定作业项事件
 */
function bindItemEvents() {
    document.querySelectorAll('.item-btn').forEach(btn => {
        btn.onclick = async (e) => {
            const itemId = parseInt(e.target.dataset.id);
            const status = e.target.dataset.status;
            await handleStatusUpdate(itemId, status);
        };
    });
}

/**
 * 处理状态更新
 */
async function handleStatusUpdate(itemId, status) {
    try {
        const result = await api.updateItemStatus(itemId, status);

        if (result.batch_ready_to_complete) {
            showCompletionModal(todayState.batch.id);
            return;
        }

        // 重新加载数据
        const params = new URLSearchParams(window.location.search);
        await loadTodayPage(params.get('id'));
        showToast('已更新');
    } catch (error) {
        console.error('[TodayPage] 更新失败:', error);
        showToast('操作出错了，再试试');
    }
}

/**
 * 图片查看器
 */
function openImageViewer(index) {
    const viewer = document.getElementById('imageViewer');
    const img = document.getElementById('imageViewerImg');

    // 按 image_type 分组
    const homeworkImages = todayState.images
        .filter(i => i.image_type === 'homework')
        .sort((a, b) => a.sort_order - b.sort_order);
    const referenceImages = todayState.images
        .filter(i => i.image_type === 'reference')
        .sort((a, b) => a.sort_order - b.sort_order);

    todayState.allImages = [...homeworkImages, ...referenceImages];
    todayState.currentImageIndex = index;

    img.src = todayState.allImages[index].file_path;
    viewer.classList.remove('hidden');
}

function closeImageViewer() {
    document.getElementById('imageViewer').classList.add('hidden');
}

function prevImage() {
    todayState.currentImageIndex = (todayState.currentImageIndex - 1 + todayState.allImages.length) % todayState.allImages.length;
    document.getElementById('imageViewerImg').src = todayState.allImages[todayState.currentImageIndex].file_path;
}

function nextImage() {
    todayState.currentImageIndex = (todayState.currentImageIndex + 1) % todayState.allImages.length;
    document.getElementById('imageViewerImg').src = todayState.allImages[todayState.currentImageIndex].file_path;
}

/**
 * 完成确认弹窗
 */
function showCompletionModal(batchId) {
    const modal = document.getElementById('completionModal');
    modal.classList.remove('hidden');

    document.getElementById('completionCancel').onclick = () => {
        modal.classList.add('hidden');
        // 重新加载数据
        const params = new URLSearchParams(window.location.search);
        loadTodayPage(params.get('id'));
    };

    document.getElementById('completionConfirm').onclick = async () => {
        try {
            await api.completeBatch(batchId);
            modal.classList.add('hidden');
            showToast('作业本已完成');
            // 跳转到登记簿
            window.location.href = '/registry.html';
        } catch (error) {
            console.error('[TodayPage] 完成批次失败:', error);
            showToast('操作出错了，再试试');
        }
    };
}

// 初始化事件监听
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('imageViewerClose').onclick = closeImageViewer;
    document.getElementById('imageViewerPrev').onclick = prevImage;
    document.getElementById('imageViewerNext').onclick = nextImage;

    // 键盘导航
    document.addEventListener('keydown', (e) => {
        const viewer = document.getElementById('imageViewer');
        if (viewer.classList.contains('hidden')) return;

        if (e.key === 'Escape') closeImageViewer();
        if (e.key === 'ArrowLeft') prevImage();
        if (e.key === 'ArrowRight') nextImage();
    });
});
