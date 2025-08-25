# Prompt 管理系統使用範例

## 概述

Prompt 管理系統提供了一個全域的、動態的 Prompt 載入和管理機制，讓您可以在需要時才載入所需的 Prompt，而不是在系統初始化時自動載入所有 Prompt。

## 基本使用

### 1. 導入模組

```python
# 導入便捷 API
from libs.PromptManagementHandler import (
    get_prompt, get_multiple_prompts, get_ai_coder_initialization_prompt,
    get_mgfd_principal_prompt, get_combined_prompt
)

# 或者導入管理器類
from libs.PromptManagementHandler import PromptManager, get_global_prompt_manager
```

### 2. 獲取單個 Prompt

```python
# 使用便捷函數
ai_coder_prompt = get_ai_coder_initialization_prompt()

# 或者使用通用函數
ai_coder_prompt = get_prompt("ai_coder_initialization")

# 強制重新載入
ai_coder_prompt = get_prompt("ai_coder_initialization", force_reload=True)
```

### 3. 批量獲取多個 Prompt

```python
# 批量獲取多個 Prompt
prompts = get_multiple_prompts([
    "ai_coder_initialization",
    "mgfd_principal",
    "slot_collection"
])

# 結果是一個字典
for name, content in prompts.items():
    print(f"{name}: {len(content)} 字符")
```

### 4. 組合 Prompt

```python
# 組合 MGFD 主提示與 AI Coder 提示
combined_prompt = get_combined_prompt([
    "mgfd_principal",
    "ai_coder_initialization"
])

# 使用自定義分隔符
combined_prompt = get_combined_prompt([
    "mgfd_principal",
    "ai_coder_initialization"
], separator="\n---\n")
```

## 在 MGFD 系統中使用

### 1. 在 LLM 管理器中使用

```python
from libs.PromptManagementHandler import get_ai_coder_initialization_prompt

class MGFDLLMManager:
    def __init__(self):
        # 不再在初始化時載入 Prompt
        self.llm = None
        # Prompt 將在需要時動態載入
    
    def invoke_with_ai_coder(self, user_prompt: str) -> str:
        """使用 AI Coder 提示調用 LLM"""
        # 動態載入 AI Coder 提示
        ai_coder_prompt = get_ai_coder_initialization_prompt()
        
        if ai_coder_prompt:
            # 組合提示
            combined_prompt = f"{ai_coder_prompt}\n\n{user_prompt}"
            return self.llm.invoke(combined_prompt)
        else:
            # 回退到普通調用
            return self.llm.invoke(user_prompt)
```

### 2. 在銷售助手服務中使用

```python
from libs.PromptManagementHandler import get_sales_rag_prompt, get_ai_coder_initialization_prompt

class SalesAssistantService:
    def process_query(self, query: str) -> str:
        """處理銷售查詢"""
        # 動態載入銷售 RAG 提示
        sales_prompt = get_sales_rag_prompt()
        ai_coder_prompt = get_ai_coder_initialization_prompt()
        
        if sales_prompt and ai_coder_prompt:
            # 組合提示
            combined_prompt = f"{ai_coder_prompt}\n\n{sales_prompt}\n\n用戶查詢: {query}"
            return self.llm.invoke(combined_prompt)
        else:
            # 回退處理
            return self.fallback_process(query)
```

## 在 API 路由中使用

### 1. 在 FastAPI 路由中使用

```python
from fastapi import APIRouter
from libs.PromptManagementHandler import get_prompt, get_combined_prompt

router = APIRouter()

@router.post("/chat")
async def chat(request: ChatRequest):
    """聊天 API"""
    # 根據需要動態載入 Prompt
    if request.use_ai_coder:
        prompt = get_combined_prompt([
            "mgfd_principal",
            "ai_coder_initialization"
        ])
    else:
        prompt = get_prompt("mgfd_principal")
    
    # 處理聊天邏輯
    response = process_chat_with_prompt(prompt, request.message)
    return response
```

### 2. 在 MGFD 路由中使用

```python
from libs.PromptManagementHandler import get_mgfd_principal_prompt

@router.post("/chat")
async def mgfd_chat(request: ChatRequest):
    """MGFD 聊天 API"""
    # 動態載入 MGFD 主提示
    principal_prompt = get_mgfd_principal_prompt()
    
    if principal_prompt:
        # 使用載入的提示處理消息
        result = mgfd_system.process_message_with_prompt(
            request.session_id, 
            request.message, 
            principal_prompt
        )
    else:
        # 回退處理
        result = mgfd_system.process_message(
            request.session_id, 
            request.message
        )
    
    return result
```

## 緩存管理

### 1. 查看緩存狀態

```python
from libs.PromptManagementHandler import get_cache_stats, list_cached_prompts

# 查看緩存統計
stats = get_cache_stats()
print(f"緩存統計: {stats}")

# 查看已緩存的 Prompt
cached_prompts = list_cached_prompts()
print(f"已緩存的 Prompt: {cached_prompts}")
```

### 2. 清理緩存

```python
from libs.PromptManagementHandler import clear_cache

# 清理特定 Prompt 的緩存
clear_cache("ai_coder_initialization")

# 清理所有緩存
clear_cache()
```

### 3. 重新載入 Prompt

```python
from libs.PromptManagementHandler import reload_prompt

# 重新載入特定 Prompt
success = reload_prompt("ai_coder_initialization")
if success:
    print("重新載入成功")
else:
    print("重新載入失敗")
```

## 配置管理

### 1. 添加新的 Prompt 路徑

```python
from libs.PromptManagementHandler import add_prompt_path

# 添加新的 Prompt 路徑
add_prompt_path(
    "custom_prompt",
    "HumanData/PromptsHub/custom_prompts/my_custom_prompt.txt"
)

# 使用新添加的 Prompt
custom_prompt = get_prompt("custom_prompt")
```

### 2. 移除 Prompt 路徑

```python
from libs.PromptManagementHandler import remove_prompt_path

# 移除 Prompt 路徑
remove_prompt_path("custom_prompt")
```

## 錯誤處理

### 1. 處理不存在的 Prompt

```python
from libs.PromptManagementHandler import get_prompt

# 安全地獲取 Prompt
prompt = get_prompt("non_existent_prompt")
if prompt is None:
    print("Prompt 不存在，使用默認處理")
    # 使用默認邏輯
else:
    # 使用載入的 Prompt
    pass
```

### 2. 處理載入失敗

```python
try:
    prompt = get_prompt("ai_coder_initialization")
    if prompt:
        # 使用 Prompt
        pass
    else:
        # 處理載入失敗
        print("Prompt 載入失敗，使用備用方案")
except Exception as e:
    print(f"獲取 Prompt 時發生錯誤: {e}")
    # 錯誤處理邏輯
```

## 性能優化

### 1. 批量預載入常用 Prompt

```python
from libs.PromptManagementHandler import get_multiple_prompts

# 在系統啟動時預載入常用 Prompt
def preload_common_prompts():
    """預載入常用 Prompt"""
    common_prompts = [
        "mgfd_principal",
        "ai_coder_initialization",
        "slot_collection"
    ]
    
    prompts = get_multiple_prompts(common_prompts)
    print(f"預載入了 {len(prompts)} 個 Prompt")
    return prompts
```

### 2. 監控緩存性能

```python
from libs.PromptManagementHandler import get_cache_stats

def monitor_cache_performance():
    """監控緩存性能"""
    stats = get_cache_stats()
    
    print(f"總緩存數: {stats['total_cached']}")
    print(f"有效緩存: {stats['valid_cached']}")
    print(f"過期緩存: {stats['expired_cached']}")
    print(f"總大小: {stats['total_size_bytes']} 字節")
    
    # 如果過期緩存太多，清理緩存
    if stats['expired_cached'] > stats['valid_cached']:
        clear_cache()
        print("已清理過期緩存")
```

## 最佳實踐

### 1. 按需載入

```python
# 好的做法：按需載入
def process_user_request(request_type: str, user_input: str):
    if request_type == "sales":
        prompt = get_sales_rag_prompt()
    elif request_type == "mgfd":
        prompt = get_mgfd_principal_prompt()
    else:
        prompt = None
    
    # 處理邏輯
    return process_with_prompt(prompt, user_input)

# 避免的做法：一次性載入所有 Prompt
def bad_practice():
    all_prompts = get_multiple_prompts(list_available_prompts())
    # 這樣會載入所有 Prompt，浪費資源
```

### 2. 錯誤處理

```python
def safe_prompt_usage(prompt_name: str, fallback_content: str = ""):
    """安全地使用 Prompt"""
    try:
        prompt = get_prompt(prompt_name)
        if prompt:
            return prompt
        else:
            print(f"Warning: Prompt '{prompt_name}' 載入失敗，使用備用內容")
            return fallback_content
    except Exception as e:
        print(f"Error: 獲取 Prompt '{prompt_name}' 時發生錯誤: {e}")
        return fallback_content
```

### 3. 緩存管理

```python
def smart_cache_management():
    """智能緩存管理"""
    stats = get_cache_stats()
    
    # 如果緩存太大，清理舊的緩存
    if stats['total_size_bytes'] > 1024 * 1024:  # 1MB
        print("緩存過大，清理舊緩存")
        clear_cache()
    
    # 定期清理過期緩存
    if stats['expired_cached'] > 0:
        print(f"清理 {stats['expired_cached']} 個過期緩存")
        # 這裡可以實現更精細的清理邏輯
```

這個 Prompt 管理系統提供了靈活、高效的 Prompt 載入和管理機制，讓您可以根據需要動態載入 Prompt，而不是在系統初始化時載入所有 Prompt。
