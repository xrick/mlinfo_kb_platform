#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Vector Store for Parent-Child Chunking

This module implements an enhanced storage and retrieval system optimized for
parent-child chunking strategy, providing fast semantic matching and context-aware retrieval.
"""

import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict
import numpy as np

from .parent_child_models import (
    ParentDocument, ChildChunk, TopicCategory, QueryAnalysisResult, 
    RetrievalResult
)
from .laptop_spec_chunker import QueryAnalyzer


class EnhancedVectorStore:
    """
    Enhanced storage and retrieval system for parent-child chunking
    
    This store:
    1. Indexes parent documents by various criteria
    2. Creates semantic indexes for child chunks  
    3. Supports fast retrieval based on topic categories
    4. Returns full parent context when child chunks match
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the enhanced vector store
        
        Args:
            cache_dir: Directory to store cached indexes
        """
        # Core storage
        self.parent_documents: Dict[str, ParentDocument] = {}
        self.child_chunks: List[ChildChunk] = []
        
        # Indexes for fast retrieval
        self.topic_to_chunks: Dict[TopicCategory, List[ChildChunk]] = defaultdict(list)
        self.parent_to_chunks: Dict[str, List[ChildChunk]] = defaultdict(list)
        self.model_series_index: Dict[str, List[ParentDocument]] = defaultdict(list)
        self.keyword_index: Dict[str, Set[str]] = defaultdict(set)  # keyword -> chunk_ids
        
        # Query analyzer for processing user queries
        self.query_analyzer = QueryAnalyzer()
        
        # Cache settings
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent / "vector_store_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        logging.info("EnhancedVectorStore initialized")
    
    def add_documents(self, parent_docs: List[ParentDocument], child_chunks: List[ChildChunk]):
        """
        Add parent documents and child chunks to the store
        
        Args:
            parent_docs: List of parent documents to add
            child_chunks: List of child chunks to add
        """
        # Add parent documents
        for doc in parent_docs:
            self.parent_documents[doc.doc_id] = doc
            
            # Index by model series for filtering
            model_type = doc.metadata.get('model_type', '')
            if model_type:
                self.model_series_index[model_type].append(doc)
        
        # Add child chunks and build indexes
        for chunk in child_chunks:
            self.child_chunks.append(chunk)
            
            # Index by topic category
            self.topic_to_chunks[chunk.topic_category].append(chunk)
            
            # Index by parent document
            self.parent_to_chunks[chunk.parent_doc_id].append(chunk)
            
            # Index by keywords for fast text matching
            for keyword in chunk.keywords:
                self.keyword_index[keyword.lower()].add(chunk.chunk_id)
            
            # Also index content words
            content_words = chunk.content.lower().split()
            for word in content_words:
                if len(word) > 2:  # Skip very short words
                    self.keyword_index[word].add(chunk.chunk_id)
        
        logging.info(f"Added {len(parent_docs)} parent docs and {len(child_chunks)} child chunks")
        logging.info(f"Indexed {len(self.topic_to_chunks)} topic categories")
    
    def retrieve(self, query: str, max_parents: int = 5, max_chunks: int = 10) -> RetrievalResult:
        """
        Retrieve relevant parent documents based on query using parent-child strategy
        
        Args:
            query: User query string
            max_parents: Maximum number of parent documents to return
            max_chunks: Maximum number of child chunks to consider
            
        Returns:
            RetrievalResult with matched parents and chunks
        """
        # Analyze the query to understand user intent
        query_analysis = self.query_analyzer.analyze_query(query)
        
        # Find relevant child chunks based on query analysis
        relevant_chunks = self._find_relevant_chunks(query_analysis, max_chunks)
        
        # Get parent documents from relevant chunks
        parent_doc_ids = set(chunk.parent_doc_id for chunk in relevant_chunks)
        matched_parents = []
        
        # Apply filters from query analysis
        for doc_id in parent_doc_ids:
            parent_doc = self.parent_documents.get(doc_id)
            if parent_doc and self._passes_parent_filters(parent_doc, query_analysis):
                matched_parents.append(parent_doc)
        
        # Sort parents by relevance (based on chunk confidence scores)
        parent_relevance = self._calculate_parent_relevance(matched_parents, relevant_chunks)
        matched_parents.sort(key=lambda doc: parent_relevance.get(doc.doc_id, 0.0), reverse=True)
        
        # Limit results
        matched_parents = matched_parents[:max_parents]
        
        # Calculate overall retrieval confidence
        retrieval_confidence = self._calculate_retrieval_confidence(
            query_analysis, relevant_chunks, matched_parents
        )
        
        # Determine response strategy based on query analysis
        response_strategy = self._determine_response_strategy(query_analysis, matched_parents)
        
        result = RetrievalResult(
            query=query,
            matched_parent_docs=matched_parents,
            matched_child_chunks=relevant_chunks,
            topic_analysis=query_analysis,
            retrieval_confidence=retrieval_confidence,
            response_strategy=response_strategy
        )
        
        logging.info(f"Retrieved {len(matched_parents)} parents and {len(relevant_chunks)} chunks for: '{query}'")
        return result
    
    def _find_relevant_chunks(self, query_analysis: QueryAnalysisResult, max_chunks: int) -> List[ChildChunk]:
        """Find child chunks relevant to the analyzed query"""
        relevant_chunks = []
        chunk_scores = {}
        
        # Get chunks from detected topics
        for topic in query_analysis.detected_topics:
            topic_chunks = self.topic_to_chunks.get(topic, [])
            for chunk in topic_chunks:
                if chunk.chunk_id not in chunk_scores:
                    # Calculate chunk relevance score
                    score = self._calculate_chunk_relevance(chunk, query_analysis)
                    chunk_scores[chunk.chunk_id] = score
                    relevant_chunks.append(chunk)
        
        # Also search by keyword matching for broader coverage
        query_words = query_analysis.original_query.lower().split()
        for word in query_words:
            if len(word) > 2:  # Skip short words
                matching_chunk_ids = self.keyword_index.get(word, set())
                for chunk_id in matching_chunk_ids:
                    # Find the chunk object
                    chunk = next((c for c in self.child_chunks if c.chunk_id == chunk_id), None)
                    if chunk and chunk.chunk_id not in chunk_scores:
                        score = self._calculate_chunk_relevance(chunk, query_analysis)
                        chunk_scores[chunk.chunk_id] = score
                        relevant_chunks.append(chunk)
        
        # Sort by relevance score and limit results
        relevant_chunks.sort(key=lambda c: chunk_scores.get(c.chunk_id, 0.0), reverse=True)
        return relevant_chunks[:max_chunks]
    
    def _calculate_chunk_relevance(self, chunk: ChildChunk, query_analysis: QueryAnalysisResult) -> float:
        """Calculate how relevant a chunk is to the query analysis"""
        score = 0.0
        
        # Topic category matching
        if chunk.topic_category in query_analysis.detected_topics:
            topic_confidence = query_analysis.confidence_scores.get(chunk.topic_category, 0.0)
            score += topic_confidence * 0.6
        
        # Keyword matching
        keyword_match_score = chunk.matches_query_keywords(query_analysis.matched_keywords)
        score += keyword_match_score * 0.3
        
        # Chunk confidence
        score += chunk.confidence * 0.1
        
        return min(score, 1.0)
    
    def _passes_parent_filters(self, parent_doc: ParentDocument, query_analysis: QueryAnalysisResult) -> bool:
        """Check if parent document passes filters from query analysis"""
        filters = query_analysis.suggested_parent_filters
        
        # Model series filter
        if 'model_series' in filters:
            required_series = filters['model_series']
            doc_series = parent_doc.metadata.get('model_type', '')
            if required_series not in doc_series:
                return False
        
        # Performance level filter (simple heuristic based on GPU specs)
        if 'performance_level' in filters:
            required_level = filters['performance_level']
            gpu_spec = parent_doc.get_spec_value('gpu') or ''
            
            if required_level == 'high':
                # High performance should have dedicated GPU
                if not any(term in gpu_spec.lower() for term in ['rtx', 'gtx', 'radeon', 'dedicated']):
                    return False
            elif required_level == 'entry':
                # Entry level typically has integrated graphics
                if any(term in gpu_spec.lower() for term in ['rtx', 'gtx']):
                    return False
        
        return True
    
    def _calculate_parent_relevance(self, parents: List[ParentDocument], chunks: List[ChildChunk]) -> Dict[str, float]:
        """Calculate relevance scores for parent documents based on their chunks"""
        parent_scores = defaultdict(float)
        parent_chunk_counts = defaultdict(int)
        
        for chunk in chunks:
            if chunk.parent_doc_id in [p.doc_id for p in parents]:
                parent_scores[chunk.parent_doc_id] += chunk.confidence
                parent_chunk_counts[chunk.parent_doc_id] += 1
        
        # Normalize by chunk count and boost for multiple relevant chunks
        for parent_id in parent_scores:
            chunk_count = parent_chunk_counts[parent_id]
            if chunk_count > 0:
                # Average confidence with bonus for multiple relevant chunks
                avg_confidence = parent_scores[parent_id] / chunk_count
                multi_chunk_bonus = min(chunk_count * 0.1, 0.3)  # Max 30% bonus
                parent_scores[parent_id] = avg_confidence + multi_chunk_bonus
        
        return dict(parent_scores)
    
    def _calculate_retrieval_confidence(self, query_analysis: QueryAnalysisResult, 
                                       chunks: List[ChildChunk], parents: List[ParentDocument]) -> float:
        """Calculate overall confidence in the retrieval results"""
        if not chunks or not parents:
            return 0.0
        
        # Base confidence from query analysis
        max_topic_confidence = max(query_analysis.confidence_scores.values()) if query_analysis.confidence_scores else 0.0
        
        # Average chunk confidence
        avg_chunk_confidence = sum(chunk.confidence for chunk in chunks) / len(chunks)
        
        # Coverage factor (more chunks/parents = higher confidence)
        coverage_factor = min(len(chunks) * 0.1 + len(parents) * 0.05, 0.3)
        
        # Combine factors
        total_confidence = (max_topic_confidence * 0.5 + 
                           avg_chunk_confidence * 0.4 + 
                           coverage_factor * 0.1)
        
        return min(total_confidence, 1.0)
    
    def _determine_response_strategy(self, query_analysis: QueryAnalysisResult, 
                                   parents: List[ParentDocument]) -> str:
        """Determine the best response strategy based on query and results"""
        if not query_analysis.detected_topics:
            return "general_comparison"
        
        # Single topic focus
        if len(query_analysis.detected_topics) == 1:
            topic = query_analysis.detected_topics[0]
            if topic == TopicCategory.BATTERY_PERFORMANCE:
                return "battery_focus"
            elif topic == TopicCategory.GAMING_PERFORMANCE:
                return "gaming_focus"
            elif topic == TopicCategory.BUSINESS_PRODUCTIVITY:
                return "business_focus"
            elif topic == TopicCategory.STUDENT_VALUE:
                return "value_focus"
            elif topic == TopicCategory.DISPLAY_QUALITY:
                return "display_focus"
        
        # Multiple models comparison
        if len(parents) > 1:
            return "model_comparison"
        
        # Single model detailed specs
        if len(parents) == 1:
            return "detailed_specs"
        
        return "general_recommendation"
    
    def get_topic_statistics(self) -> Dict[str, Any]:
        """Get statistics about the indexed content"""
        stats = {
            "total_parents": len(self.parent_documents),
            "total_chunks": len(self.child_chunks),
            "topic_distribution": {},
            "model_series_distribution": {},
            "keyword_count": len(self.keyword_index)
        }
        
        # Topic distribution
        for topic, chunks in self.topic_to_chunks.items():
            stats["topic_distribution"][topic.value] = len(chunks)
        
        # Model series distribution
        for series, docs in self.model_series_index.items():
            stats["model_series_distribution"][series] = len(docs)
        
        return stats
    
    def save_cache(self, cache_name: str = "vector_store_cache.pkl"):
        """Save the vector store to cache for faster loading"""
        cache_file = self.cache_dir / cache_name
        try:
            cache_data = {
                "parent_documents": self.parent_documents,
                "child_chunks": self.child_chunks,
                "topic_to_chunks": dict(self.topic_to_chunks),
                "parent_to_chunks": dict(self.parent_to_chunks),
                "model_series_index": dict(self.model_series_index),
                "keyword_index": dict(self.keyword_index)
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logging.info(f"Vector store cached to {cache_file}")
        except Exception as e:
            logging.error(f"Failed to save cache: {e}")
    
    def load_cache(self, cache_name: str = "vector_store_cache.pkl") -> bool:
        """Load the vector store from cache"""
        cache_file = self.cache_dir / cache_name
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.parent_documents = cache_data["parent_documents"]
            self.child_chunks = cache_data["child_chunks"]
            self.topic_to_chunks = defaultdict(list, cache_data["topic_to_chunks"])
            self.parent_to_chunks = defaultdict(list, cache_data["parent_to_chunks"])
            self.model_series_index = defaultdict(list, cache_data["model_series_index"])
            self.keyword_index = defaultdict(set, cache_data["keyword_index"])
            
            logging.info(f"Vector store loaded from cache: {cache_file}")
            return True
        except Exception as e:
            logging.error(f"Failed to load cache: {e}")
            return False


def test_enhanced_vector_store():
    """Test function for the enhanced vector store"""
    print("=== Testing Enhanced Vector Store ===")
    
    # Import required modules for testing
    from .laptop_spec_chunker import LaptopSpecChunker
    
    # Sample data
    sample_specs = [
        {
            'modelname': 'AG958',
            'modeltype': '958',
            'cpu': 'AMD Ryzen 9 7940HS',
            'gpu': 'NVIDIA RTX 4060',
            'memory': '32GB DDR5',
            'storage': '1TB NVMe SSD',
            'battery': '8-10 hours',
            'lcd': '15.6" QHD 165Hz'
        },
        {
            'modelname': 'AB819-S: FP6',
            'modeltype': '819',
            'cpu': 'Intel Core i5-13500H',
            'gpu': 'Intel Iris Xe',
            'memory': '16GB DDR4',
            'storage': '512GB SSD',
            'battery': '12-14 hours',
            'lcd': '14" FHD IPS'
        }
    ]
    
    # Initialize components
    chunker = LaptopSpecChunker()
    vector_store = EnhancedVectorStore()
    
    # Process and index data
    parent_docs, child_chunks = chunker.chunk_laptop_specs(sample_specs)
    vector_store.add_documents(parent_docs, child_chunks)
    
    # Test retrieval with different queries
    test_queries = [
        "哪款筆電比較省電？",
        "推薦適合遊戲的",
        "958系列的效能怎麼樣？",
        "學生用什麼好？"
    ]
    
    print(f"\\n=== Retrieval Tests ===")
    for query in test_queries:
        print(f"\\nQuery: {query}")
        result = vector_store.retrieve(query)
        
        print(f"Retrieved {len(result.matched_parent_docs)} parents:")
        for doc in result.matched_parent_docs:
            print(f"  - {doc.model_name}")
        
        print(f"Top matching chunks:")
        for chunk in result.get_top_matching_chunks(3):
            print(f"  - {chunk.topic_category.value}: {chunk.confidence:.2f}")
        
        print(f"Confidence: {result.retrieval_confidence:.2f}")
        print(f"Strategy: {result.response_strategy}")
    
    # Show statistics
    print(f"\\n=== Store Statistics ===")
    stats = vector_store.get_topic_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    test_enhanced_vector_store()