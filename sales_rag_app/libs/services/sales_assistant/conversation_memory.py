#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
對話記憶管理模組

實現基於 RAG 多輪對話設計指南的對話記憶功能，
支援歷史感知檢索和上下文保持。
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """單輪對話記錄"""
    turn_id: str
    timestamp: datetime
    user_query: str
    system_response: str
    query_intent: str
    retrieval_confidence: float
    response_strategy: str
    matched_models: List[str] = field(default_factory=list)
    satisfaction_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationSession:
    """對話會話記錄"""
    session_id: str
    start_time: datetime
    last_activity: datetime
    turns: List[ConversationTurn] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    context_summary: str = ""
    
    def add_turn(self, turn: ConversationTurn):
        """添加對話輪次"""
        self.turns.append(turn)
        self.last_activity = datetime.now()
        
    def get_recent_turns(self, limit: int = 5) -> List[ConversationTurn]:
        """獲取最近的對話輪次"""
        return self.turns[-limit:] if self.turns else []
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """檢查會話是否已過期"""
        if not self.last_activity:
            return True
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)


class ConversationMemoryManager:
    """對話記憶管理器
    
    基於 RAG 多輪對話設計指南實現：
    1. History-Aware Retrieval - 利用對話歷史改善檢索
    2. Context Preservation - 保持對話上下文
    3. User Preference Learning - 學習用戶偏好
    """
    
    def __init__(self, max_sessions: int = 100, session_timeout: int = 30):
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
        self.sessions: Dict[str, ConversationSession] = {}
        self.session_queue = deque(maxlen=max_sessions)
        
    def create_session(self, session_id: str) -> ConversationSession:
        """創建新的對話會話"""
        if session_id in self.sessions:
            return self.sessions[session_id]
            
        session = ConversationSession(
            session_id=session_id,
            start_time=datetime.now(),
            last_activity=datetime.now()
        )
        
        # 如果會話數量超過限制，移除最舊的會話
        if len(self.sessions) >= self.max_sessions:
            self._cleanup_expired_sessions()
            
        self.sessions[session_id] = session
        self.session_queue.append(session_id)
        
        logger.info(f"Created new conversation session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """獲取對話會話"""
        session = self.sessions.get(session_id)
        if session and session.is_expired(self.session_timeout):
            self.remove_session(session_id)
            return None
        return session
    
    def remove_session(self, session_id: str):
        """移除對話會話"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.session_queue:
                # 從 deque 中移除比較複雜，重建隊列
                self.session_queue = deque(
                    [sid for sid in self.session_queue if sid != session_id],
                    maxlen=self.max_sessions
                )
            logger.info(f"Removed conversation session: {session_id}")
    
    def add_conversation_turn(
        self,
        session_id: str,
        user_query: str,
        system_response: str,
        query_intent: str,
        retrieval_confidence: float,
        response_strategy: str,
        matched_models: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> ConversationTurn:
        """添加對話輪次"""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        
        turn = ConversationTurn(
            turn_id=f"{session_id}_{len(session.turns) + 1}",
            timestamp=datetime.now(),
            user_query=user_query,
            system_response=system_response,
            query_intent=query_intent,
            retrieval_confidence=retrieval_confidence,
            response_strategy=response_strategy,
            matched_models=matched_models or [],
            metadata=metadata or {}
        )
        
        session.add_turn(turn)
        self._update_user_preferences(session, turn)
        
        logger.debug(f"Added conversation turn to session {session_id}")
        return turn
    
    def get_conversation_context(
        self,
        session_id: str,
        max_turns: int = 5,
        include_system_responses: bool = True
    ) -> Dict[str, Any]:
        """獲取對話上下文
        
        根據 RAG 指南，生成獨立的檢索查詢所需的上下文
        """
        session = self.get_session(session_id)
        if not session:
            return {"has_context": False, "turns": [], "summary": ""}
        
        recent_turns = session.get_recent_turns(max_turns)
        
        context = {
            "has_context": len(recent_turns) > 0,
            "session_id": session_id,
            "turns": [],
            "summary": session.context_summary,
            "user_preferences": session.user_preferences.copy(),
            "conversation_flow": self._analyze_conversation_flow(recent_turns)
        }
        
        for turn in recent_turns:
            turn_data = {
                "user_query": turn.user_query,
                "query_intent": turn.query_intent,
                "response_strategy": turn.response_strategy,
                "matched_models": turn.matched_models,
                "timestamp": turn.timestamp.isoformat()
            }
            
            if include_system_responses:
                turn_data["system_response"] = turn.system_response[:200] + "..." if len(turn.system_response) > 200 else turn.system_response
            
            context["turns"].append(turn_data)
        
        return context
    
    def create_contextualized_query(
        self,
        session_id: str,
        current_query: str
    ) -> str:
        """創建基於上下文的獨立查詢
        
        實現 RAG 指南中的 "History-Aware Retriever" 概念
        """
        context = self.get_conversation_context(session_id, max_turns=3, include_system_responses=False)
        
        if not context["has_context"]:
            return current_query
        
        # 構建上下文感知的查詢
        recent_intents = [turn["query_intent"] for turn in context["turns"]]
        recent_models = []
        for turn in context["turns"]:
            recent_models.extend(turn["matched_models"])
        
        # 去重並保持順序
        recent_models = list(dict.fromkeys(recent_models))
        
        contextualized_parts = [current_query]
        
        # 添加相關的歷史意圖上下文
        if recent_intents:
            dominant_intent = max(set(recent_intents), key=recent_intents.count)
            if dominant_intent != "general_comparison":
                contextualized_parts.append(f"延續 {dominant_intent} 相關討論")
        
        # 添加之前討論過的機型上下文
        if recent_models:
            models_context = ", ".join(recent_models[:3])  # 最多3個型號
            contextualized_parts.append(f"考慮之前討論的型號: {models_context}")
        
        # 添加用戶偏好上下文
        preferences = context["user_preferences"]
        if preferences:
            pref_items = []
            for key, value in preferences.items():
                if key in ["preferred_use_case", "budget_preference", "brand_preference"]:
                    pref_items.append(f"{key}: {value}")
            
            if pref_items:
                contextualized_parts.append(f"用戶偏好: {'; '.join(pref_items[:2])}")
        
        contextualized_query = " | ".join(contextualized_parts)
        
        logger.debug(f"Contextualized query for session {session_id}: {contextualized_query}")
        return contextualized_query
    
    def _analyze_conversation_flow(self, turns: List[ConversationTurn]) -> Dict[str, Any]:
        """分析對話流程模式"""
        if not turns:
            return {"pattern": "new_conversation", "focus_area": None}
        
        intents = [turn.query_intent for turn in turns]
        strategies = [turn.response_strategy for turn in turns]
        
        # 檢測對話模式
        if len(set(intents)) == 1:
            pattern = "focused_inquiry"  # 專注於單一主題
        elif len(turns) >= 3 and "comparison" in " ".join(strategies):
            pattern = "comparative_analysis"  # 比較分析模式
        elif any("value" in strategy for strategy in strategies):
            pattern = "value_seeking"  # 尋求性價比
        else:
            pattern = "exploratory"  # 探索性對話
        
        # 確定焦點領域
        focus_area = max(set(intents), key=intents.count) if intents else None
        
        return {
            "pattern": pattern,
            "focus_area": focus_area,
            "turn_count": len(turns),
            "consistency_score": len(set(intents)) / len(intents) if intents else 0
        }
    
    def _update_user_preferences(self, session: ConversationSession, turn: ConversationTurn):
        """根據對話輪次更新用戶偏好"""
        # 學習用戶的使用場景偏好
        intent_mapping = {
            "gaming_performance": "gaming",
            "business_productivity": "business", 
            "student_value": "student",
            "battery_performance": "battery_focused"
        }
        
        if turn.query_intent in intent_mapping:
            use_case = intent_mapping[turn.query_intent]
            session.user_preferences["preferred_use_case"] = use_case
        
        # 學習預算偏好
        if "value" in turn.response_strategy:
            session.user_preferences["budget_preference"] = "value_conscious"
        elif "gaming" in turn.response_strategy:
            session.user_preferences["budget_preference"] = "performance_focused"
        
        # 學習品牌偏好（從匹配的型號中推斷）
        if turn.matched_models:
            model_series = []
            for model in turn.matched_models:
                if "958" in model:
                    model_series.append("958_series")
                elif "819" in model:
                    model_series.append("819_series")
                elif "839" in model:
                    model_series.append("839_series")
            
            if model_series:
                preferred_series = max(set(model_series), key=model_series.count)
                session.user_preferences["preferred_series"] = preferred_series
        
        # 更新上下文摘要
        self._update_context_summary(session)
    
    def _update_context_summary(self, session: ConversationSession):
        """更新會話的上下文摘要"""
        if not session.turns:
            return
        
        recent_turns = session.get_recent_turns(3)
        intents = [turn.query_intent for turn in recent_turns]
        
        if len(set(intents)) == 1:
            summary = f"用戶專注於 {intents[0]} 相關查詢"
        else:
            summary = f"用戶在 {', '.join(set(intents))} 之間進行比較"
        
        if session.user_preferences:
            prefs = []
            for key, value in session.user_preferences.items():
                prefs.append(f"{key}: {value}")
            summary += f" | 偏好: {', '.join(prefs[:2])}"
        
        session.context_summary = summary
    
    def _cleanup_expired_sessions(self):
        """清理過期的會話"""
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(self.session_timeout)
        ]
        
        for session_id in expired_sessions:
            self.remove_session(session_id)
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """獲取會話統計信息"""
        active_sessions = len(self.sessions)
        total_turns = sum(len(session.turns) for session in self.sessions.values())
        
        return {
            "active_sessions": active_sessions,
            "total_conversation_turns": total_turns,
            "average_turns_per_session": total_turns / active_sessions if active_sessions else 0,
            "memory_usage": f"{active_sessions}/{self.max_sessions} sessions"
        }