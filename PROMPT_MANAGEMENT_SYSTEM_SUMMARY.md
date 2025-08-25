# Prompt 管理系統架構總結

## 系統概述

Prompt 管理系統是一個全域的、動態的 Prompt 載入和管理機制，解決了系統初始化時自動載入所有 Prompt 的問題，改為按需載入的方式。

## 架構設計

### 1. 核心組件

```
libs/PromptManagementHandler/
├── __init__.py              # 模組初始化
├── prompt_manager.py        # 核心管理器類
└── api.py                   # 便捷 API 接口
```

### 2. 文件結構

```
HumanData/PromptsHub/
├── prompt_paths_config.json                    # Prompt 路徑配置
├── MGFD_Principal_Prompts/
│   ├── MGFD_Principal_Prompt_20250821.txt      # MGFD 主提示
│   └── ai_coder_indepnedent_initialization_prompt.txt  # AI Coder 提示
├── prompts_for_collect_slot_values/
│   └── MGFD_collect_slot_value_prompt_v1.txt   # 槽位收集提示
└── basic_prompts_for_users/
    └── recept_guest_prompt1.txt                # 客戶接待提示
```

## 核心功能

### 1. PromptManager 類

**主要功能：**
- 動態載入 Prompt 文件
- 智能緩存管理
- 路徑配置管理
- 錯誤處理和回退機制

**關鍵方法：**
```python
class PromptManager:
    def get_prompt(self, prompt_name: str, force_reload: bool = False) -> Optional[str]
    def get_multiple_prompts(self, prompt_names: List[str]) -> Dict[str, str]
    def reload_prompt(self, prompt_name: str) -> bool
    def clear_cache(self, prompt_name: Optional[str] = None)
    def get_cache_stats(self) -> Dict[str, Any]
    def add_prompt_path(self, prompt_name: str, file_path: str)
```

### 2. 全域管理

**全域實例管理：**
```python
# 獲取全域實例
manager = get_global_prompt_manager()

# 設定全域實例
set_global_prompt_manager(custom_manager)
```

### 3. 便捷 API

**預定義函數：**
```python
# 單個 Prompt 獲取
get_ai_coder_initialization_prompt()
get_mgfd_principal_prompt()
get_slot_collection_prompt()
get_sales_rag_prompt()

# 組合 Prompt
get_combined_prompt(["mgfd_principal", "ai_coder_initialization"])
get_mgfd_with_ai_coder_prompt()
get_sales_with_ai_coder_prompt()
```

## 使用方式

### 1. 基本使用

```python
# 導入便捷 API
from libs.PromptManagementHandler import get_ai_coder_initialization_prompt

# 按需載入
ai_coder_prompt = get_ai_coder_initialization_prompt()
if ai_coder_prompt:
    # 使用 Prompt
    result = llm.invoke(ai_coder_prompt + user_input)
```

### 2. 在 MGFD 系統中使用

```python
# 在 LLM 管理器中動態載入
def invoke_with_ai_coder(self, user_prompt: str):
    ai_coder_prompt = get_ai_coder_initialization_prompt()
    if ai_coder_prompt:
        combined_prompt = f"{ai_coder_prompt}\n\n{user_prompt}"
        return self.llm.invoke(combined_prompt)
    else:
        return self.llm.invoke(user_prompt)
```

### 3. 在 API 路由中使用

```python
@router.post("/chat")
async def chat(request: ChatRequest):
    # 根據需要動態載入
    if request.use_ai_coder:
        prompt = get_combined_prompt([
            "mgfd_principal",
            "ai_coder_initialization"
        ])
    else:
        prompt = get_prompt("mgfd_principal")
    
    return process_chat_with_prompt(prompt, request.message)
```

## 緩存機制

### 1. 緩存策略

- **TTL 緩存**：默認 1 小時過期
- **智能清理**：自動清理過期緩存
- **大小監控**：監控緩存大小和性能

### 2. 緩存管理

```python
# 查看緩存狀態
stats = get_cache_stats()

# 清理緩存
clear_cache("ai_coder_initialization")  # 清理特定 Prompt
clear_cache()  # 清理所有緩存

# 重新載入
reload_prompt("ai_coder_initialization")
```

## 配置管理

### 1. 路徑配置

**配置文件：** `HumanData/PromptsHub/prompt_paths_config.json`

```json
{
  "mgfd_principal": "HumanData/PromptsHub/MGFD_Principal_Prompts/MGFD_Principal_Prompt_20250821.txt",
  "ai_coder_initialization": "HumanData/PromptsHub/MGFD_Principal_Prompts/ai_coder_indepnedent_initialization_prompt.txt",
  "slot_collection": "HumanData/PromptsHub/prompts_for_collect_slot_values/MGFD_collect_slot_value_prompt_v1.txt"
}
```

### 2. 動態配置

```python
# 添加新路徑
add_prompt_path("custom_prompt", "path/to/custom_prompt.txt")

# 移除路徑
remove_prompt_path("custom_prompt")
```

## 錯誤處理

### 1. 載入失敗處理

```python
prompt = get_prompt("ai_coder_initialization")
if prompt is None:
    # 使用默認處理邏輯
    return fallback_process()
else:
    # 使用載入的 Prompt
    return process_with_prompt(prompt)
```

### 2. 異常處理

```python
try:
    prompt = get_prompt("ai_coder_initialization")
    # 使用 Prompt
except Exception as e:
    logger.error(f"Prompt 載入失敗: {e}")
    # 錯誤處理邏輯
```

## 性能優化

### 1. 按需載入

- **避免初始化載入**：不在系統啟動時載入所有 Prompt
- **動態載入**：只在需要時載入特定 Prompt
- **智能緩存**：載入後緩存以提高性能

### 2. 批量操作

```python
# 批量獲取多個 Prompt
prompts = get_multiple_prompts([
    "mgfd_principal",
    "ai_coder_initialization",
    "slot_collection"
])
```

### 3. 緩存優化

- **TTL 管理**：自動過期機制
- **大小控制**：監控緩存大小
- **清理策略**：定期清理過期緩存

## 與現有系統的整合

### 1. 替換原有的自動載入

**原來的做法：**
```python
class MGFDLLMManager:
    def __init__(self):
        # 自動載入所有 Prompt
        self._load_principal_prompt()
        self._load_ai_coder_prompt()
```

**新的做法：**
```python
class MGFDLLMManager:
    def __init__(self):
        # 不載入 Prompt，按需載入
        self.llm = None
    
    def invoke_with_prompt(self, user_prompt: str):
        # 動態載入需要的 Prompt
        ai_coder_prompt = get_ai_coder_initialization_prompt()
        if ai_coder_prompt:
            return self.llm.invoke(ai_coder_prompt + user_prompt)
        else:
            return self.llm.invoke(user_prompt)
```

### 2. 在銷售助手中的應用

```python
class SalesAssistantService:
    def process_query(self, query: str):
        # 動態載入銷售相關 Prompt
        sales_prompt = get_sales_rag_prompt()
        ai_coder_prompt = get_ai_coder_initialization_prompt()
        
        if sales_prompt and ai_coder_prompt:
            combined_prompt = f"{ai_coder_prompt}\n\n{sales_prompt}\n\n查詢: {query}"
            return self.llm.invoke(combined_prompt)
        else:
            return self.fallback_process(query)
```

## 測試驗證

### 1. 功能測試

創建了 `test_prompt_management_system.py` 來驗證：
- 基本載入功能
- 緩存機制
- 錯誤處理
- 組合功能
- 性能表現

### 2. 測試結果

```
✅ 成功導入 Prompt 管理系統
✅ 全域管理器類型: PromptManager
✅ 可用 Prompt 數量: 6
✅ AI Coder 提示載入成功
✅ MGFD 主提示載入成功
✅ 批量獲取成功
✅ Prompt 組合成功
✅ 緩存統計正常
✅ 所有測試通過！
```

## 優勢總結

### 1. 性能優勢

- **按需載入**：避免不必要的 Prompt 載入
- **智能緩存**：提高重複使用效率
- **記憶體優化**：減少記憶體佔用

### 2. 靈活性優勢

- **動態配置**：支持運行時添加/移除 Prompt
- **組合使用**：支持多個 Prompt 組合
- **錯誤回退**：提供完善的錯誤處理機制

### 3. 維護性優勢

- **集中管理**：統一的 Prompt 管理接口
- **配置驅動**：通過配置文件管理 Prompt 路徑
- **監控能力**：提供詳細的緩存和性能監控

### 4. 擴展性優勢

- **模組化設計**：易於擴展新功能
- **API 友好**：提供豐富的 API 接口
- **全域訪問**：支持全域範圍內的 Prompt 管理

這個 Prompt 管理系統成功解決了系統初始化時自動載入所有 Prompt 的問題，提供了更靈活、高效的 Prompt 管理機制。
