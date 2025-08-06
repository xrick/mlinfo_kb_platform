// History management for SalesRAG Integration

// Load and display history
async function loadHistory() {
    console.log('Loading history...');
    
    const historyContainer = document.getElementById('historyContainer');
    if (!historyContainer) return;
    
    // Show loading state
    historyContainer.innerHTML = '<div class="history-loading">載入歷史記錄中...</div>';
    
    try {
        const response = await fetch('/api/history/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayHistory(data.history || []);
        
    } catch (error) {
        console.error('Failed to load history:', error);
        historyContainer.innerHTML = `
            <div class="history-error">
                <p style="color: red;">載入歷史記錄失敗</p>
                <p style="font-size: 12px;">${error.message}</p>
                <button onclick="loadHistory()" class="btn btn--sm">重試</button>
            </div>
        `;
    }
}

// Display history in the sidebar
function displayHistory(historyData) {
    const historyContainer = document.getElementById('historyContainer');
    if (!historyContainer) return;
    
    if (historyData.length === 0) {
        historyContainer.innerHTML = `
            <div class="history-empty">
                <p>尚無資料處理記錄</p>
                <small>成功處理的資料會顯示在這裡</small>
            </div>
        `;
        return;
    }
    
    // Create history items
    const historyHTML = historyData.map(item => createHistoryItem(item)).join('');
    historyContainer.innerHTML = historyHTML;
    
    // Add click event listeners for history items
    historyContainer.querySelectorAll('.history-item').forEach(item => {
        item.addEventListener('click', () => {
            const itemId = item.dataset.id;
            showHistoryDetails(itemId);
        });
    });
}

// Create individual history item HTML
function createHistoryItem(item) {
    const timestamp = new Date(item.timestamp).toLocaleString('zh-TW');
    const statusClass = item.status === 'success' ? 'success' : 'error';
    const statusText = item.status === 'success' ? '成功' : '部分失敗';
    
    return `
        <div class="history-item" data-id="${item.id}" title="點擊查看詳情">
            <div class="history-item-header">
                <div class="history-item-name">${item.filename}</div>
                <div class="history-item-status ${statusClass}">${statusText}</div>
            </div>
            <div class="history-item-info">
                <div>類型: ${getDataTypeText(item.data_type)}</div>
                <div>筆數: ${item.record_count}</div>
                <div>時間: ${timestamp}</div>
            </div>
        </div>
    `;
}

// Get user-friendly data type text
function getDataTypeText(dataType) {
    const typeMap = {
        'specifications': '規格資料',
        'sales': '銷售資料',
        'inventory': '庫存資料',
        'unknown': '未知類型'
    };
    
    return typeMap[dataType] || dataType;
}

// Show detailed information for a history item
async function showHistoryDetails(itemId) {
    try {
        // For now, just show a simple alert
        // In the future, you could open a modal with more details
        
        const historyItem = document.querySelector(`.history-item[data-id="${itemId}"]`);
        if (historyItem) {
            const filename = historyItem.querySelector('.history-item-name').textContent;
            const recordCount = historyItem.querySelector('.history-item-info').textContent;
            
            alert(`檔案詳情:\n檔案名稱: ${filename}\n${recordCount}`);
        }
        
    } catch (error) {
        console.error('Failed to show history details:', error);
        alert('無法載入詳細資訊');
    }
}

// Refresh history manually
function refreshHistory() {
    console.log('Refreshing history...');
    loadHistory();
}

// Add new history record (called from other modules)
async function addHistoryRecord(filename, dataType, recordCount, errorCount = 0) {
    try {
        const response = await fetch('/api/history/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: filename,
                data_type: dataType,
                record_count: recordCount,
                error_count: errorCount,
                status: errorCount === 0 ? 'success' : 'partial'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('History record added:', result);
        
        // Refresh history display
        loadHistory();
        
        return result;
        
    } catch (error) {
        console.error('Failed to add history record:', error);
        throw error;
    }
}

// Delete history record
async function deleteHistoryRecord(itemId) {
    try {
        const response = await fetch(`/api/history/${itemId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Refresh history display
        loadHistory();
        
    } catch (error) {
        console.error('Failed to delete history record:', error);
        alert('刪除記錄失敗');
    }
}

// Get history statistics
async function getHistoryStats() {
    try {
        const response = await fetch('/api/history/stats');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const stats = await response.json();
        return stats;
        
    } catch (error) {
        console.error('Failed to get history stats:', error);
        return null;
    }
}

// Export functions for use in other modules
window.loadHistory = loadHistory;
window.refreshHistory = refreshHistory;
window.addHistoryRecord = addHistoryRecord;
window.deleteHistoryRecord = deleteHistoryRecord;
window.getHistoryStats = getHistoryStats;