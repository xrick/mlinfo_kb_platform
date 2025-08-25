# MGFD (Multi-Guided Funnel Dialogue) 系統

## 概述

MGFD是一個基於The Multiturn Guided Funnel Framework的筆記型電腦銷售對話系統，實現了"Think, Then Act"的對話架構，能夠智能引導用戶從模糊需求到精確的產品推薦。

## 系統架構

### 核心組件

1. **DialogueManager** (`dialogue_manager.py`)
   - 管理對話狀態和會話
   - 實現"Think"步驟的邏輯
   - 處理槽位提取和產品推薦

2. **StateMachine** (`state_machine.py`)
   - 實現"Act"步驟的邏輯
   - 管理對話流程和狀態轉換
   - 處理不同類型的用戶輸入

3. **KnowledgeBase** (`knowledge_base.py`)
   - 管理筆記型電腦產品數據
   - 提供產品搜索和過濾功能
   - 支持語義搜索

4. **Models** (`models.py`)
   - 定義數據結構和類型
   - 包含槽位架構和對話狀態模型

## 功能特性

### 1. 智能對話引導
- 自動識別用戶意圖
- 逐步收集必要信息
- 動態調整問題策略

### 2. 產品推薦引擎
- 基於用戶偏好的智能過濾
- 多維度產品匹配
- 個性化推薦排序

### 3. 會話管理
- 會話狀態持久化
- 多用戶並發支持
- 自動清理過期會話

### 4. 錯誤處理
- 中斷意圖識別
- 對話修復機制
- 優雅的錯誤回應

## API 端點

### 對話相關
- `POST /api/mgfd_cursor/chat` - 發送消息
- `POST /api/mgfd_cursor/chat/stream` - 串流對話
- `POST /api/mgfd_cursor/session/create` - 創建會話
- `GET /api/mgfd_cursor/session/{session_id}` - 獲取會話信息
- `DELETE /api/mgfd_cursor/session/{session_id}` - 刪除會話

### 系統管理
- `GET /api/mgfd_cursor/stats` - 系統統計
- `POST /api/mgfd_cursor/cleanup` - 清理過期會話
- `GET /api/mgfd_cursor/products` - 獲取產品列表
- `GET /api/mgfd_cursor/products/search` - 搜索產品

## 使用方式

### 1. 啟動系統
```bash
python main.py
```

### 2. 訪問界面
- 主界面: http://localhost:8000/
- MGFD界面: http://localhost:8000/mgfd_cursor

### 3. API測試
```bash
# 創建會話
curl -X POST http://localhost:8000/api/mgfd_cursor/session/create \
  -H "Content-Type: application/json" \
  -d '{}'

# 發送消息
curl -X POST http://localhost:8000/api/mgfd_cursor/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "我想要一台遊戲筆電", "session_id": "your_session_id"}'
```

### 4. 運行測試
```bash
python test_mgfd_system.py
```

## 對話流程示例

```
用戶: "我想要一台遊戲筆電"
系統: "您主要會用這台筆電做什麼？遊戲、工作、學習還是其他用途？"

用戶: "主要打遊戲"
系統: "考慮到您需要遊戲性能，您的預算大概在哪個範圍？"

用戶: "預算3萬左右"
系統: "您有品牌偏好吗？"

用戶: "偏好華碩"
系統: 根據您的需求，我為您推薦以下筆電：
     1. ASUS ROG Strix G15
     2. HP Pavilion Gaming
     ...
```

## 配置說明

### 槽位架構
系統預定義了以下槽位：
- `usage_purpose`: 使用目的 (必填)
- `budget_range`: 預算範圍 (必填)
- `performance_priority`: 性能優先級 (可選)
- `portability_need`: 便攜性需求 (可選)
- `brand_preference`: 品牌偏好 (可選)

### 產品數據
系統包含示例產品數據，支持以下屬性：
- 基本信息：名稱、品牌、系列
- 規格信息：CPU、GPU、RAM、存儲
- 使用場景：遊戲、商務、學生等
- 價格範圍：budget、mid_range、premium、luxury

## 擴展指南

### 添加新槽位
1. 在 `models.py` 中的 `NOTEBOOK_SLOT_SCHEMA` 添加新槽位定義
2. 在 `dialogue_manager.py` 的 `extract_slots_from_input` 方法中添加提取邏輯
3. 更新相關的提示模板

### 添加新產品
1. 在 `knowledge_base.py` 的 `_get_sample_products` 方法中添加產品數據
2. 或者創建CSV文件並更新 `csv_path` 參數

### 自定義推薦邏輯
1. 修改 `dialogue_manager.py` 中的 `generate_recommendations` 方法
2. 調整 `knowledge_base.py` 中的過濾邏輯

## 技術特點

1. **模組化設計**: 各組件獨立，易於維護和擴展
2. **類型安全**: 使用TypedDict和dataclass確保類型安全
3. **錯誤處理**: 完善的異常處理和錯誤恢復機制
4. **可擴展性**: 支持插件式擴展和自定義邏輯
5. **測試覆蓋**: 包含完整的單元測試和集成測試

## 未來規劃

1. **LLM集成**: 集成大語言模型提升對話質量
2. **向量搜索**: 實現基於向量的語義搜索
3. **持久化存儲**: 支持數據庫持久化
4. **多語言支持**: 支持多種語言對話
5. **A/B測試**: 支持對話策略的A/B測試

## 貢獻指南

1. Fork 項目
2. 創建功能分支
3. 提交更改
4. 發起 Pull Request

## 授權

本項目採用 MIT 授權。



