/**
 * 编辑器视图模块
 * 全屏弹窗：新建/编辑作业
 */

// ==================== 全局状态初始化 ====================

// 确保 window.state 存在（兼容 registry.html 等页面）
if (!window.state) {
    window.state = {
        subjects: [],
    };
}
var state = window.state;  // 使用 var 允许重复声明

// ==================== 编辑器状态 ====================

const editorState = {
    open: false,
    mode: 'new',          // 'new' | 'edit'
    batchId: null,
    images: [],           // {id, url, name, type}
    items: [],            // 待确认的作业项
    deadlineAt: null,
};

// ==================== 图片查看器状态 ====================

const editorImageViewerState = {
    images: [],
    currentIndex: 0,
};

// ==================== DOM 元素 ====================

const editorElements = {
    modal: null,
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
    cameraBtn: null,
    galleryBtn: null,
};

// ==================== 初始化 ====================

/**
 * 初始化编辑器
 */
function initEditor() {
    // 缓存 DOM 元素
    editorElements.modal = document.getElementById('editorModal');
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
    editorElements.cameraBtn = document.getElementById('editorCameraBtn');
    editorElements.galleryBtn = document.getElementById('editorGalleryBtn');

    // 绑定事件
    bindEditorEvents();

    // 初始化拖拽上传
    initDropZone();
}

/**
 * 绑定编辑器事件
 */
function bindEditorEvents() {
    // 取消按钮
    if (editorElements.cancelBtn) {
        editorElements.cancelBtn.addEventListener('click', editorView.close);
    }

    // 保存按钮
    if (editorElements.saveBtn) {
        editorElements.saveBtn.addEventListener('click', editorView.save);
    }

    // 添加作业项按钮
    if (editorElements.addItemBtn) {
        editorElements.addItemBtn.addEventListener('click', handleEditorAddItem);
    }

    // 作业项列表事件
    if (editorElements.itemsList) {
        editorElements.itemsList.addEventListener('click', handleEditorItemListClick);
        editorElements.itemsList.addEventListener('change', handleEditorItemChange);
    }

    // 图片列表事件
    if (editorElements.imagesList) {
        editorElements.imagesList.addEventListener('click', handleEditorImageListClick);
    }

    // 上传弹窗事件
    if (editorElements.cameraBtn) {
        editorElements.cameraBtn.addEventListener('click', handleEditorCameraUpload);
    }
    if (editorElements.galleryBtn) {
        editorElements.galleryBtn.addEventListener('click', handleEditorGalleryUpload);
    }

    // 上传弹窗关闭按钮
    if (editorElements.uploadCloseBtn) {
        editorElements.uploadCloseBtn.addEventListener('click', () => {
            if (editorElements.uploadModal) {
                editorElements.uploadModal.classList.add('hidden');
            }
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

/**
 * 初始化拖拽上传功能
 */
function initDropZone() {
    const dropZone = editorElements.dropZone;
    const fileInput = editorElements.fileInput;

    if (!dropZone || !fileInput) return;

    // 点击触发文件选择
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // 文件选择
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleEditorImageUpload(Array.from(e.target.files));
            fileInput.value = ''; // 重置
        }
    });

    // 拖拽事件 - 阻止默认行为
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // 拖拽高亮效果
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

    // 处理拖拽放下
    dropZone.addEventListener('drop', (e) => {
        const files = Array.from(e.dataTransfer.files).filter(f =>
            f.type.startsWith('image/')
        );
        if (files.length > 0) {
            handleEditorImageUpload(files);
        }
    });
}

// ==================== 编辑器视图对象 ====================

/**
 * 编辑器视图
 */
const editorView = {
    /**
     * 打开编辑器
     * @param {string} mode - 'new' | 'edit'
     * @param {number} batchId - 批次 ID（编辑模式）
     */
    async open(mode = 'new', batchId = null) {
        editorState.mode = mode;
        editorState.batchId = batchId;
        editorState.open = true;

        // 根据模式加载数据
        if (mode === 'edit' && batchId) {
            await this.load(batchId);
            editorElements.title.textContent = '编辑作业';
        } else {
            this.reset();
            editorElements.title.textContent = '新建作业';
        }

        // 显示弹窗
        editorElements.modal.classList.remove('hidden');
    },

    /**
     * 关闭编辑器
     */
    close() {
        // 清理 URL 中的 edit 参数（刷新后不再自动打开编辑器）
        const url = new URL(window.location);
        url.searchParams.delete('edit');
        window.history.replaceState({}, '', url);

        editorElements.modal.classList.add('hidden');
        editorState.open = false;

        // 清理上传弹窗
        if (editorElements.uploadModal) {
            editorElements.uploadModal.classList.add('hidden');
        }
    },

    /**
     * 加载批次数据（编辑模式）
     * @param {number} batchId - 批次 ID
     */
    async load(batchId) {
        try {
            // 确保科目数据已加载
            if (!state.subjects || state.subjects.length === 0) {
                state.subjects = await api.getSubjects();
            }

            const batch = await api.getBatch(batchId);

            // 加载图片
            const images = (batch.images || []).map(img => ({
                id: img.id,
                url: img.file_path,
                name: img.file_name,
                type: img.image_type,
            }));

            // 加载作业项
            const items = (batch.items || []).map(item => ({
                id: item.id,
                subject_id: item.subject.id,
                text: item.text,
                key_concept: item.key_concept || '',
            }));

            // 更新状态
            editorState.images = images;
            editorState.items = items;
            editorState.deadlineAt = batch.deadline_at;

            // 渲染
            this.render();
            showToast('加载完成');
        } catch (error) {
            console.error('加载批次失败:', error);
            alert('加载失败，请重试');
        }
    },

    /**
     * 重置编辑器状态（新建模式）
     */
    reset() {
        editorState.batchId = null;
        editorState.images = [];
        editorState.items = [];
        editorState.deadlineAt = null;
        this.render();
    },

    /**
     * 渲染编辑器内容
     */
    render() {
        renderEditorImages(editorState.images);
        renderEditorItems(editorState.items, state.subjects);
        renderEditorDeadline(editorState.deadlineAt);
    },

    /**
     * 保存编辑器内容
     */
    async save() {
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

                // 编辑模式保留 ID
                const existingId = el.dataset.id;
                if (existingId) {
                    item.id = parseInt(existingId);
                }

                items.push(item);
            }
        });

        if (items.length === 0) {
            alert('至少要写一条作业');
            return;
        }

        // 收集截止时间
        const deadlineAt = editorElements.deadlineInput.value
            ? new Date(editorElements.deadlineInput.value).toISOString()
            : null;

        try {
            if (editorState.mode === 'new') {
                // 新建模式：创建草稿批次
                if (editorState.images.length === 0) {
                    alert('请先上传作业图片');
                    return;
                }

                // 使用 v1ConfirmBatch 确认批次
                await api.v1ConfirmBatch(
                    editorState.batchId,
                    items,
                    null,  // 暂不保存图片分类
                    deadlineAt
                );

                showToast('保存成功');
            } else {
                // 编辑模式：更新批次
                const data = {
                    items: items,  // 发送所有作业项，后端会同步（新增/更新/删除）
                    deadline_at: deadlineAt,
                };

                await api.updateBatch(editorState.batchId, data);
                showToast('保存成功');
            }

            // 关闭编辑器
            this.close();

            // 刷新批次列表
            if (typeof loadBatchList === 'function') {
                await loadBatchList();
            }

            // 返回登记簿
            if (typeof router !== 'undefined') {
                router.navigate('batches');
            }
        } catch (error) {
            console.error('保存失败:', error);
            alert('保存出错了，再试试');
        }
    },
};

// ==================== 事件处理函数 ====================

/**
 * 处理添加作业项
 */
function handleEditorAddItem() {
    editorState.items.push({
        subject_id: state.subjects[0]?.id || 1,
        text: '',
        key_concept: '',
    });
    renderEditorItems(editorState.items, state.subjects);
}

/**
 * 处理作业项列表点击
 */
function handleEditorItemListClick(e) {
    const removeBtn = e.target.closest('.editor-item-remove');
    if (removeBtn) {
        const itemEl = removeBtn.closest('.editor-item');
        const index = parseInt(itemEl.dataset.index);
        editorState.items.splice(index, 1);
        renderEditorItems(editorState.items, state.subjects);
    }
}

/**
 * 处理作业项内容变更
 */
function handleEditorItemChange(e) {
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
}

/**
 * 处理图片列表点击
 */
async function handleEditorImageListClick(e) {
    const addBtn = e.target.closest('.editor-image-add');
    const imgDiv = e.target.closest('.editor-image');

    // 点击添加按钮
    if (addBtn) {
        editorElements.uploadModal.classList.remove('hidden');
        return;
    }

    // 点击图片缩略图
    if (imgDiv) {
        const index = parseInt(imgDiv.dataset.index);
        // 如果 openImageViewer 函数存在则调用，否则在新标签页打开图片
        if (typeof openImageViewer === 'function') {
            openImageViewer(editorState.images, index);
        } else {
            // 简单的图片预览：在新标签页打开
            const imageUrl = editorState.images[index].url;
            window.open(imageUrl, '_blank');
        }
    }
}

/**
 * 处理拍照上传
 */
async function handleEditorCameraUpload() {
    try {
        // 创建文件输入
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.capture = 'environment';  // 优先使用后置摄像头

        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (file) {
                await handleEditorImageUpload([file]);
            }
        };

        input.click();
    } catch (error) {
        console.error('拍照失败:', error);
        alert('拍照功能暂不可用');
    }
}

/**
 * 处理相册上传
 */
async function handleEditorGalleryUpload() {
    try {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.multiple = true;

        input.onchange = async (e) => {
            const files = Array.from(e.target.files);
            if (files.length > 0) {
                await handleEditorImageUpload(files);
            }
        };

        input.click();
    } catch (error) {
        console.error('选择图片失败:', error);
        alert('选择图片失败');
    }
}

/**
 * 处理图片上传
 * @param {File[]} files - 图片文件数组
 */
async function handleEditorImageUpload(files) {
    try {
        // 上传图片并创建草稿批次
        const result = await api.v1UploadDraft(files);

        // 保存批次 ID
        editorState.batchId = result.batch.id;

        // 添加图片到列表
        const newImages = result.images.map(img => ({
            id: img.id,
            url: img.file_path,
            name: img.file_name,
            type: img.image_type,
        }));
        editorState.images.push(...newImages);

        // 如果 VLM 解析成功，添加作业项
        if (result.parsed && result.parsed.success) {
            // 合并新科目
            if (result.parsed.new_subjects && result.parsed.new_subjects.length > 0) {
                state.subjects.push(...result.parsed.new_subjects);
            }

            // 添加作业项
            const newItems = result.parsed.items.map(item => ({
                ...item,
                tempId: Date.now() + Math.random(),
            }));
            editorState.items.push(...newItems);
        }

        // 重新渲染
        editorView.render();

        // 关闭上传弹窗
        editorElements.uploadModal.classList.add('hidden');

        showToast('上传成功');
    } catch (error) {
        console.error('上传失败:', error);
        alert('上传失败: ' + error.message);
    }
}

// ==================== 渲染函数 ====================

/**
 * 渲染编辑器图片列表
 * @param {Array} images - 图片数组
 */
function renderEditorImages(images) {
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
        <div class="editor-image-add flex-shrink-0 w-20 h-20 rounded-xl border-2 border-dashed border-stone-300 hover:border-amber-400 flex items-center justify-center cursor-pointer transition-colors bg-stone-50 hover:bg-amber-50">
            <svg class="w-8 h-8 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
        </div>
    `;
}

/**
 * 渲染编辑器作业项列表
 * @param {Array} items - 作业项数组
 * @param {Array} subjects - 科目数组
 */
function renderEditorItems(items, subjects) {
    if (!editorElements.itemsList) return;

    if (items.length === 0) {
        editorElements.itemsList.innerHTML = `
            <div class="text-center py-8 text-stone-400 text-sm">
                暂无作业项，点击下方按钮添加
            </div>
        `;
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
}

/**
 * 渲染编辑器截止时间
 * @param {string|null} deadlineAt - 截止时间（ISO 格式）
 */
function renderEditorDeadline(deadlineAt) {
    if (!editorElements.deadlineInput) return;

    if (deadlineAt) {
        const dateStr = deadlineAt.split('T')[0];
        const timePart = deadlineAt.split('T')[1];
        const hourMinute = timePart.substring(0, 5);
        editorElements.deadlineInput.value = `${dateStr}T${hourMinute}`;
    } else {
        editorElements.deadlineInput.value = '';
    }
}

// ==================== 图片查看器函数 ====================

/**
 * 打开图片查看器
 * @param {Array} images - 图片数组
 * @param {number} index - 当前显示的图片索引
 */
function openImageViewer(images, index) {
    const viewer = document.getElementById('editorImageViewer');
    const img = viewer?.querySelector('.viewer-image');

    if (!viewer || !img) {
        // 如果查看器元素不存在，在新标签页打开
        if (images && images[index]) {
            window.open(images[index].url, '_blank');
        }
        return;
    }

    editorImageViewerState.images = images;
    editorImageViewerState.currentIndex = index;

    img.src = images[index].url;
    viewer.classList.remove('hidden');
}

/**
 * 关闭图片查看器
 */
function editorCloseImageViewer() {
    const viewer = document.getElementById('editorImageViewer');
    if (viewer) {
        viewer.classList.add('hidden');
    }
}

/**
 * 上一张图片
 */
function editorPrevImage() {
    const { images, currentIndex } = editorImageViewerState;
    if (images.length === 0) return;

    const newIndex = (currentIndex - 1 + images.length) % images.length;
    editorImageViewerState.currentIndex = newIndex;

    const img = document.querySelector('#editorImageViewer .viewer-image');
    if (img) {
        img.src = images[newIndex].url;
    }
}

/**
 * 下一张图片
 */
function editorNextImage() {
    const { images, currentIndex } = editorImageViewerState;
    if (images.length === 0) return;

    const newIndex = (currentIndex + 1) % images.length;
    editorImageViewerState.currentIndex = newIndex;

    const img = document.querySelector('#editorImageViewer .viewer-image');
    if (img) {
        img.src = images[newIndex].url;
    }
}

// 导出图片查看器函数到全局（供 HTML onclick 调用）
window.editorCloseImageViewer = editorCloseImageViewer;
window.editorPrevImage = editorPrevImage;
window.editorNextImage = editorNextImage;

/**
 * 删除图片
 * @param {number} imageId - 图片 ID
 */
async function deleteImage(imageId) {
    if (!confirm('确定要删除这张图片吗？')) return;

    try {
        await api.v1DeleteImage(editorState.batchId, imageId);
        // 从本地状态移除
        editorState.images = editorState.images.filter(i => i.id !== imageId);
        editorView.render();
        showToast('图片已删除');
    } catch (error) {
        console.error('删除图片失败:', error);
        showToast('删除失败，请重试');
    }
}

/**
 * 切换图片类型
 * @param {number} imageId - 图片 ID
 * @param {string} currentType - 当前类型
 */
async function toggleImageType(imageId, currentType) {
    const newType = currentType === 'homework' ? 'reference' : 'homework';
    try {
        await api.v1UpdateImageType(editorState.batchId, imageId, newType);
        // 更新本地状态
        const img = editorState.images.find(i => i.id === imageId);
        if (img) img.type = newType;
        editorView.render();
        showToast('已切换为' + (newType === 'homework' ? '作业' : '参考'));
    } catch (error) {
        console.error('切换图片类型失败:', error);
        showToast('切换失败，请重试');
    }
}

// 导出删除函数到全局
window.deleteImage = deleteImage;
window.toggleImageType = toggleImageType;

// ==================== 导出 ====================

// 将编辑器视图挂载到全局
window.editorView = editorView;
window.editorState = editorState;

// 桥接函数，供 app.js 调用
async function loadEditorView(mode, batchId) {
    await editorView.open(mode, batchId);
}
window.loadEditorView = loadEditorView;

// 在 DOM 加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initEditor);
} else {
    initEditor();
}
