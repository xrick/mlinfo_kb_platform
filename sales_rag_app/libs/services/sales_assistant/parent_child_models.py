#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parent-Child Data Models for Laptop Specification Chunking

This module defines the core data structures for organizing laptop specifications
using a parent-child chunking strategy, where:
- Parent: Complete laptop model with full specifications  
- Child: Topic-specific chunks (battery, gaming, business, etc.)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class TopicCategory(Enum):
    """Enumeration of topic categories for child chunks"""
    BATTERY_PERFORMANCE = "battery_performance"
    GAMING_PERFORMANCE = "gaming_performance" 
    BUSINESS_PRODUCTIVITY = "business_productivity"
    STUDENT_VALUE = "student_value"
    DISPLAY_QUALITY = "display_quality"
    TECHNICAL_SPECS = "technical_specs"
    PORTABILITY = "portability"
    CONNECTIVITY = "connectivity"
    SECURITY = "security"
    GENERAL_INFO = "general_info"


@dataclass
class ParentDocument:
    """
    Represents a complete laptop model with full specifications.
    This is the "parent" document that contains comprehensive information
    and will be returned to users for complete context.
    """
    doc_id: str  # Unique identifier (e.g., "AG958", "AB819-S: FP6")
    model_name: str  # Human-readable model name
    full_specs: Dict[str, Any]  # Complete specification dictionary
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_spec_value(self, spec_field: str) -> Any:
        """Get value of a specific specification field"""
        return self.full_specs.get(spec_field, "")
    
    def to_text_summary(self) -> str:
        """Generate human-readable text summary of the laptop"""
        summary_parts = [f"型號：{self.model_name}"]
        
        # Key specifications for summary
        key_specs = {
            'cpu': 'CPU處理器',
            'gpu': '顯示卡', 
            'memory': '記憶體',
            'storage': '儲存空間',
            'battery': '電池',
            'lcd': '螢幕',
            'modeltype': '系列類型'
        }
        
        for field, label in key_specs.items():
            value = self.get_spec_value(field)
            if value and str(value).strip():
                summary_parts.append(f"{label}：{value}")
        
        return "，".join(summary_parts)


@dataclass  
class ChildChunk:
    """
    Represents a topic-specific chunk derived from a ParentDocument.
    This is the "child" that will be used for semantic retrieval and matching.
    """
    chunk_id: str  # Unique identifier for this chunk
    parent_doc_id: str  # Reference to parent document
    topic_category: TopicCategory  # Topic this chunk represents
    content: str  # Text content of this chunk
    spec_fields: List[str] = field(default_factory=list)  # Spec fields included
    keywords: List[str] = field(default_factory=list)  # Relevant keywords
    confidence: float = 1.0  # Confidence score for this chunk
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def matches_query_keywords(self, query_keywords: List[str]) -> float:
        """
        Calculate how well this chunk matches given query keywords
        Returns confidence score between 0.0 and 1.0
        """
        if not query_keywords:
            return 0.0
            
        # Check keyword matches in content and keywords list
        content_lower = self.content.lower()
        chunk_keywords_lower = [kw.lower() for kw in self.keywords]
        
        matches = 0
        for query_kw in query_keywords:
            query_kw_lower = query_kw.lower()
            if (query_kw_lower in content_lower or 
                any(query_kw_lower in chunk_kw for chunk_kw in chunk_keywords_lower)):
                matches += 1
        
        return min(matches / len(query_keywords), 1.0) * self.confidence


@dataclass
class TopicDefinition:
    """
    Defines how to identify and create chunks for a specific topic category
    """
    category: TopicCategory
    display_name: str  # Human-readable name
    spec_fields: List[str]  # Specification fields related to this topic
    keywords: List[str]  # Keywords that indicate this topic
    query_patterns: List[str]  # Common query patterns for this topic
    priority: int = 1  # Priority for conflicting topics (higher = more important)
    
    def matches_specs(self, specs: Dict[str, Any]) -> bool:
        """Check if laptop specs are relevant to this topic"""
        for field in self.spec_fields:
            value = specs.get(field, "")
            if value and str(value).strip():
                return True
        return False
    
    def calculate_relevance_score(self, specs: Dict[str, Any]) -> float:
        """Calculate how relevant the specs are to this topic (0.0 to 1.0)"""
        if not self.spec_fields:
            return 0.0
            
        relevant_fields = 0
        total_fields = len(self.spec_fields)
        
        for field in self.spec_fields:
            value = specs.get(field, "")
            if value and str(value).strip() and str(value) != "N/A":
                relevant_fields += 1
        
        return relevant_fields / total_fields


@dataclass
class QueryAnalysisResult:
    """
    Result of analyzing a user query for parent-child chunking
    """
    original_query: str
    detected_topics: List[TopicCategory]
    matched_keywords: List[str]
    confidence_scores: Dict[TopicCategory, float]
    suggested_parent_filters: Dict[str, Any] = field(default_factory=dict)
    
    def get_top_topics(self, limit: int = 3) -> List[TopicCategory]:
        """Get top N topics by confidence score"""
        sorted_topics = sorted(
            self.confidence_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        return [topic for topic, score in sorted_topics[:limit] if score > 0.0]
    
    def get_best_topic(self) -> Optional[TopicCategory]:
        """Get the topic with highest confidence score"""
        if not self.confidence_scores:
            return None
        return max(self.confidence_scores.items(), key=lambda x: x[1])[0]


@dataclass
class RetrievalResult:
    """
    Result of parent-child chunking retrieval process
    """
    query: str
    matched_parent_docs: List[ParentDocument]
    matched_child_chunks: List[ChildChunk]
    topic_analysis: QueryAnalysisResult
    retrieval_confidence: float
    response_strategy: str = "general"  # How to format the response
    
    def get_unique_models(self) -> List[str]:
        """Get list of unique model names from matched parents"""
        return list(set(doc.model_name for doc in self.matched_parent_docs))
    
    def get_top_matching_chunks(self, limit: int = 5) -> List[ChildChunk]:
        """Get top matching chunks sorted by relevance"""
        # Sort by confidence and topic priority
        return sorted(
            self.matched_child_chunks,
            key=lambda chunk: chunk.confidence,
            reverse=True
        )[:limit]
    
    def has_sufficient_results(self, min_parents: int = 1, min_chunks: int = 1) -> bool:
        """Check if we have sufficient results for a good response"""
        return (len(self.matched_parent_docs) >= min_parents and 
                len(self.matched_child_chunks) >= min_chunks and
                self.retrieval_confidence > 0.3)


# Topic definitions for laptop specifications
LAPTOP_TOPIC_DEFINITIONS = [
    TopicDefinition(
        category=TopicCategory.BATTERY_PERFORMANCE,
        display_name="電池續航表現",
        spec_fields=["battery", "thermal", "powerbutton"],
        keywords=["省電", "續航", "電池", "充電", "電源", "節能", "長時間", "小時", "mah"],
        query_patterns=["哪款比較省電", "續航能力", "電池怎麼樣", "能用多久", "不插電"]
    ),
    
    TopicDefinition(
        category=TopicCategory.GAMING_PERFORMANCE,
        display_name="遊戲效能表現", 
        spec_fields=["gpu", "cpu", "memory", "thermal", "storage"],
        keywords=["遊戲", "電競", "gaming", "顯卡", "gpu", "效能", "fps", "高階", "強勁"],
        query_patterns=["適合遊戲", "電競筆電", "遊戲效果", "高效能", "玩遊戲"]
    ),
    
    TopicDefinition(
        category=TopicCategory.BUSINESS_PRODUCTIVITY,
        display_name="商務辦公需求",
        spec_fields=["keyboard", "fingerprint", "tpm", "webcamera", "wireless"],
        keywords=["辦公", "商務", "business", "工作", "企業", "安全", "指紋", "鍵盤"],
        query_patterns=["適合辦公", "商務筆電", "工作用", "企業級", "專業"]
    ),
    
    TopicDefinition(
        category=TopicCategory.STUDENT_VALUE,
        display_name="學生性價比需求",
        spec_fields=["cpu", "memory", "storage", "battery"],
        keywords=["學生", "便宜", "性價比", "划算", "預算", "經濟", "實惠", "入門"],
        query_patterns=["學生用", "便宜的", "性價比高", "預算有限", "經濟實惠"]
    ),
    
    TopicDefinition(
        category=TopicCategory.DISPLAY_QUALITY,
        display_name="螢幕顯示品質",
        spec_fields=["lcd", "lcdconnector", "touchpanel"],
        keywords=["螢幕", "顯示", "screen", "display", "面板", "解析度", "色彩", "亮度"],
        query_patterns=["螢幕效果", "顯示品質", "看影片", "視覺效果"]
    ),
    
    TopicDefinition(
        category=TopicCategory.TECHNICAL_SPECS,
        display_name="技術規格詳情",
        spec_fields=["cpu", "gpu", "memory", "storage", "mainboard"],
        keywords=["規格", "spec", "配置", "參數", "技術", "詳細", "配備"],
        query_patterns=["詳細規格", "技術參數", "配置信息", "硬體規格"]
    ),
    
    TopicDefinition(
        category=TopicCategory.PORTABILITY,
        display_name="攜帶便利性",
        spec_fields=["structconfig", "battery", "thermal"],
        keywords=["輕薄", "便攜", "攜帶", "重量", "厚度", "移動", "外出", "輕便", "輕巧", "便利", "尺寸", "小巧", "輕鬆"],
        query_patterns=["輕薄筆電", "便於攜帶", "移動辦公", "外出使用", "輕便筆電", "更輕便", "比較輕便", "何者更輕便"]
    ),
    
    TopicDefinition(
        category=TopicCategory.CONNECTIVITY,
        display_name="連接擴展能力", 
        spec_fields=["iointerface", "wireless", "lan", "bluetooth", "wifislot"],
        keywords=["接口", "連接", "wifi", "藍牙", "usb", "擴展", "網路"],
        query_patterns=["連接性", "接口豐富", "擴展能力", "網路連接"]
    ),
    
    TopicDefinition(
        category=TopicCategory.SECURITY,
        display_name="安全防護功能",
        spec_fields=["fingerprint", "tpm", "webcamera", "rtc"],
        keywords=["安全", "防護", "指紋", "tpm", "加密", "隱私", "保護"],
        query_patterns=["安全性", "防護功能", "企業安全", "數據保護"]
    )
]

# Create lookup dictionary for quick access
TOPIC_LOOKUP = {topic.category: topic for topic in LAPTOP_TOPIC_DEFINITIONS}