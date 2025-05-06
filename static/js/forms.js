/**
 * forms.js - 表单处理模块
 * 提供表单验证、提交和处理功能
 */

// 导入所需函数
import { getCsrfToken } from './common.js';
import { showNotification } from './notifications.js';

/**
 * 表单验证器
 * 提供常用的表单字段验证方法
 */
const validators = {
    /**
     * 验证必填字段
     * @param {string} value - 待验证的值
     * @returns {boolean} 是否有效
     */
    required: function(value) {
        return value !== undefined && value !== null && value.trim() !== '';
    },
    
    /**
     * 验证最小长度
     * @param {string} value - 待验证的值
     * @param {number} length - 最小长度
     * @returns {boolean} 是否有效
     */
    minLength: function(value, length) {
        return value && value.length >= length;
    },
    
    /**
     * 验证最大长度
     * @param {string} value - 待验证的值
     * @param {number} length - 最大长度
     * @returns {boolean} 是否有效
     */
    maxLength: function(value, length) {
        return value && value.length <= length;
    },
    
    /**
     * 验证电子邮件格式
     * @param {string} value - 待验证的电子邮件
     * @returns {boolean} 是否有效
     */
    email: function(value) {
        const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return pattern.test(value);
    },
    
    /**
     * 验证身份证号
     * @param {string} value - 待验证的身份证号
     * @returns {boolean} 是否有效
     */
    idCard: function(value) {
        const pattern = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/;
        return pattern.test(value);
    },
    
    /**
     * 验证手机号码
     * @param {string} value - 待验证的手机号
     * @returns {boolean} 是否有效
     */
    phone: function(value) {
        const pattern = /^1[3-9]\d{9}$/;
        return pattern.test(value);
    },
    
    /**
     * 验证数字
     * @param {string} value - 待验证的数字
     * @returns {boolean} 是否有效
     */
    numeric: function(value) {
        return !isNaN(parseFloat(value)) && isFinite(value);
    },
    
    /**
     * 验证整数
     * @param {string} value - 待验证的整数
     * @returns {boolean} 是否有效
     */
    integer: function(value) {
        return /^-?\d+$/.test(value);
    },
    
    /**
     * 验证正整数
     * @param {string} value - 待验证的正整数
     * @returns {boolean} 是否有效
     */
    positiveInteger: function(value) {
        return /^\d+$/.test(value) && parseInt(value) > 0;
    },
    
    /**
     * 验证范围
     * @param {number} value - 待验证的数值
     * @param {number} min - 最小值
     * @param {number} max - 最大值
     * @returns {boolean} 是否有效
     */
    range: function(value, min, max) {
        const num = parseFloat(value);
        return !isNaN(num) && num >= min && num <= max;
    },
    
    /**
     * 验证日期
     * @param {string} value - 待验证的日期字符串
     * @returns {boolean} 是否有效
     */
    date: function(value) {
        const date = new Date(value);
        return !isNaN(date.getTime());
    }
};

/**
 * 初始化表单验证
 * @param {string} formId - 表单ID
 * @param {Object} rules - 验证规则
 * @param {Object} messages - 错误消息
 * @param {Function} submitCallback - 提交回调函数
 */
function initializeFormValidation(formId, rules, messages = {}, submitCallback = null) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    // 表单提交事件
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 执行验证
        const errors = validateForm(form, rules, messages);
        
        // 如果有错误，显示错误消息
        if (Object.keys(errors).length > 0) {
            // 显示第一个错误
            const firstField = Object.keys(errors)[0];
            const firstError = errors[firstField];
            showNotification('error', '表单验证失败', firstError);
            
            // 为错误字段添加错误样式
            Object.keys(errors).forEach(field => {
                const input = form.querySelector(`[name="${field}"]`);
                if (input) {
                    input.classList.add('is-invalid');
                    
                    // 添加错误消息
                    let feedbackElement = input.nextElementSibling;
                    if (!feedbackElement || !feedbackElement.classList.contains('invalid-feedback')) {
                        feedbackElement = document.createElement('div');
                        feedbackElement.className = 'invalid-feedback';
                        input.parentNode.insertBefore(feedbackElement, input.nextSibling);
                    }
                    feedbackElement.textContent = errors[field];
                }
            });
            
            // 焦点到第一个错误字段
            const firstInput = form.querySelector(`[name="${Object.keys(errors)[0]}"]`);
            if (firstInput) {
                firstInput.focus();
            }
            
            return;
        }
        
        // 验证通过，处理提交
        if (submitCallback) {
            submitCallback(form);
        } else {
            // 默认提交行为
            form.submit();
        }
    });
    
    // 添加输入事件监听，清除错误状态
    form.querySelectorAll('input, select, textarea').forEach(input => {
        input.addEventListener('input', function() {
            this.classList.remove('is-invalid');
            const feedbackElement = this.nextElementSibling;
            if (feedbackElement && feedbackElement.classList.contains('invalid-feedback')) {
                feedbackElement.textContent = '';
            }
        });
    });
    
    /**
     * 验证表单
     * @param {HTMLFormElement} form - 表单元素
     * @param {Object} rules - 验证规则
     * @param {Object} messages - 错误消息
     * @returns {Object} 错误消息对象
     */
    function validateForm(form, rules, messages) {
        const errors = {};
        const formData = new FormData(form);
        
        for (const field in rules) {
            const value = formData.get(field);
            const fieldRules = rules[field];
            
            // 处理单个规则
            if (typeof fieldRules === 'string') {
                if (!validateField(value, fieldRules)) {
                    errors[field] = messages[field] || `${field}字段验证失败`;
                }
                continue;
            }
            
            // 处理多个规则
            for (const rule in fieldRules) {
                const ruleValue = fieldRules[rule];
                
                // 处理简单规则 (如 required: true)
                if (typeof ruleValue === 'boolean' && ruleValue) {
                    if (!validators[rule](value)) {
                        errors[field] = messages[field]?.[rule] || `${field}字段验证失败`;
                        break;
                    }
                } 
                // 处理带参数的规则 (如 minLength: 5)
                else if (typeof ruleValue !== 'boolean') {
                    if (!validators[rule](value, ruleValue)) {
                        errors[field] = messages[field]?.[rule] || `${field}字段验证失败`;
                        break;
                    }
                }
            }
        }
        
        return errors;
    }
    
    /**
     * 验证单个字段
     * @param {string} value - 字段值
     * @param {string} rule - 验证规则
     * @returns {boolean} 是否有效
     */
    function validateField(value, rule) {
        if (validators[rule]) {
            return validators[rule](value);
        }
        return true;
    }
}

/**
 * 异步提交表单
 * @param {string} formId - 表单ID
 * @param {string} url - 提交URL
 * @param {Object} options - 配置选项
 */
function submitFormAsync(formId, url, options = {}) {
    const defaultOptions = {
        method: 'POST',
        successMessage: '提交成功',
        errorMessage: '提交失败',
        beforeSubmit: null,
        onSuccess: null,
        onError: null,
        redirect: null
    };
    
    const config = {...defaultOptions, ...options};
    const form = document.getElementById(formId);
    
    if (!form) return;
    
    // 创建FormData对象
    const formData = new FormData(form);
    
    // 前置处理
    if (config.beforeSubmit) {
        const shouldContinue = config.beforeSubmit(formData);
        if (shouldContinue === false) {
            return;
        }
    }
    
    // 显示加载状态
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 提交中...';
    }
    
    // 发送请求
    fetch(url, {
        method: config.method,
        body: formData,
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(response.statusText);
        }
        return response.json();
    })
    .then(data => {
        // 显示成功消息
        showNotification('success', '成功', config.successMessage);
        
        // 成功回调
        if (config.onSuccess) {
            config.onSuccess(data);
        }
        
        // 如果需要重定向
        if (config.redirect) {
            setTimeout(() => {
                window.location.href = typeof config.redirect === 'function' ? 
                    config.redirect(data) : config.redirect;
            }, 1000);
        }
    })
    .catch(error => {
        // 显示错误消息
        showNotification('error', '错误', config.errorMessage);
        
        // 错误回调
        if (config.onError) {
            config.onError(error);
        }
    })
    .finally(() => {
        // 恢复按钮状态
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    });
}

// 导出所有函数和对象
export {
    validators,
    initializeFormValidation,
    submitFormAsync
}; 