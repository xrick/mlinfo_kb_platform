"""
STATE_TRANSITIONS 表驅動配置
基於 MGFD 系統設計文件 v0.4.3 的完整狀態機配置

狀態機流程：
Start -> Collecting_Needs -> Needs_Defined -> Providing_Options -> Decision_Making -> Purchase_Intention -> End
        ↑                  ↓                    ↓                      ↓
        └─ 深入追問 ──────┘    → After_Sales ←─  → Order_Confirmed ←──┘

實現功能：
1. 完整的對話狀態流程
2. 智能狀態轉換邏輯
3. 動作和條件配置
4. 性能優化和錯誤處理
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from .StateTransition import (
    StateTransition, FixedResolver, ConditionalResolver, DynamicStateResolver,
    StateCondition, ConditionOperator, RetryPolicy
)

logger = logging.getLogger(__name__)


# =================== 標準動作函數定義 ===================

async def initialize_session(context: Dict[str, Any]) -> Dict[str, Any]:
    """初始化會話 - 標準動作合約"""
    logger.info(f"初始化會話: {context.get('session_id', 'unknown')}")
    
    return {
        "session_initialized": True,
        "session_start_time": datetime.now().isoformat(),
        "user_profile": context.get("user_profile", {}),
        "slots": context.get("slots", {}),
        "history": context.get("history", []),
        "stage": "INIT"
    }

async def load_user_profile(context: Dict[str, Any]) -> Dict[str, Any]:
    """載入用戶檔案 - 標準動作合約"""
    user_id = context.get("user_id")
    
    # 模擬用戶檔案載入
    user_profile = {
        "user_id": user_id,
        "is_returning_user": bool(user_id),
        "previous_purchases": [],
        "preferred_brands": [],
        "budget_range": None,
        "technical_level": "beginner"
    }
    
    logger.debug(f"載入用戶檔案: {user_id}")
    
    return {
        "user_profile": user_profile,
        "user_loaded": True
    }

async def detect_user_intent(context: Dict[str, Any]) -> Dict[str, Any]:
    """檢測用戶意圖 - 標準動作合約"""
    user_message = context.get("user_message", "").lower()
    intent = context.get("intent", "unknown")
    confidence = context.get("confidence", 0.0)
    
    # 增強意圖檢測邏輯
    intent_keywords = {
        "ask_recommendation": ["推薦", "建議", "找", "買", "want", "需要"],
        "ask_comparison": ["比較", "對比", "差異", "哪個好", "比較好"],
        "ask_price": ["價格", "多少錢", "預算", "便宜", "貴"],
        "ask_specs": ["規格", "配置", "cpu", "gpu", "記憶體", "storage"],
        "greet": ["你好", "hello", "hi", "嗨"],
        "goodbye": ["再見", "bye", "謝謝", "結束"]
    }
    
    detected_intent = intent
    max_confidence = confidence
    
    for intent_type, keywords in intent_keywords.items():
        keyword_matches = sum(1 for keyword in keywords if keyword in user_message)
        if keyword_matches > 0:
            current_confidence = min(keyword_matches / len(keywords) + 0.3, 1.0)
            if current_confidence > max_confidence:
                detected_intent = intent_type
                max_confidence = current_confidence
    
    return {
        "intent": detected_intent,
        "confidence": max_confidence,
        "intent_detected": True
    }

async def setup_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """設置處理上下文 - 標準動作合約"""
    return {
        "context_ready": True,
        "processing_timestamp": datetime.now().isoformat(),
        "context_version": "1.0"
    }

async def generate_funnel_introduction(context: Dict[str, Any]) -> Dict[str, Any]:
    """生成漏斗介紹 - 標準動作合約"""
    user_profile = context.get("user_profile", {})
    is_returning = user_profile.get("is_returning_user", False)
    
    if is_returning:
        intro_message = "歡迎回來！讓我幫您找到更適合的筆電。"
    else:
        intro_message = "歡迎使用筆電購物助手！讓我幫您找到最適合的筆電。"
    
    return {
        "funnel_intro": intro_message,
        "funnel_started": True,
        "response_message": intro_message
    }

async def create_first_question(context: Dict[str, Any]) -> Dict[str, Any]:
    """創建第一個問題 - 標準動作合約"""
    # 基於用戶意圖決定第一個問題
    intent = context.get("intent", "")
    
    questions = {
        "ask_recommendation": "請問您主要會用這台筆電來做什麼呢？例如工作、學習、遊戲或創作？",
        "ask_price": "請問您的預算大概是多少呢？",
        "ask_specs": "請問您對筆電的效能有什麼特別需求嗎？",
        "default": "請問您主要會用這台筆電來做什麼呢？"
    }
    
    question = questions.get(intent, questions["default"])
    
    return {
        "current_question": question,
        "question_type": "usage_purpose",
        "question_created": True,
        "response_message": question
    }

async def initialize_slot_collection(context: Dict[str, Any]) -> Dict[str, Any]:
    """初始化槽位收集 - 標準動作合約"""
    required_slots = [
        "usage_purpose", "price_range", "cpu_performance", 
        "gpu_performance", "portability", "screen_size", "brand"
    ]
    
    slots_status = {}
    for slot in required_slots:
        slots_status[slot] = {
            "filled": slot in context.get("slots", {}),
            "priority": 1 if slot in ["usage_purpose", "price_range"] else 2,
            "required": slot in ["usage_purpose", "price_range"]
        }
    
    return {
        "slots_status": slots_status,
        "collection_initialized": True,
        "required_slots_remaining": sum(1 for s in slots_status.values() if s["required"] and not s["filled"])
    }

async def process_user_answer(context: Dict[str, Any]) -> Dict[str, Any]:
    """處理用戶回答 - 標準動作合約"""
    user_message = context.get("user_message", "")
    current_question_type = context.get("question_type", "")
    
    # 從用戶回答中提取槽位值（簡化版本）
    extracted_slots = {}
    
    if current_question_type == "usage_purpose":
        usage_keywords = {
            "工作": ["工作", "辦公", "文書", "商務", "office"],
            "學習": ["學習", "讀書", "上課", "study", "education"],
            "遊戲": ["遊戲", "gaming", "玩", "電競"],
            "創作": ["創作", "設計", "影片", "剪輯", "繪圖"]
        }
        
        for usage, keywords in usage_keywords.items():
            if any(keyword in user_message.lower() for keyword in keywords):
                extracted_slots["usage_purpose"] = usage
                break
    
    return {
        "extracted_slots": extracted_slots,
        "answer_processed": True,
        "user_cooperative": len(user_message.split()) >= 2  # 簡單的合作度判斷
    }

async def update_slot_values(context: Dict[str, Any]) -> Dict[str, Any]:
    """更新槽位值 - 標準動作合約"""
    current_slots = context.get("slots", {})
    extracted_slots = context.get("extracted_slots", {})
    
    # 合併槽位
    updated_slots = {**current_slots, **extracted_slots}
    
    return {
        "slots": updated_slots,
        "slots_updated": True,
        "new_slots_count": len(extracted_slots)
    }

async def evaluate_information_completeness(context: Dict[str, Any]) -> Dict[str, Any]:
    """評估信息完整性 - 標準動作合約"""
    slots = context.get("slots", {})
    required_slots = ["usage_purpose", "price_range"]
    optional_slots = ["cpu_performance", "gpu_performance", "portability", "screen_size", "brand"]
    
    required_filled = sum(1 for slot in required_slots if slot in slots and slots[slot])
    optional_filled = sum(1 for slot in optional_slots if slot in slots and slots[slot])
    
    completeness_score = (required_filled / len(required_slots) * 0.7 + 
                         optional_filled / len(optional_slots) * 0.3)
    
    slots_sufficient = required_filled >= len(required_slots) and completeness_score >= 0.6
    
    return {
        "completeness_score": completeness_score,
        "required_slots_filled": required_filled,
        "optional_slots_filled": optional_filled,
        "slots_sufficient": slots_sufficient,
        "information_evaluated": True
    }

async def generate_next_question(context: Dict[str, Any]) -> Dict[str, Any]:
    """生成下一個問題 - 標準動作合約"""
    slots = context.get("slots", {})
    
    # 決定下一個問題
    next_questions = {
        "price_range": "請問您的預算大概是多少呢？",
        "cpu_performance": "您對筆電的運算效能有什麼要求嗎？例如需要處理大型檔案或多工作業？",
        "gpu_performance": "您需要獨立顯示卡來玩遊戲或處理圖像嗎？",
        "portability": "您希望筆電輕便好攜帶，還是效能優先呢？",
        "screen_size": "您偏好多大的螢幕尺寸？",
        "brand": "您有偏好的品牌嗎？"
    }
    
    # 找到第一個未填充的槽位
    next_question_type = None
    next_question = "還有其他需求嗎？"
    
    for slot_type, question in next_questions.items():
        if slot_type not in slots or not slots[slot_type]:
            next_question_type = slot_type
            next_question = question
            break
    
    return {
        "current_question": next_question,
        "question_type": next_question_type,
        "next_question_generated": True,
        "response_message": next_question
    }

async def validate_collected_requirements(context: Dict[str, Any]) -> Dict[str, Any]:
    """驗證收集的需求 - 標準動作合約"""
    slots = context.get("slots", {})
    
    # 驗證邏輯
    validation_results = []
    
    # 檢查用途和效能需求的一致性
    usage = slots.get("usage_purpose", "")
    cpu_perf = slots.get("cpu_performance", "")
    
    if usage == "遊戲" and cpu_perf == "低":
        validation_results.append({
            "type": "inconsistency",
            "message": "遊戲用途通常需要較高的 CPU 效能"
        })
    
    return {
        "requirements_valid": len(validation_results) == 0,
        "validation_results": validation_results,
        "requirements_validated": True
    }

async def search_knowledge_base(context: Dict[str, Any]) -> Dict[str, Any]:
    """搜尋知識庫 - 標準動作合約"""
    slots = context.get("slots", {})
    
    # 模擬知識庫搜尋
    search_results = [
        {
            "product_id": "NB001",
            "name": "高效能商務筆電 Pro",
            "brand": "TechBrand",
            "price": 35000,
            "cpu": "Intel i7",
            "gpu": "整合式",
            "ram": "16GB",
            "storage": "512GB SSD",
            "screen": "14吋",
            "weight": "1.2kg",
            "match_score": 0.85
        },
        {
            "product_id": "NB002", 
            "name": "輕薄學習筆電 Lite",
            "brand": "EduTech",
            "price": 22000,
            "cpu": "Intel i5",
            "gpu": "整合式",
            "ram": "8GB",
            "storage": "256GB SSD", 
            "screen": "13吋",
            "weight": "1.0kg",
            "match_score": 0.78
        }
    ]
    
    return {
        "search_results": search_results,
        "results_count": len(search_results),
        "knowledge_searched": True
    }

async def rank_recommendations(context: Dict[str, Any]) -> Dict[str, Any]:
    """排序推薦 - 標準動作合約"""
    search_results = context.get("search_results", [])
    
    # 根據 match_score 排序
    ranked_results = sorted(search_results, key=lambda x: x.get("match_score", 0), reverse=True)
    
    return {
        "ranked_recommendations": ranked_results,
        "top_recommendation": ranked_results[0] if ranked_results else None,
        "recommendations_ranked": True
    }

async def prepare_comparison_data(context: Dict[str, Any]) -> Dict[str, Any]:
    """準備比較數據 - 標準動作合約"""
    recommendations = context.get("ranked_recommendations", [])
    
    # 準備比較表格數據
    comparison_data = []
    if len(recommendations) >= 2:
        comparison_headers = ["規格項目"] + [rec["name"] for rec in recommendations[:3]]
        
        specs_to_compare = [
            ("品牌", "brand"),
            ("價格", "price"),
            ("處理器", "cpu"),
            ("顯示卡", "gpu"),
            ("記憶體", "ram"),
            ("儲存空間", "storage"),
            ("螢幕尺寸", "screen"),
            ("重量", "weight")
        ]
        
        for spec_name, spec_key in specs_to_compare:
            row = [spec_name]
            for rec in recommendations[:3]:
                row.append(str(rec.get(spec_key, "N/A")))
            comparison_data.append(row)
    
    return {
        "comparison_data": comparison_data,
        "comparison_ready": len(comparison_data) > 0,
        "data_prepared": True
    }

# =================== STATE_TRANSITIONS 配置 ===================

def create_state_transitions_config() -> Dict[str, StateTransition]:
    """
    創建完整的狀態轉換配置
    基於 MGFD 系統設計文件的狀態機流程
    """
    
    return {
        # =================== 初始狀態 ===================
        "INIT": StateTransition(
            actions=[
                initialize_session,
                load_user_profile,
                detect_user_intent,
                setup_context
            ],
            next_state_resolver=DynamicStateResolver({
                "new_user": "FUNNEL_START",
                "returning_user_with_history": "CONTEXT_RECALL",
                "direct_question": "ELICITATION",
                "price_inquiry": "PRICE_FOCUSED_ELICITATION",
                "technical_question": "TECHNICAL_QA"
            }),
            preconditions=[
                StateCondition("session_id", ConditionOperator.EXISTS, True, weight=1.0)
            ],
            postconditions=[
                StateCondition("session_initialized", ConditionOperator.EQUALS, True)
            ],
            timeout_ms=5000,
            retry_policy=RetryPolicy(max_retries=2),
            description="系統初始化，載入用戶檔案並檢測意圖",
            tags=["initialization", "critical"],
            performance_critical=True
        ),
        
        # =================== 漏斗對話開始 ===================
        "FUNNEL_START": StateTransition(
            actions=[
                generate_funnel_introduction,
                create_first_question,
                initialize_slot_collection
            ],
            next_state_resolver=ConditionalResolver({
                "user_cooperative": "FUNNEL_QUESTION",
                "direct_request": "DIRECT_RECOMMENDATION",
                "user_confused": "CLARIFICATION"
            }, default_state="FUNNEL_QUESTION"),
            context_enrichment=[
                # 這裡可以添加市場趨勢、用戶偏好等豐富化函數
            ],
            description="開始漏斗對話流程，介紹系統並提出第一個問題",
            tags=["funnel", "engagement"]
        ),
        
        # =================== 漏斗問題循環 ===================
        "FUNNEL_QUESTION": StateTransition(
            actions=[
                process_user_answer,
                update_slot_values,
                evaluate_information_completeness,
                generate_next_question
            ],
            next_state_resolver=ConditionalResolver({
                "slots_sufficient": "RECOMMENDATION_PREPARATION",
                "need_more_info": "FUNNEL_QUESTION",  # 繼續循環
                "user_frustrated": "SIMPLIFY_QUESTIONS",
                "conflicting_requirements": "REQUIREMENT_CLARIFICATION"
            }, default_state="FUNNEL_QUESTION"),
            adaptive_behavior=True,  # 可以學習優化問題順序
            description="循環進行問題詢問，收集用戶需求信息",
            tags=["funnel", "data_collection", "adaptive"]
        ),
        
        # =================== 推薦準備 ===================
        "RECOMMENDATION_PREPARATION": StateTransition(
            actions=[
                validate_collected_requirements,
                search_knowledge_base,
                rank_recommendations,
                prepare_comparison_data
            ],
            next_state_resolver=FixedResolver("RECOMMENDATION_PRESENTATION"),
            performance_critical=True,
            timeout_ms=10000,  # 搜尋可能需要更長時間
            description="準備推薦內容，搜尋並排序產品",
            tags=["recommendation", "search", "performance_critical"]
        ),
        
        # =================== 推薦展示 ===================
        "RECOMMENDATION_PRESENTATION": StateTransition(
            actions=[
                # 這些動作將由 ResponseGenHandler 提供
            ],
            next_state_resolver=ConditionalResolver({
                "accept_recommendation": "PURCHASE_GUIDANCE",
                "need_more_options": "EXPAND_RECOMMENDATIONS",
                "modify_requirements": "REQUIREMENT_REFINEMENT",
                "ask_questions": "PRODUCT_QA",
                "compare_products": "PRODUCT_COMPARISON"
            }, default_state="PRODUCT_QA"),
            success_metrics=["user_satisfaction", "conversion_rate"],
            description="展示推薦結果並處理用戶反饋",
            tags=["recommendation", "presentation", "conversion"]
        ),
        
        # =================== 產品問答 ===================
        "PRODUCT_QA": StateTransition(
            actions=[
                # 產品問答相關動作
            ],
            next_state_resolver=ConditionalResolver({
                "question_answered": "RECOMMENDATION_PRESENTATION",
                "need_technical_details": "TECHNICAL_DETAILS",
                "ready_to_purchase": "PURCHASE_GUIDANCE"
            }, default_state="RECOMMENDATION_PRESENTATION"),
            description="回答用戶對產品的具體問題",
            tags=["qa", "support"]
        ),
        
        # =================== 需求澄清 ===================
        "ELICITATION": StateTransition(
            actions=[
                # 需求澄清相關動作
            ],
            next_state_resolver=ConditionalResolver({
                "requirements_clear": "RECOMMENDATION_PREPARATION",
                "need_more_clarification": "ELICITATION",
                "start_funnel": "FUNNEL_START"
            }, default_state="FUNNEL_START"),
            description="澄清不明確的用戶需求",
            tags=["elicitation", "clarification"]
        ),
        
        # =================== 錯誤處理 ===================
        "ERROR": StateTransition(
            actions=[
                # 錯誤處理和恢復動作
            ],
            next_state_resolver=ConditionalResolver({
                "error_resolved": "FUNNEL_START",
                "critical_error": "END"
            }, default_state="END"),
            description="處理系統錯誤並嘗試恢復",
            tags=["error", "recovery"]
        ),
        
        # =================== 結束狀態 ===================
        "END": StateTransition(
            actions=[
                # 會話結束清理動作
            ],
            next_state_resolver=FixedResolver("END"),
            description="會話正常結束",
            tags=["termination"]
        )
    }


# =================== 工廠函數 ===================

def get_state_transitions() -> Dict[str, StateTransition]:
    """獲取狀態轉換配置的工廠函數"""
    try:
        config = create_state_transitions_config()
        logger.info(f"載入了 {len(config)} 個狀態轉換配置")
        return config
    except Exception as e:
        logger.error(f"載入狀態轉換配置失敗: {e}")
        # 返回最小配置以避免系統崩潰
        return {
            "INIT": StateTransition(
                actions=[initialize_session],
                next_state_resolver=FixedResolver("FUNNEL_START")
            ),
            "FUNNEL_START": StateTransition(
                actions=[generate_funnel_introduction],
                next_state_resolver=FixedResolver("END")
            ),
            "END": StateTransition(
                actions=[],
                next_state_resolver=FixedResolver("END")
            )
        }


# 導出配置
STATE_TRANSITIONS = get_state_transitions()


# =================== 簡化 DSM 系統配置 ===================

def get_dsm_simplified_config() -> Dict[str, Any]:
    """
    獲取簡化 DSM 系統配置
    
    Returns:
        簡化 DSM 配置字典
    """
    return {
        "system_name": "DSM_Simplified_Linear_Flow",
        "version": "1.0.0",
        "description": "DSM 簡化線性流程配置",
        "states": {
            "OnReceiveMsg": {
                "state_id": "OnReceiveMsg",
                "state_name": "接收消息",
                "description": "接收和解析用戶消息，提取關鍵詞和意圖",
                "execution_order": 1,
                "action_function": "receive_msg",
                "next_state": "OnResponseMsg",
                "transition_condition": "always"
            },
            "OnResponseMsg": {
                "state_id": "OnResponseMsg",
                "state_name": "回應消息",
                "description": "根據流程方向生成回應和準備數據處理",
                "execution_order": 2,
                "action_function": "response_msg",
                "next_state": "OnGenFunnelChat",
                "transition_condition": "always"
            },
            "OnGenFunnelChat": {
                "state_id": "OnGenFunnelChat",
                "state_name": "生成漏斗對話",
                "description": "生成漏斗對話引導，收集用戶需求",
                "execution_order": 3,
                "action_function": "gen_funnel_chat",
                "next_state": "OnGenMDContent",
                "transition_condition": "always"
            },
            "OnGenMDContent": {
                "state_id": "OnGenMDContent",
                "state_name": "生成 Markdown 內容",
                "description": "根據回應類型生成相應的 Markdown 內容",
                "execution_order": 4,
                "action_function": "gen_md_content",
                "next_state": "OnDataQuery",
                "transition_condition": "always"
            },
            "OnDataQuery": {
                "state_id": "OnDataQuery",
                "state_name": "執行數據查詢",
                "description": "執行內部數據查詢，獲取相關信息",
                "execution_order": 5,
                "action_function": "data_query",
                "next_state": "OnQueriedDataProcessing",
                "transition_condition": "always"
            },
            "OnQueriedDataProcessing": {
                "state_id": "OnQueriedDataProcessing",
                "state_name": "處理查詢數據",
                "description": "處理查詢結果，更新 Markdown 內容",
                "execution_order": 6,
                "action_function": "queried_data_processing",
                "next_state": "OnSendFront",
                "transition_condition": "always"
            },
            "OnSendFront": {
                "state_id": "OnSendFront",
                "state_name": "發送到前端",
                "description": "將處理後的數據發送到前端瀏覽器",
                "execution_order": 7,
                "action_function": "send_front",
                "next_state": "OnWaitMsg",
                "transition_condition": "always"
            },
            "OnWaitMsg": {
                "state_id": "OnWaitMsg",
                "state_name": "等待下一個消息",
                "description": "準備接收下一個用戶消息",
                "execution_order": 8,
                "action_function": "wait_msg",
                "next_state": "OnReceiveMsg",
                "transition_condition": "always"
            }
        },
        "flow_transitions": {
            "linear_sequence": [
                "OnReceiveMsg",
                "OnResponseMsg", 
                "OnGenFunnelChat",
                "OnGenMDContent",
                "OnDataQuery",
                "OnQueriedDataProcessing",
                "OnSendFront",
                "OnWaitMsg"
            ],
            "execution_mode": "linear",
            "error_handling": "continue_on_error"
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "author": "System Architect",
            "tags": ["DSM", "Linear Flow", "Simplified"]
        }
    }


def get_dsm_linear_execution_order() -> List[str]:
    """
    獲取 DSM 線性執行順序
    
    Returns:
        狀態執行順序列表
    """
    config = get_dsm_simplified_config()
    return config["flow_transitions"]["linear_sequence"]


def get_dsm_state_info(state_id: str) -> Dict[str, Any]:
    """
    獲取 DSM 狀態信息
    
    Args:
        state_id: 狀態 ID
        
    Returns:
        狀態信息字典
    """
    config = get_dsm_simplified_config()
    return config["states"].get(state_id, {})


# 導出 DSM 配置
DSM_SIMPLIFIED_CONFIG = get_dsm_simplified_config()
DSM_LINEAR_EXECUTION_ORDER = get_dsm_linear_execution_order()