/**
 * common.js - 通用功能模块
 * 包含基础功能如导航处理、下拉菜单、工具提示和表格高亮等
 */

// 设置当前活动导航项
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link:not(.submenu-item):not(.submenu-toggle)');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== 'javascript:void(0)' && currentPath.includes(href)) {
            link.classList.add('active');
            
            // 如果是子菜单内的链接，展开父菜单
            const submenuToggle = link.closest('.collapse');
            if (submenuToggle) {
                const parentToggle = document.querySelector(`[data-bs-target="#${submenuToggle.id}"]`);
                if (parentToggle) {
                    parentToggle.classList.add('active');
                    new bootstrap.Collapse(submenuToggle).show();
                }
            }
        }
    });
    
    // 处理子菜单项的高亮
    const submenuItems = document.querySelectorAll('.submenu-item');
    submenuItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href && currentPath.includes(href)) {
            item.classList.add('active');
            // 确保父菜单已展开
            const submenu = item.closest('.collapse');
            if (submenu) {
                new bootstrap.Collapse(submenu).show();
                const parentToggle = document.querySelector(`[data-bs-target="#${submenu.id}"]`);
                if (parentToggle) {
                    parentToggle.classList.add('active');
                }
            }
        }
    });
}

// 初始化子菜单
function initializeSubmenus() {
    const submenuToggles = document.querySelectorAll('.submenu-toggle');
    
    submenuToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            // 切换指示器图标
            const indicator = this.querySelector('.submenu-indicator');
            if (indicator) {
                if (this.getAttribute('aria-expanded') === 'true') {
                    indicator.style.transform = 'rotate(0deg)';
                } else {
                    indicator.style.transform = 'rotate(180deg)';
                }
            }
        });
    });
}

// 初始化移动端侧边栏
function initializeMobileSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebarToggle && sidebar) {
        // 点击菜单按钮切换侧边栏
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            sidebarToggle.classList.toggle('active');
        });
        
        // 点击主内容区域关闭侧边栏
        mainContent.addEventListener('click', function() {
            if (sidebar.classList.contains('show') && window.innerWidth < 768) {
                sidebar.classList.remove('show');
                sidebarToggle.classList.remove('active');
            }
        });
        
        // 窗口调整大小时处理
        window.addEventListener('resize', function() {
            if (window.innerWidth >= 768) {
                sidebar.classList.remove('show');
                sidebarToggle.classList.remove('active');
            }
        });
    }
}

// 初始化下拉菜单
function initializeDropdowns() {
    const dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
}

// 初始化工具提示
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover'
        });
    });
}

// 初始化表格行高亮
function initializeTableHighlight() {
    const tableRows = document.querySelectorAll('table.table tbody tr');
    
    tableRows.forEach(row => {
        row.addEventListener('mouseover', function() {
            this.classList.add('bg-hover');
        });
        
        row.addEventListener('mouseout', function() {
            this.classList.remove('bg-hover');
        });
    });
}

// 获取CSRF Token
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 导出所有函数
export {
    setActiveNavItem,
    initializeSubmenus,
    initializeMobileSidebar,
    initializeDropdowns,
    initializeTooltips,
    initializeTableHighlight,
    getCsrfToken
}; 