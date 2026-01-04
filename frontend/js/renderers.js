/**
 * 渲染函数模块
 * 负责生成 HTML 和更新 DOM
 */

// ==================== 筛选按钮 ====================

/**
 * 更新筛选按钮状态
 * @param {string} currentFilter - 当前筛选状态
 */
function updateFilterButtons(currentFilter) {
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        const isActive = btn.dataset.status === currentFilter;
        if (isActive) {
            btn.classList.add('active', 'bg-amber-500', 'text-white');
            btn.classList.remove('text-stone-600', 'hover:bg-amber-100');
        } else {
            btn.classList.remove('active', 'bg-amber-500', 'text-white');
            btn.classList.add('text-stone-600', 'hover:bg-amber-100');
        }
    });
}

// ==================== 作业列表渲染 ====================

/**
 * 创建作业项 HTML
 * @param {object} item - 作业项对象
 * @returns {string} HTML 字符串
 */
function createHomeworkItemHTML(item) {
    // 温暖主题配色
    const statusConfig = {
        'todo': { border: 'border-gray-200', bg: 'bg-gray-50', text: 'text-gray-400' },
        'doing': { border: 'border-amber-400', bg: 'bg-amber-50', text: 'text-amber-500' },
        'done': { border: 'border-emerald-400', bg: 'bg-emerald-50', text: 'text-emerald-500' },
    };
    const config = statusConfig[item.status] || statusConfig['todo'];

    // 操作按钮
    const actionButtons = {
        'todo': `<button class="status-btn p-2 text-xl hover:bg-amber-50 rounded-lg transition-colors" data-id="${item.id}" data-status="doing" title="开始">🚀</button>`,
        'doing': `<button class="status-btn p-2 text-xl hover:bg-emerald-50 rounded-lg transition-colors" data-id="${item.id}" data-status="done" title="完成">✔️</button>`,
        'done': `<span class="p-2 text-xl" title="已完成">🎉</span>`,
    };

    // 时间显示
    let duration = '';
    if (item.status === 'doing' && item.started_at) {
        duration = `<div class="mt-2 text-xs text-gray-400">已用时 ${formatDuration(item.started_at)}</div>`;
    } else if (item.status === 'done' && item.started_at && item.finished_at) {
        duration = `<div class="mt-2 text-xs text-gray-400">耗时 ${formatDuration(item.started_at, item.finished_at)} · 完成于 ${formatDateTime(item.finished_at)}</div>`;
    }

    return `
        <div class="homework-item bg-white rounded-xl shadow-sm p-4 border-l-4 ${config.border}" data-id="${item.id}">
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="w-2 h-2 rounded-full ${config.bg}"></span>
                        <span class="px-2 py-0.5 text-xs rounded-full font-medium" style="background-color: ${item.subject.color}20; color: ${item.subject.color}">
                            ${item.subject.name}
                        </span>
                        ${item.key_concept ? `<span class="text-xs px-2 py-0.5 bg-stone-100 text-stone-500 rounded-full">${item.key_concept}</span>` : ''}
                    </div>
                    <p class="text-stone-700">${item.text}</p>
                    ${duration}
                </div>
                <div class="flex gap-2 ml-4">
                    ${actionButtons[item.status]}
                    ${item.status !== 'done' ? `
                        <button class="delete-item-btn p-2 text-xl text-stone-400 hover:text-red-500 transition-colors" data-id="${item.id}" title="删除">🚮</button>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

// ==================== 批次列表渲染 ====================

/**
 * 创建批次卡片 HTML
 * @param {object} batch - 批次对象
 * @returns {string} HTML 字符串
 */
function createBatchCardHTML(batch) {
    const statusConfig = {
        'draft': { label: '草稿', bg: 'bg-stone-100', text: 'text-stone-500' },
        'active': { label: '正在做', bg: 'bg-amber-100', text: 'text-amber-600' },
        'completed': { label: '已完成', bg: 'bg-emerald-100', text: 'text-emerald-600' },
    };
    const config = statusConfig[batch.status] || statusConfig['draft'];

    // 计算完成进度
    const items = batch.items || [];
    const totalItems = items.length;
    const completedItems = items.filter(i => i.status === 'done').length;
    const progressPercent = totalItems > 0 ? (completedItems / totalItems) * 100 : 0;

    // 格式化日期
    const dateStr = formatDate(batch.created_at);

    // 草稿状态添加删除按钮
    const deleteHTML = batch.status === 'draft' ? `
        <button class="delete-draft-btn px-2 py-1 text-xs text-red-500 hover:bg-red-50 rounded-lg transition-colors" data-id="${batch.id}">
            删除
        </button>
    ` : '';

    // 格式化截止时间
    let deadlineHTML = '';
    if (batch.deadline_at && batch.status === 'active') {
        const deadlineInfo = formatDeadline(batch.deadline_at);
        if (deadlineInfo) {
            deadlineHTML = `
                <div class="flex items-center gap-1 text-xs ${deadlineInfo.className}">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>${deadlineInfo.text}</span>
                </div>
            `;
        }
    }

    return `
        <div class="batch-card bg-white rounded-xl shadow-sm p-4 border border-stone-100 hover:shadow-md transition-all cursor-pointer" data-id="${batch.id}">
            <div class="flex items-center justify-between mb-3">
                <span class="px-2 py-1 text-xs rounded-lg ${config.bg} ${config.text}">${config.label}</span>
                <div class="flex items-center gap-2">
                    ${deleteHTML}
                    <span class="text-xs text-stone-400">${dateStr}</span>
                </div>
            </div>
            <h3 class="text-stone-800 font-medium mb-3">${batch.name || '未命名批次'}</h3>

            ${totalItems > 0 ? `
                <div class="mb-3">
                    <div class="flex justify-between text-xs text-stone-500 mb-1">
                        <span>完成情况</span>
                        <span>${completedItems}/${totalItems}</span>
                    </div>
                    <div class="w-full bg-stone-100 rounded-full h-2 overflow-hidden">
                        <div class="h-full rounded-full transition-all duration-300 ${progressPercent === 100 ? 'bg-emerald-500' : 'bg-amber-500'}"
                             style="width: ${progressPercent}%"></div>
                    </div>
                </div>
            ` : '<p class="text-xs text-stone-400 mb-3">还没有作业</p>'}

            ${deadlineHTML ? `<div class="mt-2">${deadlineHTML}</div>` : ''}
        </div>
    `;
}

// ==================== 确认列表渲染 ====================

/**
 * 创建确认项 HTML
 * @param {object} item - 作业项对象
 * @param {number} index - 索引
 * @param {array} subjects - 科目列表
 * @returns {string} HTML 字符串
 */
function createConfirmItemHTML(item, index, subjects) {
    return `
        <div class="confirm-item flex gap-2 p-2 bg-stone-50 rounded-xl border border-stone-100" data-index="${index}">
            <select class="item-subject flex-0 border border-stone-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none" style="min-width: 80px">
                ${subjects.map(s => `<option value="${s.id}" ${item.subject_id === s.id ? 'selected' : ''}>${s.name}</option>`).join('')}
            </select>
            <input type="text" class="item-text flex-1 border border-stone-200 rounded-lg px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none" value="${item.text}" placeholder="要做什么作业">
            <input type="text" class="item-concept w-24 border border-stone-200 rounded-lg px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none" value="${item.key_concept || ''}" placeholder="知识点">
            <button class="remove-item px-2 text-stone-400 hover:text-red-500 transition-colors">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    `;
}

/**
 * 渲染确认项列表
 * @param {array} items - 作业项数组
 * @param {array} subjects - 科目列表
 */
function renderConfirmItems(items, subjects) {
    const itemCount = document.getElementById('itemCount');
    const itemList = document.getElementById('itemList');

    if (itemCount) itemCount.textContent = `(${items.length})`;
    if (itemList) {
        itemList.innerHTML = items.map((item, index) => createConfirmItemHTML(item, index, subjects)).join('');
    }
}

// ==================== 图片预览渲染 ====================

/**
 * 渲染图片预览
 * @param {array} images - 图片数组
 */
function renderPreviewImages(images) {
    const previewImages = document.getElementById('previewImages');
    if (!previewImages) return;

    previewImages.innerHTML = images.map((img, index) => `
        <div class="preview-image flex-shrink-0 relative group cursor-pointer" data-index="${index}">
            <img src="${img.url}" alt="${img.name}" class="w-20 h-20 object-cover rounded-xl shadow-sm">
            <div class="image-type-badge absolute top-1 left-1 px-1.5 py-0.5 text-xs rounded-lg ${img.type === 'homework' ? 'bg-amber-500 text-white' : 'bg-stone-400 text-white'}">
                ${img.type === 'homework' ? '作业' : '参考'}
            </div>
            <button class="toggle-type absolute top-1 right-1 p-1 bg-white rounded-lg shadow-sm opacity-0 group-hover:opacity-100 transition-opacity" title="切换图片类型">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
            </button>
        </div>
    `).join('');
}

// ==================== 图片弹窗渲染 ====================

/**
 * 渲染图片弹窗内容
 * @param {object} batch - 批次对象
 */
function renderImagesModal(batch) {
    const imagesList = document.getElementById('imagesList');
    if (!imagesList || !batch) return;

    const images = batch.images || [];
    const homeworkImages = images.filter(img => img.image_type === 'homework');
    const referenceImages = images.filter(img => img.image_type === 'reference');

    imagesList.innerHTML = '';

    if (homeworkImages.length > 0) {
        imagesList.innerHTML += `
            <div class="col-span-2">
                <p class="text-sm font-medium text-stone-700 mb-2">作业照片</p>
                <div class="grid grid-cols-2 gap-4">
                    ${homeworkImages.map(img => `
                        <div class="relative">
                            <img src="/uploads/${img.file_path}" alt="${img.file_name}" class="w-full rounded-xl cursor-pointer hover:opacity-90 transition-opacity" onclick="window.open(this.src, '_blank')">
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    if (referenceImages.length > 0) {
        imagesList.innerHTML += `
            <div class="col-span-2">
                <p class="text-sm font-medium text-stone-700 mb-2">参考书</p>
                <div class="grid grid-cols-2 gap-4">
                    ${referenceImages.map(img => `
                        <div class="relative">
                            <img src="/uploads/${img.file_path}" alt="${img.file_name}" class="w-full rounded-xl cursor-pointer hover:opacity-90 transition-opacity" onclick="window.open(this.src, '_blank')">
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    if (homeworkImages.length === 0 && referenceImages.length === 0) {
        imagesList.innerHTML = '<p class="col-span-2 text-center text-stone-400 py-8">还没有照片</p>';
    }
}

// ==================== 批次头部渲染 ====================

/**
 * 渲染批次头部信息
 * @param {object} batch - 批次对象
 */
function renderBatchHeader(batch) {
    const currentBatchName = document.getElementById('currentBatchName');
    const batchDeadline = document.getElementById('batchDeadline');
    const deadlineText = document.getElementById('deadlineText');

    if (!currentBatchName) return;

    // 更新批次名称
    if (batch) {
        currentBatchName.textContent = batch.name || '';

        // 更新截止时间显示
        const deadlineInfo = formatDeadline(batch.deadline_at);
        if (deadlineInfo && batchDeadline && deadlineText) {
            batchDeadline.classList.remove('hidden');
            deadlineText.textContent = deadlineInfo.text;
            // 移除旧的样式类，添加新的
            batchDeadline.classList.remove('text-stone-500', 'text-amber-600', 'text-red-500', 'font-medium', 'animate-pulse');
            const classes = deadlineInfo.className.split(' ');
            batchDeadline.classList.add(...classes);
        } else if (batchDeadline) {
            batchDeadline.classList.add('hidden');
        }
    } else {
        currentBatchName.textContent = '';
        if (batchDeadline) batchDeadline.classList.add('hidden');
    }
}

// ==================== 进度重置 ====================

/**
 * 重置上传进度 UI
 */
function resetUploadProgress() {
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressText = document.getElementById('progressText');

    if (progressBar) {
        progressBar.style.width = '0%';
        progressBar.classList.remove('bg-red-400');
        progressBar.style.background = 'linear-gradient(90deg, #FBBF24, #F59E0B)';
    }
    if (progressPercent) progressPercent.textContent = '0%';
    if (progressText) progressText.textContent = '正在上传图片...';
}
