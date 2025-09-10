/**
 * Milvus Collection Viewer - 前端邏輯
 * 提供 Milvus 資料庫和集合的視覺化查看功能
 */

class MilvusViewer {
    constructor() {
        this.currentDatabase = 'default';
        this.currentCollection = null;
        this.currentPage = 1;
        this.pageSize = 50;
        this.isLoading = false;
        
        this.init();
    }
    
    /**
     * 初始化 Milvus Viewer
     */
    init() {
        this.createViewerHTML();
        this.bindEvents();
        this.loadInitialData();
    }
    
    /**
     * 創建 Milvus Viewer 的 HTML 結構
     */
    createViewerHTML() {
        const mainContent = document.querySelector('.main-content');
        
        const viewerHTML = `
            <!-- Milvus Viewer -->
            <div id="milvus-viewer-view" class="content-view">
                <div class="viewer-header">
                    <h1>🗂️ Milvus Collection Viewer</h1>
                    <p>查看和管理 Milvus 向量資料庫集合</p>
                </div>

                <div class="viewer-content">
                    <!-- 左側：資料庫和集合選擇 -->
                    <div class="viewer-sidebar">
                        <div class="database-section">
                            <h3>📊 資料庫</h3>
                            <select id="databaseSelect" class="form-control">
                                <option value="default">default (預設)</option>
                            </select>
                        </div>
                        
                        <div class="collections-section">
                            <div class="collections-header">
                                <h3>📁 集合列表</h3>
                                <button id="refreshCollections" class="btn btn--sm btn--outline">
                                    🔄 刷新
                                </button>
                            </div>
                            <div id="collectionsContainer" class="collections-container">
                                <div class="loading-indicator">載入中...</div>
                            </div>
                        </div>
                        
                        <div class="connection-status">
                            <h4>🔗 連接狀態</h4>
                            <div id="connectionStatus" class="status-indicator">
                                <span class="status-dot"></span>
                                <span class="status-text">檢查中...</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 右側：集合詳細資訊 -->
                    <div class="viewer-main">
                        <div id="collectionDetails" class="collection-details">
                            <div class="no-selection">
                                <div class="placeholder-icon">📋</div>
                                <h3>請選擇一個集合</h3>
                                <p>從左側集合列表中選擇要查看的集合</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        mainContent.insertAdjacentHTML('beforeend', viewerHTML);
    }
    
    /**
     * 綁定事件處理器
     */
    bindEvents() {
        // 資料庫選擇變更
        document.getElementById('databaseSelect').addEventListener('change', (e) => {
            this.currentDatabase = e.target.value;
            this.loadCollections();
        });
        
        // 刷新集合列表
        document.getElementById('refreshCollections').addEventListener('click', () => {
            this.loadCollections();
        });
    }
    
    /**
     * 載入初始資料
     */
    async loadInitialData() {
        await this.checkConnectionStatus();
        await this.loadDatabases();
        await this.loadCollections();
    }
    
    /**
     * 檢查 Milvus 連接狀態
     */
    async checkConnectionStatus() {
        try {
            const response = await fetch('/api/milvus/connection/status');
            const result = await response.json();
            
            const statusElement = document.getElementById('connectionStatus');
            const statusDot = statusElement.querySelector('.status-dot');
            const statusText = statusElement.querySelector('.status-text');
            
            if (result.success && result.data.can_connect) {
                statusDot.className = 'status-dot status-connected';
                statusText.textContent = `已連接 (${result.data.host}:${result.data.port})`;
            } else {
                statusDot.className = 'status-dot status-disconnected';
                statusText.textContent = '連接失敗';
            }
        } catch (error) {
            console.error('檢查連接狀態失敗:', error);
            const statusElement = document.getElementById('connectionStatus');
            const statusDot = statusElement.querySelector('.status-dot');
            const statusText = statusElement.querySelector('.status-text');
            statusDot.className = 'status-dot status-error';
            statusText.textContent = '檢查失敗';
        }
    }
    
    /**
     * 載入資料庫列表
     */
    async loadDatabases() {
        try {
            const response = await fetch('/api/milvus/databases');
            const result = await response.json();
            
            if (result.success) {
                const select = document.getElementById('databaseSelect');
                select.innerHTML = '';
                
                result.data.databases.forEach(db => {
                    const option = document.createElement('option');
                    option.value = db;
                    option.textContent = db === 'default' ? `${db} (預設)` : db;
                    option.selected = db === result.data.default_database;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('載入資料庫列表失敗:', error);
        }
    }
    
    /**
     * 載入集合列表
     */
    async loadCollections() {
        const container = document.getElementById('collectionsContainer');
        container.innerHTML = '<div class="loading-indicator">載入中...</div>';
        
        try {
            const response = await fetch('/api/milvus/collections');
            const result = await response.json();
            
            if (result.success) {
                const collections = result.data.collections;
                
                if (collections.length === 0) {
                    container.innerHTML = '<div class="empty-state">此資料庫中沒有集合</div>';
                    return;
                }
                
                let html = '<div class="collections-list">';
                collections.forEach(collection => {
                    const statusClass = this.getStatusClass(collection.status);
                    html += `
                        <div class="collection-item" data-collection="${collection.name}">
                            <div class="collection-header">
                                <h4 class="collection-name">${collection.name}</h4>
                                <span class="collection-status ${statusClass}">${collection.status}</span>
                            </div>
                            <div class="collection-meta">
                                <span class="record-count">📊 ${collection.row_count.toLocaleString()} 筆記錄</span>
                                ${collection.description ? `<p class="collection-description">${collection.description}</p>` : ''}
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                
                container.innerHTML = html;
                
                // 綁定集合點擊事件
                container.querySelectorAll('.collection-item').forEach(item => {
                    item.addEventListener('click', () => {
                        const collectionName = item.getAttribute('data-collection');
                        this.selectCollection(collectionName);
                    });
                });
                
                // 如果有預設的集合，自動選擇
                if (collections.find(c => c.name === 'product_semantic_chunks')) {
                    this.selectCollection('product_semantic_chunks');
                }
            } else {
                container.innerHTML = `<div class="error-state">載入失敗: ${result.message}</div>`;
            }
        } catch (error) {
            console.error('載入集合列表失敗:', error);
            container.innerHTML = '<div class="error-state">載入集合列表時發生錯誤</div>';
        }
    }
    
    /**
     * 選擇集合
     */
    async selectCollection(collectionName) {
        if (this.isLoading) return;
        
        // 更新選中狀態
        document.querySelectorAll('.collection-item').forEach(item => {
            item.classList.remove('selected');
        });
        document.querySelector(`[data-collection="${collectionName}"]`).classList.add('selected');
        
        this.currentCollection = collectionName;
        this.currentPage = 1;
        
        await this.loadCollectionDetails(collectionName);
    }
    
    /**
     * 載入集合詳細資訊
     */
    async loadCollectionDetails(collectionName) {
        this.isLoading = true;
        const detailsContainer = document.getElementById('collectionDetails');
        
        detailsContainer.innerHTML = '<div class="loading-indicator">載入集合詳細資訊中...</div>';
        
        try {
            // 並行載入 schema、統計資訊和資料
            const [schemaResponse, statsResponse, dataResponse] = await Promise.all([
                fetch(`/api/milvus/collection/${collectionName}/schema`),
                fetch(`/api/milvus/collection/${collectionName}/statistics`),
                fetch(`/api/milvus/collection/${collectionName}/data?page=1&page_size=${this.pageSize}`)
            ]);
            
            const schemaResult = await schemaResponse.json();
            const statsResult = await statsResponse.json();
            const dataResult = await dataResponse.json();
            
            if (schemaResult.success && statsResult.success && dataResult.success) {
                this.renderCollectionDetails(schemaResult.data, statsResult.data, dataResult.data);
            } else {
                detailsContainer.innerHTML = '<div class="error-state">載入集合詳細資訊失敗</div>';
            }
        } catch (error) {
            console.error('載入集合詳細資訊失敗:', error);
            detailsContainer.innerHTML = '<div class="error-state">載入時發生錯誤</div>';
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * 渲染集合詳細資訊
     */
    renderCollectionDetails(schema, stats, data) {
        const detailsContainer = document.getElementById('collectionDetails');
        
        let html = `
            <div class="collection-header-info">
                <h2>📋 ${schema.collection_name}</h2>
                ${schema.description ? `<p class="collection-description">${schema.description}</p>` : ''}
            </div>
            
            <div class="collection-tabs">
                <button class="tab-button active" data-tab="data">📊 資料</button>
                <button class="tab-button" data-tab="schema">🏗️ Schema</button>
                <button class="tab-button" data-tab="stats">📈 統計</button>
            </div>
            
            <div class="tab-content">
                <div id="data-tab" class="tab-pane active">
                    ${this.renderDataTab(data)}
                </div>
                <div id="schema-tab" class="tab-pane">
                    ${this.renderSchemaTab(schema)}
                </div>
                <div id="stats-tab" class="tab-pane">
                    ${this.renderStatsTab(stats)}
                </div>
            </div>
        `;
        
        detailsContainer.innerHTML = html;
        
        // 綁定 tab 切換事件
        detailsContainer.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', () => {
                this.switchTab(button.getAttribute('data-tab'));
            });
        });
        
        // 如果有資料，綁定分頁事件
        if (data.pagination) {
            this.bindPaginationEvents(data.pagination);
        }
    }
    
    /**
     * 渲染資料 tab
     */
    renderDataTab(data) {
        if (!data.records || data.records.length === 0) {
            return '<div class="empty-state">此集合中沒有資料</div>';
        }
        
        const pagination = data.pagination;
        let html = `
            <div class="data-section">
                <div class="data-header">
                    <h3>📊 集合資料</h3>
                    <div class="data-info">
                        共 ${pagination.total_records.toLocaleString()} 筆記錄，
                        第 ${pagination.current_page} / ${pagination.total_pages} 頁
                    </div>
                </div>
        `;
        
        // 向量欄位提示
        if (data.vector_fields && data.vector_fields.length > 0) {
            html += '<div class="vector-fields-info">';
            html += '<strong>向量欄位：</strong>';
            data.vector_fields.forEach(field => {
                html += `<span class="vector-field">${field.name} (${field.dimension}維)</span>`;
            });
            html += '</div>';
        }
        
        // 資料表格
        html += '<div class="data-table-container">';
        if (data.records.length > 0) {
            const headers = Object.keys(data.records[0]);
            
            html += '<table class="data-table">';
            html += '<thead><tr>';
            headers.forEach(header => {
                html += `<th>${header}</th>`;
            });
            html += '</tr></thead>';
            
            html += '<tbody>';
            data.records.forEach(record => {
                html += '<tr>';
                headers.forEach(header => {
                    let value = record[header];
                    if (typeof value === 'object') {
                        value = JSON.stringify(value);
                    }
                    html += `<td>${value}</td>`;
                });
                html += '</tr>';
            });
            html += '</tbody>';
            html += '</table>';
        }
        html += '</div>';
        
        // 分頁控制
        if (pagination.total_pages > 1) {
            html += this.renderPagination(pagination);
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * 渲染 Schema tab
     */
    renderSchemaTab(schema) {
        let html = `
            <div class="schema-section">
                <h3>🏗️ 集合 Schema</h3>
                
                <div class="schema-info">
                    <div class="info-item">
                        <strong>集合名稱：</strong> ${schema.collection_name}
                    </div>
                    <div class="info-item">
                        <strong>欄位數量：</strong> ${schema.fields.length}
                    </div>
                    ${schema.description ? `<div class="info-item"><strong>描述：</strong> ${schema.description}</div>` : ''}
                </div>
                
                <div class="fields-section">
                    <h4>📝 欄位定義</h4>
                    <div class="fields-table">
                        <table class="schema-table">
                            <thead>
                                <tr>
                                    <th>欄位名稱</th>
                                    <th>資料類型</th>
                                    <th>主鍵</th>
                                    <th>維度</th>
                                    <th>描述</th>
                                </tr>
                            </thead>
                            <tbody>
        `;
        
        schema.fields.forEach(field => {
            html += `
                <tr>
                    <td><strong>${field.name}</strong></td>
                    <td><span class="data-type">${field.data_type}</span></td>
                    <td>${field.is_primary ? '✅' : '❌'}</td>
                    <td>${field.dimension || '-'}</td>
                    <td>${field.description || '-'}</td>
                </tr>
            `;
        });
        
        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
        `;
        
        // 索引資訊
        if (schema.indexes && schema.indexes.length > 0) {
            html += `
                <div class="indexes-section">
                    <h4>🔍 索引資訊</h4>
                    <div class="indexes-list">
            `;
            schema.indexes.forEach(index => {
                html += `
                    <div class="index-item">
                        <strong>${index.field_name}</strong> - 
                        類型: ${index.index_type}, 
                        距離度量: ${index.metric_type}
                    </div>
                `;
            });
            html += '</div></div>';
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * 渲染統計 tab
     */
    renderStatsTab(stats) {
        return `
            <div class="stats-section">
                <h3>📈 集合統計</h3>
                
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${stats.row_count.toLocaleString()}</div>
                        <div class="stat-label">總記錄數</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.field_count}</div>
                        <div class="stat-label">欄位數量</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.is_loaded ? '已載入' : '未載入'}</div>
                        <div class="stat-label">載入狀態</div>
                    </div>
                </div>
                
                ${stats.description ? `
                    <div class="stats-description">
                        <h4>描述</h4>
                        <p>${stats.description}</p>
                    </div>
                ` : ''}
                
                <div class="raw-stats">
                    <h4>原始統計資訊</h4>
                    <pre class="stats-json">${JSON.stringify(stats.raw_stats, null, 2)}</pre>
                </div>
            </div>
        `;
    }
    
    /**
     * 渲染分頁控制
     */
    renderPagination(pagination) {
        let html = '<div class="pagination-container">';
        html += '<div class="pagination">';
        
        // 上一頁
        if (pagination.current_page > 1) {
            html += `<button class="pagination-btn" data-page="${pagination.current_page - 1}">« 上一頁</button>`;
        }
        
        // 頁碼
        const startPage = Math.max(1, pagination.current_page - 2);
        const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);
        
        if (startPage > 1) {
            html += '<button class="pagination-btn" data-page="1">1</button>';
            if (startPage > 2) html += '<span class="pagination-ellipsis">...</span>';
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === pagination.current_page ? ' active' : '';
            html += `<button class="pagination-btn${activeClass}" data-page="${i}">${i}</button>`;
        }
        
        if (endPage < pagination.total_pages) {
            if (endPage < pagination.total_pages - 1) html += '<span class="pagination-ellipsis">...</span>';
            html += `<button class="pagination-btn" data-page="${pagination.total_pages}">${pagination.total_pages}</button>`;
        }
        
        // 下一頁
        if (pagination.current_page < pagination.total_pages) {
            html += `<button class="pagination-btn" data-page="${pagination.current_page + 1}">下一頁 »</button>`;
        }
        
        html += '</div></div>';
        return html;
    }
    
    /**
     * 綁定分頁事件
     */
    bindPaginationEvents(pagination) {
        setTimeout(() => {
            document.querySelectorAll('.pagination-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const page = parseInt(btn.getAttribute('data-page'));
                    if (page && page !== pagination.current_page) {
                        await this.loadCollectionData(page);
                    }
                });
            });
        }, 100);
    }
    
    /**
     * 載入指定頁面的集合資料
     */
    async loadCollectionData(page) {
        if (!this.currentCollection || this.isLoading) return;
        
        this.isLoading = true;
        this.currentPage = page;
        
        const dataTab = document.getElementById('data-tab');
        dataTab.innerHTML = '<div class="loading-indicator">載入資料中...</div>';
        
        try {
            const response = await fetch(`/api/milvus/collection/${this.currentCollection}/data?page=${page}&page_size=${this.pageSize}`);
            const result = await response.json();
            
            if (result.success) {
                dataTab.innerHTML = this.renderDataTab(result.data);
                this.bindPaginationEvents(result.data.pagination);
            } else {
                dataTab.innerHTML = '<div class="error-state">載入資料失敗</div>';
            }
        } catch (error) {
            console.error('載入集合資料失敗:', error);
            dataTab.innerHTML = '<div class="error-state">載入時發生錯誤</div>';
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * 切換 tab
     */
    switchTab(tabName) {
        // 更新按鈕狀態
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // 更新內容顯示
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }
    
    /**
     * 取得集合狀態對應的 CSS 類別
     */
    getStatusClass(status) {
        const statusMap = {
            'loaded': 'status-loaded',
            'not_loaded': 'status-not-loaded',
            'error': 'status-error'
        };
        return statusMap[status] || 'status-unknown';
    }
}

// 全域實例
let milvusViewer;

// 當文檔載入完成時初始化
document.addEventListener('DOMContentLoaded', function() {
    // 等待頁面完全載入後再初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeMilvusViewer);
    } else {
        initializeMilvusViewer();
    }
});

function initializeMilvusViewer() {
    // 延遲初始化，確保其他腳本已載入
    setTimeout(() => {
        if (!milvusViewer) {
            milvusViewer = new MilvusViewer();
        }
    }, 500);
}