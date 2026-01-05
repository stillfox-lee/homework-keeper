/**
 * 编辑器页面逻辑
 * URL 格式：
 * - /editor.html?mode=new          (新建作业)
 * - /editor.html?mode=edit&id=123  (编辑作业)
 */

// ==================== 全局状态初始化 ====================

// 确保 window.state 存在
if (!window.state) {
    window.state = {
        subjects: [],
    };
}
var state = window.state;

// ==================== 编辑器状态 ====================

const editorState = {
    mode: 'new',          // 'new' | 'edit'
    batchId: null,
    images: [],           // {id, url, name, type}
    items: [],            // 作业项
    deadlineAt: null,
};

// ==================== 图片查看器 ====================

const editorImageViewer = createImageViewer({
    viewerId: 'editorImageViewer',
    getUrl: (item) => item.url,
    loop: false
});

// ==================== DOM 元素 ====================

const editorElements = {
    title: null,
    cancelBtn: null,
    saveBtn: null,
    imagesList: null,
    itemsList: null,
    addItemBtn: null,
    deadlineInput: null,
    uploadModal: null,
    uploadCloseBtn: null,
    dropZone: null,
    fileInput: null,
};

// ==================== 初始化 ====================

/**
 * 加载编辑器页面
 * @param {string} mode - 'new' | 'edit'
 * @param {string} batchId - 批次 ID（编辑模式）
 */
async function loadEditorPage(mode, batchId) {
    // 缓存 DOM 元素
    editorElements.title = document.getElementById('editorTitle');
    editorElements.cancelBtn = document.getElementById('editorCancelBtn');
    editorElements.saveBtn = document.getElementById('editorSaveBtn');
    editorElements.imagesList = document.getElementById('editorImagesList');
    editorElements.itemsList = document.getElementById('editorItemsList');
    editorElements.addItemBtn = document.getElementById('editorAddItemBtn');
    editorElements.deadlineInput = document.getElementById('editorDeadlineInput');
    editorElements.uploadModal = document.getElementById('editorUploadModal');
    editorElements.uploadCloseBtn = document.getElementById('editorUploadClose');
    editorElements.dropZone = document.getElementById('editorDropZone');
    editorElements.fileInput = document.getElementById('editorFileInput');

    // 初始化状态
    editorState.mode = mode || 'new';
    editorState.batchId = batchId ? parseInt(batchId) : null;

    // 绑定事件
    bindPageEvents();

    // 加载科目
    if (!state.subjects || state.subjects.length === 0) {
        state.subjects = await api.getSubjects();
    }

    // 根据模式加载数据
    if (mode === 'edit' && batchId) {
        await loadBatchData(parseInt(batchId));
        editorElements.title.textContent = '编辑作业';
    } else {
        resetEditor();
        editorElements.title.textContent = '新建作业';
    }

    // 初始化拖拽上传
    initDropZone();
}

/**
 * 绑定页面事件
 */
function bindPageEvents() {
    // 取消按钮 - 返回登记簿
    if (editorElements.cancelBtn) {
        editorElements.cancelBtn.addEventListener('click', () => {
            window.location.href = '/registry.html';
        });
    }

    // 保存按钮
    if (editorElements.saveBtn) {
        editorElements.saveBtn.addEventListener('click', handleSave);
    }

    // 添加作业项按钮
    if (editorElements.addItemBtn) {
        editorElements.addItemBtn.addEventListener('click', handleAddItem);
    }

    // 作业项列表事件
    if (editorElements.itemsList) {
        editorElements.itemsList.addEventListener('click', handleItemListClick);
        editorElements.itemsList.addEventListener('change', handleItemChange);
    }

    // 图片列表事件
    if (editorElements.imagesList) {
        editorElements.imagesList.addEventListener('click', handleImageListClick);
    }

    // 上传弹窗关闭
    if (editorElements.uploadCloseBtn) {
        editorElements.uploadCloseBtn.addEventListener('click', () => {
            editorElements.uploadModal?.classList.add('hidden');
        });
    }

    // 点击上传弹窗外部关闭
    if (editorElements.uploadModal) {
        editorElements.uploadModal.addEventListener('click', (e) => {
            if (e.target === editorElements.uploadModal) {
                editorElements.uploadModal.classList.add('hidden');
            }
        });
    }
}

// ==================== 数据加载 ====================

/**
 * 加载批次数据（编辑模式）
 * @param {number} batchId - 批次 ID
 */
async function loadBatchData(batchId) {
    try {
        const batch = await api.getBatch(batchId);

        // 加载图片
        editorState.images = (batch.images || []).map(img => ({
            id: img.id,
            url: img.file_path,
            name: img.file_name,
            type: img.image_type,
        }));

        // 加载作业项
        editorState.items = (batch.items || []).map(item => ({
            id: item.id,
            subject_id: item.subject.id,
            text: item.text,
            key_concept: item.key_concept || '',
        }));

        // 截止时间
        editorState.deadlineAt = batch.deadline_at;

        render();
    } catch (error) {
        console.error('加载批次失败:', error);
        showToast('加载失败，请重试');
    }
}

/**
 * 重置编辑器（新建模式）
 */
function resetEditor() {
    editorState.batchId = null;
    editorState.images = [];
    editorState.items = [];
    editorState.deadlineAt = null;
    render();
}

// ==================== 渲染函数 ====================

/**
 * 渲染页面
 */
function render() {
    renderImages(editorState.images);
    renderItems(editorState.items, state.subjects);
    renderDeadline(editorState.deadlineAt);
    updateSaveButtonState();
}

/**
 * 渲染图片列表
 */
function renderImages(images) {
    if (!editorElements.imagesList) return;

    editorElements.imagesList.innerHTML = images.map((img, index) => `
        <div class="editor-image flex-shrink-0 relative group cursor-pointer" data-index="${index}">
            <img src="${img.url}" alt="${img.name}" class="editor-image-thumb w-20 h-20 object-cover rounded-xl shadow-sm border-2 border-stone-200 hover:border-amber-400 transition-colors" onclick="openImageViewer(editorState.images, ${index})">
            <button class="editor-image-type-badge" data-type="${img.type}" onclick="event.stopPropagation(); toggleImageType(${img.id}, '${img.type}')">
                ${img.type === 'homework' ? '作业' : '参考'}
            </button>
            <button class="editor-image-delete" onclick="event.stopPropagation(); deleteImage(${img.id})" title="删除图片">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    `).join('') + `
        <div class="editor-image-add flex-shrink-0 w-20 h-20 rounded-xl border-2 border-dashed border-stone-300 hover:border-amber-400 flex items-center justify-center cursor-pointer transition-colors bg-stone-50 hover:bg-amber-50" onclick="openUploadModal()">
            <svg class="w-8 h-8 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
        </div>
    `;
}

/**
 * 渲染作业项列表
 */
function renderItems(items, subjects) {
    if (!editorElements.itemsList) return;

    if (items.length === 0) {
        editorElements.itemsList.innerHTML = `
            <div class="text-center py-8 text-stone-400 text-sm">
                暂无作业项，点击下方按钮添加
            </div>
        `;
        updateSaveButtonState();
        return;
    }

    editorElements.itemsList.innerHTML = items.map((item, index) => `
        <div class="editor-item flex gap-2 p-3 bg-white rounded-xl border border-stone-200 hover:border-amber-300 transition-colors" data-index="${index}" ${item.id ? `data-id="${item.id}"` : ''}>
            <select class="editor-item-subject flex-0 border border-stone-200 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none" style="min-width: 90px">
                ${subjects.map(s => `<option value="${s.id}" ${item.subject_id === s.id ? 'selected' : ''}>${s.name}</option>`).join('')}
            </select>
            <input type="text" class="editor-item-text flex-1 border border-stone-200 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none" value="${item.text}" placeholder="要做什么作业">
            <input type="text" class="editor-item-concept w-28 border border-stone-200 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none" value="${item.key_concept || ''}" placeholder="知识点">
            <button class="editor-item-remove px-3 text-stone-400 hover:text-red-500 transition-colors" title="删除">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    `).join('');

    updateSaveButtonState();
}

/**
 * 渲染截止时间
 * @param {string|null} deadlineAt - 截止时间（ISO 格式 UTC 时间）
 */
function renderDeadline(deadlineAt) {
    if (!editorElements.deadlineInput) return;
    editorElements.deadlineInput.value = utcToDatetimeLocal(deadlineAt) || '';
}

/**
 * 更新保存按钮状态
 */
function updateSaveButtonState() {
    if (!editorElements.saveBtn) return;

    const hasValidItems = editorState.items.some(item => item.text && item.text.trim() !== '');
    editorElements.saveBtn.disabled = !hasValidItems;

    if (!hasValidItems) {
        editorElements.saveBtn.classList.add('opacity-50', 'cursor-not-allowed');
    } else {
        editorElements.saveBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

// ==================== 事件处理函数 ====================

/**
 * 处理添加作业项
 */
function handleAddItem() {
    editorState.items.push({
        subject_id: state.subjects[0]?.id || 1,
        text: '',
        key_concept: '',
    });
    renderItems(editorState.items, state.subjects);
}

/**
 * 处理作业项列表点击
 */
function handleItemListClick(e) {
    const removeBtn = e.target.closest('.editor-item-remove');
    if (removeBtn) {
        const itemEl = removeBtn.closest('.editor-item');
        const index = parseInt(itemEl.dataset.index);
        editorState.items.splice(index, 1);
        renderItems(editorState.items, state.subjects);
    }
}

/**
 * 处理作业项内容变更
 */
function handleItemChange(e) {
    const itemEl = e.target.closest('.editor-item');
    if (!itemEl) return;

    const index = parseInt(itemEl.dataset.index);
    const item = editorState.items[index];

    if (e.target.classList.contains('editor-item-subject')) {
        item.subject_id = parseInt(e.target.value);
    } else if (e.target.classList.contains('editor-item-text')) {
        item.text = e.target.value;
    } else if (e.target.classList.contains('editor-item-concept')) {
        item.key_concept = e.target.value;
    }

    updateSaveButtonState();
}

/**
 * 处理图片列表点击
 */
function handleImageListClick(e) {
    const imgDiv = e.target.closest('.editor-image');
    if (imgDiv) {
        const index = parseInt(imgDiv.dataset.index);
        openImageViewer(editorState.images, index);
    }
}

/**
 * 打开上传弹窗
 */
function openUploadModal() {
    editorElements.uploadModal?.classList.remove('hidden');
}

/**
 * 处理保存
 */
async function handleSave() {
    // 收集作业项
    const itemElements = editorElements.itemsList.querySelectorAll('.editor-item');
    const items = [];

    itemElements.forEach(el => {
        const subjectId = parseInt(el.querySelector('.editor-item-subject').value);
        const text = el.querySelector('.editor-item-text').value.trim();
        const concept = el.querySelector('.editor-item-concept').value.trim();

        if (text) {
            const item = {
                subject_id: subjectId,
                text: text,
                key_concept: concept || null,
            };

            const existingId = el.dataset.id;
            if (existingId) {
                item.id = parseInt(existingId);
            }

            items.push(item);
        }
    });

    if (items.length === 0) {
        showToast('至少要写一条作业');
        return;
    }

    const deadlineAt = editorElements.deadlineInput.value || null;

    try {
        if (editorState.mode === 'new') {
            // 新建模式
            if (editorState.images.length === 0) {
                showToast('请先上传作业图片');
                return;
            }

            await api.v1ConfirmBatch(
                editorState.batchId,
                items,
                null,
                deadlineAt
            );

            showToast('保存成功');
        } else {
            // 编辑模式
            await api.updateBatch(editorState.batchId, {
                items: items,
                deadline_at: deadlineAt,
            });

            showToast('保存成功');
        }

        // 返回登记簿
        window.location.href = '/registry.html';
    } catch (error) {
        console.error('保存失败:', error);
        showToast('保存出错了，再试试');
    }
}

// ==================== 拖拽上传 ====================

/**
 * 初始化拖拽上传
 */
function initDropZone() {
    const dropZone = editorElements.dropZone;
    const fileInput = editorElements.fileInput;

    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleImageUpload(Array.from(e.target.files));
            fileInput.value = '';
        }
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drag-over');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = Array.from(e.dataTransfer.files).filter(f =>
            f.type.startsWith('image/')
        );
        if (files.length > 0) {
            handleImageUpload(files);
        }
    });
}

/**
 * 处理图片上传
 */
async function handleImageUpload(files) {
    try {
        showLoading('墨宝正在努力识别作业，请稍等...');

        const result = await api.v1UploadDraft(files);

        editorState.batchId = result.batch.id;
        editorState.deadlineAt = result.batch.deadline_at;

        const newImages = result.images.map(img => ({
            id: img.id,
            url: img.file_path,
            name: img.file_name,
            type: img.image_type,
        }));
        editorState.images.push(...newImages);

        if (result.parsed && result.parsed.success) {
            if (result.parsed.new_subjects && result.parsed.new_subjects.length > 0) {
                state.subjects.push(...result.parsed.new_subjects);
            }

            const newItems = result.parsed.items.map(item => ({
                ...item,
                tempId: Date.now() + Math.random(),
            }));
            editorState.items.push(...newItems);
        }

        render();
        hideLoading();
        editorElements.uploadModal?.classList.add('hidden');

        showToast('上传成功');
    } catch (error) {
        hideLoading();
        console.error('上传失败:', error);
        showToast('上传失败: ' + error.message);
    }
}

// ==================== 图片查看器 ====================

/**
 * 打开图片查看器
 */
function openImageViewer(images, index) {
    editorImageViewer.setImages(images);
    editorImageViewer.open(index);
}

/**
 * 删除图片
 */
async function deleteImage(imageId) {
    if (!confirm('确定要删除这张图片吗？')) return;

    try {
        await api.v1DeleteImage(editorState.batchId, imageId);
        editorState.images = editorState.images.filter(i => i.id !== imageId);
        render();
        showToast('图片已删除');
    } catch (error) {
        console.error('删除图片失败:', error);
        showToast('删除失败，请重试');
    }
}

/**
 * 切换图片类型
 */
async function toggleImageType(imageId, currentType) {
    const newType = currentType === 'homework' ? 'reference' : 'homework';
    try {
        await api.v1UpdateImageType(editorState.batchId, imageId, newType);
        const img = editorState.images.find(i => i.id === imageId);
        if (img) img.type = newType;
        render();
        showToast('已切换为' + (newType === 'homework' ? '作业' : '参考'));
    } catch (error) {
        console.error('切换图片类型失败:', error);
        showToast('切换失败，请重试');
    }
}

// ==================== 导出全局函数 ====================

window.editorCloseImageViewer = () => editorImageViewer.close();
window.editorPrevImage = () => editorImageViewer.prev();
window.editorNextImage = () => editorImageViewer.next();
window.openImageViewer = openImageViewer;
window.deleteImage = deleteImage;
window.toggleImageType = toggleImageType;
window.openUploadModal = openUploadModal;
