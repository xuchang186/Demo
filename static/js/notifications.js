/**
 * notifications.js - 通知系统模块
 * 提供通知功能，用于显示成功、警告、错误和信息类型的消息
 */

/**
 * 显示通知消息
 * @param {string} type - 通知类型: 'success', 'warning', 'error', 'info'
 * @param {string} title - 通知标题
 * @param {string} message - 通知详细信息
 * @param {number} duration - 显示时长(毫秒)，设为0则不自动消失
 * @returns {HTMLElement} 通知元素
 */
function showNotification(type, title, message, duration = 3000) {
    // 移除所有已有通知
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
        notification.remove();
    });
    
    // 创建新通知
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // 根据类型设置图标
    let icon = '';
    switch(type) {
        case 'success':
            icon = 'bi-check-circle';
            break;
        case 'warning':
            icon = 'bi-exclamation-triangle';
            break;
        case 'error':
            icon = 'bi-x-circle';
            break;
        case 'info':
        default:
            icon = 'bi-info-circle';
            break;
    }
    
    // 设置通知内容
    notification.innerHTML = `
        <i class="bi ${icon}"></i>
        <div>
            <h6 class="mb-0">${title}</h6>
            <p class="mb-0 small">${message}</p>
        </div>
        <button class="close-btn"><i class="bi bi-x"></i></button>
    `;
    
    // 添加到文档
    document.body.appendChild(notification);
    
    // 添加关闭事件
    const closeBtn = notification.querySelector('.close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            notification.remove();
        });
    }
    
    // 自动关闭
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.add('fade-out');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, duration);
    }
    
    return notification;
}

/**
 * 显示成功通知
 * @param {string} title - 通知标题
 * @param {string} message - 通知详细信息
 * @param {number} duration - 显示时长(毫秒)
 * @returns {HTMLElement} 通知元素
 */
function showSuccessNotification(title, message, duration = 3000) {
    return showNotification('success', title, message, duration);
}

/**
 * 显示警告通知
 * @param {string} title - 通知标题
 * @param {string} message - 通知详细信息
 * @param {number} duration - 显示时长(毫秒)
 * @returns {HTMLElement} 通知元素
 */
function showWarningNotification(title, message, duration = 3000) {
    return showNotification('warning', title, message, duration);
}

/**
 * 显示错误通知
 * @param {string} title - 通知标题
 * @param {string} message - 通知详细信息
 * @param {number} duration - 显示时长(毫秒)
 * @returns {HTMLElement} 通知元素
 */
function showErrorNotification(title, message, duration = 3000) {
    return showNotification('error', title, message, duration);
}

/**
 * 显示信息通知
 * @param {string} title - 通知标题
 * @param {string} message - 通知详细信息
 * @param {number} duration - 显示时长(毫秒)
 * @returns {HTMLElement} 通知元素
 */
function showInfoNotification(title, message, duration = 3000) {
    return showNotification('info', title, message, duration);
}

// 导出所有函数
export {
    showNotification,
    showSuccessNotification,
    showWarningNotification,
    showErrorNotification,
    showInfoNotification
}; 