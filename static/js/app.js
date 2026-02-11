// 全局变量
let trendChart = null;
let typeChart = null;
let currentPage = 1;

// 隐藏页面加载动画
function hidePageLoader() {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.style.opacity = '0';
        loader.style.transition = 'opacity 0.5s ease';
        setTimeout(() => {
            loader.style.display = 'none';
        }, 500);
    }
}

// 超时保护：5秒后强制显示页面
setTimeout(function() {
    hidePageLoader();
}, 5000);

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 隐藏加载动画
    hidePageLoader();
    
    // 导航切换
    setupNavigation();
    
    // 默认加载错误日志页面
    loadErrors();
    // 设置错误日志导航为激活状态
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelector('[data-page="errors"]').classList.add('active');
    
    // 设置定时刷新错误日志
    setInterval(loadErrors, 30000); // 每30秒刷新
    
    // 设置事件监听器
    setupEventListeners();
});

// 确保页面完全加载后隐藏加载动画
window.addEventListener('load', function() {
    hidePageLoader();
});

// 导航切换
function setupNavigation() {
    document.querySelectorAll('[data-page]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            switchPage(page);
            
            // 更新导航状态
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// 页面切换
function switchPage(page) {
    // 隐藏所有页面
    document.querySelectorAll('.page-content').forEach(p => p.style.display = 'none');
    
    // 显示目标页面
    document.getElementById(`${page}-page`).style.display = 'block';
    
    // 加载对应页面数据
    switch(page) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'errors':
            loadErrors();
            break;
        case 'containers':
            loadContainers();
            break;
        case 'config':
            loadConfig();
            break;
    }
}

// 加载仪表盘
async function loadDashboard() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        // 更新统计卡片
        document.getElementById('total-errors').textContent = data.total_errors;
        document.getElementById('today-errors').textContent = data.today_errors;
        document.getElementById('unresolved-errors').textContent = data.unresolved;
        document.getElementById('critical-errors').textContent = data.critical_errors;
        
        // 更新趋势图
        updateTrendChart(data.daily_trend);
        
        // 更新类型分布图
        updateTypeChart(data.error_types);
        
        // 加载最近错误
        loadRecentErrors();
    } catch (error) {
        console.error('加载仪表盘数据失败:', error);
        showToast('加载数据失败', 'error');
    }
}

// 更新趋势图
function updateTrendChart(data) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    if (trendChart) {
        trendChart.destroy();
    }
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                label: '错误数量',
                data: data.map(d => d.count),
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// 更新类型分布图
function updateTypeChart(data) {
    const ctx = document.getElementById('typeChart').getContext('2d');
    
    if (typeChart) {
        typeChart.destroy();
    }
    
    // 限制显示前5个
    const topData = data.slice(0, 5);
    
    typeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: topData.map(d => d.type),
            datasets: [{
                data: topData.map(d => d.count),
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(153, 102, 255, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// 加载最近错误
async function loadRecentErrors() {
    try {
        const response = await fetch('/api/errors?per_page=5');
        const data = await response.json();
        
        const container = document.getElementById('recent-errors');
        
        if (data.errors.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">暂无错误记录</p>';
            return;
        }
        
        let html = '<table class="table table-hover"><thead><tr>' +
                   '<th>时间</th><th>容器</th><th>错误信息</th><th>严重度</th><th>状态</th>' +
                   '</tr></thead><tbody>';
        
        data.errors.forEach(error => {
            html += `<tr onclick="showErrorDetail(${error.id})" style="cursor: pointer;">
                <td>${formatDateTime(error.timestamp)}</td>
                <td><span class="badge bg-secondary">${error.container_name}</span></td>
                <td>${truncate(error.error_message, 80)}</td>
                <td><span class="badge bg-${getSeverityColor(error.severity)}">${error.severity || 'N/A'}</span></td>
                <td><span class="badge status-${error.status}">${getStatusText(error.status)}</span></td>
            </tr>`;
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        console.error('加载最近错误失败:', error);
    }
}

// 加载错误列表
async function loadErrors(page = 1) {
    try {
        const search = document.getElementById('search-input')?.value || '';
        const status = document.getElementById('status-filter')?.value || '';
        const severity = document.getElementById('severity-filter')?.value || '';
        const container = document.getElementById('container-filter')?.value || '';
        
        const params = new URLSearchParams({
            page: page,
            per_page: 20,
            search: search,
            status: status,
            severity: severity,
            container: container
        });
        
        const response = await fetch(`/api/errors?${params}`);
        const data = await response.json();
        
        displayErrors(data.errors);
        displayPagination(data.pages, page);
        currentPage = page;
        
        // 加载容器列表到过滤器
        if (page === 1) {
            loadContainerFilter();
        }
    } catch (error) {
        console.error('加载错误列表失败:', error);
        showToast('加载错误列表失败', 'error');
    }
}

// 显示错误列表
function displayErrors(errors) {
    const container = document.getElementById('errors-list');
    
    if (errors.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-inbox"></i>
                <h4>暂无错误记录</h4>
                <p>没有找到匹配的错误记录</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    errors.forEach(error => {
        html += `
            <div class="error-item severity-${error.severity || 'error'} fade-in" onclick="showErrorDetail(${error.id})">
                <div class="error-header">
                    <h5 class="error-title">${error.container_name}</h5>
                    <span class="badge status-${error.status}">${getStatusText(error.status)}</span>
                </div>
                <div class="error-meta">
                    <span><i class="bi bi-clock"></i> ${formatDateTime(error.timestamp)}</span>
                    <span><i class="bi bi-tag"></i> ${error.error_type || 'Unknown'}</span>
                    <span><i class="bi bi-exclamation-circle"></i> ${error.severity || 'error'}</span>
                </div>
                <div class="error-message">${truncate(error.error_message, 200)}</div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// 显示分页
function displayPagination(totalPages, currentPage) {
    const container = document.getElementById('pagination-container');
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '<ul class="pagination justify-content-center">';
    
    // 上一页
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadErrors(${currentPage - 1}); return false;">上一页</a>
    </li>`;
    
    // 页码
    for (let i = 1; i <= Math.min(totalPages, 10); i++) {
        html += `<li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="#" onclick="loadErrors(${i}); return false;">${i}</a>
        </li>`;
    }
    
    // 下一页
    html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadErrors(${currentPage + 1}); return false;">下一页</a>
    </li>`;
    
    html += '</ul>';
    container.innerHTML = html;
}

// 显示错误详情
async function showErrorDetail(errorId) {
    try {
        const response = await fetch(`/api/errors/${errorId}`);
        const error = await response.json();
        
        let html = `
            <div class="mb-3">
                <h6 class="text-muted">基本信息</h6>
                <table class="table table-sm">
                    <tr><td><strong>容器:</strong></td><td>${error.container_name}</td></tr>
                    <tr><td><strong>时间:</strong></td><td>${formatDateTime(error.timestamp)}</td></tr>
                    <tr><td><strong>错误类型:</strong></td><td>${error.error_type || 'Unknown'}</td></tr>
                    <tr><td><strong>严重度:</strong></td><td><span class="badge bg-${getSeverityColor(error.severity)}">${error.severity || 'error'}</span></td></tr>
                    <tr><td><strong>状态:</strong></td><td>
                        <select class="form-select form-select-sm" onchange="updateErrorStatus(${error.id}, this.value)">
                            <option value="new" ${error.status === 'new' ? 'selected' : ''}>新错误</option>
                            <option value="investigating" ${error.status === 'investigating' ? 'selected' : ''}>调查中</option>
                            <option value="resolved" ${error.status === 'resolved' ? 'selected' : ''}>已解决</option>
                        </select>
                    </td></tr>
                </table>
            </div>
            
            <div class="mb-3">
                <h6 class="text-muted">错误信息</h6>
                <div class="log-content">${error.error_message}</div>
            </div>
        `;
        
        if (error.log_content) {
            html += `
                <div class="mb-3">
                    <h6 class="text-muted">完整日志</h6>
                    <div class="log-content">${escapeHtml(error.log_content)}</div>
                </div>
            `;
        }
        
        if (error.ai_analysis) {
            html += `
                <div class="ai-analysis">
                    <h6><i class="bi bi-robot"></i> AI 分析</h6>
                    <p>${error.ai_analysis}</p>
                </div>
            `;
        }
        
        if (error.ai_solution) {
            html += `
                <div class="ai-solution">
                    <h6><i class="bi bi-lightbulb"></i> 解决方案</h6>
                    <p>${error.ai_solution}</p>
                </div>
            `;
        }
        
        document.getElementById('error-detail-content').innerHTML = html;
        
        const modal = new bootstrap.Modal(document.getElementById('errorDetailModal'));
        modal.show();
    } catch (error) {
        console.error('加载错误详情失败:', error);
        showToast('加载错误详情失败', 'error');
    }
}

// 更新错误状态
async function updateErrorStatus(errorId, status) {
    try {
        const response = await fetch(`/api/errors/${errorId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: status })
        });
        
        if (response.ok) {
            showToast('状态已更新', 'success');
            loadErrors(currentPage);
        }
    } catch (error) {
        console.error('更新状态失败:', error);
        showToast('更新状态失败', 'error');
    }
}

// 加载容器列表
async function loadContainers() {
    try {
        const response = await fetch('/api/containers');
        const data = await response.json();
        
        const container = document.getElementById('containers-list');
        
        if (data.containers.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-box"></i>
                    <h4>暂无容器</h4>
                    <p>没有找到运行中的Docker容器</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        data.containers.forEach(c => {
            html += `
                <div class="container-item status-${c.status} fade-in">
                    <div class="container-info">
                        <div class="container-name">${c.name}</div>
                        <div class="container-meta">
                            <span><i class="bi bi-hash"></i> ${c.id}</span> | 
                            <span><i class="bi bi-image"></i> ${c.image}</span> | 
                            <span><i class="bi bi-circle-fill text-${getStatusColor(c.status)}"></i> ${c.status}</span>
                        </div>
                    </div>
                    <div class="container-actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="viewContainerLogs('${c.id}')">
                            <i class="bi bi-file-text"></i> 查看日志
                        </button>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    } catch (error) {
        console.error('加载容器列表失败:', error);
        showToast('加载容器列表失败', 'error');
    }
}

// 查看容器日志
async function viewContainerLogs(containerId) {
    try {
        const response = await fetch(`/api/containers/${containerId}/logs`);
        const data = await response.json();
        
        const content = `
            <div class="log-content">${escapeHtml(data.logs)}</div>
        `;
        
        document.getElementById('error-detail-content').innerHTML = content;
        
        const modal = new bootstrap.Modal(document.getElementById('errorDetailModal'));
        document.querySelector('#errorDetailModal .modal-title').textContent = '容器日志';
        modal.show();
    } catch (error) {
        console.error('加载容器日志失败:', error);
        showToast('加载容器日志失败', 'error');
    }
}

// 加载配置
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        
        // 将配置转换为YAML字符串显示
        document.getElementById('config-editor').value = JSON.stringify(data.config, null, 2);
    } catch (error) {
        console.error('加载配置失败:', error);
        showToast('加载配置失败', 'error');
    }
}

// 保存配置
async function saveConfig() {
    try {
        const configText = document.getElementById('config-editor').value;
        const config = JSON.parse(configText);
        
        const response = await fetch('/api/config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ config: config })
        });
        
        if (response.ok) {
            showToast('配置已保存', 'success');
        } else {
            throw new Error('保存失败');
        }
    } catch (error) {
        console.error('保存配置失败:', error);
        showToast('保存配置失败，请检查格式', 'error');
    }
}

// 加载容器过滤器选项
async function loadContainerFilter() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        const select = document.getElementById('container-filter');
        let options = '<option value="">所有容器</option>';
        
        data.containers.forEach(c => {
            options += `<option value="${c.name}">${c.name} (${c.count})</option>`;
        });
        
        select.innerHTML = options;
    } catch (error) {
        console.error('加载容器过滤器失败:', error);
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 过滤器应用按钮
    const applyFiltersBtn = document.getElementById('apply-filters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', () => loadErrors(1));
    }
    
    // 保存配置按钮
    const saveConfigBtn = document.getElementById('save-config');
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', saveConfig);
    }
    
    // 重新加载配置按钮
    const reloadConfigBtn = document.getElementById('reload-config');
    if (reloadConfigBtn) {
        reloadConfigBtn.addEventListener('click', loadConfig);
    }
    
    // 搜索框回车
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                loadErrors(1);
            }
        });
    }
}

// 工具函数
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

function truncate(str, length) {
    if (!str) return '';
    return str.length > length ? str.substring(0, length) + '...' : str;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getSeverityColor(severity) {
    const colors = {
        'critical': 'danger',
        'error': 'warning',
        'warning': 'info'
    };
    return colors[severity] || 'secondary';
}

function getStatusColor(status) {
    const colors = {
        'running': 'success',
        'exited': 'danger',
        'paused': 'warning',
        'created': 'info'
    };
    return colors[status] || 'secondary';
}

function getStatusText(status) {
    const texts = {
        'new': '新错误',
        'investigating': '调查中',
        'resolved': '已解决'
    };
    return texts[status] || status;
}

function showToast(message, type = 'info') {
    // 创建toast通知
    const colors = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    };
    
    const toast = document.createElement('div');
    toast.className = `alert ${colors[type]} alert-dismissible fade show`;
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    toast.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}
