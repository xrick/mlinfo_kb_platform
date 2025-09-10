// Main application logic for SalesRAG Integration
let currentView = 'sales-ai';

// Initialize the application
function initializeApp() {
    console.log('Initializing SalesRAG Integration App...');
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize default view
    switchView('sales-ai');
    
    // Load initial data
    loadHistory();
    
    console.log('App initialized successfully');
}

// Set up event listeners
function setupEventListeners() {
    // Navigation buttons
    document.getElementById('sales-ai-btn').addEventListener('click', () => switchView('sales-ai'));
    document.getElementById('add-specs-btn').addEventListener('click', () => switchView('add-specs'));
    document.getElementById('milvus-viewer-btn').addEventListener('click', () => switchView('milvus-viewer'));
    
    // File upload
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    
    if (fileInput && uploadArea) {
        fileInput.addEventListener('change', handleFileSelect);
        
        // Drag and drop functionality
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
    }
    
    // Upload actions
    const confirmUpload = document.getElementById('confirmUpload');
    const cancelUpload = document.getElementById('cancelUpload');
    
    if (confirmUpload) {
        confirmUpload.addEventListener('click', handleConfirmUpload);
    }
    
    if (cancelUpload) {
        cancelUpload.addEventListener('click', handleCancelUpload);
    }
}

// View switching functionality
function switchView(viewName) {
    console.log(`Switching to view: ${viewName}`);
    
    // Hide all views
    document.querySelectorAll('.content-view').forEach(view => {
        view.classList.remove('active');
        view.classList.add('hidden');
    });
    
    // Show selected view
    const targetView = document.getElementById(viewName + '-view');
    if (targetView) {
        targetView.classList.remove('hidden');
        targetView.classList.add('active');
    }
    
    // Update navigation buttons
    document.querySelectorAll('.nav-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const targetButton = document.getElementById(viewName + '-btn');
    if (targetButton) {
        targetButton.classList.add('active');
    }
    
    // Update current view
    currentView = viewName;
    
    // Initialize view-specific functionality
    if (viewName === 'sales-ai') {
        initializeSalesAI();
    } else if (viewName === 'add-specs') {
        initializeAddSpecs();
    } else if (viewName === 'milvus-viewer') {
        initializeMilvusViewer();
    }
}

// Initialize Sales-AI view
function initializeSalesAI() {
    console.log('Initializing Sales-AI view...');
    
    // Initialize sales AI functionality (from sales_ai.js)
    if (typeof initSalesAI === 'function') {
        initSalesAI();
    }
}

// Initialize Add Specifications view
function initializeAddSpecs() {
    console.log('Initializing Add Specifications view...');
    
    // Reset upload state
    resetUploadState();
    
    // Load template information
    loadTemplate();
}

// File handling functions
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        processFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        processFile(file);
    }
}

// Process uploaded file
async function processFile(file) {
    console.log('Processing file:', file.name);
    
    // Show processing section
    showProcessingSection();
    updateProgress(0, '準備處理檔案...');
    
    try {
        updateProgress(25, '讀取檔案內容...');
        
        // Read file content as text
        const fileContent = await readFileAsText(file);
        
        updateProgress(50, '解析 CSV 內容...');
        
        // Call MLINFO API for processing
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text_content: fileContent,
                custom_rules: null,
                temp_regex: null,
                file_name: file.name
            })
        });
        
        if (!response.ok) {
            throw new Error(`處理失敗: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Handle modeltype input requirement
        if (result.require_modeltype_input) {
            let userModeltype = prompt('無法自動判斷型號，請輸入 modeltype（如 960、928...）：\n或直接按確定使用檔名作為型號');
            
            // If user cancels or provides empty input, try to use filename as default
            if (!userModeltype || !userModeltype.trim()) {
                const fileName = file.name;
                const baseFileName = fileName.replace(/\.(csv|CSV)$/i, '');
                
                if (baseFileName && baseFileName.length <= 15 && /^[A-Za-z0-9_-]+$/.test(baseFileName)) {
                    userModeltype = baseFileName;
                    console.log(`使用檔名作為預設 modeltype: ${userModeltype}`);
                } else {
                    userModeltype = 'unknown';
                    console.log('使用預設 modeltype: unknown');
                }
            }
            
            // Retry with user input
            const retryResponse = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text_content: fileContent,
                    custom_rules: null,
                    temp_regex: null,
                    file_name: file.name,
                    user_modeltype: userModeltype.trim()
                })
            });
            
            if (!retryResponse.ok) {
                throw new Error(`重新處理失敗: ${retryResponse.status}`);
            }
            
            const retryResult = await retryResponse.json();
            updateProgress(75, '準備預覽...');
            showPreview(retryResult);
        } else {
            updateProgress(75, '準備預覽...');
            showPreview(result);
        }
        
        updateProgress(100, '處理完成！');
        
        // Hide processing section after a delay
        setTimeout(() => {
            hideProcessingSection();
        }, 1000);
        
    } catch (error) {
        console.error('File processing error:', error);
        updateProgress(0, `處理失敗: ${error.message}`);
        
        // Hide processing section after error
        setTimeout(() => {
            hideProcessingSection();
        }, 3000);
    }
}

// Helper function to read file as text
function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(new Error('檔案讀取失敗'));
        reader.readAsText(file, 'UTF-8');
    });
}

// Show preview of processed data
function showPreview(data) {
    const previewSection = document.getElementById('previewSection');
    const previewContainer = document.getElementById('previewContainer');
    
    if (!previewSection || !previewContainer) return;
    
    // Create preview content
    let previewHTML = `
        <div class="preview-info">
            <h4>檔案資訊</h4>
            <p><strong>檔案名稱:</strong> ${data.filename}</p>
            <p><strong>總行數:</strong> ${data.stats.total_rows}</p>
            <p><strong>總欄位數:</strong> ${data.stats.total_columns}</p>
        </div>
        
        <div class="preview-data">
            <h4>資料預覽</h4>
            <div class="preview-table-container">
                <table class="preview-table">
                    <thead>
                        <tr>
                            ${data.stats.columns.map(col => `<th>${col}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${data.preview.map(row => `
                            <tr>
                                ${data.stats.columns.map(col => `<td>${row[col] || ''}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    previewContainer.innerHTML = previewHTML;
    previewSection.style.display = 'block';
    
    // Store data for confirmation
    previewSection.dataset.uploadData = JSON.stringify(data);
}

// Handle upload confirmation
async function handleConfirmUpload() {
    const previewSection = document.getElementById('previewSection');
    const uploadData = JSON.parse(previewSection.dataset.uploadData || '{}');
    
    if (!uploadData.data) {
        alert('沒有可上傳的資料');
        return;
    }
    
    try {
        showProcessingSection();
        updateProgress(0, '開始匯入資料庫...');
        
        // Call MLINFO ingest API
        const response = await fetch('/api/ingest-to-db', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                data: uploadData.data
            })
        });
        
        updateProgress(50, '儲存至 DuckDB 和 Milvus...');
        
        if (!response.ok) {
            throw new Error(`匯入失敗: ${response.status}`);
        }
        
        const result = await response.json();
        
        updateProgress(100, '匯入完成！');
        
        // Show success message
        alert(`資料匯入完成！\nDuckDB: ${result.duckdb_rows_added} 筆\nMilvus: ${result.milvus_entities_added} 筆`);
        
        // Reset upload state
        resetUploadState();
        
        // Refresh history
        loadHistory();
        
    } catch (error) {
        console.error('Upload confirmation error:', error);
        alert(`匯入失敗: ${error.message}`);
    } finally {
        hideProcessingSection();
    }
}

// Handle upload cancellation
function handleCancelUpload() {
    resetUploadState();
}

// Reset upload state
function resetUploadState() {
    // Hide sections
    hideProcessingSection();
    const previewSection = document.getElementById('previewSection');
    if (previewSection) {
        previewSection.style.display = 'none';
    }
    
    // Reset file input
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.value = '';
    }
    
    // Reset upload area
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.classList.remove('dragover');
    }
}

// Processing section functions
function showProcessingSection() {
    const section = document.getElementById('processingSection');
    if (section) {
        section.style.display = 'block';
    }
}

function hideProcessingSection() {
    const section = document.getElementById('processingSection');
    if (section) {
        section.style.display = 'none';
    }
}

function updateProgress(percentage, text) {
    const progressFill = document.getElementById('progressFill');
    const processingText = document.getElementById('processingText');
    
    if (progressFill) {
        progressFill.style.width = percentage + '%';
    }
    
    if (processingText) {
        processingText.textContent = text;
    }
}

// Template loading
async function loadTemplate() {
    try {
        const response = await fetch('/api/specs/template');
        const template = await response.json();
        
        console.log('Template loaded:', template);
        
        // You can use this template data to show helpful information
        // about the expected data format
        
    } catch (error) {
        console.error('Failed to load template:', error);
    }
}

// Global functions for other modules
window.switchView = switchView;
window.initializeApp = initializeApp;