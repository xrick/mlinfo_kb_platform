# MGFD系統架構與資料流分析報告

**報告日期**: 2025-08-16 11:02  
**分析範圍**: libs/mgfd_cursor 完整架構  
**分析目標**: 業務AI系統行為與資料流分析

---

## 1. 業務AI系統核心行為理解

### 1.1 基本互動原則

業務AI系統的核心行為是**多輪對話的槽位收集流程**，而非一次性推薦：

```
用戶輸入 → 系統分析 → 收集槽位值 → 檢查完整性 → 
├─ 槽位不足 → 生成下一個問題 → 用戶回答 → 繼續收集
└─ 槽位完整 → 內部產品搜尋 → 推薦符合需求的產品
```

### 1.2 槽位架構設計

#### 當前槽位定義
基於 `libs/mgfd_cursor/humandata/slot_synonyms.json` 分析：

**已定義槽位**:
1. **usage_purpose** (用途): gaming, business, student, creative, general
2. **budget_range** (價格區間): budget, mid_range, premium, luxury  
3. **brand_preference** (品牌): asus, acer, lenovo, hp, dell, apple
4. **performance_features** (性能特徵): fast, portable, performance

**需要補充的槽位**:
1. **cpu_level** (CPU等級): 缺失
2. **gpu_level** (GPU等級): 缺失
3. **weight_requirement** (重量需求): 缺失
4. **screen_size** (螢幕尺寸): 缺失

#### 槽位架構增強建議

**當前架構問題**:
- 僅使用關鍵詞匹配，效能有限
- 缺乏正則表達式支援
- 無法處理複雜的用戶表達

**建議增強**:
```json
{
  "cpu_level": {
    "basic": {
      "keywords": ["基本", "入門", "一般"],
      "regex": ["i3|ryzen\\s*3|基本處理器"],
      "semantic": ["效能一般", "夠用就好"]
    },
    "mid": {
      "keywords": ["中等", "中端"],
      "regex": ["i5|ryzen\\s*5|中等處理器"],
      "semantic": ["效能不錯", "平衡效能"]
    },
    "high": {
      "keywords": ["高效能", "高級"],
      "regex": ["i7|i9|ryzen\\s*[79]|高效能"],
      "semantic": ["效能強勁", "頂級效能"]
    }
  }
}
```

---

## 2. MGFD系統架構分析

### 2.1 核心模組架構

```
MGFDSystem (主控制器)
├── ConfigLoader (配置載入器)
├── MGFDLLMManager (LLM管理器)
├── RedisStateManager (狀態管理器)
├── UserInputHandler (用戶輸入處理器)
├── DialogueManager (對話管理器)
├── ActionExecutor (動作執行器)
└── ResponseGenerator (回應生成器)
```

### 2.2 模組功能說明

#### 主要模組職責

1. **MGFDSystem** - 系統主控制器
   - 協調所有模組工作流程
   - 提供統一的處理接口
   - 管理會話生命週期

2. **UserInputHandler** - 用戶輸入處理器
   - 解析用戶輸入
   - 提取槽位值
   - 更新對話狀態

3. **DialogueManager** - 對話管理器
   - 決策下一步動作
   - 路由到適當的處理邏輯
   - 管理對話流程

4. **ActionExecutor** - 動作執行器
   - 執行具體業務邏輯
   - 產品搜尋和推薦
   - 生成回應內容

5. **ResponseGenerator** - 回應生成器
   - 格式化系統回應
   - 生成前端需要的數據結構
   - 支援串流回應
