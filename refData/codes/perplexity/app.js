// Business AI Assistant JavaScript

// Application data
const appData = {
  aiModels: [
    {
      id: "gpt4",
      name: "GPT-4",
      advantage: "創意寫作",
      description: "最適合創意內容生成、文案寫作和複雜推理任務",
      strengths: ["創意寫作", "邏輯推理", "多語言支援"],
      weaknesses: ["成本較高", "回應時間較長"],
      icon: "✍️"
    },
    {
      id: "claude",
      name: "Claude",
      advantage: "數據分析",
      description: "專精於數據分析、圖表解讀和結構化資料處理",
      strengths: ["數據分析", "文檔處理", "安全性高"],
      weaknesses: ["創意能力一般", "圖片處理限制"],
      icon: "📊"
    },
    {
      id: "gemini",
      name: "Gemini",
      advantage: "快速回應",
      description: "提供快速回應，適合即時對話和簡單任務處理",
      strengths: ["回應速度快", "成本效益高", "多模態支援"],
      weaknesses: ["複雜推理能力有限", "準確性一般"],
      icon: "⚡"
    }
  ],
  salesFlow: [
    {
      id: 1,
      title: "匯入資料",
      description: "上傳客戶資料或匯入現有資料庫",
      icon: "📄",
      details: "支援 CSV、Excel、JSON 等多種格式，自動識別資料結構"
    },
    {
      id: 2,
      title: "AI 分析 & 分群",
      description: "AI 自動分析客戶特徵並進行分群",
      icon: "✨",
      details: "基於購買行為、興趣偏好等維度進行智慧分群"
    },
    {
      id: 3,
      title: "產生初版文案",
      description: "為不同客戶群體生成個性化文案",
      icon: "✏️",
      details: "根據客戶分群特徵，自動生成適合的行銷文案"
    },
    {
      id: 4,
      title: "啟動對話",
      description: "開始與客戶進行個性化對話",
      icon: "💬",
      details: "使用 AI 協助進行客戶互動，提供即時回應建議"
    },
    {
      id: 5,
      title: "追蹤進度",
      description: "監控對話進度和轉換率",
      icon: "📈",
      details: "即時追蹤客戶互動進度，分析轉換效果"
    }
  ],
  dataImportList: [
    {
      id: 1,
      name: "客戶資料庫_2024Q1.csv",
      date: "2024-01-15",
      status: "completed",
      type: "csv",
      records: 1250
    },
    {
      id: 2,
      name: "潛在客戶_科技業.xlsx",
      date: "2024-01-16",
      status: "processing",
      type: "excel",
      records: 850
    },
    {
      id: 3,
      name: "會員資料_高價值客戶.json",
      date: "2024-01-17",
      status: "failed",
      type: "json",
      records: 320
    },
    {
      id: 4,
      name: "銷售線索_金融業.csv",
      date: "2024-01-18",
      status: "completed",
      type: "csv",
      records: 680
    }
  ],
  conversationStages: [
    {
      id: "initial",
      name: "初步接觸",
      description: "建立第一次聯繫，了解客戶基本需求"
    },
    {
      id: "exploration",
      name: "需求探索",
      description: "深入了解客戶痛點和具體需求"
    },
    {
      id: "presentation",
      name: "方案展示",
      description: "提供解決方案並展示價值"
    },
    {
      id: "closing",
      name: "成交",
      description: "完成交易並建立長期合作關係"
    }
  ],
  smartSuggestions: [
    "詢問客戶預算範圍",
    "發送產品目錄",
    "安排產品示範",
    "提供客戶案例",
    "邀請參加網路研討會"
  ]
};

// Application state
let selectedModel = null;
let currentFlowStep = 1;
let currentConversationStage = 'initial';
let currentModelForSelection = null;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
  initializeApp();
  setupEventListeners();
  
  // Add initial welcome message
  setTimeout(() => {
    addChatMessage("歡迎使用業務 AI 助理！請先選擇一個 AI 模型開始使用。", 'ai');
  }, 500);
});

function initializeApp() {
  renderModelCards();
  renderTimeline();
  renderDataList();
  renderSmartSuggestions();
  updateFunnelStage();
}

function setupEventListeners() {
  // Use event delegation for all click events
  document.addEventListener('click', function(e) {
    e.preventDefault();
    
    // Handle info button clicks FIRST (highest priority)
    if (e.target.classList.contains('info-btn')) {
      e.stopPropagation();
      showFlowDetails(e.target);
      return;
    }
    
    // Handle import button
    if (e.target.closest('#importBtn')) {
      e.stopPropagation();
      openModal('uploadModal');
      return;
    }
    
    // Handle model card clicks
    const modelCard = e.target.closest('.model-card');
    if (modelCard) {
      e.stopPropagation();
      handleModelSelection(modelCard);
      return;
    }
    
    // Handle suggestion chips
    const suggestionChip = e.target.closest('.suggestion-chip');
    if (suggestionChip) {
      e.stopPropagation();
      const chatInput = document.getElementById('chatInput');
      chatInput.value = suggestionChip.textContent;
      sendMessage();
      return;
    }
    
    // Handle send button
    if (e.target.closest('#sendBtn')) {
      e.stopPropagation();
      sendMessage();
      return;
    }
    
    // Handle modal close buttons
    if (e.target.id === 'closeModal') {
      closeModal('modelModal');
      return;
    }
    
    if (e.target.id === 'cancelBtn') {
      closeModal('modelModal');
      return;
    }
    
    if (e.target.id === 'selectBtn') {
      selectCurrentModel();
      return;
    }
    
    if (e.target.id === 'closeFlowModal') {
      closeModal('flowModal');
      return;
    }
    
    if (e.target.id === 'flowOkBtn') {
      closeModal('flowModal');
      return;
    }
    
    if (e.target.id === 'closeUploadModal') {
      closeModal('uploadModal');
      return;
    }
    
    if (e.target.id === 'cancelUpload') {
      closeModal('uploadModal');
      return;
    }
    
    if (e.target.id === 'confirmUpload') {
      handleFileUpload();
      return;
    }
  });
  
  // Chat input keypress
  document.getElementById('chatInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendMessage();
    }
  });
  
  // Upload area setup
  const uploadArea = document.getElementById('uploadArea');
  const fileInput = document.getElementById('fileInput');
  
  uploadArea.addEventListener('click', function(e) {
    e.preventDefault();
    fileInput.click();
  });
  
  uploadArea.addEventListener('dragover', handleDragOver);
  uploadArea.addEventListener('drop', handleFileDrop);
  fileInput.addEventListener('change', handleFileSelect);
  
  // Close modals on overlay click
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        closeModal(modal.id);
      }
    });
  });
}

function renderModelCards() {
  const modelCards = document.getElementById('modelCards');
  modelCards.innerHTML = appData.aiModels.map(model => `
    <div class="model-card" data-model-id="${model.id}">
      <div class="model-icon">${model.icon}</div>
      <div class="model-name">${model.name}</div>
      <div class="model-advantage">${model.advantage}</div>
    </div>
  `).join('');
}

function renderTimeline() {
  const timeline = document.getElementById('timeline');
  timeline.innerHTML = appData.salesFlow.map((step, index) => `
    <div class="timeline-item ${index + 1 === currentFlowStep ? 'current' : ''}" data-step-id="${step.id}">
      <div class="timeline-icon">${step.icon}</div>
      <div class="timeline-content">
        <div class="timeline-title">${step.title}</div>
        <div class="timeline-description">${step.description}</div>
        <button class="info-btn" data-step-id="${step.id}" data-step-title="${step.title}" data-step-description="${step.description}" data-details="${step.details}">i</button>
      </div>
    </div>
  `).join('');
}

function renderDataList() {
  const dataList = document.getElementById('dataList');
  const statusLabels = {
    'completed': '已完成',
    'processing': '處理中',
    'failed': '失敗'
  };
  
  dataList.innerHTML = appData.dataImportList.map(item => `
    <div class="data-item">
      <div class="data-info">
        <div class="data-name">${item.name}</div>
        <div class="data-meta">${item.date} • ${item.records} 筆記錄</div>
      </div>
      <div class="data-status">
        <div class="status-dot ${item.status}"></div>
        <span>${statusLabels[item.status]}</span>
      </div>
    </div>
  `).join('');
}

function renderSmartSuggestions() {
  const smartSuggestions = document.getElementById('smartSuggestions');
  smartSuggestions.innerHTML = appData.smartSuggestions.map(suggestion => `
    <div class="suggestion-chip" data-suggestion="${suggestion}">${suggestion}</div>
  `).join('');
}

function handleModelSelection(modelCard) {
  const modelId = modelCard.dataset.modelId;
  const model = appData.aiModels.find(m => m.id === modelId);
  
  if (model) {
    showModelDetails(model);
  }
}

function showModelDetails(model) {
  const modalTitle = document.getElementById('modalTitle');
  const modalBody = document.getElementById('modalBody');
  
  modalTitle.textContent = model.name;
  currentModelForSelection = model;
  
  modalBody.innerHTML = `
    <div class="model-details">
      <div class="model-detail-section">
        <div class="detail-label">描述</div>
        <p>${model.description}</p>
      </div>
      
      <div class="model-detail-section">
        <div class="detail-label">優勢</div>
        <div class="detail-list">
          ${model.strengths.map(strength => `<div class="detail-item">${strength}</div>`).join('')}
        </div>
      </div>
      
      <div class="model-detail-section">
        <div class="detail-label">限制</div>
        <div class="detail-list">
          ${model.weaknesses.map(weakness => `<div class="detail-item">${weakness}</div>`).join('')}
        </div>
      </div>
    </div>
  `;
  
  openModal('modelModal');
}

function selectCurrentModel() {
  if (currentModelForSelection) {
    selectedModel = currentModelForSelection;
    
    // Update UI
    document.querySelectorAll('.model-card').forEach(card => {
      card.classList.remove('selected');
    });
    
    document.querySelector(`[data-model-id="${selectedModel.id}"]`).classList.add('selected');
    
    // Update header
    const modelIndicator = document.querySelector('.model-indicator');
    modelIndicator.textContent = `已選擇: ${selectedModel.name}`;
    modelIndicator.style.color = '#007AFF';
    
    closeModal('modelModal');
    
    // Add a chat message about model selection
    addChatMessage(`已選擇 ${selectedModel.name} 模型，專精於${selectedModel.advantage}。我將使用此模型為您提供服務。`, 'ai');
    
    currentModelForSelection = null;
  }
}

function showFlowDetails(infoBtn) {
  const stepTitle = infoBtn.dataset.stepTitle;
  const stepDescription = infoBtn.dataset.stepDescription;
  const details = infoBtn.dataset.details;
  
  document.getElementById('flowModalTitle').textContent = stepTitle;
  document.getElementById('flowModalBody').innerHTML = `
    <div class="model-details">
      <div class="model-detail-section">
        <div class="detail-label">說明</div>
        <p>${stepDescription}</p>
      </div>
      <div class="model-detail-section">
        <div class="detail-label">詳細資訊</div>
        <p>${details}</p>
      </div>
    </div>
  `;
  
  openModal('flowModal');
}

function sendMessage() {
  const chatInput = document.getElementById('chatInput');
  const message = chatInput.value.trim();
  if (!message) return;
  
  console.log('Sending message:', message); // Debug log
  
  // Add user message
  addChatMessage(message, 'user');
  
  // Clear input
  chatInput.value = '';
  
  // Simulate AI response
  setTimeout(() => {
    const aiResponse = generateAIResponse(message);
    addChatMessage(aiResponse, 'ai');
    updateAINotes(message, aiResponse);
  }, 1000);
}

function addChatMessage(content, sender) {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) {
    console.error('Chat messages container not found');
    return;
  }
  
  console.log('Adding message:', content, 'from', sender); // Debug log
  
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}-message`;
  
  const now = new Date();
  const timeString = now.toLocaleTimeString('zh-TW', { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
  
  messageDiv.innerHTML = `
    <div class="message-content">${content}</div>
    <div class="message-time">${timeString}</div>
  `;
  
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function generateAIResponse(userMessage) {
  const responses = [
    "謝謝您的提問！基於您的需求，我建議我們先了解您的目標客戶群體。",
    "很好的想法！讓我為您分析一下最適合的解決方案。",
    "我了解您的需求。根據我的分析，建議我們從數據分析開始。",
    "這是一個很棒的機會！我們可以利用 AI 來優化您的業務流程。",
    "基於您提供的資訊，我推薦以下幾個步驟來達成您的目標。"
  ];
  
  return responses[Math.floor(Math.random() * responses.length)];
}

function updateAINotes(userMessage, aiResponse) {
  const notesContent = document.getElementById('notesContent');
  if (!notesContent) return;
  
  // Simulate updating AI notes based on conversation
  const notes = [
    { label: "當前階段", value: getStageLabel(currentConversationStage) },
    { label: "客戶需求", value: "正在分析中..." },
    { label: "下一步行動", value: "深入了解需求" }
  ];
  
  notesContent.innerHTML = notes.map(note => `
    <div class="note-item">
      <span class="note-label">${note.label}：</span>
      <span class="note-value">${note.value}</span>
    </div>
  `).join('');
}

function updateFunnelStage() {
  document.querySelectorAll('.funnel-stage').forEach(stage => {
    stage.classList.remove('active');
  });
  
  const activeStage = document.querySelector(`[data-stage="${currentConversationStage}"]`);
  if (activeStage) {
    activeStage.classList.add('active');
  }
}

function getStageLabel(stageId) {
  const stage = appData.conversationStages.find(s => s.id === stageId);
  return stage ? stage.name : '未知階段';
}

function handleDragOver(e) {
  e.preventDefault();
  const uploadArea = e.target.closest('.upload-area');
  if (uploadArea) {
    uploadArea.style.borderColor = '#007AFF';
    uploadArea.style.background = 'rgba(0, 122, 255, 0.05)';
  }
}

function handleFileDrop(e) {
  e.preventDefault();
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    processFile(files[0]);
  }
  resetUploadArea();
}

function handleFileSelect(e) {
  const files = e.target.files;
  if (files.length > 0) {
    processFile(files[0]);
  }
}

function handleFileUpload() {
  const fileInput = document.getElementById('fileInput');
  if (fileInput.files.length > 0) {
    processFile(fileInput.files[0]);
    closeModal('uploadModal');
  } else {
    alert('請先選擇一個檔案');
  }
}

function processFile(file) {
  console.log('Processing file:', file.name); // Debug log
  
  // Simulate file processing
  const newItem = {
    id: Date.now(),
    name: file.name,
    date: new Date().toISOString().split('T')[0],
    status: 'processing',
    type: file.name.split('.').pop().toLowerCase(),
    records: Math.floor(Math.random() * 1000) + 100
  };
  
  appData.dataImportList.unshift(newItem);
  renderDataList();
  
  // Add chat message about file upload
  addChatMessage(`正在處理檔案 "${file.name}"...`, 'ai');
  
  // Simulate processing completion
  setTimeout(() => {
    newItem.status = 'completed';
    renderDataList();
    addChatMessage(`檔案 "${file.name}" 已成功處理完成，共匯入 ${newItem.records} 筆資料。`, 'ai');
  }, 3000);
  
  resetUploadArea();
}

function resetUploadArea() {
  const uploadArea = document.getElementById('uploadArea');
  if (uploadArea) {
    uploadArea.style.borderColor = '';
    uploadArea.style.background = '';
  }
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
  
  // Reset file input if it's the upload modal
  if (modalId === 'uploadModal') {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
      fileInput.value = '';
    }
  }
}