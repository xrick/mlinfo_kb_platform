#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 數據模型定義
"""

from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class DialogueStage(Enum):
    """對話階段枚舉"""
    AWARENESS = "awareness"
    INTEREST = "interest" 
    EVALUATION = "evaluation"
    ENGAGEMENT = "engagement"
    ACTION = "action"

class ActionType(Enum):
    """行動類型枚舉"""
    ELICIT_INFORMATION = "elicit_information"
    RECOMMEND_PRODUCTS = "recommend_products"
    RECOMMEND_POPULAR_PRODUCTS = "recommend_popular_products"
    HANDLE_INTERRUPTION = "handle_interruption"
    CLARIFY_INPUT = "clarify_input"

class NotebookDialogueState(TypedDict):
    """筆記型電腦銷售對話狀態"""
    chat_history: List[Dict[str, Any]]
    filled_slots: Dict[str, Any]
    recommendations: List[str]
    user_preferences: Dict[str, Any]
    current_stage: str
    session_id: str
    created_at: datetime
    last_updated: datetime

@dataclass
class SlotSchema:
    """槽位架構定義"""
    name: str
    data_type: str
    options: List[str]
    required: bool
    example_question: str
    description: str

@dataclass
class DialogueAction:
    """對話行動定義"""
    action_type: ActionType
    target_slot: Optional[str] = None
    message: Optional[str] = None
    confidence: float = 1.0
    extracted_slots: Optional[Dict[str, Any]] = None
    special_case: Optional[Dict[str, Any]] = None

# 筆記型電腦產品槽位架構
NOTEBOOK_SLOT_SCHEMA = {
    "usage_purpose": SlotSchema(
        name="usage_purpose",
        data_type="list",
        options=["gaming", "business", "student", "creative", "general"],
        required=True,
        example_question="您主要會用這台筆電做什麼？遊戲、工作、學習還是其他用途？",
        description="使用目的"
    ),
    "budget_range": SlotSchema(
        name="budget_range",
        data_type="string",
        options=["budget", "mid_range", "premium", "luxury"],
        required=True,
        example_question="您的預算大概在哪個範圍？",
        description="預算範圍"
    ),
    "performance_priority": SlotSchema(
        name="performance_priority",
        data_type="list",
        options=["cpu", "gpu", "ram", "storage", "battery"],
        required=False,
        example_question="您最重視哪個方面的性能？",
        description="性能優先級"
    ),
    "portability_need": SlotSchema(
        name="portability_need",
        data_type="string",
        options=["ultra_portable", "balanced", "desktop_replacement"],
        required=False,
        example_question="您需要經常攜帶嗎？",
        description="便攜性需求"
    ),
    "brand_preference": SlotSchema(
        name="brand_preference",
        data_type="list",
        options=["asus", "acer", "lenovo", "hp", "dell", "apple"],
        required=False,
        example_question="您有品牌偏好吗？",
        description="品牌偏好"
    )
}



