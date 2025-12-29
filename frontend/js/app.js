/**
 * 主应用逻辑 - 批次版本
 */

// ==================== 状态管理 ====================
const state = {
    currentBatch: null,      // 当前 active 批次
    subjects: [],            // 科目列表
    currentFilter: 'all',    // 筛选状态: all/todo/doing/done
    draftBatch: null,        // 上传中的 draft 批次
    draftItems: [],          // 待确认的作业项
    previewImages: [],       // 上传的图片预览
};

// ==================== DOM 元素 ====================
const elements = {
    // 页面元素
    homeworkList: document.getElementById('homeworkList'),
    emptyState: document.getElementById('emptyState'),
    currentBatchName: document.getElementById('currentBatchName'),
    loadingToast: document.getElementById('loadingToast'),

    // 按钮
    uploadBtn: document.getElementById('uploadBtn'),
    imagesBtn: document.getElementById('imagesBtn'),
    confirmBtn: document.getElementById('confirmBtn'),
    addItemBtn: document.getElementById('addItemBtn'),
    filterBtns: document.querySelectorAll('.filter-btn'),

    // 弹窗
    uploadModal: document.getElementById('uploadModal'),
    imagesModal: document.getElementById('imagesModal'),

    // 上传流程
    dropZone: document.getElementById('dropZone'),
    imageInput: document.getElementById('imageInput'),
    uploadProgress: document.getElementById('uploadProgress'),
    uploadStep: document.getElementById('uploadStep'),
    confirmStep: document.getElementById('confirmStep'),
    imagePreviewSection: document.getElementById('imagePreviewSection'),
    progressBar: document.getElementById('progressBar'),
    progressPercent: document.getElementById('progressPercent'),
    progressText: document.getElementById('progressText'),

    // 确认区域
    previewImages: document.getElementById('previewImages'),
    itemList: document.getElementById('itemList'),
    itemCount: document.getElementById('itemCount'),
    deadlineInput: document.getElementById('deadlineInput'),
    imagesList: document.getElementById('imagesList'),

    // 关闭按钮
    modalClose: document.querySelectorAll('.modal-close'),
};

// ==================== 初始化 ====================
async function init() {
    await loadSubjects();
    await loadCurrentBatch();
    bindEvents();
}

// ==================== 数据加载 ====================
async function loadSubjects() {
    try {
        state.subjects = await api.getSubjects();
    } catch (error) {
        console.error('加载科目失败:', error);
        // 默认科目
        state.subjects = [
            { id: 1, name: '语文', color: '#EF4444' },
            { id: 2, name: '数学', color: '#3B82F6' },
            { id: 3, name: '英语', color: '#10B981' },
        ];
    }
}

async function loadCurrentBatch() {
    try {
        const batch = await api.getCurrentBatch();
        state.currentBatch = batch;
        renderBatch();
    } catch (error) {
        console.error('加载批次失败:', error);
        state.currentBatch = null;
        renderBatch();
    }
}

// ==================== 渲染 ====================
function renderBatch() {
    // 更新批次名称
    if (state.currentBatch) {
        elements.currentBatchName.textContent = state.currentBatch.name || '';
    } else {
        elements.currentBatchName.textContent = '';
    }

    renderHomeworkList();
}

function renderHomeworkList() {
    const items = state.currentBatch?.items || [];
    const filteredItems = filterItems(items);

    if (filteredItems.length === 0) {
        elements.homeworkList.innerHTML = '';
        elements.emptyState.classList.remove('hidden');
        return;
    }

    elements.emptyState.classList.add('hidden');
    elements.homeworkList.innerHTML = filteredItems.map(item => createHomeworkItemHTML(item)).join('');
}

function filterItems(items) {
    if (state.currentFilter === 'all') return items;
    return items.filter(item => item.status === state.currentFilter);
}

function createHomeworkItemHTML(item) {
    const statusConfig = {
        'todo': { border: 'border-gray-300', bg: 'bg-gray-100', text: 'text-gray-500' },
        'doing': { border: 'border-blue-500', bg: 'bg-blue-100', text: 'text-blue-500' },
        'done': { border: 'border-green-500', bg: 'bg-green-100', text: 'text-green-500' },
    };
    const config = statusConfig[item.status] || statusConfig['todo'];

    const actionButtons = {
        'todo': `<button class="status-btn px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100" data-id="${item.id}" data-status="doing">开始</button>`,
        'doing': `<button class="status-btn px-3 py-1 text-sm bg-green-50 text-green-600 rounded-lg hover:bg-green-100" data-id="${item.id}" data-status="done">完成</button>`,
        'done': `<span class="text-sm text-green-500">已完成</span>`,
    };

    const duration = item.status === 'doing' && item.started_at
        ? `<div class="mt-2 text-xs text-gray-400">已用时 ${formatDuration(item.started_at)}</div>`
        : '';

    return `
        <div class="homework-item bg-white rounded-lg shadow-sm p-4 border-l-4 ${config.border}" data-id="${item.id}">
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="w-2 h-2 rounded-full ${config.bg}"></span>
                        <span class="px-2 py-0.5 text-xs rounded-full font-medium" style="background-color: ${item.subject.color}20; color: ${item.subject.color}">
                            ${item.subject.name}
                        </span>
                        ${item.key_concept ? `<span class="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full">${item.key_concept}</span>` : ''}
                    </div>
                    <p class="text-gray-800">${item.text}</p>
                    ${duration}
                </div>
                <div class="flex gap-2 ml-4">
                    ${actionButtons[item.status]}
                    ${item.status !== 'done' ? `
                        <button class="delete-item-btn px-2 py-1 text-sm text-gray-400 hover:text-red-500" data-id="${item.id}">
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                        </button>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function formatDuration(startTime) {
    const start = new Date(startTime);
    const now = new Date();
    const minutes = Math.floor((now - start) / 60000);
    if (minutes < 60) return `${minutes} 分钟`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours} 小时 ${mins} 分钟`;
}

function renderConfirmItems() {
    elements.itemCount.textContent = `(${state.draftItems.length})`;
    elements.itemList.innerHTML = state.draftItems.map((item, index) => createConfirmItemHTML(item, index)).join('');
}

function createConfirmItemHTML(item, index) {
    return `
        <div class="confirm-item flex gap-2 p-2 bg-gray-50 rounded-lg" data-index="${index}">
            <select class="item-subject flex-0 border rounded px-2 py-1 text-sm" style="min-width: 80px">
                ${state.subjects.map(s => `<option value="${s.id}" ${item.subject_id === s.id ? 'selected' : ''}>${s.name}</option>`).join('')}
            </select>
            <input type="text" class="item-text flex-1 border rounded px-2 py-1 text-sm" value="${item.text}" placeholder="作业内容">
            <input type="text" class="item-concept w-24 border rounded px-2 py-1 text-sm" value="${item.key_concept || ''}" placeholder="关键概念">
            <button class="remove-item px-2 text-gray-400 hover:text-red-500">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    `;
}

function renderPreviewImages() {
    elements.previewImages.innerHTML = state.previewImages.map((img, index) => `
        <div class="preview-image flex-shrink-0 relative group cursor-pointer" data-index="${index}">
            <img src="${img.url}" alt="${img.name}" class="w-20 h-20 object-cover rounded-lg">
            <div class="image-type-badge absolute top-1 left-1 px-1.5 py-0.5 text-xs rounded ${img.type === 'homework' ? 'bg-blue-500 text-white' : 'bg-gray-500 text-white'}">
                ${img.type === 'homework' ? '作业' : '参考'}
            </div>
            <button class="toggle-type absolute top-1 right-1 p-1 bg-white rounded shadow opacity-0 group-hover:opacity-100 transition-opacity" title="切换图片类型">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
            </button>
        </div>
    `).join('');
}

function renderImagesModal() {
    const images = state.currentBatch?.images || [];
    const homeworkImages = images.filter(img => img.image_type === 'homework');
    const referenceImages = images.filter(img => img.image_type === 'reference');

    elements.imagesList.innerHTML = '';

    if (homeworkImages.length > 0) {
        elements.imagesList.innerHTML += `
            <div class="col-span-2">
                <p class="text-sm font-medium text-gray-700 mb-2">作业清单</p>
                <div class="grid grid-cols-2 gap-4">
                    ${homeworkImages.map(img => `
                        <div class="relative">
                            <img src="/uploads/${img.file_path}" alt="${img.file_name}" class="w-full rounded-lg cursor-pointer hover:opacity-90" onclick="window.open(this.src, '_blank')">
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    if (referenceImages.length > 0) {
        elements.imagesList.innerHTML += `
            <div class="col-span-2">
                <p class="text-sm font-medium text-gray-700 mb-2">参考资料</p>
                <div class="grid grid-cols-2 gap-4">
                    ${referenceImages.map(img => `
                        <div class="relative">
                            <img src="/uploads/${img.file_path}" alt="${img.file_name}" class="w-full rounded-lg cursor-pointer hover:opacity-90" onclick="window.open(this.src, '_blank')">
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    if (homeworkImages.length === 0 && referenceImages.length === 0) {
        elements.imagesList.innerHTML = '<p class="col-span-2 text-center text-gray-400 py-8">暂无图片</p>';
    }
}

// ==================== 事件绑定 ====================
function bindEvents() {
    // 筛选按钮
    elements.filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            elements.filterBtns.forEach(b => {
                b.classList.remove('active', 'bg-blue-500', 'text-white');
                b.classList.add('text-gray-600', 'hover:bg-gray-100');
            });
            btn.classList.add('active', 'bg-blue-500', 'text-white');
            btn.classList.remove('text-gray-600', 'hover:bg-gray-100');
            state.currentFilter = btn.dataset.status;
            renderHomeworkList();
        });
    });

    // 上传按钮
    elements.uploadBtn.addEventListener('click', () => {
        openUploadModal();
    });

    // 图片按钮
    elements.imagesBtn.addEventListener('click', () => {
        renderImagesModal();
        elements.imagesModal.classList.remove('hidden');
    });

    // 关闭弹窗
    elements.modalClose.forEach(btn => {
        btn.addEventListener('click', closeModals);
    });

    // 点击弹窗外部关闭
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            closeModals();
        }
    });

    // 拖拽上传
    elements.dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.dropZone.classList.add('border-blue-400', 'bg-blue-50');
    });

    elements.dropZone.addEventListener('dragleave', () => {
        elements.dropZone.classList.remove('border-blue-400', 'bg-blue-50');
    });

    elements.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.dropZone.classList.remove('border-blue-400', 'bg-blue-50');
        const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
        if (files.length > 0) {
            handleFilesUpload(files);
        }
    });

    elements.dropZone.addEventListener('click', () => {
        elements.imageInput.click();
    });

    elements.imageInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            handleFilesUpload(files);
        }
    });

    // 手动添加作业项
    elements.addItemBtn.addEventListener('click', () => {
        state.draftItems.push({
            subject_id: state.subjects[0]?.id || 1,
            text: '',
            key_concept: '',
            source_image_id: null,
        });
        renderConfirmItems();
    });

    // 确认按钮
    elements.confirmBtn.addEventListener('click', handleConfirmBatch);

    // 作业列表事件
    elements.homeworkList.addEventListener('click', handleHomeworkListClick);

    // 确认列表事件
    elements.itemList.addEventListener('click', handleItemListClick);
    elements.itemList.addEventListener('change', handleItemChange);

    // 图片预览事件
    elements.previewImages.addEventListener('click', handlePreviewClick);
}

// ==================== 事件处理 ====================
async function handleFilesUpload(files) {
    // 显示进度区域，隐藏拖拽区域
    elements.dropZone.classList.add('hidden');
    elements.uploadProgress.classList.remove('hidden');

    // 启动进度模拟
    const progressController = startProgress();

    try {
        // 上传阶段
        const result = await api.uploadDraft(files);
        state.draftBatch = result.batch;

        // 保存图片信息用于预览
        state.previewImages = result.images.map(img => ({
            id: img.id,
            url: img.file_path,  // 后端已包含 /uploads/ 前缀
            name: img.file_name,
            type: img.image_type,
        }));

        // 显示图片预览区域（上传步骤）
        renderPreviewImages();
        elements.imagePreviewSection.classList.remove('hidden');

        // OCR 阶段
        progressController.setStage('ocr');
        const parseResult = await api.parseOCR(state.draftBatch.id);

        // 设置作业项 (API 返回数组，不是对象)
        state.draftItems = (parseResult || []).map(item => ({
            ...item,
            tempId: Date.now() + Math.random(),
        }));

        // 完成进度
        progressController.complete();

        // 延迟后切换到确认步骤（图片预览保持显示）
        setTimeout(() => {
            elements.uploadStep.classList.add('hidden');
            elements.uploadProgress.classList.add('hidden');
            elements.confirmStep.classList.remove('hidden');
            elements.confirmBtn.textContent = '确认';
            renderConfirmItems();
        }, 500);

    } catch (error) {
        clearInterval(progressInterval);
        elements.progressText.textContent = '处理失败';
        elements.progressBar.classList.remove('bg-blue-500');
        elements.progressBar.classList.add('bg-red-500');
        console.error('上传失败:', error);
        alert('上传失败: ' + error.message);
        closeModals();
    }
}

async function handleConfirmBatch() {
    // 收集编辑后的作业项
    const itemElements = elements.itemList.querySelectorAll('.confirm-item');
    const items = [];

    itemElements.forEach(el => {
        const subjectId = parseInt(el.querySelector('.item-subject').value);
        const text = el.querySelector('.item-text').value.trim();
        const concept = el.querySelector('.item-concept').value.trim();

        if (text) {
            items.push({
                subject_id: subjectId,
                text: text,
                key_concept: concept || null,
            });
        }
    });

    if (items.length === 0) {
        alert('请至少添加一项作业');
        return;
    }

    const deadlineAt = elements.deadlineInput.value
        ? new Date(elements.deadlineInput.value).toISOString()
        : null;

    try {
        showToast('正在保存...');
        await api.confirmBatch(state.draftBatch.id, items, deadlineAt);
        showToast('保存成功！');
        closeModals();
        await loadCurrentBatch();
    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败: ' + error.message);
    }
}

async function handleHomeworkListClick(e) {
    const statusBtn = e.target.closest('.status-btn');
    const deleteBtn = e.target.closest('.delete-item-btn');

    if (statusBtn) {
        const itemId = parseInt(statusBtn.dataset.id);
        const newStatus = statusBtn.dataset.status;
        await updateItemStatus(itemId, newStatus);
    } else if (deleteBtn) {
        const itemId = parseInt(deleteBtn.dataset.id);
        if (confirm('确定要删除这项作业吗？')) {
            await deleteItem(itemId);
        }
    }
}

async function updateItemStatus(itemId, status) {
    try {
        await api.updateItemStatus(itemId, status);
        await loadCurrentBatch();
        showToast('状态已更新');
    } catch (error) {
        alert('操作失败: ' + error.message);
    }
}

async function deleteItem(itemId) {
    try {
        await api.deleteItem(itemId);
        await loadCurrentBatch();
        showToast('已删除');
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

function handleItemListClick(e) {
    const removeBtn = e.target.closest('.remove-item');
    if (removeBtn) {
        const index = parseInt(removeBtn.closest('.confirm-item').dataset.index);
        state.draftItems.splice(index, 1);
        renderConfirmItems();
    }
}

function handleItemChange(e) {
    const itemEl = e.target.closest('.confirm-item');
    if (!itemEl) return;

    const index = parseInt(itemEl.dataset.index);
    const item = state.draftItems[index];

    if (e.target.classList.contains('item-subject')) {
        item.subject_id = parseInt(e.target.value);
    } else if (e.target.classList.contains('item-text')) {
        item.text = e.target.value;
    } else if (e.target.classList.contains('item-concept')) {
        item.key_concept = e.target.value;
    }
}

async function handlePreviewClick(e) {
    const toggleBtn = e.target.closest('.toggle-type');
    const imgDiv = e.target.closest('.preview-image');

    if (toggleBtn && imgDiv) {
        e.preventDefault();
        const index = parseInt(imgDiv.dataset.index);
        const img = state.previewImages[index];
        const newType = img.type === 'homework' ? 'reference' : 'homework';

        try {
            await api.updateImageType(state.draftBatch.id, img.id, newType);
            img.type = newType;
            renderPreviewImages();
        } catch (error) {
            alert('切换失败: ' + error.message);
        }
    }
}

// ==================== 弹窗管理 ====================
function openUploadModal() {
    // 清理进度定时器
    clearInterval(progressInterval);

    // 重置状态
    state.draftBatch = null;
    state.draftItems = [];
    state.previewImages = [];

    // 重置 UI
    elements.uploadStep.classList.remove('hidden');
    elements.confirmStep.classList.add('hidden');
    elements.uploadProgress.classList.add('hidden');
    elements.dropZone.classList.remove('hidden');
    elements.imagePreviewSection.classList.add('hidden');
    elements.deadlineInput.value = '';

    // 重置进度条
    elements.progressBar.style.width = '0%';
    elements.progressBar.classList.remove('bg-red-500');
    elements.progressBar.classList.add('bg-blue-500');
    elements.progressPercent.textContent = '0%';
    elements.progressText.textContent = '正在上传图片...';

    elements.uploadModal.classList.remove('hidden');
}

function closeModals() {
    document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
    elements.imageInput.value = '';
    elements.imagePreviewSection.classList.add('hidden');
}

// ==================== 工具函数 ====================
// 进度控制
let progressInterval = null;

function startProgress() {
    let progress = 0;
    let stage = 'upload'; // upload -> ocr -> parse

    progressInterval = setInterval(() => {
        // 根据阶段调整增长速度
        const increment = stage === 'upload' ? 5 : stage === 'ocr' ? 2 : 5;
        const maxProgress = stage === 'upload' ? 30 : stage === 'ocr' ? 90 : 100;

        if (progress < maxProgress) {
            progress = Math.min(progress + increment, maxProgress);
            updateProgressUI(progress, stage);
        }
    }, 100);

    return { setStage: (s) => stage = s, complete: () => completeProgress() };
}

function updateProgressUI(percent, stage) {
    elements.progressBar.style.width = percent + '%';
    elements.progressPercent.textContent = percent + '%';

    const stageTexts = {
        'upload': '正在上传图片...',
        'ocr': '正在识别作业内容...',
        'parse': '正在解析作业项...'
    };
    elements.progressText.textContent = stageTexts[stage] || '处理中...';
}

function completeProgress() {
    clearInterval(progressInterval);
    elements.progressBar.style.width = '100%';
    elements.progressPercent.textContent = '100%';
    elements.progressText.textContent = '识别完成！';
}

function showToast(message, duration = 2000) {
    elements.loadingToast.textContent = message;
    elements.loadingToast.classList.remove('hidden');
    setTimeout(() => {
        elements.loadingToast.classList.add('hidden');
    }, duration);
}

// ==================== 启动应用 ====================
init();
