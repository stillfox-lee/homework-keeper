/**
 * API 调用封装
 */

const API_BASE = window.location.origin;

// 获取带认证的请求头
function getAuthHeaders() {
    const token = window.getCurrentToken ? window.getCurrentToken() : null;
    const headers = {};
    if (token) {
        headers['X-Access-Token'] = token;
    }
    return headers;
}

// 通用请求处理
async function handleResponse(response) {
    if (!response.ok) {
        // 401 未授权
        if (response.status === 401) {
            throw new Error('请使用正确的链接访问（需要 token 参数）');
        }
        const error = await response.json().catch(() => ({ message: '网络出错了' }));
        throw new Error(error.message || error.detail || '网络出错了');
    }
    return response.json();
}

// API 对象
const api = {
    // 获取当前批次
    async getCurrentBatch() {
        const response = await fetch(`${API_BASE}/api/batches/current`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    // 获取批次列表
    async getBatches(params = {}) {
        const query = new URLSearchParams(params).toString();
        const response = await fetch(`${API_BASE}/api/batches?${query}`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    // 获取批次详情
    async getBatch(batchId) {
        const response = await fetch(`${API_BASE}/api/batches/${batchId}`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    // 获取批次作业项
    async getBatchItems(batchId, params = {}) {
        const query = new URLSearchParams(params).toString();
        const response = await fetch(`${API_BASE}/api/batches/${batchId}/items${query ? '?' + query : ''}`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    // 确认完成批次
    async completeBatch(batchId) {
        const response = await fetch(`${API_BASE}/api/batches/${batchId}/complete`, {
            method: 'POST',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
        });
        return handleResponse(response);
    },

    // 删除批次
    async deleteBatch(batchId) {
        const response = await fetch(`${API_BASE}/api/batches/${batchId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    // 上传图片创建 draft 批次
    async uploadDraft(files) {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        const response = await fetch(`${API_BASE}/api/upload/draft`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });
        return handleResponse(response);
    },

    // 解析 OCR 文本
    async parseOCR(batchId) {
        const formData = new FormData();
        formData.append('batch_id', batchId);

        const response = await fetch(`${API_BASE}/api/upload/parse`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });
        return handleResponse(response);
    },

    // 确认批次
    async confirmBatch(batchId, items, deadlineAt) {
        const response = await fetch(`${API_BASE}/api/upload/${batchId}/confirm`, {
            method: 'POST',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({
                items: items,
                deadline_at: deadlineAt
            })
        });
        return handleResponse(response);
    },

    // 更新作业项状态
    async updateItemStatus(itemId, status) {
        const response = await fetch(`${API_BASE}/api/items/${itemId}/status`, {
            method: 'PATCH',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        return handleResponse(response);
    },

    // 删除作业项
    async deleteItem(itemId) {
        const response = await fetch(`${API_BASE}/api/items/${itemId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    // 获取科目列表
    async getSubjects() {
        const response = await fetch(`${API_BASE}/api/subjects`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    // 获取批次图片（使用 V1 API）
    async getBatchImages(batchId) {
        const response = await fetch(`${API_BASE}/api/v1/upload/${batchId}/images`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    // 更新图片类型
    async updateImageType(batchId, imageId, imageType) {
        const formData = new FormData();
        formData.append('image_type', imageType);

        const response = await fetch(`${API_BASE}/api/upload/${batchId}/images/${imageId}/type`, {
            method: 'PATCH',
            headers: getAuthHeaders(),
            body: formData
        });
        return handleResponse(response);
    },

    // ==================== V1 API (使用 VLM) ====================

    // V1: 上传图片创建 draft 批次（使用 VLM 解析）
    async v1UploadDraft(files) {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        const response = await fetch(`${API_BASE}/api/v1/upload/draft`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });
        return handleResponse(response);
    },

    // V1: 确认批次（支持图片分类）
    async v1ConfirmBatch(batchId, items, imageClassification, deadlineAt) {
        const response = await fetch(`${API_BASE}/api/v1/upload/${batchId}/confirm`, {
            method: 'POST',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({
                items: items,
                image_classification: imageClassification,
                deadline_at: deadlineAt
            })
        });
        return handleResponse(response);
    },

    // V1: 获取批次图片
    async v1GetBatchImages(batchId) {
        const response = await fetch(`${API_BASE}/api/v1/upload/${batchId}/images`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    // V1: 更新图片类型
    async v1UpdateImageType(batchId, imageId, imageType) {
        const formData = new FormData();
        formData.append('image_type', imageType);

        const response = await fetch(`${API_BASE}/api/v1/upload/${batchId}/images/${imageId}/type`, {
            method: 'PATCH',
            headers: getAuthHeaders(),
            body: formData
        });
        return handleResponse(response);
    },

    // 向批次添加单个作业项
    async addBatchItem(batchId, item) {
        const response = await fetch(`${API_BASE}/api/batches/${batchId}/items`, {
            method: 'POST',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify(item)
        });
        return handleResponse(response);
    },

    // 更新批次
    async updateBatch(batchId, data) {
        const response = await fetch(`${API_BASE}/api/batches/${batchId}`, {
            method: 'PUT',
            headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return handleResponse(response);
    },

    // V1: 删除批次图片
    async v1DeleteImage(batchId, imageId) {
        const response = await fetch(`${API_BASE}/api/v1/upload/${batchId}/images/${imageId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    }
};

// 导出到全局
window.api = api;
