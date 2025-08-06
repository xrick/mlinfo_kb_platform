#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多輪對話系統資料模型定義
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

class FeatureType(Enum):
    """NB特點類型"""
    CPU = "cpu"
    GPU = "gpu" 
    MEMORY = "memory"
    STORAGE = "storage"
    SIZE = "size"
    WEIGHT = "weight"
    PRICE = "price"

class ResponseType(Enum):
    """回應類型"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    RANGE_INPUT = "range_input"
    TEXT_INPUT = "text_input"

@dataclass
class NBFeature:
    """NB特點定義"""
    feature_id: str
    feature_type: FeatureType
    name: str
    description: str
    question_template: str
    response_type: ResponseType
    options: List[Dict[str, Any]] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    priority: int = 1
    required: bool = True

@dataclass 
class FeatureOption:
    """特點選項"""
    option_id: str
    label: str
    description: str
    keywords: List[str] = field(default_factory=list)
    db_filter: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureResponse:
    """使用者對特點的回應"""
    response_id: str
    feature_id: str
    feature_type: FeatureType
    user_choice: str
    user_input: Optional[str] = None
    confidence: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ChatChain:
    """對話鍊定義"""
    chain_id: str
    features_order: List[str]
    strategy: str = "random"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "active"
    
@dataclass
class ConversationSession:
    """對話會話"""
    session_id: str
    user_query: str
    chat_chain: ChatChain
    current_step: int = 0
    total_steps: int = 0
    collected_responses: List[FeatureResponse] = field(default_factory=list)
    session_state: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_complete: bool = False

@dataclass
class ChatQuestion:
    """對話問題"""
    question_id: str
    session_id: str
    feature: NBFeature
    step: int
    question_text: str
    options: List[FeatureOption]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

def generate_id() -> str:
    """產生唯一ID"""
    return str(uuid.uuid4())