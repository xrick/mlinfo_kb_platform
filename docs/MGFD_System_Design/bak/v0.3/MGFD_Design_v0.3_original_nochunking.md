# MGFD 系統架構分析報告

**報告日期**: 2025-08-17 01:49
**系統版本**: MGFD SalesRAG Integration System v0.3
**分析範圍**: 完整系統架構、模組依賴、配置文件使用分析

## 1. 系統模組組成

### 1.1 核心模組架構

#### **主控制器層**

```
MGFDSystem (mgfd_system.py)
├── 系統初始化和協調
├── 工作流程管理
└── 統一接口提供
```

#### **輸入處理層**

```
UserInputHandler (user_input_handler.py)
├── 用戶輸入解析
├── 槽位提取協調
└── 狀態更新管理
```

#### **狀態管理層**

```
RedisStateManager (redis_state_manager.py)
├── 會話狀態持久化
├── 對話歷史管理
├── 槽位信息存儲
└── 數據類型轉換
```

#### **回應生成層**

```
ResponseGenerator (response_generator.py)
├── 回應格式化
├── 前端渲染信息
├── 多類型回應處理
└── JSON序列化
```

#### **智能提取層**

```
EnhancedSlotExtractor (enhanced_slot_extractor.py)
├── 傳統關鍵詞匹配
├── LLM智能分類
├── 特殊案例處理
└── 置信度評估
```

#### **知識庫層**

```
NotebookKnowledgeBase (knowledge_base.py)
├── 產品數據管理
├── 搜索和過濾
├── 語義搜索
└── 推薦引擎
```

#### **狀態機層**

```
MGFDStateMachine (state_machine.py)
├── 狀態轉換管理
├── 流程控制
└── 事件處理
```

## 1.2 模組功能詳細分析

### 所有模組運作總述：

我們的目標是建立能夠服務客戶，回答客戶問題，幫客戶想到未能想到的需求，同時又能夠做知識庫，讓客戶能查詢所有產品的規格。

我會先用一個案例來描述這個系統的完整且符合預期的行為。

case-1:
user-input-1 :"請介紹目前新出的筆電"-> system:各模組進行處理，發現需要啟動funnnel chat進行槽位資料收集->system:依照預設的槽位資料收集的問題向客戶詢問->客戶回答->[optional:若預到系統無法理解的字詞，請詢問LLM，並產生回答與客戶進行確認，直到確定後，再繼續進行槽位資料收集]->system進行槽位資料收集->直到槽位資料滿足可以進行產品查詢->system進行內部產品搜尋->呈現產品詳細規格給客戶。

以上是一個非常簡單的流程，請按照case-1，進行研究，如何把目前複雜的處理程序，先完成初版可以達成case-1的system功能。
