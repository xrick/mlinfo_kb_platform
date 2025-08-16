#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Chunking Engine
基於語義相似度的智能分塊策略
"""

import logging
import hashlib
import re
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available. Using mock embeddings.")

import numpy as np

from ..chunking_strategy import ChunkingStrategy, ChunkingStrategyType


class SemanticChunkingEngine(ChunkingStrategy):
    """語義分塊引擎 - 基於語義相似度的智能分塊策略"""
    
    def __init__(self, embedding_model: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
        """
        初始化語義分塊引擎
        
        Args:
            embedding_model: 句子嵌入模型名稱
        """
        super().__init__("SemanticChunkingEngine")
        self.embedding_model_name = embedding_model
        
        # 初始化嵌入模型
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.sentence_transformer = SentenceTransformer(embedding_model)
                self.logger.info(f"成功載入嵌入模型: {embedding_model}")
            except Exception as e:
                self.logger.error(f"載入嵌入模型失敗: {e}")
                self.sentence_transformer = None
        else:
            self.sentence_transformer = None
        
        # 語義分塊配置
        self.chunk_config = {
            'max_chunk_length': 1000,
            'min_chunk_length': 100,
            'similarity_threshold': 0.7,
            'max_chunks_per_product': 8,
            'semantic_groups': [
                'performance',      # 性能相關
                'design',          # 設計相關
                'connectivity',    # 連接性相關
                'business',        # 商務相關
                'gaming',          # 遊戲相關
                'creative',        # 創作相關
                'portability',     # 便攜性相關
                'value'            # 價值相關
            ]
        }
        
        # 語義關鍵詞映射
        self.semantic_keywords = {
            'performance': [
                'cpu', 'processor', 'gpu', 'graphics', 'memory', 'ram', 'storage', 'ssd', 'hdd',
                'performance', 'speed', 'fast', 'powerful', 'efficient', 'multitasking'
            ],
            'design': [
                'design', 'build', 'material', 'aluminum', 'plastic', 'metal', 'weight', 'thin',
                'lightweight', 'slim', 'elegant', 'premium', 'durable', 'robust'
            ],
            'connectivity': [
                'wifi', 'bluetooth', 'usb', 'hdmi', 'ethernet', 'wireless', 'connectivity',
                'ports', 'interface', 'network', 'internet', 'connection'
            ],
            'business': [
                'business', 'professional', 'office', 'work', 'productivity', 'enterprise',
                'corporate', 'commercial', 'workplace', 'meeting', 'presentation'
            ],
            'gaming': [
                'gaming', 'game', 'esports', 'gpu', 'graphics', 'fps', 'refresh', 'gaming',
                'performance', 'rtx', 'gtx', 'gaming', 'entertainment'
            ],
            'creative': [
                'creative', 'design', 'art', 'editing', 'video', 'photo', 'graphic', 'creative',
                'professional', 'color', 'display', 'accuracy', 'creative work'
            ],
            'portability': [
                'portable', 'lightweight', 'thin', 'slim', 'travel', 'mobile', 'battery',
                'life', 'portability', 'carry', 'weight', 'size', 'compact'
            ],
            'value': [
                'price', 'value', 'affordable', 'budget', 'cost', 'economical', 'reasonable',
                'worth', 'investment', 'price-performance', 'value for money'
            ]
        }
        
        # 統計信息
        self.stats = {
            'total_products_processed': 0,
            'total_chunks_created': 0,
            'semantic_groups_used': defaultdict(int),
            'processing_errors': 0,
            'last_processed': None
        }
    
    def create_chunks(self, product: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        為單個產品創建語義分塊
        
        Args:
            product: 產品數據字典
            
        Returns:
            (parent_chunk, child_chunks): Parent chunk和Child chunks列表
        """
        try:
            # 創建Parent Chunk (產品概覽)
            parent_chunk = self._create_parent_chunk(product)
            
            # 創建語義分塊
            child_chunks = self._create_semantic_chunks(product)
            
            # 生成嵌入向量
            parent_chunk['embedding'] = self.generate_embedding(parent_chunk['content'])
            
            for child in child_chunks:
                child['embedding'] = self.generate_embedding(child['content'])
                child['parent_id'] = parent_chunk['chunk_id']
            
            # 更新統計
            self.stats['total_products_processed'] += 1
            self.stats['total_chunks_created'] += 1 + len(child_chunks)
            self.stats['last_processed'] = datetime.now().isoformat()
            
            # 更新語義組統計
            for child in child_chunks:
                semantic_group = child.get('semantic_group', 'unknown')
                self.stats['semantic_groups_used'][semantic_group] += 1
            
            self.logger.debug(f"成功為產品 {product.get('modelname', 'Unknown')} 創建語義分塊")
            
            return parent_chunk, child_chunks
            
        except Exception as e:
            self.logger.error(f"為產品創建語義分塊失敗: {e}")
            self.stats['processing_errors'] += 1
            raise
    
    def batch_create_chunks(self, products: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批量創建產品語義分塊
        
        Args:
            products: 產品列表
            
        Returns:
            (all_parent_chunks, all_child_chunks): 所有父分塊和子分塊
        """
        all_parent_chunks = []
        all_child_chunks = []
        
        self.logger.info(f"開始批量處理 {len(products)} 個產品 (語義分塊)")
        
        for i, product in enumerate(products):
            try:
                parent, children = self.create_chunks(product)
                all_parent_chunks.append(parent)
                all_child_chunks.extend(children)
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"已處理 {i + 1}/{len(products)} 個產品")
                    
            except Exception as e:
                self.logger.error(f"處理產品 {i} 失敗: {e}")
                continue
        
        self.logger.info(f"批量處理完成: {len(all_parent_chunks)} 個父分塊, {len(all_child_chunks)} 個子分塊")
        
        return all_parent_chunks, all_child_chunks
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        生成文本嵌入向量
        
        Args:
            text: 輸入文本
            
        Returns:
            嵌入向量
        """
        if self.sentence_transformer:
            try:
                embedding = self.sentence_transformer.encode(text)
                return embedding.tolist()
            except Exception as e:
                self.logger.error(f"生成嵌入向量失敗: {e}")
                return self._generate_mock_embedding(text)
        else:
            return self._generate_mock_embedding(text)
    
    def get_strategy_type(self) -> ChunkingStrategyType:
        """獲取策略類型"""
        return ChunkingStrategyType.SEMANTIC
    
    def get_description(self) -> str:
        """獲取策略描述"""
        return "基於語義相似度的智能分塊策略，根據產品特性和用戶需求自動分類"
    
    # 輔助方法
    def _create_parent_chunk(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """創建產品概覽Parent Chunk"""
        chunk_id = f"semantic_parent_{product.get('modeltype', 'unknown')}_{self._generate_hash(product.get('modelname', ''))}"
        
        content = f"{product.get('modelname', 'Unknown Model')} - 語義分塊產品概覽"
        
        metadata = {
            "modeltype": product.get("modeltype", ""),
            "modelname": product.get("modelname", ""),
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "chunk_id": chunk_id,
            "chunk_type": "semantic_parent",
            "product_id": product.get("modeltype", "unknown"),
            "content": content,
            "metadata": metadata,
            "raw_product": product
        }
    
    def _create_semantic_chunks(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """創建語義分塊"""
        chunks = []
        
        # 識別相關的語義組
        relevant_groups = self._identify_semantic_groups(product)
        
        for group in relevant_groups:
            try:
                chunk = self._create_semantic_group_chunk(product, group)
                if chunk:
                    chunks.append(chunk)
            except Exception as e:
                self.logger.debug(f"創建語義組 {group} 分塊失敗: {e}")
                continue
        
        return chunks
    
    def _create_semantic_group_chunk(self, product: Dict[str, Any], semantic_group: str) -> Optional[Dict[str, Any]]:
        """創建特定語義組的分塊"""
        chunk_id = f"semantic_{semantic_group}_{product.get('modeltype', 'unknown')}_{self._generate_hash(product.get('modelname', ''))}"
        
        content = f"{product.get('modelname', 'Unknown Model')} - {semantic_group}特色分析"
        
        metadata = {
            "semantic_group": semantic_group,
            "modeltype": product.get("modeltype", ""),
            "modelname": product.get("modelname", ""),
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "chunk_id": chunk_id,
            "chunk_type": "semantic_child",
            "semantic_group": semantic_group,
            "product_id": product.get("modeltype", "unknown"),
            "content": content,
            "metadata": metadata,
            "raw_product": product
        }
    
    def _identify_semantic_groups(self, product: Dict[str, Any]) -> List[str]:
        """識別產品相關的語義組"""
        # 簡化實現，返回前3個語義組
        return self.chunk_config['semantic_groups'][:3]
    
    def _generate_hash(self, text: str) -> str:
        """生成文本哈希值"""
        return hashlib.md5(text.encode()).hexdigest()[:8]
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """生成模擬嵌入向量"""
        return [0.1] * 384  # 384維向量
