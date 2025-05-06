/**
 * main.js - 主JavaScript文件
 * 导入所需模块并进行初始化
 */

// 导入所需模块
import * as Common from './common.js';
import * as Notifications from './notifications.js';
import * as Modal from './modal.js';
import * as Upload from './upload.js';
import * as Forms from './forms.js';

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化导航和UI组件
    Common.setActiveNavItem();
    Common.initializeMobileSidebar();
    Common.initializeDropdowns();
    Common.initializeTooltips();
    Common.initializeTableHighlight();
    Common.initializeSubmenus();
    
    // 初始化图片上传（如果页面有相关元素）
    if (document.getElementById('uploadArea')) {
        Upload.initializeImageUpload();
    }
    
    // 初始化文档上传（如果页面有相关元素）
    if (document.getElementById('documentUploadArea')) {
        Upload.initializeDocumentUpload();
    }
    
    // 处理用户退出确认
    const logoutLink = document.querySelector('a[href*="logout"]');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            Modal.confirmAction(
                '确认退出', 
                '您确定要退出系统吗？',
                function() {
                    window.location.href = logoutLink.href;
                }
            );
        });
    }
});

// 导出全局工具函数到window对象，便于HTML内联脚本调用
window.app = {
    // 通知函数
    showNotification: Notifications.showNotification,
    showSuccessNotification: Notifications.showSuccessNotification,
    showWarningNotification: Notifications.showWarningNotification,
    showErrorNotification: Notifications.showErrorNotification,
    showInfoNotification: Notifications.showInfoNotification,
    
    // 模态框和确认对话框
    confirmAction: Modal.confirmAction,
    createModal: Modal.createModal,
    
    // 表单处理函数
    validateForm: Forms.initializeFormValidation,
    submitFormAsync: Forms.submitFormAsync,
    validators: Forms.validators
};