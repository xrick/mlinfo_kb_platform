# MGFD 系統實作報告

## 1. 系統概述

### 1.1 設計目標
基於 MGFD (Multi-Guided Funnel Dialogue) 架構，實現一個智能筆記型電腦銷售對話系統。系統採用表驅動狀態機設計，整合五大核心模組，提供自然語言對話、智能槽位抽取、產品推薦等功能。

### 1.2 核心架構
- **MGFDKernel**: 系統大腦，對外唯一介面
- **UserInputHandler**: 輸入解析與槽位抽取
- **StateManagementHandler**: 狀態機驅動與流程控制
- **PromptManagementHandler**: 提示工程管理
- **KnowledgeManagementHandler**: 知識庫查詢與產品搜尋
- **ResponseGenHandler**: 回應生成與格式化

## 2. 系統各模組責任理解

### 2.1 MGFDKernel（核心控制器）
**主要責任**：
- 作為系統對外唯一介面，處理所有外部請求
- 協調五大模組的運作順序與數據流
- 管理會話生命週期（創建、更新、重置）
- 確保系統狀態一致性與錯誤處理

**關鍵職責**：
- 接收用戶輸入，建立統一上下文（context）
- 按順序調用各模組處理邏輯
- 格式化回應以符合前端期望
- 管理 Redis 會話狀態持久化

### 2.2 UserInputHandler（輸入處理層）
**主要責任**：
- 解析自然語言輸入為結構化意圖與槽位
- 基於 `default_slots.json` 的11個核心槽位進行抽取
- 利用 `default_keywords.json` 的同義詞進行智能匹配
- 判斷是否需要啟動漏斗對話或問卷模式

**關鍵職責**：
- 意圖分類（greet, ask_recommendation, ask_comparison 等）
- 槽位抽取與驗證
- 控制指令生成（start_funnel, start_multichat）
- 輸入錯誤檢測與處理

### 2.3 StateManagementHandler（狀態管理層）
**主要責任**：
- 實現表驅動狀態機，管理對話流程
- 根據當前狀態與用戶輸入決定下一步動作
- 執行標準動作合約 `action(context) -> dict`
- 維護會話狀態的完整性與一致性

**關鍵職責**：
- 狀態轉換邏輯管理
- 動作序列執行與結果合併
- 會話狀態持久化（Redis）
- 狀態機異常處理與恢復

### 2.4 PromptManagementHandler（提示工程管理層）
**主要責任**：
- 整合 `MGFD_Principal_Prompt.txt` 與 `recept_guest_prompt1.txt`
- 根據對話階段選擇合適的提示模板
- 動態生成符合企業級助理規範的回應
- 管理提示庫的版本與更新

**關鍵職責**：
- 提示模板選擇與渲染
- 上下文相關的提示動態生成
- 提示效果評估與優化
- 多語言提示支援

### 2.5 KnowledgeManagementHandler（知識管理層）
**主要責任**：
- 整合 Parent-Child Chunking 搜尋引擎
- 基於語義相似度的產品匹配
- 多維度產品特徵分析與比較
- 智能推薦算法實現

**關鍵職責**：
- 語義搜尋查詢構建
- 產品分塊向量化與索引
- 相似度計算與排序
- 推薦理由生成

### 2.6 ResponseGenHandler（回應生成層）
**主要責任**：
- 格式化回應以符合 `mgfd_ai.js` 期望
- 生成多種類型的回應（funnel_question, recommendation 等）
- 整合 Markdown 表格與結構化數據
- 確保回應的一致性与可讀性

**關鍵職責**：
- 回應類型路由與格式化
- 前端事件類型對齊
- 錯誤回應處理
- 回應品質控制

## 3. 狀態機在系統中的作用

### 3.1 狀態機的核心價值
狀態機是 MGFD 系統的流程控制核心，實現了以下關鍵功能：

**3.1.1 對話流程管理**
- 將複雜的對話邏輯分解為離散狀態
- 每個狀態對應特定的業務邏輯與用戶期望
- 確保對話按照預設路徑進行，避免邏輯混亂

**3.1.2 數據流控制**
- 通過 `context`