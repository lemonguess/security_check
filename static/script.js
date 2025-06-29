// 全局变量
// 动态获取API基础URL，基于当前页面的协议、主机和端口
const API_BASE = `${window.location.protocol}//${window.location.host}`;
let currentPage = 1;
let totalRecords = 0;
let pageSize = 10;
let selectedContent = new Set();
// 审核相关全局变量
let auditCurrentPage = 1;
let auditTotalRecords = 0;
let auditPageSize = 10;
let auditSelectedContent = new Set();
let auditContentList = [];
let auditCurrentColumnType = '';

// 抓取相关全局变量
let selectedColumnType = '';
let selectedAuditColumnType = ''
let isScrapingInProgress = false;
// 页面加载完成后执行
window.onload = function() {
    console.log('页面加载完成');
    loadStats();
    switchTab('scraping'); // 默认显示抓取测试页面
    initializeScrapeModal();
};
// 初始化抓取进度弹窗
function initializeScrapeModal() {
    const modalHtml = `
        <div id="scrapeModal" class="scrape-modal">
            <div class="scrape-modal-content">
                <h3 id="scrapeModalTitle">🚀 正在抓取内容</h3>
                <div class="scrape-progress">
                    <div id="scrapeProgressBar" class="scrape-progress-bar"></div>
                </div>
                <div id="scrapeStatus" class="scrape-status">准备开始抓取...</div>
                <div id="scrapeResults" class="scrape-results" style="display: none;"></div>
                <button id="scrapeCloseBtn" class="btn btn-secondary" onclick="closeScrapeModal()" style="display: none;">关闭</button>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

// 标签页切换功能
function switchTab(tabName) {
    console.log('切换到标签页:', tabName);
    
    // 如果正在抓取中，阻止切换
    // if (isScrapingInProgress && tabName !== 'scraping') {
    //     showNotification('抓取进行中，无法切换标签页', 'warning');
    //     return;
    // }
    
    // 隐藏所有标签页内容
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });
    
    // 移除所有标签的活动状态
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 显示选中的标签页内容
    const selectedContent = document.getElementById(tabName + 'Tab');
    if (selectedContent) {
        selectedContent.classList.add('active');
        console.log('成功显示标签页内容:', tabName);
    } else {
        console.error('未找到标签页内容:', tabName + 'Tab');
    }
    
    // 激活选中的标签
    const selectedTab = document.querySelector(`[onclick="switchTab('${tabName}')"]`);
    if (selectedTab) {
        selectedTab.classList.add('active');
        console.log('成功激活标签:', tabName);
    } else {
        console.error('未找到标签按钮:', tabName);
    }
    
    // 如果切换到内容审核页面，自动加载内容
    if (tabName === 'audit') {
        // 可以在这里添加自动加载逻辑
    }
}

// 通知系统
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// 选择栏目类型
function selectColumnType(type) {
    if (isScrapingInProgress) {
        showNotification('抓取进行中，无法更改选择', 'warning');
        return;
    }
    
    // 移除抓取tab中所有卡片的选中状态
    document.querySelectorAll('#scrapingTab .column-type-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // 添加选中状态
    const selectedCard = document.querySelector(`#scrapingTab [data-type="${type}"]`);
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }
    
    // 更新全局变量和显示
    selectedColumnType = type;
    const selectedTypeElement = document.getElementById('selectedColumnType');
    if (selectedTypeElement) {
        selectedTypeElement.textContent = type;
    }
    
    // 启用抓取按钮
    const scrapeBtn = document.getElementById('scrapeBtn');
    if (scrapeBtn) {
        scrapeBtn.disabled = false;
    }
    
    console.log('选择栏目类型:', type);
}

// 选择审核栏目类型
function selectAuditColumnType(type) {
    console.log('selectAuditColumnType调用，参数type:', type);
    
    // 移除审核tab中所有卡片的选中状态
    document.querySelectorAll('#auditTab .column-type-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // 添加选中状态
    const selectedCard = document.querySelector(`#auditTab [data-type="${type}"]`);
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }
    
    // 更新全局变量和显示
    selectedAuditColumnType = type;
    auditCurrentColumnType = type;
    console.log('selectedAuditColumnType已设置为:', selectedAuditColumnType);
    console.log('auditCurrentColumnType已设置为:', auditCurrentColumnType);
    const selectedTypeElement = document.getElementById('selectedAuditColumnType');
    if (selectedTypeElement) {
        selectedTypeElement.textContent = type;
    }
    
    // 启用加载按钮
    const loadBtn = document.getElementById('loadAuditBtn');
    if (loadBtn) {
        loadBtn.disabled = false;
    }
    
    console.log('选择审核栏目类型完成:', type, '当前selectedAuditColumnType:', selectedAuditColumnType);
}

// 开始抓取
async function startScraping() {
    if (!selectedColumnType) {
        showNotification('请先选择栏目类型', 'warning');
        return;
    }
    
    if (isScrapingInProgress) {
        showNotification('抓取正在进行中', 'warning');
        return;
    }
    
    // 设置抓取状态
    isScrapingInProgress = true;
    setScrapingUIState(true);
    
    // 显示进度弹窗
    showScrapeModal();
    
    try {
        console.log('开始抓取，栏目类型:', selectedColumnType);
        
        // 立即开始API请求（并行执行）
        const apiPromise = performScraping();
        
        // 同时开始进度条动画
        const progressSteps = [
            { progress: 10, message: '正在连接服务器...', delay: 1000 },
            { progress: 25, message: '正在分析网站结构...', delay: 2000 },
            { progress: 45, message: '正在抓取内容数据...', delay: 4000 },
            { progress: 70, message: '正在处理抓取数据...', delay: 4000 },
            { progress: 90, message: '正在保存数据入库...', delay: 1500 }
        ];
        
        let currentStep = 0;
        let progressCompleted = false;
        let apiCompleted = false;
        let apiResult = null;
        
        // 进度条动画函数
        const executeStep = () => {
            if (currentStep < progressSteps.length) {
                const step = progressSteps[currentStep];
                updateScrapeProgress(step.progress, step.message);
                currentStep++;
                setTimeout(executeStep, step.delay);
            } else {
                progressCompleted = true;
                // 如果API已完成，立即显示结果
                if (apiCompleted && apiResult) {
                    showApiResult(apiResult);
                }
            }
        };
        
        // 开始进度条动画
        executeStep();
        
        // 等待API完成
        apiPromise.then(result => {
            apiCompleted = true;
            apiResult = result;
            // 如果进度条已完成，立即显示结果；否则等待进度条完成
            if (progressCompleted) {
                showApiResult(result);
            }
        }).catch(error => {
            apiCompleted = true;
            apiResult = { error: error };
            // API失败时也要等待进度条或立即显示
            if (progressCompleted) {
                showApiResult({ error: error });
            }
        });
        
    } catch (error) {
        console.error('抓取失败:', error);
        updateScrapeProgress(0, `抓取失败: ${error.message}`);
        showNotification(`抓取失败: ${error.message}`, 'error');
        
        // 显示模拟数据
        setTimeout(() => {
            const mockData = {
                total_count: 25,
                column_type: selectedColumnType,
                processing_time: '10.0s',
                success_rate: '96%'
            };
            showScrapeResults(mockData);
            showNotification('显示模拟抓取结果', 'info');
        }, 1000);
    }
}

// 执行实际的抓取请求
async function performScraping() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/scrape`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                column_type: selectedColumnType
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('抓取结果:', result);
        
        if (result.success) {
            // 修复数据结构问题
            const scrapeData = {
                total_count: result.total_count || 0,
                column_type: result.data && result.data.length > 0 ? result.data[0].column_type : selectedColumnType,
                processing_time: result.processing_time || '0.0s',
                success_count: result.success_count || 0,
                message: result.message || '成功'
            };
            
            return { success: true, data: scrapeData };
        } else {
            throw new Error(result.message || '抓取失败');
        }
        
    } catch (error) {
        console.error('抓取请求失败:', error);
        // 返回模拟数据
        const mockData = {
            total_count: 25,
            column_type: selectedColumnType,
            processing_time: '10.0s',
            success_rate: '96%'
        };
        return { success: false, data: mockData, error: error };
    }
}

// 显示API结果
function showApiResult(result) {
    updateScrapeProgress(100, '抓取完成！');
    
    if (result.error) {
        console.log('显示模拟抓取结果');
        showScrapeResults(result.data);
        showNotification('显示模拟抓取结果', 'info');
    } else {
        showScrapeResults(result.data);
        showNotification(result.data.message || '抓取成功', 'success');
    }
    
    // 3秒后自动跳转到内容审核页面
    startCountdownAndRedirect();
    
    // 重置抓取状态
    setTimeout(() => {
        isScrapingInProgress = false;
        setScrapingUIState(false);
    }, 4000);
}

// 设置抓取时的UI状态
function setScrapingUIState(isScrapingActive) {
    const cards = document.querySelectorAll('.column-type-card');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const tabs = document.querySelectorAll('.tab');
    
    if (isScrapingActive) {
        // 禁用所有栏目类型卡片（除了已选中的）
        cards.forEach(card => {
            if (!card.classList.contains('selected')) {
                card.classList.add('disabled');
            }
        });
        
        // 禁用抓取按钮
        scrapeBtn.disabled = true;
        scrapeBtn.textContent = '抓取中...';
        
        // 禁用其他标签页
        tabs.forEach(tab => {
            if (!tab.classList.contains('active')) {
                tab.style.opacity = '0.5';
                tab.style.pointerEvents = 'none';
            }
        });
    } else {
        // 恢复所有UI元素
        cards.forEach(card => {
            card.classList.remove('disabled');
        });
        
        scrapeBtn.disabled = false;
        scrapeBtn.textContent = '🚀 开始抓取';
        
        tabs.forEach(tab => {
            tab.style.opacity = '1';
            tab.style.pointerEvents = 'auto';
        });
    }
}

// 显示抓取进度弹窗
function showScrapeModal() {
    const modal = document.getElementById('scrapeModal');
    if (modal) {
        modal.style.display = 'block';
        document.getElementById('scrapeResults').style.display = 'none';
        document.getElementById('scrapeCloseBtn').style.display = 'none';
    }
}

// 关闭抓取进度弹窗
function closeScrapeModal() {
    const modal = document.getElementById('scrapeModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// 更新抓取进度
function updateScrapeProgress(percentage, status) {
    const progressBar = document.getElementById('scrapeProgressBar');
    const statusText = document.getElementById('scrapeStatus');
    
    if (progressBar) {
        progressBar.style.width = percentage + '%';
    }
    
    if (statusText) {
        statusText.textContent = status;
    }
}

// 显示抓取结果
function showScrapeResults(data) {
    const resultsDiv = document.getElementById('scrapeResults');
    const closeBtn = document.getElementById('scrapeCloseBtn');
    
    if (resultsDiv) {
        resultsDiv.innerHTML = `
            <h4>✅ 抓取完成</h4>
            <p><strong>栏目类型:</strong> ${data.column_type || '未知'}</p>
            <p><strong>新增数量:</strong> ${data.success_count || 0} 条</p>
            <p><strong>处理时间:</strong> ${data.processing_time || '0s'}</p>
            <p style="margin-top: 15px; color: #28a745;"><span id="countdown">3</span> 秒后自动跳转到内容审核页面...</p>
        `;
        resultsDiv.style.display = 'block';
    }
    
    if (closeBtn) {
        closeBtn.style.display = 'inline-block';
    }
}

// 开始倒计时并跳转
function startCountdownAndRedirect() {
    let seconds = 3;
    const countdownElement = document.getElementById('countdown');
    
    if (countdownElement) {
        countdownElement.textContent = seconds;
        
        const countdownInterval = setInterval(() => {
            seconds--;
            if (seconds <= 0) {
                clearInterval(countdownInterval);
                // 跳转到内容审核页面
                closeScrapeModal();
                switchTab('audit');
                // 自动加载对应栏目类型的内容
                selectedAuditColumnType = selectedColumnType;
                document.getElementById('selectedAuditColumnType').textContent = selectedColumnType;
                document.getElementById('loadAuditBtn').disabled = false;
                loadAuditContent();
            } else {
                countdownElement.textContent = seconds;
            }
        }, 1000);
    } else {
        // 如果找不到倒计时元素，直接跳转
        setTimeout(() => {
            closeScrapeModal();
            switchTab('audit');
            selectedAuditColumnType = selectedColumnType;
            document.getElementById('selectedAuditColumnType').textContent = selectedColumnType;
            document.getElementById('loadAuditBtn').disabled = false;
            loadAuditContent();
        }, 3000);
    }
}

// 显示策略测试结果
function showStrategyTestResults(data) {
    const resultsDiv = document.getElementById('testResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = `
        <h3>🎯 抓取策略测试结果</h3>
        <div class="stats-grid">
            <div class="stat-card">
                <h3>${data.strategies_tested || 0}</h3>
                <p>策略测试数</p>
            </div>
            <div class="stat-card">
                <h3>${data.successful_strategies || 0}</h3>
                <p>成功策略数</p>
            </div>
            <div class="stat-card">
                <h3>${data.content_extracted || 0}</h3>
                <p>提取内容数</p>
            </div>
            <div class="stat-card">
                <h3>${data.processing_time || '0s'}</h3>
                <p>处理时间</p>
            </div>
        </div>
        <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
            <h4>📊 媒体文件统计</h4>
            <p>图片: ${data.media_files?.images || 0} 个</p>
            <p>视频: ${data.media_files?.videos || 0} 个</p>
            <p>推荐策略: ${data.recommended_strategy || '未知'}</p>
        </div>
    `;
}

// 提取媒体文件
function extractMediaFromContent(content) {
    const images = [];
    const videos = [];
    
    // 模拟媒体文件提取
    const imageUrls = [
        'https://example.com/image1.jpg',
        'https://example.com/image2.png',
        'https://example.com/image3.gif'
    ];
    
    const videoUrls = [
        'https://example.com/video1.mp4',
        'https://example.com/video2.avi'
    ];
    
    imageUrls.forEach((url, index) => {
        images.push({
            id: `img_${index}`,
            url: url,
            type: 'image',
            size: Math.floor(Math.random() * 1000) + 100 + 'KB'
        });
    });
    
    videoUrls.forEach((url, index) => {
        videos.push({
            id: `vid_${index}`,
            url: url,
            type: 'video',
            duration: Math.floor(Math.random() * 300) + 30 + 's',
            size: Math.floor(Math.random() * 50) + 10 + 'MB'
        });
    });
    
    return { images, videos };
}

// 审核媒体文件
async function moderateMediaFiles(mediaFiles) {
    const results = {
        images: [],
        videos: []
    };
    
    // 审核图片
    for (const image of mediaFiles.images) {
        const result = await moderateImages([image]);
        results.images.push({
            ...image,
            moderation_result: result[0]
        });
    }
    
    // 审核视频
    for (const video of mediaFiles.videos) {
        const result = await moderateVideos([video]);
        results.videos.push({
            ...video,
            moderation_result: result[0]
        });
    }
    
    return results;
}

// 审核图片
async function moderateImages(images) {
    // 模拟图片审核
    return images.map(image => ({
        risk_level: ['SAFE', 'SUSPICIOUS', 'RISKY'][Math.floor(Math.random() * 3)],
        confidence: Math.random(),
        categories: ['正常内容', '可疑内容'][Math.floor(Math.random() * 2)],
        processing_time: Math.random() * 2 + 0.5
    }));
}

// 审核视频
async function moderateVideos(videos) {
    // 模拟视频审核
    return videos.map(video => ({
        risk_level: ['SAFE', 'SUSPICIOUS', 'RISKY'][Math.floor(Math.random() * 3)],
        confidence: Math.random(),
        categories: ['正常内容', '可疑内容'][Math.floor(Math.random() * 2)],
        processing_time: Math.random() * 5 + 1
    }));
}

// 按栏目类型抓取内容
async function scrapeByColumnType() {
    const websiteUrl = document.getElementById('websiteUrl').value;
    const columnType = document.getElementById('columnType').value;
    
    if (!websiteUrl) {
        showNotification('请输入网站URL', 'warning');
        return;
    }
    
    const scrapeBtn = document.getElementById('scrapeBtn');
    const originalText = scrapeBtn.textContent;
    scrapeBtn.textContent = '抓取中...';
    scrapeBtn.disabled = true;
    
    try {
        console.log('开始按栏目类型抓取:', { websiteUrl, columnType });
        
        const response = await fetch(`${API_BASE}/api/v1/scrape-by-column`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: websiteUrl,
                column_type: columnType,
                page: currentPage,
                page_size: pageSize
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('抓取结果:', result);
        
        if (result.success) {
            displayContentList(result.data.content);
            totalRecords = result.data.total;
            updatePaginationInfo();
            showNotification(`成功抓取 ${result.data.content.length} 条内容`, 'success');
        } else {
            throw new Error(result.message || '抓取失败');
        }
        
    } catch (error) {
        console.error('抓取失败:', error);
        showNotification(`抓取失败: ${error.message}`, 'error');
        
        // 显示模拟数据
        const mockContent = generateMockContent();
        displayContentList(mockContent);
        totalRecords = 50;
        updatePaginationInfo();
        showNotification('显示模拟抓取结果', 'info');
    } finally {
        scrapeBtn.textContent = originalText;
        scrapeBtn.disabled = false;
    }
}

// 生成模拟内容
function generateMockContent() {
    const titles = [
        '重要新闻：科技创新推动经济发展',
        '社会热点：环保政策新举措',
        '文化资讯：传统文化传承与发展',
        '教育动态：在线教育新模式探索',
        '健康生活：科学饮食与运动指南'
    ];
    
    return titles.map((title, index) => ({
        id: generateContentId(),
        title: title,
        url: `https://example.com/article/${index + 1}`,
        publishDate: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        author: `作者${index + 1}`,
        type: document.getElementById('columnType').value || '新闻',
        content: `这是${title}的详细内容...`,
        mediaFiles: extractMediaFromContent(`内容${index + 1}`)
    }));
}

// 设置示例
function setExample(type) {
    const examples = {
        news: {
            url: 'https://news.example.com',
            columnType: '新闻'
        },
        blog: {
            url: 'https://blog.example.com',
            columnType: '博客'
        },
        forum: {
            url: 'https://forum.example.com',
            columnType: '论坛'
        }
    };
    
    if (examples[type]) {
        document.getElementById('websiteUrl').value = examples[type].url;
        document.getElementById('columnType').value = examples[type].columnType;
        showNotification(`已设置${examples[type].columnType}示例`, 'info');
    }
}

// 生成内容ID
function generateContentId() {
    return 'content_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// 显示内容列表
function displayContentList(contentList) {
    const listElement = document.getElementById('contentList');
    listElement.innerHTML = '';
    
    contentList.forEach((item, index) => {
        // 构建mediaFiles对象，避免URL编码问题
        if (!item.mediaFiles && (item.images || item.videos || item.audios)) {
            item.mediaFiles = {
                images: (item.images || []).map((url, idx) => ({
                    id: `img_${item.id}_${idx}`,
                    url: url,
                    type: 'image',
                    size: '未知大小'
                })),
                videos: (item.videos || []).map((url, idx) => ({
                    id: `vid_${item.id}_${idx}`,
                    url: url,
                    type: 'video',
                    duration: '未知时长',
                    size: '未知大小'
                }))
            };
        }
        
        const itemDiv = document.createElement('div');
        itemDiv.className = 'content-item';
        itemDiv.style.cssText = 'padding: 15px; border-bottom: 1px solid #eee; display: flex; align-items: center;';
        
        // 创建可点击的标题链接
        const titleLink = item.url ? 
            `<a href="${item.url}" target="_blank" style="color: #c41e3a; text-decoration: none; font-weight: bold;" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">${item.title}</a>` :
            `<span style="font-weight: bold;">${item.title}</span>`;
        
        itemDiv.innerHTML = `
            <div style="margin-right: 15px;">
                <input type="checkbox" id="check_${item.id}" onchange="toggleSelection('${item.id}')">
            </div>
            <div style="flex: 1;">
                <div style="margin-bottom: 8px;">
                    <span id="status_${item.id}" style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 12px; color: #666; margin-right: 8px;">[${item.type}]</span>
                    ${titleLink}
                </div>
                ${item.publishDate ? `<div style="font-size: 12px; color: #999; margin-bottom: 5px;">📅 ${item.publishDate}</div>` : ''}
                ${item.author ? `<div style="font-size: 12px; color: #999; margin-bottom: 5px;">✍️ ${item.author}</div>` : ''}
                ${generateMediaInfoHtml(item)}
                <div id="result_${item.id}" style="margin-top: 8px;"></div>
            </div>
            <div style="margin-left: 15px;">
                <button onclick="auditSingleItem('${item.id}')" class="btn btn-primary" style="padding: 5px 10px; font-size: 12px;">${getAuditButtonText(item.audit_status || item.status)}</button>
            </div>
        `;
        
        listElement.appendChild(itemDiv);
    });
    
    // 存储当前内容列表供其他函数使用
    window.currentContentList = contentList;
}

// 显示媒体文件
function showMediaFiles(contentId) {
    const content = window.currentContentList?.find(item => item.id === contentId);
    if (!content || !content.mediaFiles) {
        showNotification('未找到媒体文件', 'warning');
        return;
    }
    
    const modal = document.getElementById('mediaModal');
    const modalBody = document.getElementById('mediaModalBody');
    
    let mediaHtml = '<h3>📷 图片文件</h3><div class="media-grid">';
    
    content.mediaFiles.images.forEach(image => {
        mediaHtml += `
            <div class="media-item">
                <img src="${image.url}" alt="图片" style="max-width: 100%; height: 150px; object-fit: cover;">
                <p style="margin: 5px 0; font-size: 12px;">${image.size}</p>
                <div id="img_result_${image.id}" style="font-size: 11px; color: #666;"></div>
            </div>
        `;
    });
    
    mediaHtml += '</div><h3>🎥 视频文件</h3><div class="media-grid">';
    
    content.mediaFiles.videos.forEach(video => {
        mediaHtml += `
            <div class="media-item">
                <div style="width: 100%; height: 150px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; border-radius: 5px;">
                    <span style="font-size: 24px;">🎥</span>
                </div>
                <p style="margin: 5px 0; font-size: 12px;">${video.duration} | ${video.size}</p>
                <div id="vid_result_${video.id}" style="font-size: 11px; color: #666;"></div>
            </div>
        `;
    });
    
    mediaHtml += '</div>';
    modalBody.innerHTML = mediaHtml;
    modal.style.display = 'block';
    
    // 自动审核媒体文件
    moderateMediaFiles(content.mediaFiles).then(results => {
        results.images.forEach(image => {
            const resultDiv = document.getElementById(`img_result_${image.id}`);
            if (resultDiv) {
                resultDiv.innerHTML = getDetailedResultHtml(image.moderation_result);
            }
        });
        
        results.videos.forEach(video => {
            const resultDiv = document.getElementById(`vid_result_${video.id}`);
            if (resultDiv) {
                resultDiv.innerHTML = getDetailedResultHtml(video.moderation_result);
            }
        });
    });
}

// 关闭媒体模态框
function closeMediaModal() {
    document.getElementById('mediaModal').style.display = 'none';
}

// 获取详细结果HTML
function getDetailedResultHtml(result) {
    return `
        <div style="font-size: 11px; padding: 5px; background: #f8f9fa; border-radius: 3px; margin-top: 5px;">
            <div><strong>AI引擎:</strong> <span class="risk-badge ${getRiskClass(result.risk_level)}">${result.risk_level}</span></div>
            <div><strong>置信度:</strong> ${(result.confidence * 100).toFixed(1)}%</div>
            <div><strong>处理时间:</strong> ${result.processing_time.toFixed(2)}s</div>
        </div>
    `;
}

// 审核单个项目
async function auditSingleItem(contentId) {
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = '审核中...';

    try {
        const result = await moderateContentByIds([contentId]);
        displayAuditResult(contentId, result);
    } catch (error) {
        console.error(`审核内容 #${contentId} 失败:`, error);
        displayAuditResult(contentId, { success: false, message: error.message });
        // 审核失败时恢复原始按钮文本
        button.textContent = originalText;
    } finally {
        button.disabled = false;
        // 注意：成功时按钮文本会在updateStatusLabel中更新，这里不需要设置
    }
}

// 审核所有内容（内容列表页面）
async function auditAllContentList() {
    if (!window.currentContentList || window.currentContentList.length === 0) {
        showNotification('没有可审核的内容', 'warning');
        return;
    }
    
    const confirmResult = confirm(`确定要审核所有 ${window.currentContentList.length} 条内容吗？`);
    if (!confirmResult) return;
    
    showProgress();
    
    try {
        // 提取所有内容的ID
        const idList = window.currentContentList.map(content => content.id);
        updateProgress(1, 1, '正在批量审核...');
        
        // 发送ID列表到后端进行批量审核
        const result = await moderateContentByIds(idList);
        
        // 显示审核结果
        if (result.data && Array.isArray(result.data)) {
            result.data.forEach((auditResult, index) => {
                const contentId = idList[index];
                showResult(contentId, auditResult);
            });
        }
        
        showNotification('批量审核完成', 'success');
    } catch (error) {
        console.error('批量审核失败:', error);
        showNotification('批量审核失败', 'error');
    }
    
    hideProgress();
}

// 显示进度
function showProgress() {
    const progressContainer = document.getElementById('batchProgress');
    progressContainer.style.display = 'block';
    
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    progressFill.style.width = '0%';
    progressText.textContent = '准备开始...';
}

// 更新进度
function updateProgress(current, total, message) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    const percentage = (current / total) * 100;
    progressFill.style.width = `${percentage}%`;
    progressText.textContent = `${message} (${current}/${total})`;
}

// 隐藏进度
function hideProgress() {
    setTimeout(() => {
        const progressContainer = document.getElementById('batchProgress');
        progressContainer.style.display = 'none';
    }, 2000);
}

// 导出结果
function exportResults() {
    if (!window.currentContentList || window.currentContentList.length === 0) {
        showNotification('没有可导出的数据', 'warning');
        return;
    }
    
    // 生成CSV数据
    const csvData = [];
    csvData.push(['标题', '类型', '发布时间', '作者', '链接', '审核结果', '风险等级', '置信度']);
    
    window.currentContentList.forEach(item => {
        const resultDiv = document.getElementById(`result_${item.id}`);
        let auditResult = '未审核';
        let riskLevel = '';
        let confidence = '';
        
        if (resultDiv && resultDiv.innerHTML && !resultDiv.innerHTML.includes('loading-spinner')) {
            auditResult = '已审核';
            // 这里可以解析具体的审核结果
        }
        
        csvData.push([
            `"${item.title}"`,
            item.type,
            item.publishDate || '',
            item.author || '',
            item.url || '',
            auditResult,
            riskLevel,
            confidence
        ]);
    });
    
    const csvContent = csvData.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `内容审核结果_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    showNotification('结果导出成功', 'success');
}

// 加载统计数据
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/stats`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const stats = await response.json();
        
        if (stats.success) {
            updateStatsDisplay(stats.data);
        } else {
            throw new Error(stats.message || '获取统计数据失败');
        }
        
    } catch (error) {
        console.error('加载统计数据失败:', error);
        
        // 显示模拟数据
        const mockStats = {
            total_requests: 1234,
            success_rate: 98.5,
            avg_processing_time: 1.2,
            today_audits: 156
        };
        updateStatsDisplay(mockStats);
    }
}

// 更新统计显示
function updateStatsDisplay(stats) {
    document.getElementById('totalRequests').textContent = stats.total_requests || 0;
    document.getElementById('successRate').textContent = (stats.success_rate || 0) + '%';
    document.getElementById('avgProcessingTime').textContent = (stats.avg_processing_time || 0) + 's';
    document.getElementById('todayAudits').textContent = stats.today_audits || 0;
}

// 内容审核
async function moderateContent(content, contentId) {
    try {
        const response = await fetch(`${API_BASE}/api/v1/moderate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: content,
                content_id: contentId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        console.error('API调用失败，使用模拟数据:', error);
        
        // 返回模拟审核结果
        return await moderateBatch([{ content, content_id: contentId }]);
    }
}

// 批量审核
async function moderateBatch(contents) {
    // 模拟批量审核
    return contents.map(item => moderateText(item.content));
}

// 文本审核
function moderateText(text) {
    // 模拟审核逻辑
    const riskKeywords = ['危险', '违法', '暴力', '色情'];
    const suspiciousKeywords = ['可疑', '争议', '敏感'];
    
    let riskLevel = 'SAFE';
    let confidence = 0.9;
    
    if (riskKeywords.some(keyword => text.includes(keyword))) {
        riskLevel = 'RISKY';
        confidence = 0.95;
    } else if (suspiciousKeywords.some(keyword => text.includes(keyword))) {
        riskLevel = 'SUSPICIOUS';
        confidence = 0.8;
    }
    
    return {
        final_decision: riskLevel,
        confidence_score: confidence,
        ai_engine: {
            decision: riskLevel,
            confidence: confidence,
            processing_time: Math.random() * 2 + 0.5
        },
        rule_engine: {
            decision: riskLevel,
            confidence: confidence * 0.9,
            processing_time: Math.random() * 0.5 + 0.1
        },
        fusion_engine: {
            decision: riskLevel,
            confidence: confidence,
            processing_time: Math.random() * 0.3 + 0.1
        }
    };
}

// 显示审核结果
function showResult(contentId, result) {
    const resultDiv = document.getElementById(`result_${contentId}`);
    if (!resultDiv) return;
    
    const riskLevel = result.final_decision || 'UNKNOWN';
    const confidence = result.confidence_score || 0;
    
    resultDiv.innerHTML = `
        <div style="font-size: 12px; padding: 8px; background: #f8f9fa; border-radius: 5px; border-left: 3px solid ${getRiskColor(riskLevel)};">
            <div style="margin-bottom: 5px;">
                <strong>最终决策:</strong> 
                <span class="risk-badge ${getRiskClass(riskLevel)}">${riskLevel}</span>
                <span style="margin-left: 10px;">置信度: ${(confidence * 100).toFixed(1)}%</span>
            </div>
            <div style="font-size: 11px; color: #666;">
                <div>AI引擎: <span class="risk-badge ${getRiskClass(result.ai_engine?.decision)}">${result.ai_engine?.decision}</span> (${(result.ai_engine?.confidence * 100).toFixed(1)}%)</div>
                <div>规则引擎: <span class="risk-badge ${getRiskClass(result.rule_engine?.decision)}">${result.rule_engine?.decision}</span> (${(result.rule_engine?.confidence * 100).toFixed(1)}%)</div>
                <div>处理时间: ${(result.ai_engine?.processing_time || 0).toFixed(2)}s</div>
            </div>
            <div style="margin-top: 5px; font-size: 11px;">
                <strong>建议操作:</strong> ${getActionRecommendation(riskLevel)}
            </div>
        </div>
    `;
}

// 显示批量结果
function showBatchResults(results) {
    results.forEach((result, index) => {
        if (window.currentContentList && window.currentContentList[index]) {
            showResult(window.currentContentList[index].id, result);
        }
    });
}

// 获取风险等级样式类
function getRiskClass(riskLevel) {
    switch (riskLevel) {
        case 'SAFE': return 'risk-safe';
        case 'SUSPICIOUS': return 'risk-suspicious';
        case 'RISKY': return 'risk-risky';
        case 'BLOCKED': return 'risk-blocked';
        default: return 'risk-safe';
    }
}

// 获取风险等级颜色
function getRiskColor(riskLevel) {
    switch (riskLevel) {
        case 'SAFE': return '#28a745';
        case 'SUSPICIOUS': return '#ffc107';
        case 'RISKY': return '#fd7e14';
        case 'BLOCKED': return '#dc3545';
        default: return '#6c757d';
    }
}

// 获取操作建议
function getActionRecommendation(riskLevel) {
    switch (riskLevel) {
        case 'SAFE': return '✅ 内容安全，可以发布';
        case 'SUSPICIOUS': return '⚠️ 内容可疑，建议人工复审';
        case 'RISKY': return '🚫 内容有风险，建议修改后发布';
        case 'BLOCKED': return '❌ 内容违规，禁止发布';
        default: return '❓ 未知状态，建议人工审核';
    }
}

// 切换选择
function toggleSelection(contentId) {
    const checkbox = document.getElementById(`check_${contentId}`);
    if (checkbox.checked) {
        selectedContent.add(contentId);
    } else {
        selectedContent.delete(contentId);
    }
    updateCrawlSelectedCount();
}

// 更新选中数量 - 处理爬取内容的选择计数
function updateCrawlSelectedCount() {
    const selectedCount = document.getElementById('crawlSelectedCount');
    if (selectedCount) {
        selectedCount.textContent = `已选择: ${selectedContent.size} 项`;
    }
}

// 分页相关函数
function changePage(direction) {
    const newPage = currentPage + direction;
    const totalPages = Math.ceil(totalRecords / pageSize);
    
    if (newPage >= 1 && newPage <= totalPages) {
        currentPage = newPage;
        scrapeByColumnType();
    }
}

function updatePaginationInfo() {
    const totalPages = Math.ceil(totalRecords / pageSize);
    
    const paginationInfo = document.getElementById('paginationInfo');
    if (paginationInfo) {
        paginationInfo.textContent = `第 ${currentPage} 页，共 ${totalRecords} 条记录`;
    }
    
    const currentPageNum = document.getElementById('currentPageNum');
    if (currentPageNum) {
        currentPageNum.textContent = currentPage;
    }
    
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    
    if (prevPageBtn) prevPageBtn.disabled = currentPage <= 1;
    if (nextPageBtn) nextPageBtn.disabled = currentPage >= totalPages;
}

// 内容审核Tab相关功能
async function loadAuditContent() {
    console.log('开始加载审核内容，选中的栏目类型:', selectedAuditColumnType);
    
    if (!selectedAuditColumnType) {
        showNotification('请选择栏目类型', 'warning');
        return;
    }
    
    auditCurrentColumnType = selectedAuditColumnType;
    auditCurrentPage = 1;
    auditSelectedContent.clear();
    
    console.log('准备调用fetchAuditContent');
    await fetchAuditContent();
}

// 获取审核内容
async function fetchAuditContent() {
    console.log('fetchAuditContent开始执行');
    
    // 只在切换栏目类型或首次加载时清空选择状态
    // 分页时保持选择状态
    if (auditCurrentPage === 1) {
        auditSelectedContent.clear();
        updateSelectedCount();
    }
    
    try {
        console.log('发送API请求到:', `${API_BASE}/api/v1/content/list?column_type=${encodeURIComponent(auditCurrentColumnType)}&page=${auditCurrentPage}&page_size=${auditPageSize}`);
        
        const response = await fetch(`${API_BASE}/api/v1/content/list?column_type=${encodeURIComponent(auditCurrentColumnType)}&page=${auditCurrentPage}&page_size=${auditPageSize}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        console.log('API响应状态:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('API响应数据:', result);
        
        if (result.success) {
            auditContentList = (result.data.items || []).map(item => ({
                ...item,
                audit_status: item.audit_status || 'pending',  // 确保每个项目都有审核状态
                status: item.status || 'pending'  // 确保每个项目都有默认状态
            }));
            auditTotalRecords = result.data.total || 0;
            
            console.log('处理成功，内容数量:', auditContentList.length);
            
            displayAuditContentList();
            updateAuditPaginationInfo();
            
            console.log('准备显示auditContentContainer');
            const container = document.getElementById('auditContentContainer');
            if (container) {
                container.style.display = 'block';
                console.log('auditContentContainer已显示');
            } else {
                console.error('找不到auditContentContainer元素');
            }
            
            const titleElement = document.getElementById('auditContentTitle');
            if (titleElement) {
                titleElement.textContent = `📋 ${auditCurrentColumnType} - 内容列表`;
            }
            
            showNotification(`成功加载${auditCurrentColumnType} ${auditContentList.length} 条内容`, 'success');
        } else {
            throw new Error(result.message || '加载失败');
        }
        
    } catch (error) {
        console.error('加载审核内容失败:', error);
        console.log('进入错误处理，显示模拟数据');
        
        showNotification(`加载失败: ${error.message}`, 'error');
        
        // 显示模拟数据
        auditContentList = generateMockAuditContent();
        auditTotalRecords = 25;
        
        console.log('生成模拟数据，数量:', auditContentList.length);
        console.log('模拟数据内容:', auditContentList);
        
        displayAuditContentList(auditContentList);
        updateAuditPaginationInfo();
        
        // 只在首次加载时清空选中状态
        if (auditCurrentPage === 1) {
            auditSelectedContent.clear();
        }
        updateSelectedCount();
        
        console.log('准备显示auditContentContainer（模拟数据）');
        const container = document.getElementById('auditContentContainer');
        if (container) {
            container.style.display = 'block';
            console.log('auditContentContainer已显示（模拟数据）');
        } else {
            console.error('找不到auditContentContainer元素（模拟数据）');
        }
        
        const titleElement = document.getElementById('auditContentTitle');
        if (titleElement) {
            titleElement.textContent = `📋 ${auditCurrentColumnType} - 内容列表`;
        }
        
        showNotification(`显示模拟数据: ${auditContentList.length} 条内容`, 'info');
    }
}

// 生成模拟审核内容
function generateMockAuditContent() {
    const titles = [
        '科技创新驱动经济高质量发展',
        '绿色环保理念深入人心',
        '教育改革助力人才培养',
        '文化传承与现代发展并重',
        '健康生活方式受到关注'
    ];
    
    return titles.map((title, index) => ({
        id: `audit_${Date.now()}_${index}`,
        title: title,
        url: `https://example.com/audit/${index + 1}`,
        publishDate: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        author: `编辑${index + 1}`,
        type: auditCurrentColumnType || '新闻',
        audit_status: 'pending'  // 默认状态为待审核
    }));
}

// 获取状态样式类
function getStatusClass(status) {
    const statusClasses = {
        'approved': 'status-approved',
        'rejected': 'status-rejected', 
        'reviewing': 'status-reviewing',
        'pending': 'status-pending'
    };
    return statusClasses[status] || 'status-pending';
}

// 显示审核内容列表
function displayAuditContentList(items = null) {
    const listElement = document.getElementById('auditContentList');
    listElement.innerHTML = '';
    
    const contentItems = items || auditContentList;
    if (!contentItems || contentItems.length === 0) {
        listElement.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">暂无内容</div>';
        return;
    }
    
    if (items) {
        auditContentList = items;
    }
    
    if (!auditContentList) {
        auditContentList = contentItems;
    }
    
    contentItems.forEach((item, index) => {
        // 构建mediaFiles对象，避免URL编码问题
        if (!item.mediaFiles && (item.images || item.videos || item.audios)) {
            item.mediaFiles = {
                images: (item.images || []).map((url, idx) => ({
                    id: `img_${item.id}_${idx}`,
                    url: url,
                    type: 'image',
                    size: '未知大小'
                })),
                videos: (item.videos || []).map((url, idx) => ({
                    id: `vid_${item.id}_${idx}`,
                    url: url,
                    type: 'video',
                    duration: '未知时长',
                    size: '未知大小'
                }))
            };
        }
        
        const itemDiv = document.createElement('div');
        itemDiv.className = 'content-item';
        itemDiv.id = `content-item-${item.id}`;
        itemDiv.style.cssText = 'padding: 15px; border-bottom: 1px solid #eee; display: flex; align-items: center;';
        
        const titleLink = item.url ? 
            `<a href="${item.url}" target="_blank" style="color: #c41e3a; text-decoration: none; font-weight: bold;" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">${item.title}</a>` :
            `<span style="font-weight: bold;">${item.title}</span>`;
        

        
        const isSelected = auditSelectedContent.has(String(item.id));
        
        itemDiv.innerHTML = `
            <div style="margin-right: 15px;">
                <input type="checkbox" id="audit_check_${item.id}" ${isSelected ? 'checked' : ''}>
            </div>
            <div style="flex: 1;">
                <div style="margin-bottom: 8px;">
                    <span style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 12px; color: #666; margin-right: 8px;">[${item.column_type || item.type || '未知'}]</span>
                    <span id="status_${item.id}" class="status ${getStatusClass(item.audit_status || item.status || 'pending')}">${getStatusText(item.audit_status || item.status || 'pending')}</span>
                    ${titleLink}
                </div>
                ${item.publish_time ? `<div style="font-size: 12px; color: #999; margin-bottom: 5px;">🕒 发布时间: ${new Date(item.publish_time).toLocaleString()}</div>` : ''}
                ${item.created_at ? `<div style="font-size: 12px; color: #999; margin-bottom: 5px;">📅 创建时间: ${new Date(item.created_at).toLocaleString()}</div>` : ''}
                ${item.content ? `<div style="font-size: 12px; color: #666; margin-bottom: 5px;">📝 ${item.content.substring(0, 100)}${item.content.length > 100 ? '...' : ''}</div>` : ''}
                ${generateMediaInfoHtml(item)}
                <div id="audit_result_${item.id}" class="audit-details-container" style="margin-top: 8px;"></div>
            </div>
            <div style="margin-left: 15px;">
                <button onclick="auditSingleItem('${item.id}')" class="btn btn-primary" style="padding: 5px 10px; font-size: 12px;">${getAuditButtonText(item.audit_status || item.status)}</button>
            </div>
        `;
        
        listElement.appendChild(itemDiv);

        const checkbox = document.getElementById(`audit_check_${item.id}`);
        if (checkbox) {
            checkbox.addEventListener('change', () => toggleAuditSelection(item.id));
        }

        if(item.auditResult) {
            displayAuditResult(item.id, item.auditResult);
        }
    });

    updateSelectedCount();
}



// 切换审核内容选择
function toggleAuditSelection(itemId) {
    const checkbox = document.getElementById(`audit_check_${itemId}`);
    if (!checkbox) {
        return;
    }
    
    const stringId = String(itemId);
    
    if (checkbox.checked) {
        auditSelectedContent.add(stringId);
    } else {
        auditSelectedContent.delete(stringId);
    }
    
    updateSelectedCount();
}

// 全选/取消全选
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const isChecked = selectAllCheckbox.checked;
    
    console.log('toggleSelectAll调用，isChecked:', isChecked);
    console.log('当前auditContentList:', auditContentList);
    
    // 清空当前选择状态
    auditSelectedContent.clear();
    
    // 使用auditContentList
    if (auditContentList && auditContentList.length > 0) {
        auditContentList.forEach(item => {
            const checkbox = document.getElementById(`audit_check_${item.id}`);
            if (checkbox) {
                checkbox.checked = isChecked;
                const stringId = String(item.id);
                if (isChecked) {
                    auditSelectedContent.add(stringId);
                }
                // 手动触发change事件，确保其他逻辑正确执行
                checkbox.dispatchEvent(new Event('change'));
            }
        });
    }
    
    updateSelectedCount();
}

// 审核页面分页
function changeAuditPage(direction) {
    const newPage = auditCurrentPage + direction;
    const totalPages = Math.ceil(auditTotalRecords / auditPageSize);
    
    if (newPage >= 1 && newPage <= totalPages) {
        auditCurrentPage = newPage;
        // 确保auditCurrentColumnType有值
        if (!auditCurrentColumnType && selectedAuditColumnType) {
            auditCurrentColumnType = selectedAuditColumnType;
        }
        fetchAuditContent();
    }
}

// 更新审核分页信息
function updateAuditPaginationInfo() {
    const totalPages = Math.ceil(auditTotalRecords / auditPageSize);
    
    document.getElementById('auditPaginationInfo').textContent = 
        `第 ${auditCurrentPage} 页，共 ${auditTotalRecords} 条记录`;
    document.getElementById('auditCurrentPageNum').textContent = auditCurrentPage;
    
    document.getElementById('auditPrevPageBtn').disabled = auditCurrentPage <= 1;
    document.getElementById('auditNextPageBtn').disabled = auditCurrentPage >= totalPages;
}

// 审核所有内容
async function auditAllContent() {
    if (auditContentList.length === 0) {
        showNotification('没有可审核的内容', 'warning');
        return;
    }
    
    const confirmResult = confirm(`确定要审核当前页面的所有 ${auditContentList.length} 条内容吗？`);
    if (!confirmResult) return;
    
    await performBatchAudit(auditContentList.map(item => item.id));
}

// 审核选中内容
async function auditSelectedItems() {
    if (auditSelectedContent.size === 0) {
        showNotification('请先选择要审核的内容', 'warning');
        return;
    }
    
    const confirmResult = confirm(`确定要审核选中的 ${auditSelectedContent.size} 条内容吗？`);
    if (!confirmResult) return;
    
    await performBatchAudit(Array.from(auditSelectedContent));
}

// 执行批量审核
async function performBatchAudit() {
    const selectedIds = Array.from(auditSelectedContent);
    if (selectedIds.length === 0) {
        showNotification('请先选择要审核的内容', 'warning');
        return;
    }

    // 先将所有选中项的右侧审核按钮更新为"审核中..."
    selectedIds.forEach(contentId => {
        const auditButton = document.querySelector(`button[onclick="auditSingleItem('${contentId}')"]`);
        if (auditButton) {
            auditButton.disabled = true;
            auditButton.textContent = '审核中...';
        }
        updateStatusLabel(contentId, 'reviewing');
    });

    try {
        const result = await moderateContentByIds(selectedIds);
        
        if (result.success && result.data) {
            showNotification(result.message || '批量审核成功', 'success');
            result.data.forEach(auditResult => {
                displayAuditResult(auditResult.content_id, result);
            });
        } else {
            throw new Error(result.message || '批量审核失败');
        }
    } catch (error) {
        console.error('批量审核失败:', error);
        showNotification(`批量审核失败: ${error.message}`, 'error');
        // 审核失败时，将状态和按钮恢复为待审核
        selectedIds.forEach(contentId => {
            updateStatusLabel(contentId, 'pending');
            const auditButton = document.querySelector(`button[onclick="auditSingleItem('${contentId}')"]`);
            if (auditButton) {
                auditButton.disabled = false;
                auditButton.textContent = '审核';
            }
        });
    }
}

// 审核单条内容
async function auditSingleContent(item) {
    const response = await fetch(`${API_BASE}/api/v1/moderate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content: item.title,
            content_id: item.id
        })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    return result;
}

// 根据ID列表审核内容
async function moderateContentByIds(idList) {
    const response = await fetch(`${API_BASE}/api/v1/moderation/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            id_list: idList
        })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    console.log('moderateContentByIds result:', result);
    if (result.success) {
        return result;
    } else {
        throw new Error(result.message || '审核失败');
    }
}

// 显示审核结果
function displayAuditResult(contentId, result) {
    const resultDiv = document.getElementById(`audit_result_${contentId}`) || document.getElementById(`result_${contentId}`);
    if (!resultDiv) {
        console.error(`Result div not found for contentId: ${contentId}`);
        return;
    }

    if (result && result.success && result.data && result.data.length > 0) {
        const auditData = result.data.find(d => d.content_id == contentId);
        if (!auditData) {
            resultDiv.innerHTML = `<span class="badge bg-warning">审核结果未找到</span>`;
            return;
        }

        resultDiv.innerHTML = createAuditResultCard(contentId, auditData);
        // 将后端返回的大写状态转换为小写
        const statusMapping = {
            'APPROVED': 'approved',
            'REJECTED': 'rejected',
            'REVIEWING': 'reviewing',
            'PENDING': 'pending'
        };
        const frontendStatus = statusMapping[auditData.final_decision] || 'pending';
        updateStatusLabel(contentId, frontendStatus);
    } else {
        resultDiv.innerHTML = `<div class="alert alert-danger">审核失败: ${result ? result.message : '未知错误'}</div>`;
        updateStatusLabel(contentId, 'rejected');
    }
}

// 更新状态标签
function updateStatusLabel(contentId, status) {
    const statusElement = document.getElementById(`status_${contentId}`);
    if (!statusElement) return;

    const statusMap = {
        'approved': { text: '审核通过', class: 'status-approved', audit_status: 'approved' },
        'reviewing': { text: '审核中...', class: 'status-reviewing', audit_status: 'reviewing' },
        'rejected': { text: '审核不通过', class: 'status-rejected', audit_status: 'rejected' },
        'pending': { text: '待审核', class: 'status-pending', audit_status: 'pending' }
    };

    const newStatus = statusMap[status] || statusMap['pending'];

    statusElement.textContent = newStatus.text;
    statusElement.className = `status ${newStatus.class}`;
    
    // 更新按钮文本和状态
    const auditButton = document.querySelector(`button[onclick="auditSingleItem('${contentId}')"]`);
    if (auditButton) {
        auditButton.textContent = getAuditButtonText(newStatus.audit_status);
        auditButton.disabled = false; // 确保按钮可用
    }
    
    // 更新内存中的数据状态
    if (window.currentAuditContentList) {
        const item = window.currentAuditContentList.find(item => item.id == contentId);
        if (item) {
            item.audit_status = newStatus.audit_status;
        }
    }
}

function createAuditResultCard(contentId, auditData) {
    const { final_decision, confidence_score, data } = auditData;
    const fusionResult = data?.fusion_result;
    const detailsId = `details_${contentId}`;

    const getRiskLevelClass = (level) => {
        if (level === 'safe') return 'text-success';
        if (level === 'review') return 'text-warning';
        if (level === 'reject') return 'text-danger';
        return 'text-muted';
    };

    const summarySection = `
        <div class="mb-3">
            <h6 class="card-subtitle mb-2 text-muted">审核摘要</h6>
            <p class="card-text">
                <strong>最终决策:</strong> 
                <span class="fw-bold ${getRiskLevelClass(final_decision)}">${final_decision || 'N/A'}</span>
            </p>
            ${fusionResult?.risk_reasons?.length > 0 ? `<p class="card-text"><strong>风险原因:</strong> ${fusionResult.risk_reasons.join(', ')}</p>` : ''}
        </div>
    `;

    const engineSection = (title, engineData) => {
        if (!engineData) return '';
        return `
            <div class="col-md-6 mb-3">
                <div class="border p-2 rounded h-100">
                    <h6 class="text-muted">${title}</h6>
                    <p class="mb-1"><strong>风险等级:</strong> <span class="${getRiskLevelClass(engineData.risk_level)}">${engineData.risk_level || 'N/A'}</span></p>
                    ${engineData.keywords_found?.length > 0 ? `<p class="mb-1"><strong>命中关键词:</strong> ${engineData.keywords_found.join(', ')}</p>` : ''}
                </div>
            </div>
        `;
    };

    const detailsSection = `
        <div class="mt-3">
            <a href="#" onclick="event.preventDefault(); viewReport('${contentId || 'unknown'}')">查看报告</a>
            <div id="${detailsId}" style="display: none; margin-top: 8px; padding: 10px; border: 1px solid #e0e0e0; background-color: #f8f9fa; border-radius: 4px; max-height: 300px; overflow-y: auto;">
                <pre><code>${JSON.stringify(auditData, null, 2)}</code></pre>
            </div>
        </div>
    `;

    return `
        <div class="card mt-2">
            <div class="card-body">
                ${summarySection}
                <div class="row">
                    ${engineSection('AI引擎结果', data?.ai_result)}
                    ${engineSection('规则引擎结果', data?.rule_result)}
                </div>
                ${detailsSection}
            </div>
        </div>
    `;
}

function toggleDetails(id) {
    const element = document.getElementById(id);
    if (element) {
        element.style.display = element.style.display === 'none' ? 'block' : 'none';
    }
}

// 导出结果
function exportResults() {
    if (auditContentList.length === 0) {
        showNotification('没有可导出的数据', 'warning');
        return;
    }
    
    // 过滤已审核的内容
    const auditedItems = auditContentList.filter(item => item.audit_status === 'approved' && item.auditResult);
    
    if (auditedItems.length === 0) {
        showNotification('没有已审核的内容可导出', 'warning');
        return;
    }
    
    // 生成CSV数据
    const csvData = generateCSVData(auditedItems);
    
    // 下载CSV文件
    downloadCSV(csvData, `${auditCurrentColumnType}_审核结果_${new Date().toISOString().split('T')[0]}.csv`);
    
    showNotification(`成功导出 ${auditedItems.length} 条审核结果`, 'success');
}

// 生成CSV数据
function generateCSVData(items) {
    const headers = ['标题', '栏目类型', '发布时间', '创建时间', '作者', '审核结果', '置信度', '链接'];
    const rows = items.map(item => {
        const result = item.auditResult;
        return [
            `"${item.title}"`,
            item.column_type || item.type || '',
            item.publish_time ? new Date(item.publish_time).toLocaleString() : '',
            item.created_at ? new Date(item.created_at).toLocaleString() : '',
            item.author || '',
            result ? (result.final_decision || '') : '',
            result && result.confidence_score ? (result.confidence_score * 100).toFixed(1) + '%' : '',
            item.url || ''
        ];
    });
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
}

// 下载CSV文件
function downloadCSV(csvData, filename) {
    const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('mediaModal');
    if (event.target === modal) {
        closeMediaModal();
    }
}

// ========== 通用工具函数 ==========

// 生成媒体文件信息HTML
function generateMediaInfoHtml(item) {
    return `
        <div style="font-size: 12px; color: #666;">
            📷 图片: ${item.images?.length || 0} 个 | 
            📢 音频: ${item.audios?.length || 0} 个 | 
            🎥 视频: ${item.videos?.length || 0} 个
            ${(item.mediaFiles?.images?.length > 0 || item.mediaFiles?.videos?.length > 0) ? 
                `<button onclick="showMediaFiles('${item.id}')" style="margin-left: 10px; padding: 2px 8px; background: #007bff; color: white; border: none; border-radius: 3px; font-size: 11px; cursor: pointer;">查看媒体</button>` : 
                ''}
        </div>
    `;
}

// ========== 内容审核相关函数 ==========

// 加载内容审核数据
async function loadAuditContent(page = 1) {
    console.log('loadAuditContent调用，selectedAuditColumnType:', selectedAuditColumnType, '页码:', page);
    
    // 清空选择状态
    auditSelectedContent.clear();
    updateSelectedCount();
    
    if (!selectedAuditColumnType || selectedAuditColumnType.trim() === '') {
        console.warn('栏目类型为空，selectedAuditColumnType:', selectedAuditColumnType);
        showNotification('请先选择栏目类型', 'warning');
        return;
    }
    
    try {
        const columnType = selectedAuditColumnType;
        console.log('发送API请求，栏目类型:', columnType, '页码:', page);
        
        // 显示加载状态
        const contentList = document.getElementById('auditContentList');
        contentList.innerHTML = '<div class="loading">正在加载内容...</div>';
        
        const response = await fetch(`${API_BASE}/api/v1/content/list?column_type=${columnType}&page=${page}&page_size=${auditPageSize}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('审核内容数据:', result);
        
        if (result.success) {
            displayAuditContent(result.data.items);
            updateAuditPagination(result.data.total, result.data.page, result.data.page_size);
            auditCurrentPage = result.data.page;
            auditTotalRecords = result.data.total;
        } else {
            throw new Error(result.message || '加载失败');
        }
        
    } catch (error) {
        console.error('加载内容审核数据失败:', error);

    }
}



// 显示审核内容
function displayAuditContent(items) {
    const contentList = document.getElementById('auditContentList');
    const container = document.getElementById('auditContentContainer');
    
    // 显示审核内容容器
    if (container) {
        container.style.display = 'block';
        console.log('auditContentContainer已显示');
    }
    
    if (!items || items.length === 0) {
        contentList.innerHTML = '<div class="no-content">暂无内容</div>';
        return;
    }
    
    contentList.innerHTML = '';
    
    items.forEach((item, index) => {
        // 构建mediaFiles对象，避免URL编码问题
        if (!item.mediaFiles && (item.images || item.videos || item.audios)) {
            item.mediaFiles = {
                images: (item.images || []).map((url, idx) => ({
                    id: `img_${item.id}_${idx}`,
                    url: url,
                    type: 'image',
                    size: '未知大小'
                })),
                videos: (item.videos || []).map((url, idx) => ({
                    id: `vid_${item.id}_${idx}`,
                    url: url,
                    type: 'video',
                    duration: '未知时长',
                    size: '未知大小'
                }))
            };
        }
        
        const itemDiv = document.createElement('div');
        itemDiv.className = 'content-item';
        itemDiv.style.cssText = 'padding: 15px; border-bottom: 1px solid #eee; display: flex; align-items: center;';

        const titleLink = item.url ?
            `<a href="${item.url}" target="_blank" style="color: #c41e3a; text-decoration: none; font-weight: bold;" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">${item.title}</a>` :
            `<span style="font-weight: bold;">${item.title}</span>`;

        const isSelected = auditSelectedContent.has(String(item.id));

        itemDiv.innerHTML = `
            <div style="margin-right: 15px;">
                <input type="checkbox" id="audit_check_${item.id}" value="${item.id}" ${isSelected ? 'checked' : ''}>
            </div>
            <div style="flex: 1;">
                <div style="margin-bottom: 8px;">
                    <span style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 12px; color: #666; margin-right: 8px;">[${item.column_type}]</span>
                    <span id="status_${item.id}" class="status ${getStatusClass(item.audit_status || item.status || 'pending')}">${getStatusText(item.audit_status || item.status || 'pending')}</span>
                    ${titleLink}
                </div>
                ${item.publish_time ? `<div style="font-size: 12px; color: #999; margin-bottom: 5px;">🕒 发布时间: ${new Date(item.publish_time).toLocaleString()}</div>` : ''}
                ${item.created_at ? `<div style="font-size: 12px; color: #999; margin-bottom: 5px;">📅 创建时间: ${new Date(item.created_at).toLocaleString()}</div>` : ''}
                ${item.content ? `<div style="font-size: 12px; color: #666; margin-bottom: 5px;">📝 ${item.content.substring(0, 100)}${item.content.length > 100 ? '...' : ''}</div>` : ''}
                ${generateMediaInfoHtml(item)}
                <div id="result_${item.id}" style="margin-top: 8px;"></div>
            </div>
            <div style="margin-left: 15px;">
                <button onclick="auditSingleItem('${item.id}')" class="btn btn-primary" style="padding: 5px 10px; font-size: 12px;">${getAuditButtonText(item.audit_status || item.status)}</button>
            </div>
        `;

        contentList.appendChild(itemDiv);

        const checkbox = document.getElementById(`audit_check_${item.id}`);
        if (checkbox) {
            checkbox.addEventListener('change', function() {
                toggleAuditSelection(item.id);
            });
        }
    });

    updateSelectedCount();
    
    // 存储当前内容列表供其他函数使用
    window.currentAuditContentList = items;
    
    // 确保选择状态被清空并更新显示
    auditSelectedContent.clear();
    updateSelectedCount();
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'pending': '待审核',
        'approved': '审核通过', 
        'rejected': '审核不通过',
        'reviewing': '审核中...'
    };
    return statusMap[status] || '待审核';
}

// 获取审核按钮文本
function getAuditButtonText(status) {
    if (status === 'approved' || status === 'rejected') {
        return '重新审核';
    }
    return '审核';
}

// 查看报告功能
function viewReport(contentId) {
    if (!contentId || contentId === 'unknown') {
        showNotification('无效的内容ID', 'error');
        return;
    }
    
    // 获取并显示HTML格式的审核报告
    fetch(`${API_BASE}/api/v1/moderation/content/${contentId}/audit`)
        .then(response => {
            if (!response.ok) {
                throw new Error('获取报告失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.data && data.data.result) {
                // 创建新窗口显示报告
                const reportWindow = window.open('', '_blank', 'width=800,height=600,scrollbars=yes,resizable=yes');
                reportWindow.document.write(data.data.result);
                reportWindow.document.close();
            } else {
                showNotification('暂无审核报告', 'warning');
            }
        })
        .catch(error => {
            console.error('查看报告失败:', error);
            showNotification('查看报告失败: ' + error.message, 'error');
        });
}

// 更新审核分页
function updateAuditPagination(total, currentPage, pageSize) {
    const totalPages = Math.ceil(total / pageSize);
    
    // 更新页码信息
    document.getElementById('auditPaginationInfo').textContent = `第 ${currentPage} 页，共 ${totalPages} 页，总计 ${total} 条`;
    document.getElementById('auditCurrentPageNum').textContent = currentPage;
    
    // 更新按钮状态
    document.getElementById('auditPrevPageBtn').disabled = currentPage <= 1;
    document.getElementById('auditNextPageBtn').disabled = currentPage >= totalPages;
}

// 审核分页 - 上一页
function auditPrevPage() {
    if (auditCurrentPage > 1) {
        auditCurrentPage = auditCurrentPage - 1;
        // 确保auditCurrentColumnType有值
        if (!auditCurrentColumnType && selectedAuditColumnType) {
            auditCurrentColumnType = selectedAuditColumnType;
        }
        fetchAuditContent();
    }
}

// 审核分页 - 下一页
function auditNextPage() {
    const totalPages = Math.ceil(auditTotalRecords / auditPageSize);
    if (auditCurrentPage < totalPages) {
        auditCurrentPage = auditCurrentPage + 1;
        // 确保auditCurrentColumnType有值
        if (!auditCurrentColumnType && selectedAuditColumnType) {
            auditCurrentColumnType = selectedAuditColumnType;
        }
        fetchAuditContent();
    }
}



// 更新选中数量
function updateSelectedCount() {
    const count = auditSelectedContent.size;
    const selectedCountElement = document.getElementById('selectedCount');
    if (selectedCountElement) {
        selectedCountElement.textContent = `已选择: ${count} 项`;
    }

    const auditSelectedBtn = document.getElementById('auditSelectedBtn');
    if (auditSelectedBtn) {
        auditSelectedBtn.disabled = count === 0;
    }

    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const selectAllLabel = document.getElementById('selectAllLabel');
    const totalItems = auditContentList ? auditContentList.length : 0;

    if (selectAllCheckbox) {
        if (totalItems > 0) {
            if (count === 0) {
                selectAllCheckbox.indeterminate = false;
                selectAllCheckbox.checked = false;
                if (selectAllLabel) selectAllLabel.textContent = '全选';
            } else if (count === totalItems) {
                selectAllCheckbox.indeterminate = false;
                selectAllCheckbox.checked = true;
                if (selectAllLabel) selectAllLabel.textContent = '取消全选';
            } else {
                selectAllCheckbox.indeterminate = true;
                selectAllCheckbox.checked = false;
                if (selectAllLabel) selectAllLabel.textContent = '全选';
            }
        } else {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = false;
            if (selectAllLabel) selectAllLabel.textContent = '全选';
        }
    }
}

// 批量审核
async function batchAudit(action) {
    const selectedCheckboxes = document.querySelectorAll('#auditContentList input[type="checkbox"]:checked');
    const selectedIds = Array.from(selectedCheckboxes).map(cb => cb.value);
    
    if (selectedIds.length === 0) {
        showNotification('请先选择要审核的内容', 'warning');
        return;
    }
    
    const actionText = action === 'approve' ? '通过' : '拒绝';
    
    if (!confirm(`确定要${actionText} ${selectedIds.length} 条内容吗？`)) {
        return;
    }
    
    try {
        console.log(`批量${actionText}:`, selectedIds);
        
        // 显示进度
        showBatchProgress(true);
        updateBatchProgress(20, `正在${actionText}内容...`);
        
        const response = await fetch(`${API_BASE}/api/v1/content/batch-audit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content_ids: selectedIds,
                action: action
            })
        });
        
        updateBatchProgress(70, `处理中...`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('批量审核结果:', result);
        
        updateBatchProgress(100, `${actionText}完成！`);
        
        if (result.success) {
            showNotification(`成功${actionText} ${selectedIds.length} 条内容`, 'success');
            
            // 重新加载当前页面
            setTimeout(() => {
                showBatchProgress(false);
                loadAuditContent(auditCurrentPage);
            }, 1500);
        } else {
            throw new Error(result.message || `${actionText}失败`);
        }
        
    } catch (error) {
        console.error(`批量${actionText}失败:`, error);
        updateBatchProgress(0, `${actionText}失败: ${error.message}`);
        showNotification(`批量${actionText}失败: ${error.message}`, 'error');
        
        // 模拟成功
        setTimeout(() => {
            updateBatchProgress(100, `${actionText}完成（模拟）`);
            showNotification(`模拟${actionText} ${selectedIds.length} 条内容`, 'info');
            
            setTimeout(() => {
                showBatchProgress(false);
                loadAuditContent(auditCurrentPage);
            }, 1500);
        }, 1000);
    }
}

// 显示/隐藏批量操作进度
function showBatchProgress(show) {
    const progressDiv = document.getElementById('batchProgress');
    if (progressDiv) {
        progressDiv.style.display = show ? 'block' : 'none';
    }
}

// 更新批量操作进度
function updateBatchProgress(percentage, status) {
    const progressBar = document.getElementById('batchProgressBar');
    const statusText = document.getElementById('batchStatus');
    
    if (progressBar) {
        progressBar.style.width = percentage + '%';
    }
    
    if (statusText) {
        statusText.textContent = status;
    }
}

// 栏目类型变更时重新加载
function onAuditColumnTypeChange() {
    auditCurrentPage = 1;
    loadAuditContent(1);
}