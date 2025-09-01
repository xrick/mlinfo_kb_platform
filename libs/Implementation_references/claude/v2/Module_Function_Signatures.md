# MGFD 系統模組函式簽名詳細說明

## 1. MGFDKernel 類別

### 1.1 初始化與配置
```python
class MGFDKernel:
    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """
        初始化 MGFD 核心控制器
        
        Args:
            redis_client: Redis 客戶端實例，用於會話狀態持久化
        """
    
    def _load_config(self) -> Dict[str, Any]:
        """載入系統配置"""
        pass
    
    def _load_slot_schema(self) -> Dict[str, str]:
        """載入槽位架構定義"""
        pass
```

### 1.2 公開介面
```python
    async def process_message(
        self, 
        session_id: str, 
        message: str, 
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        處理用戶消息 - 主要入口點
        
        Args:
            session_id: 會話識別碼
            message: 用戶輸入消息
            stream: 是否使用串流回應
            
        Returns:
            包含回應內容的字典，格式對齊 mgfd_ai.js 期望
        """
    
    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        獲取會話狀態
        
        Args:
            session_id: 會話識別碼
            
        Returns:
            會話狀態字典
        """
    
    async def reset_session(self, session_id: str) -> Dict[str, Any]:
        """
        重置會話
        
        Args:
            session_id: 會話識別碼
            
        Returns:
            重置結果字典
        """
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        獲取系統狀態
        
        Returns:
            系統狀態字典
        """
```

### 1.3 內部處理方法
```python
    async def _process_message_internal(
        self, 
        session_id: str, 
        message: str
    ) -> Dict[str, Any]:
        """
        內部消息處理流程
        
        Args:
            session_id: 會話識別碼
            message: 用戶輸入消息
            
        Returns:
            處理結果字典
        """
    
    async def _build_context(
        self, 
        session_id: str, 
        message: str
    ) -> Dict[str, Any]:
        """
        建立處理上下文
        
        Args:
            session_id: 會話識別碼
            message: 用戶輸入消息
            
        Returns:
            上下文字典
        """
    
    def _format_frontend_response(
        self, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        格式化前端回應
        
        Args:
            context: 處理上下文
            
        Returns:
            格式化後的回應字典
        """
```

## 2. UserInputHandler 類別

### 2.1 初始化與配置
```python
class UserInputHandler:
    def __init__(self) -> None:
        """初始化用戶輸入處理器"""
    
    def _load_intent_classifier(self) -> Any:
        """載入意圖分類器"""
        pass
    
    def _load_slot_extractor(self) -> Any:
        """載入槽位抽取器"""
        pass
```

### 2.2 主要處理方法
```python
    async def parse(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析用戶輸入
        
        Args:
            message: 用戶輸入消息
            context: 當前上下文
            
        Returns:
            解析結果字典，包含：
            - intent: 識別出的意圖
            - slots_update: 槽位更新
            - control: 控制指令
            - errors: 錯誤信息
            - confidence: 置信度
        """
    
    async def _classify_intent(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        意圖分類
        
        Args:
            message: 用戶輸入消息
            context: 當前上下文
            
        Returns:
            識別出的意圖字符串
        """
    
    async def _extract_slots(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        槽位抽取
        
        Args:
            message: 用戶輸入消息
            context: 當前上下文
            
        Returns:
            抽取的槽位字典
        """
    
    async def _determine_control(
        self, 
        intent: str, 
        slots_update: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        確定控制指令
        
        Args:
            intent: 識別出的意圖
            slots_update: 槽位更新
            context: 當前上下文
            
        Returns:
            控制指令字典
        """
    
    async def _validate_input(
        self, 
        message: str, 
        intent: str, 
        slots_update: Dict[str, Any]
    ) -> List[str]:
        """
        輸入驗證
        
        Args:
            message: 用戶輸入消息
            intent: 識別出的意圖
            slots_update: 槽位更新
            
        Returns:
            錯誤信息列表
        """
    
    def _calculate_confidence(
        self, 
        intent: str, 
        slots_update: Dict[str, Any]
    ) -> float:
        """
        計算置信度
        
        Args:
            intent: 識別出的意圖
            slots_update: 槽位更新
            
        Returns:
            置信度分數 (0.0-1.0)
        """
```

### 2.3 輔助方法
```python
    def _match_intent(
        self, 
        message: str, 
        intents: Dict[str, List[str]]
    ) -> str:
        """
        意圖匹配
        
        Args:
            message: 用戶輸入消息
            intents: 意圖定義字典
            
        Returns:
            匹配的意圖字符串
        """
    
    def _extract_slot_value(
        self, 
        message: str, 
        slot_name: str, 
        keywords: Dict[str, Any]
    ) -> Optional[str]:
        """
        抽取特定槽位值
        
        Args:
            message: 用戶輸入消息
            slot_name: 槽位名稱
            keywords: 關鍵詞定義
            
        Returns:
            抽取的槽位值
        """
```

## 3. StateManagementHandler 類別

### 3.1 初始化與配置
```python
class StateManagementHandler:
    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """
        初始化狀態管理器
        
        Args:
            redis_client: Redis 客戶端實例
        """
    
    def _load_state_transitions(self) -> Dict[str, StateTransition]:
        """載入狀態轉換表"""
        pass
```

### 3.2 狀態機核心方法
```python
    async def process_state(
        self, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        處理當前狀態
        
        Args:
            context: 當前上下文
            
        Returns:
            狀態處理結果
        """
    
    def get_current_state(self, context: Dict[str, Any]) -> str:
        """
        獲取當前狀態
        
        Args:
            context: 當前上下文
            
        Returns:
            當前狀態字符串
        """
    
    def transition_to_state(
        self, 
        context: Dict[str, Any], 
        new_state: str
    ) -> Dict[str, Any]:
        """
        狀態轉換
        
        Args:
            context: 當前上下文
            new_state: 目標狀態
            
        Returns:
            更新後的上下文
        """
```

### 3.3 會話管理方法
```python
    async def update_session(
        self, 
        session_id: str, 
        context: Dict[str, Any]
    ) -> bool:
        """
        更新會話狀態
        
        Args:
            session_id: 會話識別碼
            context: 會話上下文
            
        Returns:
            更新是否成功
        """
    
    async def get_session(
        self, 
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        獲取會話狀態
        
        Args:
            session_id: 會話識別碼
            
        Returns:
            會話狀態字典
        """
    
    async def delete_session(self, session_id: str) -> bool:
        """
        刪除會話
        
        Args:
            session_id: 會話識別碼
            
        Returns:
            刪除是否成功
        """
```

## 4. PromptManagementHandler 類別

### 4.1 初始化與配置
```python
class PromptManagementHandler:
    def __init__(self) -> None:
        """初始化提示管理器"""
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """載入提示模板"""
        pass
```

### 4.2 提示管理方法
```python
    async def select_prompt(
        self, 
        context: Dict[str, Any]
    ) -> str:
        """
        選擇合適的提示
        
        Args:
            context: 當前上下文
            
        Returns:
            選擇的提示字符串
        """
    
    def render_prompt(
        self, 
        template: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        渲染提示模板
        
        Args:
            template: 提示模板
            context: 當前上下文
            
        Returns:
            渲染後的提示字符串
        """
    
    def _get_funnel_intro_prompt(self) -> str:
        """獲取漏斗介紹提示"""
        pass
    
    def _get_elicitation_prompt(
        self, 
        context: Dict[str, Any]
    ) -> str:
        """
        獲取信息收集提示
        
        Args:
            context: 當前上下文
            
        Returns:
            信息收集提示字符串
        """
    
    def _get_recommendation_prompt(
        self, 
        context: Dict[str, Any]
    ) -> str:
        """
        獲取推薦提示
        
        Args:
            context: 當前上下文
            
        Returns:
            推薦提示字符串
        """
    
    def _get_general_prompt(self) -> str:
        """獲取通用提示"""
        pass
```

## 5. KnowledgeManagementHandler 類別

### 5.1 初始化與配置
```python
class KnowledgeManagementHandler:
    def __init__(self) -> None:
        """初始化知識管理器"""
    
    def _load_product_database(self) -> Any:
        """載入產品數據庫"""
        pass
    
    def _initialize_chunking_engine(self) -> Any:
        """初始化分塊引擎"""
        pass
```

### 5.2 搜尋與推薦方法
```python
    async def search(
        self, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        執行知識搜尋
        
        Args:
            context: 當前上下文
            
        Returns:
            搜尋結果字典
        """
    
    async def semantic_search(
        self, 
        query: str, 
        slots: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        語義搜尋
        
        Args:
            query: 搜尋查詢
            slots: 槽位信息
            
        Returns:
            搜尋結果列表
        """
    
    async def generate_recommendations(
        self, 
        search_results: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        生成推薦
        
        Args:
            search_results: 搜尋結果
            context: 當前上下文
            
        Returns:
            推薦結果列表
        """
    
    def _build_search_query(
        self, 
        slots: Dict[str, Any]
    ) -> str:
        """
        構建搜尋查詢
        
        Args:
            slots: 槽位信息
            
        Returns:
            搜尋查詢字符串
        """
    
    def _calculate_similarity(
        self, 
        query_vector: List[float], 
        product_vector: List[float]
    ) -> float:
        """
        計算相似度
        
        Args:
            query_vector: 查詢向量
            product_vector: 產品向量
            
        Returns:
            相似度分數
        """
```

## 6. ResponseGenHandler 類別

### 6.1 初始化與配置
```python
class ResponseGenHandler:
    def __init__(self) -> None:
        """初始化回應生成器"""
    
    def _load_response_templates(self) -> Dict[str, str]:
        """載入回應模板"""
        pass
```

### 6.2 回應生成方法
```python
    async def generate(
        self, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成回應
        
        Args:
            context: 當前上下文
            
        Returns:
            生成的回應字典
        """
    
    def format_funnel_question(
        self, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        格式化漏斗問題
        
        Args:
            context: 當前上下文
            
        Returns:
            漏斗問題字典
        """
    
    def format_recommendation(
        self, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        格式化推薦回應
        
        Args:
            context: 當前上下文
            
        Returns:
            推薦回應字典
        """
    
    def format_elicitation(
        self, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        格式化信息收集回應
        
        Args:
            context: 當前上下文
            
        Returns:
            信息收集回應字典
        """
    
    def _generate_markdown_table(
        self, 
        data: List[Dict[str, Any]]
    ) -> str:
        """
        生成 Markdown 表格
        
        Args:
            data: 表格數據
            
        Returns:
            Markdown 表格字符串
        """
    
    def _validate_response_format(
        self, 
        response: Dict[str, Any]
    ) -> bool:
        """
        驗證回應格式
        
        Args:
            response: 回應字典
            
        Returns:
            格式是否有效
        """
```

## 7. 標準動作合約

### 7.1 動作函式簽名
```python
def action_function(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    標準動作合約
    
    Args:
        context: 包含當前所有狀態資料的字典
        
    Returns:
        包含此動作產生的新資料的字典
    """
```

### 7.2 常用動作函式
```python
def initialize_session(context: Dict[str, Any]) -> Dict[str, Any]:
    """初始化會話"""
    pass

def determine_next_action(context: Dict[str, Any]) -> Dict[str, Any]:
    """決定下一步動作"""
    pass

def build_funnel_intro(context: Dict[str, Any]) -> Dict[str, Any]:
    """構建漏斗介紹"""
    pass

def process_user_answer(context: Dict[str, Any]) -> Dict[str, Any]:
    """處理用戶回答"""
    pass

def evaluate_slots(context: Dict[str, Any]) -> Dict[str, Any]:
    """評估槽位填充"""
    pass

def build_search_query(context: Dict[str, Any]) -> Dict[str, Any]:
    """構建搜尋查詢"""
    pass

def format_response(context: Dict[str, Any]) -> Dict[str, Any]:
    """格式化回應"""
    pass
```
