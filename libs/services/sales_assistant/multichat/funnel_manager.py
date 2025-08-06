#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多輪漏斗式對話管理器 (Multi-round Funnel Conversation Manager)
負責處理模糊查詢的智能分流，通過精準追問幫助用戶明確需求類型
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

from .models import generate_id

class FunnelQueryType(Enum):
    """漏斗查詢類型"""
    SERIES_COMPARISON = "series_comparison"        # 系列比較查詢
    PURPOSE_RECOMMENDATION = "purpose_recommendation"  # 用途推薦查詢
    MIXED_AMBIGUOUS = "mixed_ambiguous"           # 混合模糊查詢
    SPECIFIC_QUERY = "specific_query"             # 明確查詢（不需要漏斗）

class FunnelFlowType(Enum):
    """漏斗流程類型"""
    SERIES_COMPARISON_FLOW = "series_comparison_flow"
    PURPOSE_RECOMMENDATION_FLOW = "purpose_recommendation_flow"
    HYBRID_FLOW = "hybrid_flow"

@dataclass
class FunnelQuestion:
    """漏斗問題數據結構"""
    question_id: str
    question_text: str
    options: List[Dict[str, Any]]
    context: Dict[str, Any]
    priority: int = 1

@dataclass
class FunnelSession:
    """漏斗對話會話"""
    session_id: str
    original_query: str
    detected_type: FunnelQueryType
    current_question: Optional[FunnelQuestion]
    user_responses: List[Dict[str, Any]]
    target_flow: Optional[FunnelFlowType]
    created_at: datetime
    is_completed: bool = False

class FunnelConversationManager:
    """多輪漏斗式對話管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化漏斗對話管理器
        
        Args:
            config_path: 漏斗問題配置檔案路徑
        """
        self.config_path = config_path or self._get_default_config_path()
        self.funnel_config = self._load_funnel_config()
        self.active_sessions: Dict[str, FunnelSession] = {}
        
        # 查詢類型識別規則
        self.classification_rules = self._build_classification_rules()
        
        logging.info(f"漏斗對話管理器初始化完成，載入 {len(self.funnel_config.get('questions', {}))} 個問題模板")
    
    def _get_default_config_path(self) -> str:
        """取得預設配置檔案路徑"""
        return str(Path(__file__).parent / "funnel_questions.json")
    
    def _load_funnel_config(self) -> Dict:
        """載入漏斗問題配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logging.info("成功載入漏斗問題配置")
                return config
        except FileNotFoundError:
            logging.warning(f"漏斗配置檔案不存在: {self.config_path}，使用預設配置")
            return self._get_default_config()
        except Exception as e:
            logging.error(f"載入漏斗配置失敗: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """取得預設漏斗配置"""
        return {
            "questions": {
                "series_vs_purpose": {
                    "question_id": "series_vs_purpose",
                    "question_text": "為了更精準地幫助您，請選擇您的需求類型：",
                    "context": {
                        "description": "主要需求類型分流",
                        "trigger_conditions": "模糊查詢且包含比較或推薦意圖"
                    },
                    "options": [
                        {
                            "option_id": "series_comparison",
                            "label": "🔍 系列比較",
                            "description": "我想比較某個系列（如958系列）內所有機型的規格差異",
                            "route": "series_comparison_flow",
                            "keywords": ["比較", "系列", "規格", "差異", "不同"]
                        },
                        {
                            "option_id": "purpose_recommendation",
                            "label": "🎯 用途推薦", 
                            "description": "我想根據特定用途（如遊戲、辦公）找到最適合的筆電推薦",
                            "route": "purpose_recommendation_flow",
                            "keywords": ["推薦", "適合", "用途", "遊戲", "辦公", "學習"]
                        }
                    ]
                }
            },
            "flows": {
                "series_comparison_flow": {
                    "name": "系列比較流程",
                    "steps": ["confirm_series", "confirm_comparison_focus", "execute_comparison"]
                },
                "purpose_recommendation_flow": {
                    "name": "用途推薦流程", 
                    "steps": ["confirm_purpose", "collect_preferences", "generate_recommendation"]
                }
            }
        }
    
    def _build_classification_rules(self) -> Dict:
        """建立查詢分類規則"""
        return {
            "series_comparison_indicators": [
                r'比較.*\d{3}.*系列',           # 比較xxx系列
                r'\d{3}.*系列.*比較',           # xxx系列比較
                r'\d{3}.*系列.*差異',           # xxx系列差異
                r'\d{3}.*系列.*不同',           # xxx系列不同
                r'\d{3}.*系列.*規格',           # xxx系列規格
                r'系列.*比較.*規格',            # 系列比較規格
            ],
            "purpose_recommendation_indicators": [
                r'推薦.*適合.*\w+',             # 推薦適合xxx
                r'適合.*\w+.*筆電',             # 適合xxx筆電
                r'\w+.*用.*筆電',               # xxx用筆電
                r'找.*\w+.*筆電',               # 找xxx筆電
                r'需要.*\w+.*筆電',             # 需要xxx筆電
                r'想要.*\w+.*筆電',             # 想要xxx筆電
            ],
            "mixed_indicators": [
                r'比較.*適合.*\w+',             # 比較適合xxx
                r'哪.*適合.*\w+',               # 哪個適合xxx
                r'系列.*適合.*\w+',             # 系列適合xxx
            ]
        }
    
    def classify_ambiguous_query(self, query: str) -> Tuple[FunnelQueryType, float]:
        """
        分類模糊查詢類型
        
        Args:
            query: 使用者查詢
            
        Returns:
            (查詢類型, 信心度分數)
        """
        try:
            logging.info(f"開始分類查詢: '{query}'")
            
            query_lower = query.lower()
            scores = {
                FunnelQueryType.SERIES_COMPARISON: 0.0,
                FunnelQueryType.PURPOSE_RECOMMENDATION: 0.0,
                FunnelQueryType.MIXED_AMBIGUOUS: 0.0
            }
            
            # 檢查系列比較指標
            for pattern in self.classification_rules["series_comparison_indicators"]:
                if re.search(pattern, query, re.IGNORECASE):
                    scores[FunnelQueryType.SERIES_COMPARISON] += 1.0
                    logging.info(f"系列比較指標匹配: {pattern}")
            
            # 檢查用途推薦指標
            for pattern in self.classification_rules["purpose_recommendation_indicators"]:
                if re.search(pattern, query, re.IGNORECASE):
                    scores[FunnelQueryType.PURPOSE_RECOMMENDATION] += 1.0
                    logging.info(f"用途推薦指標匹配: {pattern}")
            
            # 檢查混合指標
            for pattern in self.classification_rules["mixed_indicators"]:
                if re.search(pattern, query, re.IGNORECASE):
                    scores[FunnelQueryType.MIXED_AMBIGUOUS] += 1.5  # 混合查詢權重較高
                    logging.info(f"混合指標匹配: {pattern}")
            
            # 額外的關鍵字權重調整
            purpose_keywords = ["遊戲", "辦公", "學習", "商務", "創作", "設計", "工作", "學生"]
            series_keywords = ["819", "839", "958", "系列", "機型", "型號"]
            
            for keyword in purpose_keywords:
                if keyword in query_lower:
                    scores[FunnelQueryType.PURPOSE_RECOMMENDATION] += 0.5
            
            for keyword in series_keywords:
                if keyword in query_lower:
                    scores[FunnelQueryType.SERIES_COMPARISON] += 0.5
            
            # 選擇最高分數的類型
            best_type = max(scores.keys(), key=lambda k: scores[k])
            best_score = scores[best_type]
            
            # 如果分數太低，歸類為混合模糊查詢
            if best_score < 0.5:
                best_type = FunnelQueryType.MIXED_AMBIGUOUS
                best_score = 0.8  # 給混合查詢一個基礎信心度
            
            logging.info(f"查詢分類結果: {best_type.value}, 信心度: {best_score}")
            return best_type, best_score
            
        except Exception as e:
            logging.error(f"查詢分類失敗: {e}")
            return FunnelQueryType.MIXED_AMBIGUOUS, 0.5
    
    def should_trigger_funnel(self, query: str) -> Tuple[bool, FunnelQueryType]:
        """
        判斷是否應該觸發漏斗對話
        
        Args:
            query: 使用者查詢
            
        Returns:
            (是否觸發漏斗, 查詢類型)
        """
        try:
            # 首先檢查是否為明確的具體查詢
            if self._is_specific_query(query):
                logging.info(f"檢測到明確查詢，不觸發漏斗: {query}")
                return False, FunnelQueryType.SPECIFIC_QUERY
            
            query_type, confidence = self.classify_ambiguous_query(query)
            
            # 明確查詢不觸發漏斗
            if query_type == FunnelQueryType.SPECIFIC_QUERY:
                return False, query_type
            
            # 高信心度且非明確查詢的情況下觸發漏斗
            should_trigger = confidence >= 0.5 and query_type != FunnelQueryType.SPECIFIC_QUERY
            
            logging.info(f"漏斗觸發判斷: {should_trigger}, 類型: {query_type.value}, 信心度: {confidence}")
            return should_trigger, query_type
            
        except Exception as e:
            logging.error(f"漏斗觸發判斷失敗: {e}")
            return False, FunnelQueryType.MIXED_AMBIGUOUS
    
    def _is_specific_query(self, query: str) -> bool:
        """
        檢查是否為明確的具體查詢
        
        Args:
            query: 使用者查詢
            
        Returns:
            是否為明確查詢
        """
        # 具體查詢模式
        specific_patterns = [
            r'[A-Z]{2,3}\d{3}.*規格',           # AG958的規格
            r'[A-Z]{2,3}\d{3}.*如何',           # AG958如何
            r'[A-Z]{2,3}\d{3}.*價格',           # AG958價格
            r'列出.*型號',                      # 列出所有型號
            r'列出.*系列',                      # 列出所有系列
            r'所有.*型號',                      # 所有型號
            r'所有.*系列',                      # 所有系列
            r'\d{3}.*系列.*價格',               # 958系列價格
            r'\d{3}.*系列.*規格.*$',            # 958系列規格 (結尾)
            r'^[A-Z]{2,3}\d{3}$',               # 純機型名稱
            r'^[A-Z]{2,3}\d{3}[-:\s][A-Z0-9]+$',  # 完整機型名稱
        ]
        
        for pattern in specific_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logging.info(f"檢測到明確查詢模式: {pattern}")
                return True
        
        # 檢查是否只詢問單一機型或系列的基本資訊
        basic_info_patterns = [
            r'^[A-Z]{2,3}\d{3}.*\?$',           # AG958？
            r'^\d{3}.*系列.*\?$',               # 958系列？
            r'.*規格.*\?$',                     # ...規格？
            r'.*價格.*\?$',                     # ...價格？
        ]
        
        for pattern in basic_info_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                # 但要排除比較和推薦類型的查詢
                if not any(keyword in query.lower() for keyword in ["比較", "推薦", "適合", "哪款", "哪個"]):
                    logging.info(f"檢測到基本資訊查詢模式: {pattern}")
                    return True
        
        return False
    
    def generate_funnel_questions(self, query: str, query_type: FunnelQueryType) -> FunnelQuestion:
        """
        根據查詢類型生成相應的漏斗問題
        
        Args:
            query: 原始查詢
            query_type: 查詢類型
            
        Returns:
            漏斗問題物件
        """
        try:
            # 目前主要使用主分流問題
            question_config = self.funnel_config["questions"]["series_vs_purpose"]
            
            funnel_question = FunnelQuestion(
                question_id=question_config["question_id"],
                question_text=question_config["question_text"],
                options=question_config["options"],
                context={
                    "original_query": query,
                    "detected_type": query_type.value,
                    "generation_time": datetime.now().isoformat()
                }
            )
            
            logging.info(f"生成漏斗問題: {funnel_question.question_id}")
            return funnel_question
            
        except Exception as e:
            logging.error(f"生成漏斗問題失敗: {e}")
            # 返回預設問題
            return self._get_default_funnel_question(query, query_type)
    
    def _get_default_funnel_question(self, query: str, query_type: FunnelQueryType) -> FunnelQuestion:
        """取得預設漏斗問題"""
        return FunnelQuestion(
            question_id="default_funnel",
            question_text="請選擇您的需求類型以獲得更精準的幫助：",
            options=[
                {
                    "option_id": "series_comparison",
                    "label": "🔍 系列比較",
                    "description": "比較特定系列內所有機型的差異",
                    "route": "series_comparison_flow"
                },
                {
                    "option_id": "purpose_recommendation", 
                    "label": "🎯 用途推薦",
                    "description": "根據使用用途推薦最適合的機型",
                    "route": "purpose_recommendation_flow"
                }
            ],
            context={"original_query": query, "detected_type": query_type.value}
        )
    
    def start_funnel_session(self, query: str) -> Tuple[str, FunnelQuestion]:
        """
        開始漏斗對話會話
        
        Args:
            query: 使用者查詢
            
        Returns:
            (會話ID, 漏斗問題)
        """
        try:
            # 分類查詢並生成問題
            query_type, confidence = self.classify_ambiguous_query(query)
            funnel_question = self.generate_funnel_questions(query, query_type)
            
            # 建立會話
            session_id = generate_id()
            session = FunnelSession(
                session_id=session_id,
                original_query=query,
                detected_type=query_type,
                current_question=funnel_question,
                user_responses=[],
                target_flow=None,
                created_at=datetime.now()
            )
            
            self.active_sessions[session_id] = session
            
            logging.info(f"漏斗會話已建立: {session_id}")
            return session_id, funnel_question
            
        except Exception as e:
            logging.error(f"建立漏斗會話失敗: {e}")
            raise
    
    def process_funnel_choice(self, session_id: str, choice_id: str) -> Dict[str, Any]:
        """
        處理使用者的漏斗選擇
        
        Args:
            session_id: 會話ID
            choice_id: 選擇的選項ID
            
        Returns:
            處理結果
        """
        try:
            if session_id not in self.active_sessions:
                return {"error": "會話不存在或已過期"}
            
            session = self.active_sessions[session_id]
            
            # 找到選擇的選項
            chosen_option = None
            for option in session.current_question.options:
                if option["option_id"] == choice_id:
                    chosen_option = option
                    break
            
            if not chosen_option:
                return {"error": "無效的選擇"}
            
            # 記錄使用者回應
            session.user_responses.append({
                "question_id": session.current_question.question_id,
                "choice_id": choice_id,
                "choice_label": chosen_option["label"],
                "timestamp": datetime.now().isoformat()
            })
            
            # 確定目標流程
            target_flow = FunnelFlowType(chosen_option["route"])
            session.target_flow = target_flow
            session.is_completed = True
            
            # 生成結果
            result = {
                "action": "route_to_flow",
                "target_flow": target_flow.value,
                "original_query": session.original_query,
                "user_choice": chosen_option,
                "session_summary": {
                    "detected_type": session.detected_type.value,
                    "chosen_flow": target_flow.value,
                    "total_responses": len(session.user_responses)
                }
            }
            
            logging.info(f"漏斗選擇處理完成: {choice_id} -> {target_flow.value}")
            return result
            
        except Exception as e:
            logging.error(f"處理漏斗選擇失敗: {e}")
            return {"error": f"處理失敗: {str(e)}"}
    
    def route_to_specialized_flow(self, flow_type: FunnelFlowType, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        路由到專業化對話流程
        
        Args:
            flow_type: 流程類型
            context: 上下文資訊
            
        Returns:
            路由結果
        """
        try:
            flow_config = self.funnel_config["flows"].get(flow_type.value, {})
            
            result = {
                "flow_type": flow_type.value,
                "flow_name": flow_config.get("name", "未知流程"),
                "next_steps": flow_config.get("steps", []),
                "context": context,
                "routing_instructions": self._get_routing_instructions(flow_type)
            }
            
            logging.info(f"路由到專業流程: {flow_type.value}")
            return result
            
        except Exception as e:
            logging.error(f"流程路由失敗: {e}")
            return {"error": f"路由失敗: {str(e)}"}
    
    def _get_routing_instructions(self, flow_type: FunnelFlowType) -> Dict[str, Any]:
        """取得流程路由指令"""
        instructions = {
            FunnelFlowType.SERIES_COMPARISON_FLOW: {
                "handler": "execute_series_comparison",
                "skip_general_multichat": True,
                "direct_comparison": True,
                "focus": "series_internal_comparison"
            },
            FunnelFlowType.PURPOSE_RECOMMENDATION_FLOW: {
                "handler": "execute_purpose_recommendation", 
                "use_purpose_specific_questions": True,
                "skip_general_multichat": False,
                "focus": "purpose_based_filtering"
            }
        }
        
        return instructions.get(flow_type, {})
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """清理過期的會話"""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                age = current_time - session.created_at
                if age.total_seconds() > max_age_hours * 3600:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
            
            if expired_sessions:
                logging.info(f"清理了 {len(expired_sessions)} 個過期會話")
                
        except Exception as e:
            logging.error(f"清理過期會話失敗: {e}")
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """取得會話資訊"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            return {
                "session_id": session_id,
                "original_query": session.original_query,
                "detected_type": session.detected_type.value,
                "is_completed": session.is_completed,
                "target_flow": session.target_flow.value if session.target_flow else None,
                "responses_count": len(session.user_responses),
                "created_at": session.created_at.isoformat()
            }
        return None