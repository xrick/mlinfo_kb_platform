"""
StateManageHandler - MGFD 狀態管理模組

提供完整的狀態管理功能：
1. StateManagementHandler - 主要狀態管理器
2. EventStore - 事件溯源存儲系統
3. StateTransition - 狀態轉換邏輯
4. 狀態解析器 (FixedResolver, ConditionalResolver, DynamicStateResolver)
5. 狀態驗證器和工具類別

基於 MGFD 系統設計 v0.4.3，實現：
- 表驅動狀態機 (STATE_TRANSITIONS)
- Redis 狀態持久化
- 事件溯源架構
- 智能狀態恢復
- 完整驗證和預測系統
"""

# 導入核心類別
from .StateManagementHandler import StateManagementHandler
from .EventStore import EventStore, EventStoreError, EventSchemaValidator
from .StateTransition import (
    StateTransition, 
    StateResolver, 
    FixedResolver, 
    ConditionalResolver,
    DynamicStateResolver,
    BusinessRuleEngine,
    StateCondition,
    ConditionOperator,
    TransitionResult,
    RetryPolicy
)
from .StateTransitionsConfig import (
    STATE_TRANSITIONS,
    get_state_transitions,
    create_state_transitions_config,
    # 導出所有標準動作函數
    initialize_session,
    load_user_profile,
    detect_user_intent,
    setup_context,
    generate_funnel_introduction,
    create_first_question,
    initialize_slot_collection,
    process_user_answer,
    update_slot_values,
    evaluate_information_completeness,
    generate_next_question,
    validate_collected_requirements,
    search_knowledge_base,
    rank_recommendations,
    prepare_comparison_data
)

# 導入支援工具類別
from .StateStrategyFactory import (
    StateStrategyFactory,
    StateStrategy,
    DefaultStrategy,
    PerformanceStrategy,
    LearningStrategy
)
from .TransitionPredictor import TransitionPredictor
from .StateValidator import (
    StateValidator,
    ValidationResult,
    ValidationSeverity,
    ValidationType
)

# 版本信息
__version__ = "1.0.0"
__author__ = "MGFD Development Team"

# 導出的主要類別和函數
__all__ = [
    # 核心組件
    "StateManagementHandler",
    "EventStore",
    "EventStoreError",
    "EventSchemaValidator",
    
    # 狀態轉換系統
    "StateTransition",
    "StateResolver",
    "FixedResolver", 
    "ConditionalResolver",
    "DynamicStateResolver",
    "BusinessRuleEngine",
    "StateCondition",
    "ConditionOperator",
    "TransitionResult",
    "RetryPolicy",
    
    # 配置和動作函數
    "STATE_TRANSITIONS",
    "get_state_transitions",
    "create_state_transitions_config",
    "initialize_session",
    "load_user_profile",
    "detect_user_intent",
    "setup_context",
    "generate_funnel_introduction",
    "create_first_question",
    "initialize_slot_collection",
    "process_user_answer",
    "update_slot_values",
    "evaluate_information_completeness",
    "generate_next_question",
    "validate_collected_requirements",
    "search_knowledge_base",
    "rank_recommendations",
    "prepare_comparison_data",
    
    # 支援工具
    "StateStrategyFactory",
    "StateStrategy",
    "DefaultStrategy",
    "PerformanceStrategy", 
    "LearningStrategy",
    "TransitionPredictor",
    "StateValidator",
    "ValidationResult",
    "ValidationSeverity",
    "ValidationType",
]

# 模組初始化日誌
import logging
logger = logging.getLogger(__name__)
logger.info(f"StateManageHandler 模組已載入 (版本 {__version__})")

# 便利函數：創建預配置的狀態管理器
def create_state_manager(redis_client=None, **kwargs):
    """
    創建預配置的狀態管理器實例
    
    Args:
        redis_client: Redis 客戶端實例（可選）
        **kwargs: 其他配置參數
        
    Returns:
        StateManagementHandler 實例
    """
    try:
        return StateManagementHandler(redis_client=redis_client, **kwargs)
    except Exception as e:
        logger.error(f"創建狀態管理器失敗: {e}")
        raise

# 便利函數：創建事件存儲
def create_event_store(redis_client, **kwargs):
    """
    創建事件存儲實例
    
    Args:
        redis_client: Redis 客戶端實例
        **kwargs: 其他配置參數
        
    Returns:
        EventStore 實例
    """
    try:
        return EventStore(redis_client, **kwargs)
    except Exception as e:
        logger.error(f"創建事件存儲失敗: {e}")
        raise

# 便利函數：創建狀態驗證器
def create_state_validator(**kwargs):
    """
    創建狀態驗證器實例
    
    Args:
        **kwargs: 配置參數
        
    Returns:
        StateValidator 實例
    """
    try:
        return StateValidator(**kwargs)
    except Exception as e:
        logger.error(f"創建狀態驗證器失敗: {e}")
        raise