from typing import Dict, Any, List, Callable, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
import time
from enum import Enum

# =====================================
# 1. 增強版標準合約定義
# =====================================

class ActionStatus(Enum):
    """
    動作執行狀態枚舉類
    
    定義了MGFD系統中所有動作函數的可能執行狀態，用於標準化動作執行結果的狀態表示。
    這個枚舉確保了系統各個模組對動作執行結果有統一的理解和處理方式。
    
    Attributes:
        SUCCESS (str): 動作執行成功，所有預期的操作都已完成
        ERROR (str): 動作執行失敗，發生了阻止動作完成的錯誤
        PENDING (str): 動作正在執行中，尚未完成（用於異步操作）
        SKIPPED (str): 動作被跳過，通常因為前置條件不滿足或業務邏輯判斷
    
    Usage:
        status = ActionStatus.SUCCESS
        if status == ActionStatus.ERROR:
            handle_error()
    """
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    SKIPPED = "skipped"

@dataclass
class ActionResult:
    """
    標準動作結果封裝類
    
    這個dataclass定義了MGFD系統中所有動作函數的標準返回格式。通過統一的結果格式，
    系統可以以一致的方式處理各種動作的執行結果，無論動作的具體業務邏輯如何差異。
    
    這個設計實現了關注點分離，將動作的執行狀態、業務數據、錯誤信息等不同層面的
    信息清晰地分開管理，便於系統的錯誤處理、性能監控和調試。
    
    Attributes:
        status (ActionStatus): 動作執行的狀態，使用ActionStatus枚舉值
        data (Dict[str, Any]): 動作執行產生的業務數據，以鍵值對形式存儲
        message (Optional[str]): 可選的執行消息，通常用於成功時的提示或失敗時的錯誤描述
        error_code (Optional[str]): 可選的錯誤代碼，用於程序化處理特定類型的錯誤
        execution_time (Optional[float]): 可選的執行時間（秒），用於性能監控和優化
    
    Usage:
        # 成功情況
        result = ActionResult(
            status=ActionStatus.SUCCESS,
            data={"user_id": 123, "name": "張三"},
            execution_time=0.05
        )
        
        # 錯誤情況
        result = ActionResult(
            status=ActionStatus.ERROR,
            data={},
            message="用戶不存在",
            error_code="USER_NOT_FOUND"
        )
    
    Note:
        - data字典即使在錯誤情況下也應該初始化，避免None值處理問題
        - execution_time如果提供，建議使用time.time()的差值計算
        - error_code應該使用預定義的常數，便於錯誤分類和處理
    """
    status: ActionStatus
    data: Dict[str, Any]
    message: Optional[str] = None
    error_code: Optional[str] = None
    execution_time: Optional[float] = None

# 增強版標準合約：所有動作函數必須遵循此簽名
def enhanced_action_contract(context: Dict[str, Any]) -> ActionResult:
    """
    增強版標準動作合約
    
    Args:
        context: 共享上下文字典，包含所有狀態數據
        
    Returns:
        ActionResult: 包含執行狀態、數據更新、錯誤信息等的標準化結果
    """
    pass

# =====================================
# 2. MGFDKernel 核心通信協議
# =====================================

class MGFDMessageType(Enum):
    """
    MGFD系統消息類型枚舉
    
    定義了MGFD系統各個模組之間通信時使用的標準消息類型。每個消息類型代表一種特定的
    業務請求或響應，通過標準化的消息類型，系統可以實現模組間的解耦和靈活的消息路由。
    
    消息類型按照業務功能分為以下幾個類別：
    
    用戶輸入處理類：
    - USER_INPUT_REQUEST: 請求分析用戶輸入
    - USER_INPUT_RESPONSE: 用戶輸入分析結果響應
    
    知識管理類：
    - KNOWLEDGE_QUERY_REQUEST: 請求查詢知識庫
    - KNOWLEDGE_QUERY_RESPONSE: 知識庫查詢結果響應
    - CHUNKING_SEARCH_REQUEST: 請求執行語義分塊搜索
    - CHUNKING_SEARCH_RESPONSE: 語義分塊搜索結果響應
    
    提示管理類：
    - PROMPT_SELECTION_REQUEST: 請求選擇合適的提示模板
    - PROMPT_SELECTION_RESPONSE: 提示模板選擇結果響應
    - PROMPT_GENERATE_REQUEST: 請求生成定制化提示
    - PROMPT_GENERATE_RESPONSE: 定制化提示生成結果響應
    
    響應生成類：
    - RESPONSE_GENERATION_REQUEST: 請求生成回應內容
    - RESPONSE_GENERATION_RESPONSE: 回應內容生成結果響應
    - RESPONSE_FORMAT_REQUEST: 請求格式化響應
    - RESPONSE_FORMAT_RESPONSE: 響應格式化結果響應
    
    狀態管理類：
    - STATE_TRANSITION_REQUEST: 請求狀態轉換
    - STATE_TRANSITION_RESPONSE: 狀態轉換結果響應
    - STATE_UPDATE_REQUEST: 請求更新狀態
    - STATE_UPDATE_RESPONSE: 狀態更新結果響應
    
    系統控制類：
    - SYSTEM_ERROR: 系統錯誤通知
    - SYSTEM_HEARTBEAT: 系統心跳檢測
    
    Usage:
        message_type = MGFDMessageType.USER_INPUT_REQUEST
        if message_type in [MGFDMessageType.USER_INPUT_REQUEST, 
                           MGFDMessageType.USER_INPUT_RESPONSE]:
            handle_user_input_message()
    
    Note:
        - 每個請求類型都應該有對應的響應類型
        - 消息類型的命名遵循 {模組}_{操作}_{類型} 的模式
        - 新增消息類型時應該考慮向後兼容性
    """
    # 輸入處理
    USER_INPUT_REQUEST = "user_input_request"
    USER_INPUT_RESPONSE = "user_input_response"
    
    # 知識管理
    KNOWLEDGE_QUERY_REQUEST = "knowledge_query_request"
    KNOWLEDGE_QUERY_RESPONSE = "knowledge_query_response"
    CHUNKING_SEARCH_REQUEST = "chunking_search_request"
    CHUNKING_SEARCH_RESPONSE = "chunking_search_response"
    
    # 提示管理
    PROMPT_SELECTION_REQUEST = "prompt_selection_request"
    PROMPT_SELECTION_RESPONSE = "prompt_selection_response"
    PROMPT_GENERATE_REQUEST = "prompt_generate_request"
    PROMPT_GENERATE_RESPONSE = "prompt_generate_response"
    
    # 響應生成
    RESPONSE_GENERATION_REQUEST = "response_generation_request"
    RESPONSE_GENERATION_RESPONSE = "response_generation_response"
    RESPONSE_FORMAT_REQUEST = "response_format_request"
    RESPONSE_FORMAT_RESPONSE = "response_format_response"
    
    # 狀態管理
    STATE_TRANSITION_REQUEST = "state_transition_request"
    STATE_TRANSITION_RESPONSE = "state_transition_response"
    STATE_UPDATE_REQUEST = "state_update_request"
    STATE_UPDATE_RESPONSE = "state_update_response"
    
    # 系統控制
    SYSTEM_ERROR = "system_error"
    SYSTEM_HEARTBEAT = "system_heartbeat"

@dataclass
class MGFDMessage:
    """
    MGFD系統間通信的標準消息格式
    
    這個dataclass定義了MGFD系統各個模組之間通信時使用的標準消息格式。通過統一的
    消息結構，系統可以實現模組間的解耦、消息路由、錯誤追踪和性能監控。
    
    消息設計遵循了以下原則：
    1. 標準化：所有模組使用相同的消息格式
    2. 可追踪：通過message_id和correlation_id實現消息追踪
    3. 可路由：明確的發送者和接收者信息
    4. 可擴展：靈活的payload結構支持各種業務數據
    5. 可優化：優先級和時間戳支持性能調優
    
    Attributes:
        message_id (str): 消息的唯一標識符，通常使用UUID格式
        message_type (MGFDMessageType): 消息類型，定義了消息的業務含義
        sender_module (str): 發送消息的模組名稱，用於消息路由和錯誤追踪
        receiver_module (str): 接收消息的目標模組名稱
        timestamp (float): 消息創建的時間戳，使用time.time()格式
        payload (Dict[str, Any]): 消息的業務數據載體，包含具體的請求或響應數據
        correlation_id (Optional[str]): 可選的關聯ID，用於追蹤整個對話會話
        priority (int): 消息優先級，範圍1-10，數字越大優先級越高
    
    Usage:
        # 創建一個用戶輸入請求消息
        message = MGFDMessage(
            message_id=str(uuid.uuid4()),
            message_type=MGFDMessageType.USER_INPUT_REQUEST,
            sender_module="WebAPI",
            receiver_module="UserInputHandler",
            timestamp=time.time(),
            payload={"user_input": "請介紹筆電", "session_id": "sess_123"},
            correlation_id="sess_123",
            priority=5
        )
        
        # 轉換為JSON進行傳輸
        json_msg = message.to_json()
        
        # 從JSON恢復消息對象
        restored_msg = MGFDMessage.from_json(json_msg)
    
    Note:
        - message_id應該在整個系統中保持唯一性
        - correlation_id用於將相關的請求和響應關聯起來
        - priority在消息隊列滿載時用於確定處理順序
        - payload的結構應該與message_type相匹配
    """
    message_id: str
    message_type: MGFDMessageType
    sender_module: str
    receiver_module: str
    timestamp: float
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None  # 用於追蹤對話會話
    priority: int = 1  # 消息優先級 (1-10)
    
    def to_json(self) -> str:
        """
        將消息對象轉換為JSON字符串格式
        
        這個方法將MGFDMessage對象序列化為JSON字符串，便於在網絡中傳輸或存儲。
        序列化過程中會處理枚舉類型的轉換，並使用適當的JSON格式設置。
        
        Returns:
            str: 格式化的JSON字符串，包含所有消息字段
        
        Usage:
            message = MGFDMessage(...)
            json_string = message.to_json()
            # 可以通過網絡發送或存儲到文件
        
        Note:
            - 使用ensure_ascii=False支持中文字符
            - 使用indent=2提供可讀的格式
            - 枚舉值會被轉換為其字符串值
        """
        return json.dumps({
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_module": self.sender_module,
            "receiver_module": self.receiver_module,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "priority": self.priority
        }, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MGFDMessage':
        """
        從JSON字符串創建MGFDMessage對象
        
        這個類方法將JSON字符串反序列化為MGFDMessage對象，用於接收和處理
        來自其他模組或網絡的消息數據。
        
        Args:
            json_str (str): 包含消息數據的JSON字符串
        
        Returns:
            MGFDMessage: 從JSON數據創建的消息對象
        
        Raises:
            json.JSONDecodeError: 當JSON格式無效時
            KeyError: 當必需的字段缺失時
            ValueError: 當message_type枚舉值無效時
        
        Usage:
            json_data = '{"message_id": "123", ...}'
            message = MGFDMessage.from_json(json_data)
        
        Note:
            - 會自動將字符串轉換為相應的枚舉類型
            - 可選字段如果不存在會使用默認值
            - 建議在調用前驗證JSON數據的完整性
        """
        data = json.loads(json_str)
        return cls(
            message_id=data["message_id"],
            message_type=MGFDMessageType(data["message_type"]),
            sender_module=data["sender_module"],
            receiver_module=data["receiver_module"],
            timestamp=data["timestamp"],
            payload=data["payload"],
            correlation_id=data.get("correlation_id"),
            priority=data.get("priority", 1)
        )

# =====================================
# 3. 五大子模組JSON通信協議定義
# =====================================

class UserInputHandlerProtocol:
    """
    UserInputHandler模組通信協議類
    
    這個類定義了與UserInputHandler模組通信時使用的標準消息格式和協議。
    UserInputHandler負責處理用戶原始輸入，包括自然語言理解、意圖識別、
    實體提取和槽位填充等核心NLP功能。
    
    主要功能包括：
    1. 用戶輸入分析：解析和理解用戶的自然語言輸入
    2. 槽位提取：從用戶輸入中提取結構化的信息
    3. 會話狀態管理：跟踪對話進度和用戶意圖變化
    
    Usage:
        # 創建輸入分析請求
        request = UserInputHandlerProtocol.create_input_analysis_request(
            "請介紹筆電", "session_123"
        )
        
        # 創建槽位提取響應
        response = UserInputHandlerProtocol.create_slot_extraction_response(
            {"product": "筆電"}, [{"type": "PRODUCT", "value": "筆電"}]
        )
    """
    
    @staticmethod
    def create_input_analysis_request(user_input: str, session_id: str) -> Dict[str, Any]:
        """
        創建用戶輸入分析請求的標準載體
        
        這個方法創建向UserInputHandler模組發送輸入分析請求時使用的標準化數據格式。
        請求包含了進行NLP分析所需的所有基礎信息。
        
        Args:
            user_input (str): 用戶的原始輸入文本，將被進行NLP分析
            session_id (str): 會話標識符，用於維護對話上下文和狀態
        
        Returns:
            Dict[str, Any]: 標準化的請求數據字典，包含：
                - action (str): 請求的操作類型，固定為"analyze_input"
                - data (Dict): 包含輸入數據的字典
                    - raw_input (str): 原始用戶輸入
                    - session_id (str): 會話ID
                    - timestamp (float): 請求創建時間戳
                - expected_output (List[str]): 期望的輸出字段列表
        
        Usage:
            request_data = UserInputHandlerProtocol.create_input_analysis_request(
                "我想買一台新筆電", "sess_12345"
            )
            # request_data可以直接作為MGFDMessage的payload使用
        
        Note:
            - user_input應該已經經過基礎的清理（如去除多餘空格）
            - session_id應該在整個對話期間保持一致
            - timestamp用於性能分析和調試
        """
        return {
            "action": "analyze_input",
            "data": {
                "raw_input": user_input,
                "session_id": session_id,
                "timestamp": time.time()
            },
            "expected_output": ["intent", "entities", "slots", "confidence"]
        }
    
    @staticmethod
    def create_slot_extraction_response(slots: Dict[str, Any], entities: List[Dict]) -> Dict[str, Any]:
        """
        創建槽位提取響應的標準格式
        
        這個方法創建UserInputHandler模組返回槽位提取結果時使用的標準化數據格式。
        響應包含了提取出的結構化信息和處理元數據。
        
        Args:
            slots (Dict[str, Any]): 從用戶輸入中提取出的槽位信息字典
                例如: {"product_type": "筆電", "budget": "5萬以下", "brand": "ASUS"}
            entities (List[Dict]): 識別出的實體列表，每個實體包含類型、值、位置等信息
                例如: [{"type": "PRODUCT", "value": "筆電", "start": 3, "end": 5}]
        
        Returns:
            Dict[str, Any]: 標準化的響應數據字典，包含：
                - status (str): 處理狀態，通常為"success"
                - data (Dict): 處理結果數據
                    - extracted_slots (Dict): 提取的槽位信息
                    - entities (List): 識別的實體列表
                    - next_required_slots (List): 下一步需要收集的槽位
                    - completion_rate (float): 槽位填充完成度百分比
                - metadata (Dict): 處理過程的元數據
                    - processing_time (float): 處理耗時
                    - confidence_score (float): 整體置信度分數
        
        Usage:
            response_data = UserInputHandlerProtocol.create_slot_extraction_response(
                {"product": "筆電", "budget": None},
                [{"type": "PRODUCT", "value": "筆電", "confidence": 0.95}]
            )
        
        Note:
            - slots中的None值表示該槽位尚未填充
            - completion_rate用於判斷是否需要進一步的槽位收集
            - confidence_score影響後續處理策略的選擇
        """
        return {
            "status": "success",
            "data": {
                "extracted_slots": slots,
                "entities": entities,
                "next_required_slots": [],
                "completion_rate": 0.0
            },
            "metadata": {
                "processing_time": 0.0,
                "confidence_score": 0.0
            }
        }

class KnowledgeManagementHandlerProtocol:
    """
    KnowledgeManagementHandler模組通信協議類
    
    此類定義了與KnowledgeManagementHandler模組通信的標準協議。該模組負責管理
    產品知識庫、執行語義搜索、處理Parent-Child Chunking策略，以及提供智能
    推薦功能。這是MGFD系統的核心數據處理模組。
    
    主要職責包括：
    1. 語義搜索：基於用戶查詢和槽位信息執行智能搜索
    2. Chunking管理：實施Parent-Child分層搜索策略
    3. 相似度計算：使用餘弦相似度進行內容匹配
    4. 結果排序：根據相關性和業務規則排序搜索結果
    5. 知識庫維護：管理產品數據和文檔更新
    
    Usage:
        # 創建語義搜索請求
        search_req = KnowledgeManagementHandlerProtocol.create_chunking_search_request(
            "高效能筆電推薦", {"budget": "5萬", "usage": "設計工作"}
        )
        
        # 創建搜索結果響應
        search_resp = KnowledgeManagementHandlerProtocol.create_search_results_response(
            results_list, metadata_dict
        )
    """
    
    @staticmethod
    def create_chunking_search_request(query: str, slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建語義分塊搜索請求的標準載體
        
        此方法生成向KnowledgeManagementHandler發送語義搜索請求的標準數據格式。
        請求整合了用戶查詢和已提取的槽位信息，支持多維度的智能搜索。
        
        Args:
            query (str): 用戶的搜索查詢字符串，可以是自然語言描述
            slots (Dict[str, Any]): 從用戶輸入提取的結構化槽位信息，如預算、用途等
        
        Returns:
            Dict[str, Any]: 搜索請求數據結構，包含：
                - action (str): 操作類型，固定為"semantic_search"
                - data (Dict): 搜索參數
                    - query_text (str): 主要搜索查詢
                    - search_slots (Dict): 槽位約束條件
                    - search_strategy (str): 搜索策略類型
                    - similarity_threshold (float): 相似度閾值
                    - max_results (int): 最大結果數量
                - filters (Dict): 額外的搜索過濾條件
                    - product_categories (List): 產品分類過濾器
                    - price_range (Optional): 價格範圍限制
                    - availability (bool): 是否只顯示有庫存商品
        
        Usage:
            request = create_chunking_search_request(
                "適合遊戲的筆電",
                {"budget": "3萬-5萬", "usage": "遊戲", "brand_preference": "ASUS"}
            )
            
        Note:
            - similarity_threshold設為0.3，過濾掉相關性過低的結果
            - search_strategy指定使用parent_child_chunking方法
            - filters可以根據業務需求動態調整
        """
        return {
            "action": "semantic_search",
            "data": {
                "query_text": query,
                "search_slots": slots,
                "search_strategy": "parent_child_chunking",
                "similarity_threshold": 0.3,
                "max_results": 10
            },
            "filters": {
                "product_categories": [],
                "price_range": None,
                "availability": True
            }
        }
    
    @staticmethod
    def create_search_results_response(results: List[Dict], metadata: Dict) -> Dict[str, Any]:
        """
        創建搜索結果響應的標準格式
        
        此方法構建KnowledgeManagementHandler返回搜索結果時的標準數據格式。
        響應包含匹配的產品信息、相關性評分和搜索過程的詳細元數據。
        
        Args:
            results (List[Dict]): 搜索結果列表，每個項目包含產品信息和匹配詳情
            metadata (Dict): 搜索過程的元數據，包含性能指標和處理信息
        
        Returns:
            Dict[str, Any]: 標準響應格式，包含：
                - status (str): 處理狀態
                - data (Dict): 搜索結果數據
                    - search_results (List): 匹配的產品列表
                    - total_matches (int): 總匹配數量
                    - search_metadata (Dict): 搜索元數據
                - chunking_info (Dict): Chunking處理詳情
                    - parent_chunks_used (int): 使用的父分塊數量
                    - child_chunks_used (int): 使用的子分塊數量
                    - similarity_scores (List): 相似度分數列表
        
        Usage:
            results = [
                {"product_id": "LP001", "name": "Gaming Laptop", "score": 0.95},
                {"product_id": "LP002", "name": "Business Laptop", "score": 0.87}
            ]
            metadata = {"query_time": 0.15, "total_chunks": 1500}
            response = create_search_results_response(results, metadata)
            
        Note:
            - total_matches應該等於len(results)
            - similarity_scores按匹配度降序排列
            - chunking_info提供搜索過程的透明度
        """
        return {
            "status": "success",
            "data": {
                "search_results": results,
                "total_matches": len(results),
                "search_metadata": metadata
            },
            "chunking_info": {
                "parent_chunks_used": 0,
                "child_chunks_used": 0,
                "similarity_scores": []
            }
        }

class PromptManagementHandlerProtocol:
    """
    PromptManagementHandler模組通信協議類
    
    此類定義了與PromptManagementHandler模組通信的標準協議。該模組負責智能化的
    提示工程管理，包括情境化提示選擇、動態提示生成和提示效果優化。這是確保
    AI回應質量和一致性的關鍵模組。
    
    核心功能包括：
    1. 提示模板管理：維護不同情境下的提示模板庫
    2. 情境化選擇：根據對話上下文選擇最適合的提示
    3. 動態生成：基於當前狀態生成定制化提示
    4. 效果評估：監控和優化提示的使用效果
    5. 語言適配：支持多語言和多風格的提示變體
    
    Usage:
        # 請求選擇提示模板
        prompt_req = PromptManagementHandlerProtocol.create_prompt_selection_request(
            context_dict, "product_recommendation"
        )
        
        # 回應提示選擇結果
        prompt_resp = PromptManagementHandlerProtocol.create_prompt_response(
            selected_prompt_text, template_id
        )
    """
    
    @staticmethod
    def create_prompt_selection_request(context: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """
        創建提示模板選擇請求的標準載體
        
        此方法生成向PromptManagementHandler請求選擇合適提示模板時的標準數據格式。
        請求基於當前對話情境、用戶意圖和可用數據來選擇最適合的提示策略。
        
        Args:
            context (Dict[str, Any]): 當前對話的完整情境信息，包括：
                - 對話歷史、用戶意圖、已提取槽位、搜索結果等
            intent (str): 用戶的主要意圖標識符，如"product_inquiry"、"complaint_handling"
        
        Returns:
            Dict[str, Any]: 提示選擇請求結構，包含：
                - action (str): 操作類型，固定為"select_prompt_template"
                - data (Dict): 選擇參數
                    - conversation_context (Dict): 對話上下文信息
                    - user_intent (str): 用戶意圖標識
                    - current_state (str): 當前狀態機狀態
                    - available_slots (Dict): 可用的槽位信息
                - requirements (Dict): 提示要求
                    - prompt_type (str): 提示類型偏好
                    - language (str): 目標語言
                    - tone (str): 語調風格
        
        Usage:
            context = {
                "conversation_history": [...],
                "user_profile": {...},
                "current_state": "product_search",
                "slots": {"budget": "5萬", "category": "筆電"}
            }
            request = create_prompt_selection_request(context, "product_recommendation")
            
        Note:
            - language支持"zh-TW"、"en-US"等標準語言代碼
            - tone可以是"professional"、"casual"、"technical"等
            - 複雜情境可能需要組合多個提示模板
        """
        return {
            "action": "select_prompt_template",
            "data": {
                "conversation_context": context,
                "user_intent": intent,
                "current_state": context.get("current_state"),
                "available_slots": context.get("slots", {})
            },
            "requirements": {
                "prompt_type": "conversational",
                "language": "zh-TW",
                "tone": "professional_friendly"
            }
        }
    
    @staticmethod
    def create_prompt_response(selected_prompt: str, template_id: str) -> Dict[str, Any]:
        """
        創建提示選擇響應的標準格式
        
        此方法構建PromptManagementHandler返回提示選擇結果時的標準數據格式。
        響應包含選定的提示內容、模板信息和使用成本估算。
        
        Args:
            selected_prompt (str): 選定並可能經過定制化的提示文本
            template_id (str): 使用的提示模板標識符，用於追踪和分析
        
        Returns:
            Dict[str, Any]: 標準提示響應格式，包含：
                - status (str): 處理狀態
                - data (Dict): 提示數據
                    - generated_prompt (str): 生成的提示文本
                    - template_id (str): 模板標識符
                    - prompt_tokens (int): 提示的token數量
                    - estimated_cost (float): 預估使用成本
                - metadata (Dict): 處理元數據
                    - template_source (str): 模板來源類型
                    - optimization_applied (bool): 是否應用了優化
        
        Usage:
            prompt_text = "根據用戶需求推薦合適的筆電產品..."
            response = create_prompt_response(prompt_text, "product_rec_v2.1")
            
        Note:
            - prompt_tokens用於成本控制和性能監控
            - estimated_cost基於當前的API定價計算
            - optimization_applied指示是否使用了動態優化算法
        """
        return {
            "status": "success",
            "data": {
                "generated_prompt": selected_prompt,
                "template_id": template_id,
                "prompt_tokens": 0,
                "estimated_cost": 0.0
            },
            "metadata": {
                "template_source": "built_in",
                "optimization_applied": True
            }
        }

class ResponseGenHandlerProtocol:
    """
    ResponseGenHandler模組通信協議類
    
    此類定義了與ResponseGenHandler模組通信的標準協議。該模組負責生成面向用戶的
    最終回應內容，包括內容生成、格式化處理和UI元素構建。這是用戶體驗的直接決定因素。
    
    核心職責包括：
    1. 內容生成：基於搜索結果和提示生成自然的回應文本
    2. 結構化輸出：將回應內容組織成適合前端展示的格式
    3. UI元素設計：生成產品卡片、按鈕、選項等互動元素
    4. 多模態支持：處理文本、圖片、表格等不同類型的內容
    5. 個性化調整：根據用戶偏好調整回應風格和詳細程度
    
    Usage:
        # 請求生成回應內容
        gen_req = ResponseGenHandlerProtocol.create_response_generation_request(
            prompt_text, context_dict, products_list
        )
        
        # 返回格式化的回應
        gen_resp = ResponseGenHandlerProtocol.create_formatted_response(
            response_content, ui_elements_dict
        )
    """
    
    @staticmethod
    def create_response_generation_request(prompt: str, context: Dict, products: List[Dict]) -> Dict[str, Any]:
        """
        創建回應生成請求的標準載體
        
        此方法構建向ResponseGenHandler請求生成用戶回應時的標準數據格式。
        請求整合了提示工程結果、對話上下文和產品數據，確保生成高質量的個性化回應。
        
        Args:
            prompt (str): 從PromptManagementHandler獲得的優化提示文本
            context (Dict): 完整的對話上下文，包含用戶歷史、偏好等信息
            products (List[Dict]): 從KnowledgeManagementHandler獲得的產品搜索結果
        
        Returns:
            Dict[str, Any]: 回應生成請求結構，包含：
                - action (str): 操作類型，固定為"generate_response"
                - data (Dict): 生成參數
                    - system_prompt (str): 系統提示文本
                    - conversation_context (Dict): 對話情境
                    - product_data (List): 產品信息列表
                    - response_format (str): 期望的回應格式
                - parameters (Dict): 生成控制參數
                    - max_tokens (int): 最大生成長度
                    - temperature (float): 生成隨機性控制
                    - include_product_cards (bool): 是否包含產品卡片
                    - include_follow_up_questions (bool): 是否包含後續問題
        
        Usage:
            request = create_response_generation_request(
                "專業推薦以下筆電產品...",
                {"user_budget": "5萬", "usage": "辦公"},
                [{"id": "LP001", "name": "商務筆電", "price": 45000}]
            )
            
        Note:
            - response_format支持"structured_json"、"markdown"、"plain_text"
            - temperature建議設在0.3-0.8之間，平衡創造性和準確性
            - product_cards適用於電商場景，提供豐富的產品展示
        """
        return {
            "action": "generate_response",
            "data": {
                "system_prompt": prompt,
                "conversation_context": context,
                "product_data": products,
                "response_format": "structured_json"
            },
            "parameters": {
                "max_tokens": 1000,
                "temperature": 0.7,
                "include_product_cards": True,
                "include_follow_up_questions": True
            }
        }
    
    @staticmethod
    def create_formatted_response(content: str, ui_elements: Dict) -> Dict[str, Any]:
        """
        創建格式化回應的標準格式
        
        此方法構建ResponseGenHandler返回最終用戶回應時的標準數據格式。
        響應包含文本內容和豐富的UI交互元素，確保優質的用戶體驗。
        
        Args:
            content (str): 生成的主要回應文本內容
            ui_elements (Dict): 配套的UI交互元素定義，包含卡片、按鈕等
        
        Returns:
            Dict[str, Any]: 標準格式化響應結構，包含：
                - status (str): 處理狀態
                - data (Dict): 回應內容數據
                    - response_content (str): 主要文本內容
                    - ui_elements (Dict): UI交互元素
                    - response_type (str): 回應類型標識
                    - requires_user_action (bool): 是否需要用戶進一步操作
                - rendering_info (Dict): 渲染相關信息
                    - format (str): 內容格式類型
                    - estimated_render_time (float): 預估渲染時間
        
        Usage:
            ui_elements = {
                "type": "product_grid",
                "products": [...],
                "actions": ["view_details", "add_to_cart"]
            }
            response = create_formatted_response(
                "為您推薦以下筆電產品：...", ui_elements
            )
            
        Note:
            - response_type影響前端的渲染策略選擇
            - requires_user_action指示對話是否等待用戶回應
            - estimated_render_time用於性能監控和優化
        """
        return {
            "status": "success",
            "data": {
                "response_content": content,
                "ui_elements": ui_elements,
                "response_type": "product_recommendation",
                "requires_user_action": False
            },
            "rendering_info": {
                "format": "markdown_with_json",
                "estimated_render_time": 0.0
            }
        }

class StateManagementHandlerProtocol:
    """
    StateManagementHandler模組通信協議類
    
    此類定義了與StateManagementHandler模組通信的標準協議。該模組負責管理整個系統的
    狀態轉換邏輯、會話持久化和流程控制。作為FSM的核心執行引擎，它確保系統行為的
    可預測性和一致性。
    
    主要功能包括：
    1. 狀態轉換管理：執行基於規則的狀態轉換邏輯
    2. 會話持久化：將對話狀態存儲到Redis中，支持會話恢復
    3. 流程控制：協調各個模組的執行順序和條件判斷
    4. 事件處理：響應系統內部和外部事件觸發的狀態變化
    5. 異常恢復：處理異常情況下的狀態回滾和錯誤恢復
    
    Usage:
        # 請求狀態轉換
        transition_req = StateManagementHandlerProtocol.create_state_transition_request(
            "System", "search_completed", context_dict
        )
        
        # 回應狀態更新結果
        update_resp = StateManagementHandlerProtocol.create_state_update_response(
            "User", ["generate_response", "update_ui"]
        )
    """
    
    @staticmethod
    def create_state_transition_request(current_state: str, trigger: str, context: Dict) -> Dict[str, Any]:
        """
        創建狀態轉換請求的標準載體
        
        此方法構建向StateManagementHandler請求執行狀態轉換時的標準數據格式。
        請求包含當前狀態、轉換觸發條件和完整的上下文信息，確保狀態轉換的正確性。
        
        Args:
            current_state (str): 當前狀態標識符，符合FSM狀態定義
            trigger (str): 觸發狀態轉換的事件或條件標識符
            context (Dict): 當前會話的完整上下文數據
        
        Returns:
            Dict[str, Any]: 狀態轉換請求結構，包含：
                - action (str): 操作類型，固定為"transition_state"
                - data (Dict): 轉換參數
                    - current_state (str): 當前狀態標識
                    - transition_trigger (str): 轉換觸發器
                    - context_data (Dict): 上下文數據
                    - session_id (str): 會話標識符
                - validation (Dict): 驗證要求
                    - check_prerequisites (bool): 是否檢查前置條件
                    - validate_slots (bool): 是否驗證槽位完整性
        
        Usage:
            request = create_state_transition_request(
                "System",
                "user_input_processed", 
                {"session_id": "sess_123", "intent": "buy_laptop"}
            )
            
        Note:
            - current_state必須是FSM中定義的有效狀態
            - trigger應該在狀態轉換表中有對應的處理邏輯
            - validation參數影響轉換前的檢查嚴格程度
        """
        return {
            "action": "transition_state",
            "data": {
                "current_state": current_state,
                "transition_trigger": trigger,
                "context_data": context,
                "session_id": context.get("session_id")
            },
            "validation": {
                "check_prerequisites": True,
                "validate_slots": True
            }
        }
    
    @staticmethod
    def create_state_update_response(new_state: str, actions_executed: List[str]) -> Dict[str, Any]:
        """
        創建狀態更新響應的標準格式
        
        此方法構建StateManagementHandler返回狀態轉換結果時的標準數據格式。
        響應包含新的狀態信息、執行的動作列表和持久化狀態。
        
        Args:
            new_state (str): 轉換後的新狀態標識符
            actions_executed (List[str]): 在轉換過程中執行的動作函數列表
        
        Returns:
            Dict[str, Any]: 標準狀態更新響應格式，包含：
                - status (str): 處理狀態
                - data (Dict): 狀態數據
                    - new_state (str): 轉換後的狀態
                    - actions_executed (List[str]): 已執行的動作列表
                    - next_possible_states (List[str]): 下一步可能的狀態選項
                    - state_persistence_status (str): 持久化狀態
                - redis_info (Dict): Redis相關信息
                    - session_updated (bool): 會話是否已更新
                    - ttl_remaining (int): 會話剩餘存活時間(秒)
        
        Usage:
            response = create_state_update_response(
                "DataQuery", 
                ["search_knowledge_base", "format_results"]
            )
            
        Note:
            - new_state應該在後續請求中作為current_state使用
            - actions_executed用於調試和性能分析
            - ttl_remaining提供會話過期預警
        """
        return {
            "status": "success",
            "data": {
                "new_state": new_state,
                "actions_executed": actions_executed,
                "next_possible_states": [],
                "state_persistence_status": "saved"
            },
            "redis_info": {
                "session_updated": True,
                "ttl_remaining": 3600
            }
        }

# =====================================
# 4. MGFDKernel 核心協調器
# =====================================

class MGFDKernel:
    """
    MGFD系統的核心協調器
    
    MGFDKernel作為整個MGFD系統的中央協調器和消息路由器，負責管理五大子模組之間的
    通信、消息路由、會話管理和系統狀態監控。它實現了系統架構中的"centre-decide"策略，
    確保各模組間的解耦和高效協作。
    
    核心職責包括：
    1. 模組註冊管理：維護各個子模組的實例引用和狀態
    2. 消息路由：根據消息類型和目標模組進行智能路由
    3. 會話管理：維護活躍會話狀態和生命週期
    4. 錯誤處理：統一處理模組間通信錯誤和異常情況
    5. 性能監控：收集和分析各模組的性能指標
    
    Attributes:
        modules (Dict[str, Any]): 存儲已註冊的模組實例，鍵為模組名稱
        message_queue (List): 消息隊列，用於異步消息處理
        active_sessions (Dict[str, Any]): 活躍會話的狀態字典
    
    Usage:
        kernel = MGFDKernel()
        kernel.register_module("UserInputHandler", user_input_instance)
        
        # 發送消息
        response = kernel.send_message(message)
        
        # 創建會話上下文
        context = kernel.create_standard_context("session_123")
    
    Note:
        - 建議在系統啟動時一次性註冊所有模組
        - active_sessions會定期清理過期的會話數據
        - 消息路由失敗時會拋出ValueError異常
    """
    
    def __init__(self):
        """
        初始化MGFDKernel實例
        
        創建空的模組註冊表、消息隊列和會話管理字典。所有模組需要在初始化後
        通過register_module方法進行註冊。
        """
        self.modules = {
            "UserInputHandler": None,
            "ResponseGenHandler": None,
            "KnowledgeManagementHandler": None,
            "PromptManagementHandler": None,
            "StateManagementHandler": None
        }
        self.message_queue = []
        self.active_sessions = {}
    
    def register_module(self, module_name: str, module_instance):
        """
        註冊子模組實例到核心協調器
        
        將子模組實例註冊到MGFDKernel中，使其能夠接收和處理來自其他模組的消息。
        註冊後的模組可以通過消息路由機制進行通信。
        
        Args:
            module_name (str): 模組名稱，必須是預定義的五大子模組之一
            module_instance: 模組的實例對象，必須實現handle_message方法
        
        Raises:
            KeyError: 當module_name不在預定義的模組列表中時
            AttributeError: 當module_instance沒有handle_message方法時
        
        Usage:
            user_handler = UserInputHandler()
            kernel.register_module("UserInputHandler", user_handler)
        
        Note:
            - 模組實例必須實現handle_message(MGFDMessage) -> MGFDMessage方法
            - 重複註冊會覆蓋先前的實例
            - 建議在系統啟動階段完成所有模組註冊
        """
        if module_name in self.modules:
            self.modules[module_name] = module_instance
    
    def send_message(self, message: MGFDMessage) -> MGFDMessage:
        """
        發送消息到指定模組
        
        根據消息中指定的接收者模組路由消息，並調用目標模組的處理方法。
        這是系統內部模組間通信的標準方式。
        
        Args:
            message (MGFDMessage): 要發送的標準化消息對象
        
        Returns:
            MGFDMessage: 目標模組返回的響應消息
        
        Raises:
            ValueError: 當目標模組未註冊或不存在時
            Exception: 當目標模組處理消息時發生錯誤
        
        Usage:
            request_msg = MGFDMessage(
                message_id="123",
                message_type=MGFDMessageType.USER_INPUT_REQUEST,
                sender_module="WebAPI",
                receiver_module="UserInputHandler",
                timestamp=time.time(),
                payload={"user_input": "查詢筆電"}
            )
            response = kernel.send_message(request_msg)
        
        Note:
            - 消息發送是同步操作，可能會阻塞調用線程
            - 建議對長時間運行的操作使用異步處理
            - 消息處理錯誤會向上傳播給調用者
        """
        target_module = self.modules.get(message.receiver_module)
        if target_module:
            # 這裡應該調用目標模組的handle_message方法
            return target_module.handle_message(message)
        else:
            raise ValueError(f"Module {message.receiver_module} not found")
    
    def create_standard_context(self, session_id: str) -> Dict[str, Any]:
        """
        創建標準的共享上下文字典
        
        為新會話創建標準化的上下文數據結構，包含會話管理、狀態跟踪和性能監控
        所需的基礎字段。這個上下文會在整個對話過程中被各個模組使用和更新。
        
        Args:
            session_id (str): 會話的唯一標識符，建議使用UUID格式
        
        Returns:
            Dict[str, Any]: 標準上下文字典，包含以下字段：
                - session_id: 會話標識符
                - timestamp: 會話創建時間戳
                - current_state: 當前FSM狀態，初始為"User"
                - conversation_history: 對話歷史記錄列表
                - extracted_slots: 提取的槽位信息字典
                - user_intent: 用戶意圖標識
                - search_results: 知識庫搜索結果列表
                - selected_products: 選中的產品信息列表
                - response_data: 生成的回應數據字典
                - error_history: 錯誤歷史記錄列表
                - performance_metrics: 性能指標字典
        
        Usage:
            context = kernel.create_standard_context("sess_" + str(uuid.uuid4()))
            context["raw_user_input"] = "我要買筆電"
        
        Note:
            - 上下文字典會隨著對話進行不斷更新
            - performance_metrics用於監控各模組的響應時間
            - 建議定期清理過期的會話上下文以節省內存
        """
        return {
            "session_id": session_id,
            "timestamp": time.time(),
            "current_state": "User",
            "conversation_history": [],
            "extracted_slots": {},
            "user_intent": None,
            "search_results": [],
            "selected_products": [],
            "response_data": {},
            "error_history": [],
            "performance_metrics": {
                "total_processing_time": 0.0,
                "module_response_times": {}
            }
        }

# =====================================
# 5. 實際動作函數範例
# =====================================

class MGFDActionLibrary:
    """
    MGFD動作函數庫
    
    這個類包含了MGFD系統中使用的標準動作函數集合。所有函數都遵循增強版標準合約，
    接受共享上下文字典作為輸入，返回標準化的ActionResult對象。
    
    這個設計實現了動作函數的統一管理和調用，便於狀態機引擎進行統一處理。
    每個動作函數都是無狀態的純函數，可以獨立測試和重用。
    
    函數分類：
    1. 輸入處理類：分析和處理用戶輸入
    2. 搜索執行類：執行知識庫查詢和語義搜索
    3. 內容生成類：生成回應內容和格式化輸出
    4. 狀態管理類：處理狀態轉換和會話管理
    
    Usage:
        # 直接調用動作函數
        result = MGFDActionLibrary.analyze_user_input(context)
        
        # 在狀態轉換表中使用
        actions=[MGFDActionLibrary.analyze_user_input, 
                MGFDActionLibrary.perform_chunking_search]
    
    Note:
        - 所有方法都是靜態方法，不需要實例化
        - 函數執行時間會被記錄在ActionResult中
        - 異常會被捕獲並封裝在ActionResult的錯誤狀態中
    """
    
    @staticmethod
    def analyze_user_input(context: Dict[str, Any]) -> ActionResult:
        """
        分析用戶輸入動作函數
        
        這個函數代表不需要額外參數的動作函數範例。它從上下文中讀取用戶的原始輸入，
        執行自然語言處理分析，並返回分析結果。
        
        處理流程：
        1. 從context中提取原始用戶輸入
        2. 驗證輸入的有效性和完整性
        3. 執行NLP處理（意圖識別、實體提取）
        4. 計算分析置信度
        5. 返回結構化的分析結果
        
        Args:
            context (Dict[str, Any]): 共享上下文字典，期望包含：
                - raw_user_input (str): 用戶原始輸入文本
                - session_id (Optional[str]): 會話標識符
        
        Returns:
            ActionResult: 分析結果，包含：
                - status: SUCCESS/ERROR
                - data: 包含input_analysis字段的字典
                    - intent (str): 識別出的用戶意圖
                    - entities (List[Dict]): 提取的實體列表
                    - confidence (float): 整體分析置信度
                    - language (str): 檢測到的語言
                - execution_time: 處理耗時
        
        Error Cases:
            - MISSING_INPUT: 當raw_user_input字段缺失或為空時
            - ANALYSIS_FAILED: 當NLP處理過程中發生異常時
        
        Usage:
            context = {"raw_user_input": "我想買一台筆電"}
            result = MGFDActionLibrary.analyze_user_input(context)
            if result.status == ActionStatus.SUCCESS:
                intent = result.data["input_analysis"]["intent"]
        
        Note:
            - 這是無參數動作函數的典型實現範例
            - 函數不修改傳入的context，只返回新數據
            - 執行時間統計有助於性能優化
        """
        start_time = time.time()
        
        try:
            user_input = context.get("raw_user_input", "")
            if not user_input:
                return ActionResult(
                    status=ActionStatus.ERROR,
                    data={},
                    message="No user input provided",
                    error_code="MISSING_INPUT"
                )
            
            # 模擬NLP處理
            analysis_result = {
                "intent": "product_inquiry",
                "entities": [{"type": "product", "value": "筆電"}],
                "confidence": 0.85,
                "language": "zh-TW"
            }
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                data={"input_analysis": analysis_result},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                data={},
                message=str(e),
                error_code="ANALYSIS_FAILED"
            )
    
    @staticmethod
    def perform_chunking_search(context: Dict[str, Any]) -> ActionResult:
        """
        執行語義搜索動作函數
        
        這個函數代表需要參數的動作函數範例。它從上下文中讀取槽位信息和用戶意圖，
        構建搜索查詢，執行Parent-Child Chunking語義搜索，並返回匹配結果。
        
        搜索策略：
        1. 從context讀取必要的搜索參數
        2. 構建語義搜索查詢字符串
        3. 執行Parent-Child分層搜索
        4. 計算相似度評分和排序
        5. 返回結構化的搜索結果
        
        Args:
            context (Dict[str, Any]): 共享上下文字典，期望包含：
                - extracted_slots (Dict[str, Any]): 提取的槽位信息
                - intent (str): 用戶意圖標識
                - session_id (Optional[str]): 會話標識符
        
        Returns:
            ActionResult: 搜索結果，包含：
                - status: SUCCESS/ERROR
                - data: 包含search_results和search_metadata的字典
                    - search_results (List[Dict]): 匹配的產品列表
                    - search_metadata (Dict): 搜索過程元數據
                        - query (str): 實際執行的搜索查詢
                        - total_results (int): 結果總數
                        - search_strategy (str): 使用的搜索策略
                - execution_time: 處理耗時
        
        Error Cases:
            - INSUFFICIENT_PARAMS: 當slots和intent都缺失時
            - SEARCH_FAILED: 當搜索過程中發生異常時
        
        Usage:
            context = {
                "extracted_slots": {"category": "筆電", "budget": "5萬"},
                "intent": "product_inquiry"
            }
            result = MGFDActionLibrary.perform_chunking_search(context)
            if result.status == ActionStatus.SUCCESS:
                products = result.data["search_results"]
        
        Note:
            - 這是需要參數動作函數的典型實現範例
            - 實際實現中會連接到Milvus向量數據庫
            - 搜索結果按相似度降序排列
        """
        start_time = time.time()
        
        try:
            # 從context讀取必要參數
            slots = context.get("extracted_slots", {})
            user_intent = context.get("intent", "")
            
            if not slots and not user_intent:
                return ActionResult(
                    status=ActionStatus.ERROR,
                    data={},
                    message="Insufficient search parameters",
                    error_code="INSUFFICIENT_PARAMS"
                )
            
            # 構建搜索查詢
            search_query = f"推薦筆電 {' '.join(slots.values())}"
            
            # 模擬parent-child chunking搜索
            mock_results = [
                {
                    "product_id": "LAPTOP001",
                    "name": "高效能商務筆電",
                    "similarity_score": 0.92,
                    "chunk_type": "parent",
                    "matching_attributes": ["效能", "商務"]
                },
                {
                    "product_id": "LAPTOP002", 
                    "name": "輕薄攜帶筆電",
                    "similarity_score": 0.87,
                    "chunk_type": "child",
                    "matching_attributes": ["便攜性", "設計"]
                }
            ]
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                data={
                    "search_results": mock_results,
                    "search_metadata": {
                        "query": search_query,
                        "total_results": len(mock_results),
                        "search_strategy": "parent_child_chunking"
                    }
                },
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                data={},
                message=str(e),
                error_code="SEARCH_FAILED"
            )

# =====================================
# 6. 狀態轉換表定義
# =====================================

@dataclass
class EnhancedStateTransition:
    """
    增強版狀態轉換定義類
    
    這個dataclass擴展了基本的狀態轉換定義，增加了前置條件驗證、超時處理、
    重試機制等進階功能。它是Table-Driven狀態機設計的核心數據結構，
    定義了狀態間轉換的完整規則和約束。
    
    相比基礎版本的改進：
    1. 前置條件檢查：確保轉換前滿足必要條件
    2. 超時機制：避免長時間運行的動作阻塞系統
    3. 重試邏輯：提高系統在異常情況下的穩定性
    4. 增強驗證：提供更嚴格的狀態轉換控制
    
    Attributes:
        actions (List[Callable]): 在此狀態要執行的動作函數列表
        next_state (str): 執行完所有動作後的下一個狀態
        prerequisites (Optional[List[str]]): 前置條件字段列表
        timeout_seconds (Optional[int]): 動作執行超時時間限制
        retry_count (int): 失敗時的重試次數限制
    
    Usage:
        transition = EnhancedStateTransition(
            actions=[analyze_input, extract_slots],
            next_state="DataQuery",
            prerequisites=["raw_user_input"],
            timeout_seconds=30,
            retry_count=2
        )
        
        # 驗證前置條件
        if transition.validate_prerequisites(context):
            # 執行狀態轉換
            pass
    
    Note:
        - prerequisites為None時表示無前置條件要求
        - timeout_seconds為None時表示無超時限制
        - retry_count為0時表示不重試失敗的動作
    """
    actions: List[Callable[[Dict[str, Any]], ActionResult]]
    next_state: str
    prerequisites: List[str] = None  # 前置條件
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    
    def validate_prerequisites(self, context: Dict[str, Any]) -> bool:
        """
        驗證前置條件是否滿足
        
        檢查context字典中是否包含所有必需的前置條件字段。這確保了
        狀態轉換只在滿足必要條件時執行，避免因缺少關鍵數據而導致的錯誤。
        
        Args:
            context (Dict[str, Any]): 當前的共享上下文字典
        
        Returns:
            bool: 如果所有前置條件都滿足返回True，否則返回False
        
        Usage:
            context = {"user_input": "查詢筆電", "session_id": "123"}
            if transition.validate_prerequisites(context):
                print("可以執行狀態轉換")
            else:
                print("前置條件不滿足")
        
        Logic:
            1. 如果prerequisites為None，直接返回True（無條件要求）
            2. 遍歷所有前置條件字段
            3. 檢查每個字段是否存在於context中
            4. 只有當所有字段都存在時才返回True
        
        Note:
            - 只檢查字段是否存在，不檢查字段值的有效性
            - 空值（None、空字符串等）被視為存在的字段
            - 建議在狀態轉換前調用此方法進行驗證
        """
        if not self.prerequisites:
            return True
        
        for prereq in self.prerequisites:
            if prereq not in context:
                return False
        return True

# MGFD系統的狀態轉換表
MGFD_STATE_TRANSITIONS: Dict[str, EnhancedStateTransition] = {
    "User": EnhancedStateTransition(
        actions=[MGFDActionLibrary.analyze_user_input],
        next_state="System",
        prerequisites=["raw_user_input"]
    ),
    "System": EnhancedStateTransition(
        actions=[
            MGFDActionLibrary.perform_chunking_search,
            # 其他系統處理動作...
        ],
        next_state="DataQuery",
        prerequisites=["extracted_slots", "intent"]
    ),
    "DataQuery": EnhancedStateTransition(
        actions=[
            # 數據查詢和格式化動作...
        ],
        next_state="User",
        prerequisites=["search_results"]
    )
}