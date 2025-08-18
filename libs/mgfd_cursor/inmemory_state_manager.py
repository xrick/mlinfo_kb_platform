#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD In-Memory 狀態管理器（Redis 替代方案）
提供與 RedisStateManager 相同的介面以便無需 Redis 也可運行。
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime


class InMemoryStateManager:
    """簡單的記憶體狀態管理器，僅供開發與本機測試使用。"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 會話基礎資料，不含槽位/歷史
        self._sessions: Dict[str, Dict[str, Any]] = {}
        # 槽位
        self._slots: Dict[str, Dict[str, Any]] = {}
        # 歷史記錄
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        # 推薦記錄
        self._recommendations: Dict[str, List[Dict[str, Any]]] = {}

    # 與 RedisStateManager 介面對齊
    def load_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self._sessions.get(session_id)
        if not session:
            return None
        state = {
            "session_id": session_id,
            "current_stage": session.get("current_stage", "awareness"),
            "created_at": session.get("created_at"),
            "last_updated": session.get("last_updated"),
            "user_preferences": session.get("user_preferences", {}),
            "filled_slots": self._slots.get(session_id, {}),
            "chat_history": self._history.get(session_id, []),
            "recommendations": self._recommendations.get(session_id, []),
        }
        return state

    def save_session_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        try:
            now = datetime.now().isoformat()
            session_entry = self._sessions.get(session_id, {})
            session_entry.update({
                "session_id": session_id,
                "current_stage": state.get("current_stage", "awareness"),
                "created_at": state.get("created_at") or now,
                "last_updated": now,
                "user_preferences": state.get("user_preferences", {}),
            })
            self._sessions[session_id] = session_entry
            # 槽位
            self._slots[session_id] = state.get("filled_slots", {})
            # 歷史
            self._history[session_id] = state.get("chat_history", [])
            # 推薦
            self._recommendations[session_id] = state.get("recommendations", [])
            return True
        except Exception as e:
            self.logger.error(f"InMemory: 保存會話狀態失敗: {e}")
            return False

    def update_slots(self, session_id: str, slots: Dict[str, Any]) -> bool:
        try:
            current = self._slots.get(session_id, {})
            current.update(slots)
            self._slots[session_id] = current
            return True
        except Exception as e:
            self.logger.error(f"InMemory: 更新槽位失敗: {e}")
            return False

    def get_slots(self, session_id: str) -> Dict[str, Any]:
        return self._slots.get(session_id, {}).copy()

    def add_message_to_history(self, session_id: str, message: Dict[str, Any]) -> bool:
        try:
            message = dict(message)
            message.setdefault("timestamp", datetime.now().isoformat())
            self._history.setdefault(session_id, []).append(message)
            return True
        except Exception as e:
            self.logger.error(f"InMemory: 添加歷史失敗: {e}")
            return False

    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        all_history = self._history.get(session_id, [])
        return all_history[-limit:]

    def add_recommendation(self, session_id: str, recommendation: Dict[str, Any]) -> bool:
        try:
            self._recommendations.setdefault(session_id, []).append(dict(recommendation))
            return True
        except Exception as e:
            self.logger.error(f"InMemory: 添加推薦失敗: {e}")
            return False

    def get_recommendations(self, session_id: str) -> List[Dict[str, Any]]:
        return self._recommendations.get(session_id, []).copy()

    def delete_session(self, session_id: str) -> bool:
        try:
            self._sessions.pop(session_id, None)
            self._slots.pop(session_id, None)
            self._history.pop(session_id, None)
            self._recommendations.pop(session_id, None)
            return True
        except Exception as e:
            self.logger.error(f"InMemory: 刪除會話失敗: {e}")
            return False

    def cleanup_expired_sessions(self) -> int:
        # In-memory 版本不做過期清理；返回0
        return 0



