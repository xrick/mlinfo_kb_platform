#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多輪對話系統常數定義
"""

import re
from typing import Dict, List


class ScenarioKeywords:
    """場景識別關鍵詞"""
    
    BUSINESS = [
        "商務", "辦公", "工作", "企業", "商用", "業務", "職場", "公司", 
        "文書處理", "文書", "處理", "office", "business", "工作用", "上班", 
        "會議", "報告", "簡報", "excel", "word", "ppt", "專業工作"
    ]
    
    GAMING = [
        "遊戲", "gaming", "電競", "遊戲用", "玩遊戲", "game", "fps", "moba", 
        "顯卡", "gpu", "高畫質", "高效能遊戲"
    ]
    
    CREATION = [
        "創作", "設計", "繪圖", "影片編輯", "剪輯", "photoshop", "3d建模", 
        "渲染", "creator", "design", "創意", "美工"
    ]
    
    STUDY = [
        "學習", "學生", "讀書", "課業", "上課", "study", "student", "教育", 
        "大學生", "高中生", "研究", "論文"
    ]


class QueryPatterns:
    """查詢模式正則表達式"""
    
    # 具體機型模式
    SPECIFIC_MODEL_PATTERNS = [
        r'[A-Z]{2,3}\d{3}',  # 如 AG958, APX958, NB819 等
        r'i[3579]-\d+',      # 如 i7-1234 等具體CPU型號
        r'Ryzen\s+[579]\s+\d+',  # 如 Ryzen 7 5800H 等具體CPU型號
    ]
    
    # 機型名稱提及模式
    MODEL_MENTION_PATTERNS = [
        r'[A-Z]{1,3}\d{3}[A-Z]*[-\s]*[A-Z]*\d*',  # 完整機型名稱
    ]
    
    # 明確系列比較模式
    DEFINITIVE_SERIES_COMPARISON_PATTERNS = [
        r'比較\s*(819|839|958)\s*系列',      # 比較819系列
        r'(819|839|958)\s*系列.*比較.*規格',  # 819系列比較規格
        r'(819|839|958)\s*系列.*比較.*性能',  # 819系列比較性能
        r'(819|839|958)\s*系列.*比較.*差異',  # 819系列比較差異
        r'(819|839|958)\s*系列.*比較.*不同',  # 819系列比較不同
        r'(819|839|958)\s*系列.*有什麼不同',  # 819系列有什麼不同
        r'(819|839|958)\s*系列.*差異',       # 819系列差異
        r'(819|839|958)\s*系列.*顯示.*比較', # 819系列顯示比較
        r'(819|839|958)\s*系列.*螢幕.*比較', # 819系列螢幕比較
    ]
    
    # 模糊詢問模式
    AMBIGUOUS_QUESTION_PATTERNS = [
        r'有哪些.*比較',     # 有哪些...比較
        r'可以.*比較',       # 可以...比較
        r'能夠.*比較',       # 能夠...比較
        r'比較.*哪些',       # 比較...哪些
    ]


class ScenarioDetectionKeywords:
    """使用場景檢測關鍵字"""
    
    SCENARIO_KEYWORDS = ["適合", "用於", "專門", "主要", "需要", "想要", "希望", "打算"]
    
    COMPARISON_KEYWORDS = ["比較", "差別", "不同", "差異"]
    
    AMBIGUOUS_KEYWORDS = ["哪些", "可以", "能夠", "有什麼"]


class SystemDefaults:
    """系統預設值"""
    
    DEFAULT_SESSION_HOURS = 24
    DEFAULT_CONFIDENCE = 1.0
    MIN_MODEL_NAME_LENGTH = 3
    SERIES_NUMBER_PATTERN = r'^\d{3}$'
    SERIES_NUMBERS = [819, 839, 958]


class EmojiPatterns:
    """表情符號過濾模式"""
    
    EMOJI_TO_REMOVE = [
        '🎮 ', '💼 ', '🎨 ', '📚 ', '🚀 ', '⚖️ ', '🔋 ', '🤷 ', 
        '💻 ', '❓ ', '🧠 ', '💰 ', '🔧 ', '📦 ', '📁 ', '💾 ', 
        '⚡ ', '📺 ', '🖥️ ', '💻 ', '🪶 ', '🎒 ', '🏠 ', '💎 ', 
        '💳 ', '👑 ', '🤝 '
    ]