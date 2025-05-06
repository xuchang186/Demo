/**
 * upload.js - 文件上传模块
 * 处理图像上传和预览功能
 */

// 从其他模块导入所需函数
import { getCsrfToken } from './common.js';
import { showNotification } from './notifications.js';

/**
 * 初始化图片上传功能
 * 设置拖拽上传、文件选择和预览等功能
 */
function initializeImageUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('imageUpload');
    const previewContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');
    const uploadButton = document.getElementById('uploadButton');
    const fileName = document.getElementById('file-name');
    
    if (!uploadArea || !fileInput) return;
    
    // 点击上传区域触发文件选择
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('border-primary');
    });
    
    uploadArea.addEventListener('dragleave', function() {
        this.classList.remove('border-primary');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('border-primary');
        
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
    
    // 文件选择处理
    fileInput.addEventListener('change', function() {
        if (this.files.length) {
            handleFileSelect(this.files[0]);
        }
    });
    
    // 上传按钮点击
    if (uploadButton) {
        uploadButton.addEventListener('click', function() {
            if (fileInput.files.length) {
                uploadFile(fileInput.files[0]);
            } else {
                showNotification('warning', '请选择文件', '请先选择要上传的图像文件');
            }
        });
    }
    
    /**
     * 处理文件选择
     * @param {File} file - 选中的文件对象
     */
    function handleFileSelect(file) {
        // 检查文件类型
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/dicom'];
        if (!allowedTypes.includes(file.type) && !file.name.endsWith('.dcm')) {
            showNotification('error', '文件类型错误', '请选择PNG、JPEG或DICOM格式的图像文件');
            return;
        }
        
        // 显示文件名
        if (fileName) {
            fileName.textContent = file.name;
            fileName.classList.remove('d-none');
        }
        
        // 显示预览（仅对常规图像格式）
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                if (previewContainer && previewImage) {
                    previewContainer.classList.remove('d-none');
                    previewImage.src = e.target.result;
                    
                    // 显示上传按钮
                    if (uploadButton) {
                        uploadButton.classList.remove('d-none');
                    }
                }
            };
            reader.readAsDataURL(file);
        } else {
            // DICOM文件不显示预览，但显示上传按钮
            if (previewContainer) {
                previewContainer.classList.add('d-none');
            }
            if (uploadButton) {
                uploadButton.classList.remove('d-none');
            }
        }
    }
    
    /**
     * 上传文件
     * @param {File} file - 要上传的文件
     * @param {string} url - 上传URL，默认为肺炎诊断上传地址
     */
    function uploadFile(file, url = '/diagnosis/api/upload-ct/') {
        // 创建FormData
        const formData = new FormData();
        formData.append('image_file', file);
        
        // 显示上传中提示
        showNotification('info', '上传中', '正在上传图像，请稍候...');
        
        // 设置上传按钮为禁用状态
        if (uploadButton) {
            uploadButton.disabled = true;
            uploadButton.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> 上传中...';
        }
        
        // 使用fetch API上传文件
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('上传失败');
            }
            return response.json();
        })
        .then(data => {
            // 上传成功处理
            showNotification('success', '上传成功', '图像已成功上传，即将进行分析');
            
            // 重定向到结果页面
            if (data.diagnosis_id) {
                setTimeout(() => {
                    window.location.href = `/diagnosis/result/${data.diagnosis_id}/`;
                }, 1500);
            } else if (data.redirect_url) {
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 1500);
            }
        })
        .catch(error => {
            // 上传失败处理
            showNotification('error', '上传失败', error.message || '图像上传过程中出现错误，请重试');
            
            // 恢复上传按钮状态
            if (uploadButton) {
                uploadButton.disabled = false;
                uploadButton.innerHTML = '<i class="bi bi-cloud-upload me-1"></i> 开始上传';
            }
        });
    }
}

/**
 * 初始化文档上传功能
 * 用于附件、医疗报告等文档上传
 * @param {Object} options - 上传配置项
 */
function initializeDocumentUpload(options = {}) {
    const defaultOptions = {
        uploadAreaId: 'documentUploadArea',
        fileInputId: 'documentFileInput',
        fileListId: 'documentFileList',
        uploadButtonId: 'documentUploadButton',
        uploadUrl: '/patient-records/api/upload-document/',
        allowedTypes: ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt'],
        maxFileSize: 10 * 1024 * 1024, // 10MB
        maxFiles: 5
    };
    
    const config = {...defaultOptions, ...options};
    
    const uploadArea = document.getElementById(config.uploadAreaId);
    const fileInput = document.getElementById(config.fileInputId);
    const fileList = document.getElementById(config.fileListId);
    const uploadButton = document.getElementById(config.uploadButtonId);
    
    if (!uploadArea || !fileInput) return;
    
    // 已选文件列表
    let selectedFiles = [];
    
    // 点击上传区域触发文件选择
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('border-primary');
    });
    
    uploadArea.addEventListener('dragleave', function() {
        this.classList.remove('border-primary');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('border-primary');
        
        if (e.dataTransfer.files.length) {
            handleFilesSelect(Array.from(e.dataTransfer.files));
        }
    });
    
    // 文件选择处理
    fileInput.addEventListener('change', function() {
        if (this.files.length) {
            handleFilesSelect(Array.from(this.files));
            // 清空文件输入框，允许重复选择相同文件
            this.value = '';
        }
    });
    
    // 上传按钮点击
    if (uploadButton) {
        uploadButton.addEventListener('click', function() {
            if (selectedFiles.length > 0) {
                uploadFiles();
            } else {
                showNotification('warning', '请选择文件', '请先选择要上传的文件');
            }
        });
    }
    
    /**
     * 处理多文件选择
     * @param {Array} files - 选中的文件数组
     */
    function handleFilesSelect(files) {
        // 检查文件数量限制
        if (selectedFiles.length + files.length > config.maxFiles) {
            showNotification('warning', '文件数量超限', `最多只能上传${config.maxFiles}个文件`);
            return;
        }
        
        // 验证并添加文件
        for (const file of files) {
            // 检查文件大小
            if (file.size > config.maxFileSize) {
                showNotification('error', '文件过大', `文件"${file.name}"超过最大限制(${config.maxFileSize/1024/1024}MB)`);
                continue;
            }
            
            // 检查文件类型
            const fileExt = '.' + file.name.split('.').pop().toLowerCase();
            if (!config.allowedTypes.includes(fileExt) && !config.allowedTypes.includes('*')) {
                showNotification('error', '文件类型不支持', `文件"${file.name}"类型不被支持`);
                continue;
            }
            
            // 添加到已选文件列表
            selectedFiles.push(file);
            
            // 更新UI
            updateFileList();
        }
        
        // 显示上传按钮
        if (uploadButton && selectedFiles.length > 0) {
            uploadButton.classList.remove('d-none');
        }
    }
    
    /**
     * 更新文件列表UI
     */
    function updateFileList() {
        if (!fileList) return;
        
        fileList.innerHTML = '';
        
        selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item d-flex align-items-center p-2 mb-2 border rounded';
            
            // 设置文件图标
            let fileIcon = 'bi-file-earmark';
            const fileExt = file.name.split('.').pop().toLowerCase();
            if (['pdf'].includes(fileExt)) fileIcon = 'bi-file-earmark-pdf';
            else if (['doc', 'docx'].includes(fileExt)) fileIcon = 'bi-file-earmark-word';
            else if (['xls', 'xlsx'].includes(fileExt)) fileIcon = 'bi-file-earmark-excel';
            else if (['txt'].includes(fileExt)) fileIcon = 'bi-file-earmark-text';
            
            fileItem.innerHTML = `
                <i class="bi ${fileIcon} me-2 text-primary"></i>
                <div class="flex-grow-1">
                    <div class="fw-medium">${file.name}</div>
                    <div class="small text-muted">${formatFileSize(file.size)}</div>
                </div>
                <button type="button" class="btn btn-sm btn-outline-danger remove-file" data-index="${index}">
                    <i class="bi bi-x"></i>
                </button>
            `;
            
            fileList.appendChild(fileItem);
            
            // 绑定删除按钮事件
            const removeBtn = fileItem.querySelector('.remove-file');
            removeBtn.addEventListener('click', function() {
                const fileIndex = parseInt(this.getAttribute('data-index'));
                selectedFiles.splice(fileIndex, 1);
                updateFileList();
                
                // 如果没有文件了，隐藏上传按钮
                if (uploadButton && selectedFiles.length === 0) {
                    uploadButton.classList.add('d-none');
                }
            });
        });
    }
    
    /**
     * 格式化文件大小
     * @param {number} bytes - 文件大小（字节数）
     * @returns {string} 格式化后的文件大小
     */
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        else if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
        else return (bytes / 1024 / 1024).toFixed(2) + ' MB';
    }
    
    /**
     * 上传所有已选文件
     */
    function uploadFiles() {
        // 创建FormData
        const formData = new FormData();
        
        // 添加所有文件
        selectedFiles.forEach((file, index) => {
            formData.append(`file_${index}`, file);
        });
        
        // 添加文件数量
        formData.append('file_count', selectedFiles.length);
        
        // 显示上传中提示
        showNotification('info', '上传中', '正在上传文件，请稍候...');
        
        // 设置上传按钮为禁用状态
        if (uploadButton) {
            uploadButton.disabled = true;
            uploadButton.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> 上传中...';
        }
        
        // 使用fetch API上传文件
        fetch(config.uploadUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('上传失败');
            }
            return response.json();
        })
        .then(data => {
            // 上传成功处理
            showNotification('success', '上传成功', `已成功上传${selectedFiles.length}个文件`);
            
            // 清空已选文件
            selectedFiles = [];
            updateFileList();
            
            // 隐藏上传按钮
            if (uploadButton) {
                uploadButton.classList.add('d-none');
            }
            
            // 如果有回调或重定向
            if (data.redirect_url) {
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 1500);
            } else if (config.onUploadSuccess) {
                config.onUploadSuccess(data);
            }
        })
        .catch(error => {
            // 上传失败处理
            showNotification('error', '上传失败', error.message || '文件上传过程中出现错误，请重试');
            
            // 恢复上传按钮状态
            if (uploadButton) {
                uploadButton.disabled = false;
                uploadButton.innerHTML = '<i class="bi bi-cloud-upload me-1"></i> 开始上传';
            }
        });
    }
}

// 导出所有函数
export {
    initializeImageUpload,
    initializeDocumentUpload
}; 