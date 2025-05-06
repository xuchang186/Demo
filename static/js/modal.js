/**
 * modal.js - 模态框和确认对话框模块
 * 提供模态框和确认对话框功能
 */

/**
 * 显示确认对话框
 * @param {string} title - 对话框标题
 * @param {string} message - 对话框消息
 * @param {Function} confirmCallback - 确认回调函数
 * @param {Function} cancelCallback - 取消回调函数
 */
function confirmAction(title, message, confirmCallback, cancelCallback) {
    // 检查是否已经存在模态框
    let modal = document.getElementById('confirmActionModal');
    
    // 如果不存在，创建一个
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'confirmActionModal';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-hidden', 'true');
        
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"></h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-danger confirm-btn">确认</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    // 设置标题和消息
    modal.querySelector('.modal-title').textContent = title;
    modal.querySelector('.modal-body p').textContent = message;
    
    // 获取Bootstrap模态框实例
    const modalInstance = new bootstrap.Modal(modal);
    
    // 绑定确认按钮事件
    const confirmBtn = modal.querySelector('.confirm-btn');
    
    // 移除旧的事件监听器
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    // 添加新的事件监听器
    newConfirmBtn.addEventListener('click', function() {
        if (typeof confirmCallback === 'function') {
            confirmCallback();
        }
        modalInstance.hide();
    });
    
    // 绑定取消按钮事件
    modal.addEventListener('hidden.bs.modal', function() {
        if (typeof cancelCallback === 'function') {
            cancelCallback();
        }
    });
    
    // 显示模态框
    modalInstance.show();
}

/**
 * 创建自定义模态框
 * @param {string} id - 模态框ID
 * @param {string} title - 模态框标题
 * @param {string} content - 模态框内容
 * @param {Object} options - 可选配置
 * @param {string} options.size - 模态框大小：'sm', 'lg', 'xl'
 * @param {boolean} options.closeButton - 是否显示关闭按钮
 * @param {boolean} options.backdrop - 是否显示背景遮罩
 * @param {boolean} options.keyboard - 是否允许键盘关闭
 * @param {Array} options.buttons - 底部按钮配置
 * @returns {Object} 包含模态框元素和实例的对象
 */
function createModal(id, title, content, options = {}) {
    const defaultOptions = {
        size: '',
        closeButton: true,
        backdrop: true,
        keyboard: true,
        buttons: []
    };
    
    const mergedOptions = {...defaultOptions, ...options};
    
    // 检查是否已存在该ID的模态框
    let modal = document.getElementById(id);
    if (modal) {
        document.body.removeChild(modal);
    }
    
    // 创建模态框元素
    modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = id;
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-hidden', 'true');
    
    // 设置模态框大小
    let dialogClass = 'modal-dialog';
    if (mergedOptions.size) {
        dialogClass += ` modal-${mergedOptions.size}`;
    }
    
    // 准备底部按钮HTML
    let footerHTML = '';
    if (mergedOptions.buttons && mergedOptions.buttons.length > 0) {
        const buttonsHTML = mergedOptions.buttons.map(button => {
            return `<button type="button" class="btn ${button.class || 'btn-secondary'}" id="${button.id || ''}" ${button.dismiss ? 'data-bs-dismiss="modal"' : ''}>${button.text}</button>`;
        }).join('');
        
        footerHTML = `<div class="modal-footer">${buttonsHTML}</div>`;
    }
    
    // 设置模态框内容
    modal.innerHTML = `
        <div class="${dialogClass}">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    ${mergedOptions.closeButton ? '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>' : ''}
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                ${footerHTML}
            </div>
        </div>
    `;
    
    // 添加到文档
    document.body.appendChild(modal);
    
    // 创建Bootstrap模态框实例
    const modalInstance = new bootstrap.Modal(modal, {
        backdrop: mergedOptions.backdrop,
        keyboard: mergedOptions.keyboard
    });
    
    // 绑定按钮事件
    if (mergedOptions.buttons && mergedOptions.buttons.length > 0) {
        mergedOptions.buttons.forEach(button => {
            if (button.id && button.callback) {
                const buttonElement = modal.querySelector(`#${button.id}`);
                if (buttonElement) {
                    buttonElement.addEventListener('click', button.callback);
                }
            }
        });
    }
    
    return {
        element: modal,
        instance: modalInstance,
        show: () => modalInstance.show(),
        hide: () => modalInstance.hide(),
        toggle: () => modalInstance.toggle()
    };
}

// 导出所有函数
export {
    confirmAction,
    createModal
}; 