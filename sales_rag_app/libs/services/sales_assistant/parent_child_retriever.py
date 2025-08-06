#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parent-Child Retriever

This module provides the main interface for the parent-child chunking system,
integrating with the existing SalesAssistantService architecture while
replacing the three-level hierarchical intent detection.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .parent_child_models import ParentDocument, ChildChunk, RetrievalResult
from .laptop_spec_chunker import LaptopSpecChunker, QueryAnalyzer
from .enhanced_vector_store import EnhancedVectorStore


class ParentChildRetriever:
    """
    Main interface for parent-child chunking retrieval system
    
    This class:
    1. Integrates with existing DuckDB data sources
    2. Replaces three-level hierarchical intent detection
    3. Provides immediate responses without clarification
    4. Maintains compatibility with existing service architecture
    """
    
    def __init__(self, duckdb_query_instance=None, cache_dir: str = None):
        """
        Initialize the parent-child retriever
        
        Args:
            duckdb_query_instance: DuckDB query instance from existing service
            cache_dir: Directory for caching processed data
        """
        self.duckdb_query = duckdb_query_instance
        
        # Initialize core components
        self.chunker = LaptopSpecChunker()
        self.vector_store = EnhancedVectorStore(cache_dir)
        self.query_analyzer = QueryAnalyzer()
        
        # State tracking
        self.is_initialized = False
        self.last_data_load_time = None
        
        # Specification fields (matching existing service)
        self.spec_fields = [
            'modeltype', 'version', 'modelname', 'mainboard', 'devtime',
            'pm', 'structconfig', 'lcd', 'touchpanel', 'iointerface', 
            'ledind', 'powerbutton', 'keyboard', 'webcamera', 'touchpad', 
            'fingerprint', 'audio', 'battery', 'cpu', 'gpu', 'memory', 
            'lcdconnector', 'storage', 'wifislot', 'thermal', 'tpm', 'rtc', 
            'wireless', 'lan', 'bluetooth', 'softwareconfig', 'ai', 'accessory', 
            'certfications', 'otherfeatures'
        ]
        
        logging.info("ParentChildRetriever initialized")
    
    def initialize_with_data(self, force_reload: bool = False) -> bool:
        """
        Initialize the retriever with data from DuckDB
        
        Args:
            force_reload: Force reload even if cache exists
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Try to load from cache first
            if not force_reload and self.vector_store.load_cache():
                self.is_initialized = True
                stats = self.vector_store.get_topic_statistics()
                logging.info(f"Loaded from cache: {stats['total_parents']} models, {stats['total_chunks']} chunks")
                return True
            
            # Load fresh data from DuckDB
            if not self.duckdb_query:
                logging.error("No DuckDB query instance provided")
                return False
            
            # Get all laptop specifications
            specs_data = self._load_specs_from_duckdb()
            if not specs_data:
                logging.error("Failed to load specifications from DuckDB")
                return False
            
            # Process specifications into parent-child structures
            parent_docs, child_chunks = self.chunker.chunk_laptop_specs(specs_data)
            
            # Add to vector store
            self.vector_store.add_documents(parent_docs, child_chunks)
            
            # Save cache for faster future loading
            self.vector_store.save_cache()
            
            self.is_initialized = True
            
            stats = self.vector_store.get_topic_statistics()
            logging.info(f"Initialized with {stats['total_parents']} models and {stats['total_chunks']} chunks")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize ParentChildRetriever: {e}")
            return False
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query using parent-child chunking strategy
        
        This replaces the three-level hierarchical intent detection with
        immediate semantic understanding and retrieval.
        
        Args:
            query: User query string
            
        Returns:
            Dictionary compatible with existing service structure
        """
        if not self.is_initialized:
            if not self.initialize_with_data():
                return self._create_fallback_result(query)
        
        try:
            # Retrieve using parent-child strategy
            retrieval_result = self.vector_store.retrieve(query)
            
            # Convert to format compatible with existing service
            compatible_result = self._convert_to_service_format(retrieval_result)
            
            logging.info(f"Processed query '{query}' with {len(retrieval_result.matched_parent_docs)} results")
            return compatible_result
            
        except Exception as e:
            logging.error(f"Error processing query '{query}': {e}")
            return self._create_fallback_result(query)
    
    def should_clarify(self, query_result: Dict[str, Any]) -> bool:
        """
        Determine if clarification is needed
        
        For parent-child chunking, this should almost always return False
        as we aim to provide immediate responses.
        
        Args:
            query_result: Result from process_query
            
        Returns:
            False (parent-child system avoids clarification)
        """
        # Check if we have sufficient results
        parent_child_data = query_result.get("parent_child_data", {})
        retrieval_confidence = parent_child_data.get("retrieval_confidence", 0.0)
        matched_parents = parent_child_data.get("matched_parents", [])
        
        # Only request clarification in extreme cases
        if retrieval_confidence < 0.1 and len(matched_parents) == 0:
            logging.warning(f"Very low confidence retrieval, but still avoiding clarification")
            # Even in low confidence cases, we prefer to give general recommendations
        
        return False  # Parent-child system never requests clarification
    
    def get_enhanced_context_for_llm(self, query_result: Dict[str, Any]) -> str:
        """
        Generate enhanced context for LLM prompt based on parent-child retrieval
        
        Args:
            query_result: Result from process_query
            
        Returns:
            Enhanced context string for LLM
        """
        try:
            parent_child_data = query_result.get("parent_child_data", {})
            
            if not parent_child_data:
                return "提供筆電型號比較和推薦資訊"
            
            # Extract parent-child specific information
            matched_parents = parent_child_data.get("matched_parents", [])
            top_chunks = parent_child_data.get("top_chunks", [])
            topic_analysis = parent_child_data.get("topic_analysis", {})
            response_strategy = parent_child_data.get("response_strategy", "general")
            
            context_parts = []
            
            # Add query understanding context
            context_parts.append(f"用戶查詢意圖分析：{query_result.get('original_query', '')}")
            
            if topic_analysis.get("detected_topics"):
                topics_str = "，".join([topic.replace("_", " ").title() for topic in topic_analysis["detected_topics"]])
                context_parts.append(f"檢測到的主要需求類別：{topics_str}")
            
            # Add matched models context
            if matched_parents:
                model_names = [parent.get("model_name", "Unknown") for parent in matched_parents]
                context_parts.append(f"相關型號：{', '.join(model_names)}")
            
            # Add topic-specific guidance
            if top_chunks:
                chunk_topics = [chunk.get("topic_category", "").replace("_", " ") for chunk in top_chunks[:3]]
                context_parts.append(f"重點關注領域：{', '.join(chunk_topics)}")
            
            # Add response strategy guidance
            strategy_guidance = {
                "battery_focus": "重點說明電池續航和省電特色",
                "gaming_focus": "重點說明遊戲效能和顯卡CPU表現",
                "business_focus": "重點說明商務功能和安全特色",
                "value_focus": "重點說明性價比和適合學生使用的特點",
                "display_focus": "重點說明螢幕顯示品質和視覺效果",
                "model_comparison": "提供詳細的型號對比分析",
                "detailed_specs": "提供完整的規格說明",
                "general_recommendation": "提供綜合性的推薦建議"
            }
            
            guidance = strategy_guidance.get(response_strategy, "提供有用的產品資訊")
            context_parts.append(f"回應策略：{guidance}")
            
            # Add confidence and quality indicators
            confidence = parent_child_data.get("retrieval_confidence", 0.0)
            context_parts.append(f"檢索信心度：{confidence:.2f}")
            
            return "\\n".join(context_parts)
            
        except Exception as e:
            logging.error(f"Error generating enhanced context: {e}")
            return "提供筆電型號比較和推薦資訊"
    
    def _load_specs_from_duckdb(self) -> List[Dict[str, Any]]:
        """Load laptop specifications from DuckDB"""
        try:
            # Query all specifications
            sql = "SELECT * FROM specs"
            records = self.duckdb_query.query(sql)
            
            if not records:
                logging.warning("No specifications found in DuckDB")
                return []
            
            # Convert to list of dictionaries
            specs_list = []
            for record in records:
                spec_dict = dict(zip(self.spec_fields, record))
                specs_list.append(spec_dict)
            
            logging.info(f"Loaded {len(specs_list)} laptop specifications from DuckDB")
            return specs_list
            
        except Exception as e:
            logging.error(f"Error loading specs from DuckDB: {e}")
            return []
    
    def _convert_to_service_format(self, retrieval_result: RetrievalResult) -> Dict[str, Any]:
        """Convert RetrievalResult to format compatible with existing service"""
        
        # Extract model information for compatibility
        modelnames = []
        modeltypes = set()
        
        for parent_doc in retrieval_result.matched_parent_docs:
            modelnames.append(parent_doc.model_name)
            model_type = parent_doc.metadata.get('model_type', '')
            if model_type:
                modeltypes.add(model_type)
        
        # Enhanced logic for model detection in query
        query_lower = retrieval_result.query.lower()
        suggested_filters = retrieval_result.topic_analysis.suggested_parent_filters
        
        # Check if specific models were mentioned but not found
        if not modelnames and suggested_filters.get('specific_models'):
            # Models were mentioned but not found in our database
            # Provide intelligent fallback based on series
            mentioned_models = suggested_filters.get('specific_models', [])
            series_mapping = {'819': ['AB819-S: FP6'], '839': ['AHP839'], '958': ['AG958']}
            
            for mentioned_model in mentioned_models:
                if '819' in mentioned_model:
                    modeltypes.add('819')
                    # Suggest similar 819 series models
                    modelnames.extend([m for m in series_mapping.get('819', []) if m not in modelnames])
                elif '839' in mentioned_model:
                    modeltypes.add('839')
                    modelnames.extend([m for m in series_mapping.get('839', []) if m not in modelnames])
                elif '958' in mentioned_model:
                    modeltypes.add('958')
                    modelnames.extend([m for m in series_mapping.get('958', []) if m not in modelnames])
        
        # Determine query type based on results
        query_type = "unknown"
        if modelnames:
            query_type = "specific_model"
        elif modeltypes:
            query_type = "model_type"
        
        # Build compatible result structure
        result = {
            # Original service compatibility
            "modelnames": modelnames,
            "modeltypes": list(modeltypes),
            "intents": [chunk.topic_category.value for chunk in retrieval_result.get_top_matching_chunks(3)],
            "primary_intent": retrieval_result.topic_analysis.get_best_topic().value if retrieval_result.topic_analysis.get_best_topic() else "general",
            "query_type": query_type,
            "confidence_score": retrieval_result.retrieval_confidence,
            "original_query": retrieval_result.query,
            
            # Parent-child specific data
            "parent_child_data": {
                "matched_parents": [self._parent_doc_to_dict(doc) for doc in retrieval_result.matched_parent_docs],
                "top_chunks": [self._chunk_to_dict(chunk) for chunk in retrieval_result.get_top_matching_chunks(5)],
                "topic_analysis": {
                    "detected_topics": [topic.value for topic in retrieval_result.topic_analysis.detected_topics],
                    "confidence_scores": {topic.value: score for topic, score in retrieval_result.topic_analysis.confidence_scores.items()},
                    "matched_keywords": retrieval_result.topic_analysis.matched_keywords
                },
                "retrieval_confidence": retrieval_result.retrieval_confidence,
                "response_strategy": retrieval_result.response_strategy,
                "processing_method": "parent_child_chunking"
            }
        }
        
        return result
    
    def _parent_doc_to_dict(self, parent_doc: ParentDocument) -> Dict[str, Any]:
        """Convert ParentDocument to dictionary"""
        return {
            "doc_id": parent_doc.doc_id,
            "model_name": parent_doc.model_name,
            "full_specs": parent_doc.full_specs,
            "metadata": parent_doc.metadata,
            "text_summary": parent_doc.to_text_summary()
        }
    
    def _chunk_to_dict(self, chunk: ChildChunk) -> Dict[str, Any]:
        """Convert ChildChunk to dictionary"""
        return {
            "chunk_id": chunk.chunk_id,
            "parent_doc_id": chunk.parent_doc_id,
            "topic_category": chunk.topic_category.value,
            "content": chunk.content,
            "confidence": chunk.confidence,
            "keywords": chunk.keywords,
            "metadata": chunk.metadata
        }
    
    def _create_fallback_result(self, query: str) -> Dict[str, Any]:
        """Create fallback result when processing fails"""
        return {
            "modelnames": [],
            "modeltypes": ["819", "839", "958"],  # Default to all series
            "intents": ["general"],
            "primary_intent": "general",
            "query_type": "model_type",
            "confidence_score": 0.5,
            "original_query": query,
            "parent_child_data": {
                "matched_parents": [],
                "top_chunks": [],
                "topic_analysis": {
                    "detected_topics": ["general_info"],
                    "confidence_scores": {"general_info": 0.5},
                    "matched_keywords": []
                },
                "retrieval_confidence": 0.5,
                "response_strategy": "general_recommendation",
                "processing_method": "fallback",
                "fallback_reason": "initialization_failed"
            }
        }
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the parent-child system"""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        base_stats = self.vector_store.get_topic_statistics()
        base_stats.update({
            "status": "initialized",
            "chunker_counter": self.chunker.chunk_counter,
            "system_type": "parent_child_chunking"
        })
        
        return base_stats


def test_parent_child_retriever():
    """Test function for the parent-child retriever"""
    print("=== Testing Parent-Child Retriever ===")
    
    # Note: This test uses mock data since we don't have DuckDB connection
    # In real implementation, this would be integrated with the actual service
    
    retriever = ParentChildRetriever()
    
    # Mock some data for testing
    mock_specs = [
        {
            'modelname': 'AG958',
            'modeltype': '958',
            'cpu': 'AMD Ryzen 9 7940HS',
            'gpu': 'NVIDIA RTX 4060',
            'memory': '32GB DDR5',
            'battery': '8-10 hours'
        },
        {
            'modelname': 'AB819-S: FP6',
            'modeltype': '819',
            'cpu': 'Intel Core i5-13500H',
            'gpu': 'Intel Iris Xe',
            'memory': '16GB DDR4',
            'battery': '12-14 hours'
        }
    ]
    
    # Initialize with mock data
    parent_docs, child_chunks = retriever.chunker.chunk_laptop_specs(mock_specs)
    retriever.vector_store.add_documents(parent_docs, child_chunks)
    retriever.is_initialized = True
    
    # Test query processing
    test_queries = [
        "哪款筆電比較省電？",
        "推薦適合遊戲的",
        "學生用什麼好？"
    ]
    
    for query in test_queries:
        print(f"\\nTesting query: {query}")
        result = retriever.process_query(query)
        
        print(f"Models found: {result['modelnames']}")
        print(f"Primary intent: {result['primary_intent']}")
        print(f"Confidence: {result['confidence_score']:.2f}")
        print(f"Should clarify: {retriever.should_clarify(result)}")
        
        # Test enhanced context
        context = retriever.get_enhanced_context_for_llm(result)
        print(f"Enhanced context preview: {context[:150]}...")
    
    # Show system statistics
    print(f"\\n=== System Statistics ===")
    stats = retriever.get_system_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    test_parent_child_retriever()