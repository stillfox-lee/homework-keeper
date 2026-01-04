/**
 * 工具函数模块
 * 纯函数集合，与业务逻辑解耦
 */

// ==================== URL 处理 ====================

/**
 * 解析 URL hash 获取筛选状态
 * @returns {string|null} 筛选状态: all/todo/doing/done 或 null
 */
function parseHashFilter() {
    const hash = window.location.hash.slice(1); // 去掉 #
    if (hash.startsWith('filter-')) {
        const filter = hash.replace('filter-', '');
        if (['all', 'todo', 'doing', 'done'].includes(filter)) {
            return filter;
        }
    }
    return null;
}

/**
 * 更新 URL hash
 * @param {string} filter - 筛选状态
 */
function updateHashFilter(filter) {
    history.pushState(null, null, `#filter-${filter}`);
}

// ==================== 日期格式化 ====================

/**
 * 格式化日期（相对时间）
 * @param {string} dateString - ISO 日期字符串
 * @returns {string} 格式化后的日期
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return '今天';
    if (diffDays === 1) return '昨天';
    if (diffDays < 7) return `${diffDays}天前`;
    return `${date.getMonth() + 1}月${date.getDate()}日`;
}

/**
 * 格式化日期时间
 * @param {string} dateTime - ISO 日期时间字符串
 * @returns {string} 格式化后的日期时间
 */
function formatDateTime(dateTime) {
    const date = new Date(dateTime);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${month}月${day}日 ${hours}:${minutes}`;
}

/**
 * 格式化时长
 * @param {string} startTime - 开始时间
 * @param {string|null} endTime - 结束时间（null 表示当前）
 * @returns {string} 格式化后的时长
 */
function formatDuration(startTime, endTime = null) {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const minutes = Math.floor((end - start) / 60000);
    if (minutes < 60) return `${minutes} 分钟`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours} 小时 ${mins} 分钟`;
}

/**
 * 格式化截止时间（相对时间）
 * @param {string} deadlineAt - 截止时间
 * @returns {object|null} { text: string, className: string } 或 null
 */
function formatDeadline(deadlineAt) {
    if (!deadlineAt) return null;

    const deadline = new Date(deadlineAt);
    const now = new Date();
    const diffMs = deadline - now;
    const diffHours = diffMs / (1000 * 60 * 60);
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    // 获取星期几
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const weekday = weekdays[deadline.getDay()];

    // 已逾期
    if (diffMs < 0) {
        const overdueHours = Math.abs(Math.floor(diffMs / (1000 * 60 * 60)));
        if (overdueHours < 24) {
            return { text: `已逾期 ${overdueHours} 小时`, className: 'text-red-500 font-medium' };
        }
        return { text: `已逾期 ${Math.abs(diffDays)} 天`, className: 'text-red-500 font-medium' };
    }

    // 今天截止
    if (diffDays === 0) {
        const hours = deadline.getHours().toString().padStart(2, '0');
        const minutes = deadline.getMinutes().toString().padStart(2, '0');
        if (diffHours < 6) {
            return { text: `今晚 ${hours}:${minutes} 截止`, className: 'text-red-500 font-medium animate-pulse' };
        }
        if (diffHours < 12) {
            return { text: `今日 ${hours}:${minutes} 截止`, className: 'text-amber-600 font-medium' };
        }
        return { text: `今日 ${hours}:${minutes} 截止`, className: 'text-stone-500' };
    }

    // 明天截止
    if (diffDays === 1) {
        const hours = deadline.getHours().toString().padStart(2, '0');
        const minutes = deadline.getMinutes().toString().padStart(2, '0');
        if (diffHours < 36) {
            return { text: `明日 ${hours}:${minutes} 截止`, className: 'text-amber-600 font-medium' };
        }
        return { text: `明日 ${hours}:${minutes} 截止`, className: 'text-stone-500' };
    }

    // 2-6天截止，显示星期
    if (diffDays < 7) {
        const hours = deadline.getHours().toString().padStart(2, '0');
        const minutes = deadline.getMinutes().toString().padStart(2, '0');
        return { text: `${weekday} ${hours}:${minutes} 截止`, className: 'text-stone-500' };
    }

    // 更久之后
    const month = deadline.getMonth() + 1;
    const day = deadline.getDate();
    const hours = deadline.getHours().toString().padStart(2, '0');
    const minutes = deadline.getMinutes().toString().padStart(2, '0');
    return { text: `${month}月${day}日 ${hours}:${minutes} 截止`, className: 'text-stone-500' };
}

// ==================== 进度控制 ====================

/**
 * 创建进度控制器（手动控制进度，后端完成时才到 100%）
 * @returns {object} 进度控制器 { setStage, complete }
 */
function startProgress() {
    let progress = 0;

    return {
        setStage: (stage, percent) => {
            progress = percent;
            updateProgressUI(progress, stage);
        },
        complete: () => {
            progress = 100;
            completeProgress();
        }
    };
}

/**
 * 更新进度 UI
 * @param {number} percent - 进度百分比
 * @param {string} stage - 当前阶段
 */
function updateProgressUI(percent, stage) {
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressText = document.getElementById('progressText');

    if (progressBar) progressBar.style.width = percent + '%';
    if (progressPercent) progressPercent.textContent = percent + '%';

    const stageTexts = {
        'upload': '正在上传图片...',
        'ocr': '正在识别作业内容...',
        'parse': '正在解析作业项...',
        'vlm': '正在识别作业...'
    };
    if (progressText) progressText.textContent = stageTexts[stage] || '处理中...';
}

/**
 * 完成进度
 */
function completeProgress() {
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressText = document.getElementById('progressText');

    if (progressBar) progressBar.style.width = '100%';
    if (progressPercent) progressPercent.textContent = '100%';
    if (progressText) progressText.textContent = '识别完成';
}

// ==================== Toast 提示 ====================

// 保存当前的定时器 ID，用于清除之前的定时器
let toastTimer = null;

/**
 * 显示 Toast 提示
 * @param {string} message - 提示消息
 * @param {number} duration - 持续时间（毫秒）
 */
function showToast(message, duration = 2000) {
    const toast = document.getElementById('toast');
    if (toast) {
        // 清除之前的定时器
        if (toastTimer) {
            clearTimeout(toastTimer);
            toastTimer = null;
        }
        toast.textContent = message;
        toast.classList.remove('hidden');
        toastTimer = setTimeout(() => {
            toast.classList.add('hidden');
            toastTimer = null;
        }, duration);
    }
}

// 导出到全局
window.showToast = showToast;
