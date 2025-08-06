#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多輪對話導引系統 (MultiChat)
用於導引使用者從發散式詢問逐步聚焦到明確的NB機型需求
"""

from .models import (
    NBFeature,
    ChatChain, 
    ConversationSession,
    FeatureResponse
)
from .gen_chat import ChatGenerator
from .multichat_manager import MultichatManager
from .templates import ChatTemplateManager

__version__ = "1.0.0"
__all__ = [
    "NBFeature", 
    "ChatChain",
    "ConversationSession",
    "FeatureResponse",
    "ChatGenerator",
    "MultichatManager",
    "ChatTemplateManager"
]