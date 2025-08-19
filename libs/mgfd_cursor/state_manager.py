#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD State Manager
Merges state persistence (Redis) and state transition logic (State Machine).
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis
import numpy as np

from .models import NotebookDialogueState, ActionType
from .dialogue_manager import DialogueManager as MGFDDialogueManager

class StateManager:
    """
    Manages the dialogue state, including persistence in Redis and handling state transitions.
    """

    def __init__(self, redis_client: redis.Redis, dialogue_manager: MGFDDialogueManager, session_timeout: int = 3600):
        """
        Initializes the StateManager.

        Args:
            redis_client: The Redis client for state persistence.
            dialogue_manager: The dialogue manager for business logic.
            session_timeout: Session timeout in seconds.
        """
        self.redis_client = redis_client
        self.dialogue_manager = dialogue_manager
        self.session_timeout = session_timeout
        self.logger = logging.getLogger(__name__)

        # Redis key prefixes
        self.SESSION_PREFIX = "mgfd:session:"
        self.SLOTS_PREFIX = "mgfd:slots:"
        self.HISTORY_PREFIX = "mgfd:history:"
        self.RECOMMENDATIONS_PREFIX = "mgfd:recommendations:"

    # --- Methods from MGFDStateMachine ---

    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """
        Processes user input by loading state, routing to an action, executing it, and saving the new state.
        """
        try:
            self.logger.info(f"Processing user input - session_id: {session_id}, input: '{user_input[:100]}...'")
            
            # Load session state using its own methods
            state = self.load_session_state(session_id)
            if not state:
                self.logger.warning(f"Session not found: {session_id}")
                # Attempt to create a new session if none exists
                state = self.dialogue_manager.get_session(session_id)
                if not state:
                    return {"error": "Session does not exist and could not be created.", "session_id": session_id}

        except Exception as e:
            self.logger.error(f"Failed to load session state: {e}")
            return {"error": f"System error: {str(e)}", "session_id": session_id}

        try:
            # Add user message to history
            user_message = {
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            }
            state["chat_history"].append(user_message)

            # Think step: Decide the next action
            self.logger.debug("Routing action...")
            action = self.dialogue_manager.route_action(state, user_input)
            self.logger.info(f"Routed to action: {action.action_type}, target_slot: {action.target_slot}")

            # Act step: Execute the action
            if action.action_type == ActionType.ELICIT_INFORMATION:
                return self._handle_elicitation(state, action)
            elif action.action_type == ActionType.RECOMMEND_PRODUCTS:
                return self._handle_recommendation(state, action)
            elif action.action_type == ActionType.HANDLE_INTERRUPTION:
                return self._handle_interruption(state, action)
            else:
                self.logger.warning(f"Unknown action type: {action.action_type}")
                return self._handle_unknown_action(state, action)
        except Exception as e:
            self.logger.error(f"Error processing user input: {e}", exc_info=True)
            return {"error": f"Processing error: {str(e)}", "session_id": session_id}

    def _handle_elicitation(self, state: NotebookDialogueState, action) -> Dict[str, Any]:
        """Handles information elicitation."""
        extracted_slots = {}
        if hasattr(action, 'extracted_slots') and action.extracted_slots:
            extracted_slots = action.extracted_slots
        else:
            extracted_slots = self.dialogue_manager.extract_slots_from_input(
                state["chat_history"][-1]["content"], state
            )

        if extracted_slots:
            state["filled_slots"].update(extracted_slots)
            self.logger.info(f"Slots updated: {state['filled_slots']}")

        confirmation_message = self._generate_confirmation_message(extracted_slots, state)
        response_content = confirmation_message or action.message

        response_message = {
            "role": "assistant",
            "content": response_content,
            "action_type": "elicitation",
            "target_slot": action.target_slot,
            "extracted_slots": extracted_slots
        }
        state["chat_history"].append(response_message)

        # Save state using its own method
        self.save_session_state(state["session_id"], state)

        return {
            "session_id": state["session_id"],
            "response": response_content,
            "action_type": "elicitation",
            "target_slot": action.target_slot,
            "extracted_slots": extracted_slots,
            "filled_slots": state["filled_slots"],
            "current_stage": state["current_stage"]
        }

    def _generate_confirmation_message(self, extracted_slots: Dict[str, Any], state: NotebookDialogueState) -> str:
        """Generates a confirmation message for extracted slots."""
        if not extracted_slots:
            return ""
        
        confirmations = []
        purpose_map = {"gaming": "遊戲", "business": "商務工作", "student": "學習", "creative": "創作設計", "general": "一般使用"}
        budget_map = {"budget": "平價", "mid_range": "中價位", "premium": "高價位", "luxury": "頂級"}

        if "usage_purpose" in extracted_slots:
            purpose = extracted_slots["usage_purpose"]
            confirmations.append(f"使用目的：{purpose_map.get(purpose, purpose)}")
        
        if "performance_features" in extracted_slots and extracted_slots["performance_features"]:
            feature_map = {"fast": "快速開關機", "portable": "輕便攜帶", "performance": "高效能"}
            feature_names = [feature_map.get(f, f) for f in extracted_slots["performance_features"]]
            confirmations.append(f"性能需求：{', '.join(feature_names)}")

        if "budget_range" in extracted_slots:
            budget = extracted_slots["budget_range"]
            confirmations.append(f"預算範圍：{budget_map.get(budget, budget)}")
        
        return f"好的，我了解了：{', '.join(confirmations)}。現在讓我為您推薦最適合的筆電。" if confirmations else ""

    def _handle_recommendation(self, state: NotebookDialogueState, action) -> Dict[str, Any]:
        """Handles product recommendation."""
        if hasattr(action, 'extracted_slots') and action.extracted_slots:
            state["filled_slots"].update(action.extracted_slots)

        recommendations = self.dialogue_manager.generate_recommendations(state)
        recommendation_message = self.dialogue_manager.format_recommendation_message(recommendations)
        
        state["recommendations"] = [r["id"] for r in recommendations]
        state["current_stage"] = "engagement"
        
        response_message = {
            "role": "assistant",
            "content": recommendation_message,
            "action_type": "recommendation",
            "recommendations": recommendations
        }
        state["chat_history"].append(response_message)

        # Save state using its own method
        self.save_session_state(state["session_id"], state)

        return {
            "session_id": state["session_id"],
            "response": recommendation_message,
            "action_type": "recommendation",
            "recommendations": recommendations,
            "filled_slots": state["filled_slots"],
            "current_stage": state["current_stage"]
        }

    def _handle_interruption(self, state: NotebookDialogueState, action) -> Dict[str, Any]:
        """Handles an interruption."""
        state["filled_slots"] = {}
        state["recommendations"] = []
        state["current_stage"] = "awareness"
        
        response_message = {"role": "assistant", "content": action.message, "action_type": "interruption"}
        state["chat_history"].append(response_message)

        # Save state using its own method
        self.save_session_state(state["session_id"], state)

        return {
            "session_id": state["session_id"],
            "response": action.message,
            "action_type": "interruption",
            "filled_slots": state["filled_slots"],
            "current_stage": state["current_stage"]
        }

    def _handle_unknown_action(self, state: NotebookDialogueState, action) -> Dict[str, Any]:
        """Handles an unknown action."""
        error_message = "抱歉，我無法理解您的需求。請重新描述您想要的筆電。"
        response_message = {"role": "assistant", "content": error_message, "action_type": "error"}
        state["chat_history"].append(response_message)
        
        # Note: We might not save the state here to avoid cluttering history with errors.
        # For now, we'll return it without saving.
        return {
            "session_id": state["session_id"],
            "response": error_message,
            "action_type": "error",
            "filled_slots": state["filled_slots"],
            "current_stage": state["current_stage"]
        }

    # --- Methods from RedisStateManager ---

    def _convert_numpy_types(self, obj: Any) -> Any:
        """Recursively converts numpy types to native Python types for JSON serialization."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        if isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, dict):
            return {k: self._convert_numpy_types(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._convert_numpy_types(i) for i in obj]
        return obj

    def load_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Loads a session state from Redis."""
        try:
            session_key = f"{self.SESSION_PREFIX}{session_id}"
            session_data = self.redis_client.get(session_key)
            if not session_data:
                return None

            # Responses are already strings due to decode_responses=True
            session_state = json.loads(session_data)
            
            # Load other parts of the state
            slots_key = f"{self.SLOTS_PREFIX}{session_id}"
            slots_data = self.redis_client.get(slots_key)
            session_state["filled_slots"] = json.loads(slots_data) if slots_data else {}

            history_key = f"{self.HISTORY_PREFIX}{session_id}"
            history_data = self.redis_client.lrange(history_key, 0, -1)
            session_state["chat_history"] = [json.loads(m) for m in history_data]

            recs_key = f"{self.RECOMMENDATIONS_PREFIX}{session_id}"
            recs_data = self.redis_client.get(recs_key)
            session_state["recommendations"] = json.loads(recs_data) if recs_data else []
            
            self.logger.info(f"Loaded session state: {session_id}")
            return session_state
        except Exception as e:
            self.logger.error(f"Failed to load session state for {session_id}: {e}")
            return None

    def save_session_state(self, session_id: str, state: Dict[str, Any]) -> bool:
        """Saves a session state to Redis."""
        try:
            state = self._convert_numpy_types(state)
            state["last_updated"] = datetime.now().isoformat()

            # Pipeline for atomic operations
            pipe = self.redis_client.pipeline()

            # Basic session info
            session_key = f"{self.SESSION_PREFIX}{session_id}"
            session_data = {k: v for k, v in state.items() if k not in ["filled_slots", "chat_history", "recommendations"]}
            
            # Helper to serialize datetime
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

            pipe.setex(session_key, self.session_timeout, json.dumps(session_data, ensure_ascii=False, default=json_serializer))

            # Slots
            slots_key = f"{self.SLOTS_PREFIX}{session_id}"
            pipe.setex(slots_key, self.session_timeout, json.dumps(state.get("filled_slots", {}), ensure_ascii=False))

            # History
            history_key = f"{self.HISTORY_PREFIX}{session_id}"
            chat_history = state.get("chat_history", [])
            pipe.delete(history_key)
            if chat_history:
                pipe.rpush(history_key, *[json.dumps(self._convert_numpy_types(m), ensure_ascii=False) for m in chat_history])
                pipe.expire(history_key, self.session_timeout)

            # Recommendations
            recs_key = f"{self.RECOMMENDATIONS_PREFIX}{session_id}"
            pipe.setex(recs_key, self.session_timeout, json.dumps(state.get("recommendations", []), ensure_ascii=False))

            pipe.execute()
            self.logger.info(f"Saved session state: {session_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save session state for {session_id}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """Deletes a session from Redis."""
        try:
            keys_to_delete = [
                f"{self.SESSION_PREFIX}{session_id}",
                f"{self.SLOTS_PREFIX}{session_id}",
                f"{self.HISTORY_PREFIX}{session_id}",
                f"{self.RECOMMENDATIONS_PREFIX}{session_id}"
            ]
            self.redis_client.delete(*keys_to_delete)
            self.logger.info(f"Deleted session: {session_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete session {session_id}: {e}")
            return False

def create_state_manager() -> StateManager:
    """
    Factory function to create a StateManager instance with its dependencies.
    """
    # In a real application, Redis connection details would come from config
    redis_client = redis.Redis(decode_responses=True)
    dialogue_manager = MGFDDialogueManager()
    return StateManager(redis_client, dialogue_manager)
