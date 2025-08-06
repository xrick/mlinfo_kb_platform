#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Laptop Specification Chunker

This module transforms laptop specifications from DuckDB into parent-child
chunking structures optimized for semantic retrieval and user query matching.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from .parent_child_models import (
    ParentDocument, ChildChunk, TopicCategory, TopicDefinition,
    QueryAnalysisResult, LAPTOP_TOPIC_DEFINITIONS, TOPIC_LOOKUP
)


class LaptopSpecChunker:
    """
    Transforms laptop specifications into parent-child chunking structures
    
    This chunker:
    1. Takes structured laptop specs from DuckDB
    2. Creates ParentDocument objects for each laptop model
    3. Generates topic-specific ChildChunk objects
    4. Optimizes chunks for semantic retrieval
    """
    
    def __init__(self):
        """Initialize the chunker with topic definitions"""
        self.topic_definitions = LAPTOP_TOPIC_DEFINITIONS
        self.chunk_counter = 0
        
        # Specification field definitions from the service
        self.spec_fields = [
            'modeltype', 'version', 'modelname', 'mainboard', 'devtime',
            'pm', 'structconfig', 'lcd', 'touchpanel', 'iointerface', 
            'ledind', 'powerbutton', 'keyboard', 'webcamera', 'touchpad', 
            'fingerprint', 'audio', 'battery', 'cpu', 'gpu', 'memory', 
            'lcdconnector', 'storage', 'wifislot', 'thermal', 'tpm', 'rtc', 
            'wireless', 'lan', 'bluetooth', 'softwareconfig', 'ai', 'accessory', 
            'certfications', 'otherfeatures'
        ]
        
        logging.info(f"LaptopSpecChunker initialized with {len(self.topic_definitions)} topic definitions")
    
    def create_parent_document(self, spec_dict: Dict[str, Any]) -> ParentDocument:
        """
        Create a ParentDocument from a laptop specification dictionary
        
        Args:
            spec_dict: Dictionary containing laptop specifications
            
        Returns:
            ParentDocument object representing the complete laptop
        """
        # Extract key identifiers
        model_name = spec_dict.get('modelname', 'Unknown Model')
        model_type = spec_dict.get('modeltype', '')
        
        # Create unique document ID
        doc_id = self._generate_doc_id(model_name, model_type)
        
        # Create metadata
        metadata = {
            'model_type': model_type,
            'version': spec_dict.get('version', ''),
            'created_by': 'LaptopSpecChunker',
            'spec_field_count': len([k for k, v in spec_dict.items() if v and str(v).strip()])
        }
        
        parent_doc = ParentDocument(
            doc_id=doc_id,
            model_name=model_name,
            full_specs=spec_dict.copy(),
            metadata=metadata
        )
        
        return parent_doc
    
    def create_child_chunks(self, parent_doc: ParentDocument) -> List[ChildChunk]:
        """
        Generate topic-specific child chunks from a parent document
        
        Args:
            parent_doc: ParentDocument to chunk
            
        Returns:
            List of ChildChunk objects representing different topics
        """
        chunks = []
        
        for topic_def in self.topic_definitions:
            # Check if this laptop has specs relevant to this topic
            if not topic_def.matches_specs(parent_doc.full_specs):
                continue
            
            # Calculate relevance score
            relevance_score = topic_def.calculate_relevance_score(parent_doc.full_specs)
            if relevance_score < 0.1:  # Skip topics with very low relevance
                continue
            
            # Create chunk content for this topic
            chunk_content = self._generate_chunk_content(parent_doc, topic_def)
            if not chunk_content.strip():
                continue
            
            # Create the child chunk
            chunk = ChildChunk(
                chunk_id=f"{parent_doc.doc_id}-{topic_def.category.value}-{self.chunk_counter}",
                parent_doc_id=parent_doc.doc_id,
                topic_category=topic_def.category,
                content=chunk_content,
                spec_fields=topic_def.spec_fields,
                keywords=topic_def.keywords.copy(),
                confidence=relevance_score,
                metadata={
                    'topic_display_name': topic_def.display_name,
                    'parent_model': parent_doc.model_name,
                    'field_count': len([f for f in topic_def.spec_fields if parent_doc.get_spec_value(f)])
                }
            )
            
            chunks.append(chunk)
            self.chunk_counter += 1
        
        logging.info(f"Generated {len(chunks)} child chunks for {parent_doc.model_name}")
        return chunks
    
    def chunk_laptop_specs(self, specs_list: List[Dict[str, Any]]) -> Tuple[List[ParentDocument], List[ChildChunk]]:
        """
        Process a list of laptop specifications into parent-child structures
        
        Args:
            specs_list: List of dictionaries containing laptop specifications
            
        Returns:
            Tuple of (parent_documents, child_chunks)
        """
        parent_docs = []
        all_child_chunks = []
        
        for spec_dict in specs_list:
            try:
                # Create parent document
                parent_doc = self.create_parent_document(spec_dict)
                parent_docs.append(parent_doc)
                
                # Generate child chunks
                child_chunks = self.create_child_chunks(parent_doc)
                all_child_chunks.extend(child_chunks)
                
            except Exception as e:
                logging.error(f"Error chunking laptop spec {spec_dict.get('modelname', 'unknown')}: {e}")
                continue
        
        logging.info(f"Chunked {len(specs_list)} laptop specs into {len(parent_docs)} parents and {len(all_child_chunks)} children")
        return parent_docs, all_child_chunks
    
    def _generate_doc_id(self, model_name: str, model_type: str) -> str:
        """Generate a unique document ID for a laptop model"""
        # Clean and normalize the model name for ID
        clean_name = re.sub(r'[^\w\-:]', '_', model_name)
        if model_type:
            clean_type = re.sub(r'[^\w]', '_', model_type)
            return f"{clean_type}_{clean_name}"
        return clean_name
    
    def _generate_chunk_content(self, parent_doc: ParentDocument, topic_def: TopicDefinition) -> str:
        """
        Generate human-readable content for a topic-specific chunk
        
        Args:
            parent_doc: Parent document containing full specs
            topic_def: Topic definition to generate content for
            
        Returns:
            String content describing this topic for the laptop
        """
        content_parts = [f"{parent_doc.model_name} - {topic_def.display_name}："]
        
        # Extract relevant specification values
        relevant_specs = []
        for field in topic_def.spec_fields:
            value = parent_doc.get_spec_value(field)
            if value and str(value).strip() and str(value) != "N/A":
                # Map field names to human-readable labels
                field_label = self._get_field_display_name(field)
                relevant_specs.append(f"{field_label}：{value}")
        
        if relevant_specs:
            content_parts.extend(relevant_specs)
        else:
            content_parts.append("相關規格待確認")
        
        # Add topic-specific keywords for better matching
        if topic_def.keywords:
            # Select a few most relevant keywords
            key_keywords = topic_def.keywords[:5]
            content_parts.append(f"關鍵特色：{', '.join(key_keywords)}")
        
        return "；".join(content_parts)
    
    def _get_field_display_name(self, field: str) -> str:
        """Convert specification field names to human-readable labels"""
        field_labels = {
            'cpu': 'CPU處理器',
            'gpu': '顯示卡',
            'memory': '記憶體',
            'storage': '儲存空間',
            'battery': '電池',
            'lcd': '螢幕',
            'keyboard': '鍵盤',
            'fingerprint': '指紋辨識',
            'tpm': 'TPM安全',
            'wireless': '無線網路',
            'bluetooth': '藍牙',
            'webcamera': '網路攝影機',
            'thermal': '散熱系統',
            'touchpanel': '觸控面板',
            'iointerface': 'I/O接口',
            'mainboard': '主機板',
            'structconfig': '結構配置',
            'powerbutton': '電源按鈕',
            'touchpad': '觸控板',
            'audio': '音效',
            'lcdconnector': '螢幕連接',
            'wifislot': 'WiFi插槽',
            'rtc': '即時時鐘',
            'lan': '有線網路',
            'softwareconfig': '軟體配置',
            'ai': 'AI功能',
            'accessory': '配件',
            'certfications': '認證',
            'otherfeatures': '其他特色',
            'modeltype': '型號系列',
            'version': '版本',
            'modelname': '型號名稱',
            'devtime': '開發時間',
            'pm': '專案管理',
            'ledind': 'LED指示',
        }
        
        return field_labels.get(field, field.upper())


class QueryAnalyzer:
    """
    Analyzes user queries to determine relevant topics and keywords
    for parent-child chunk retrieval
    """
    
    def __init__(self):
        """Initialize the query analyzer"""
        self.topic_definitions = LAPTOP_TOPIC_DEFINITIONS
        
        # Build keyword lookup for faster matching
        self.keyword_to_topics = {}
        for topic_def in self.topic_definitions:
            for keyword in topic_def.keywords:
                if keyword not in self.keyword_to_topics:
                    self.keyword_to_topics[keyword] = []
                self.keyword_to_topics[keyword].append(topic_def.category)
        
        logging.info(f"QueryAnalyzer initialized with {len(self.keyword_to_topics)} keywords")
    
    def analyze_query(self, query: str) -> QueryAnalysisResult:
        """
        Analyze a user query to determine relevant topics and keywords
        
        Args:
            query: User query string
            
        Returns:
            QueryAnalysisResult with detected topics and confidence scores
        """
        query_lower = query.lower()
        
        # Track topic matches and scores
        topic_scores = {topic.category: 0.0 for topic in self.topic_definitions}
        matched_keywords = []
        
        # Check keyword matches
        for keyword, topic_categories in self.keyword_to_topics.items():
            if keyword.lower() in query_lower:
                matched_keywords.append(keyword)
                # Give score boost to relevant topics
                for topic_category in topic_categories:
                    topic_scores[topic_category] += 0.3
        
        # Special handling for comparison queries
        comparison_keywords = ["比較", "比较", "compare", "何者", "哪個", "哪个", "versus", "vs"]
        is_comparison = any(comp_word in query_lower for comp_word in comparison_keywords)
        if is_comparison:
            # Boost all topic scores slightly for comparison queries
            for topic in topic_scores:
                topic_scores[topic] += 0.2
        
        # Check pattern matches
        for topic_def in self.topic_definitions:
            for pattern in topic_def.query_patterns:
                pattern_lower = pattern.lower()
                if pattern_lower in query_lower:
                    topic_scores[topic_def.category] += 0.5
                    if pattern not in matched_keywords:
                        matched_keywords.append(pattern)
        
        # Normalize scores to 0-1 range
        max_score = max(topic_scores.values()) if topic_scores.values() else 1.0
        if max_score > 0:
            for topic in topic_scores:
                topic_scores[topic] = min(topic_scores[topic] / max_score, 1.0)
        
        # Determine detected topics (score > 0.1)
        detected_topics = [topic for topic, score in topic_scores.items() if score > 0.1]
        
        # Generate suggested filters based on query analysis
        suggested_filters = self._generate_parent_filters(query_lower, detected_topics)
        
        result = QueryAnalysisResult(
            original_query=query,
            detected_topics=detected_topics,
            matched_keywords=matched_keywords,
            confidence_scores=topic_scores,
            suggested_parent_filters=suggested_filters
        )
        
        logging.info(f"Query analysis for '{query}': {len(detected_topics)} topics detected")
        return result
    
    def _generate_parent_filters(self, query_lower: str, detected_topics: List[TopicCategory]) -> Dict[str, Any]:
        """Generate filters for parent document selection based on query"""
        filters = {}
        
        # Model series detection
        model_patterns = {
            '819': r'\b819\b',
            '839': r'\b839\b', 
            '958': r'\b958\b'
        }
        
        # Enhanced model name detection including AMD variants
        specific_model_patterns = {
            'AMD819-S: FT6': r'amd819[-\s]*s[:]*\s*ft6',
            'AMD819: FT6': r'amd819[:]*\s*ft6',
            'AB819-S: FP6': r'ab819[-\s]*s[:]*\s*fp6',
            'AG958': r'ag958',
            'AHP839': r'ahp839'
        }
        
        detected_models = []
        for model_name, pattern in specific_model_patterns.items():
            if re.search(pattern, query_lower):
                detected_models.append(model_name)
        
        if detected_models:
            filters['specific_models'] = detected_models
        
        # Fallback to series detection
        for series, pattern in model_patterns.items():
            if re.search(pattern, query_lower):
                filters['model_series'] = series
                break
        
        # Performance level hints
        if any(word in query_lower for word in ['高階', '頂級', '旗艦', '專業']):
            filters['performance_level'] = 'high'
        elif any(word in query_lower for word in ['入門', '基礎', '經濟', '便宜']):
            filters['performance_level'] = 'entry'
        
        return filters


def test_laptop_chunker():
    """Test function for the laptop specification chunker"""
    print("=== Testing Laptop Specification Chunker ===")
    
    # Sample laptop specifications (matching actual DuckDB structure)
    sample_specs = [
        {
            'modelname': 'AG958',
            'modeltype': '958',
            'cpu': 'AMD Ryzen 9 7940HS',
            'gpu': 'NVIDIA RTX 4060',
            'memory': '32GB DDR5',
            'storage': '1TB NVMe SSD',
            'battery': '8-10 hours',
            'lcd': '15.6" QHD 165Hz',
            'keyboard': '背光鍵盤',
            'fingerprint': '指紋辨識',
            'wireless': 'WiFi 6E',
            'bluetooth': 'Bluetooth 5.2'
        },
        {
            'modelname': 'AB819-S: FP6',
            'modeltype': '819', 
            'cpu': 'Intel Core i5-13500H',
            'gpu': 'Intel Iris Xe',
            'memory': '16GB DDR4',
            'storage': '512GB SSD',
            'battery': '12-14 hours',
            'lcd': '14" FHD IPS',
            'keyboard': '舒適鍵盤',
            'tpm': 'TPM 2.0',
            'wireless': 'WiFi 6'
        }
    ]
    
    # Initialize chunker and analyzer
    chunker = LaptopSpecChunker()
    analyzer = QueryAnalyzer()
    
    # Process specifications
    parent_docs, child_chunks = chunker.chunk_laptop_specs(sample_specs)
    
    print(f"\\nCreated {len(parent_docs)} parent documents:")
    for doc in parent_docs:
        print(f"  - {doc.model_name} ({doc.doc_id})")
    
    print(f"\\nCreated {len(child_chunks)} child chunks:")
    for chunk in child_chunks:
        print(f"  - {chunk.chunk_id}: {chunk.topic_category.value} (confidence: {chunk.confidence:.2f})")
        print(f"    Content: {chunk.content[:100]}...")
    
    # Test query analysis
    test_queries = [
        "哪款筆電比較省電？",
        "推薦適合遊戲的",
        "學生用什麼好？",
        "958系列的顯示效果怎麼樣？"
    ]
    
    print(f"\\n=== Query Analysis Tests ===")
    for query in test_queries:
        result = analyzer.analyze_query(query)
        print(f"\\nQuery: {query}")
        print(f"Detected topics: {[t.value for t in result.detected_topics]}")
        print(f"Matched keywords: {result.matched_keywords}")
        print(f"Best topic: {result.get_best_topic().value if result.get_best_topic() else 'None'}")


if __name__ == "__main__":
    test_laptop_chunker()