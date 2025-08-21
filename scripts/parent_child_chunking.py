#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parent-Child Chunking引擎
為筆電規格資料建立分層分塊結構
"""

import logging
import hashlib
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NotebookParentChildChunker:
    """筆電規格Parent-Child Chunking引擎"""
    
    def __init__(self):
        self.chunk_config = {
            'max_parent_length': 2000,
            'max_child_length': 800,
            'min_chunk_length': 100
        }
        
        # 統計資訊
        self.stats = {
            'total_products_processed': 0,
            'total_chunks_created': 0,
            'parent_chunks': 0,
            'child_chunks': 0,
            'processing_errors': 0
        }
    
    def create_parent_child_chunks(self, product_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        為單個產品創建Parent-Child chunks
        
        Args:
            product_data: 產品資料字典
            
        Returns:
            (parent_chunk, child_chunks): Parent chunk和Child chunks列表
        """
        try:
            # 創建Parent Chunk
            parent_chunk = self._create_parent_chunk(product_data)
            
            # 創建Child Chunks
            child_chunks = [
                self._create_performance_chunk(product_data),
                self._create_design_chunk(product_data),
                self._create_connectivity_chunk(product_data),
                self._create_business_chunk(product_data)
            ]
            
            # 過濾掉空的child chunks
            child_chunks = [chunk for chunk in child_chunks if chunk and chunk.get('content')]
            
            # 更新統計
            self.stats['total_products_processed'] += 1
            self.stats['parent_chunks'] += 1
            self.stats['child_chunks'] += len(child_chunks)
            self.stats['total_chunks_created'] += 1 + len(child_chunks)
            
            logger.debug(f"成功為產品 {product_data.get('modelname', 'Unknown')} 創建分塊")
            
            return parent_chunk, child_chunks
            
        except Exception as e:
            logger.error(f"為產品創建分塊失敗: {e}")
            self.stats['processing_errors'] += 1
            raise
    
    def _create_parent_chunk(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建Parent Chunk - 產品完整摘要"""
        try:
            # 提取關鍵資訊並確保是string類型
            modeltype = str(product_data.get('modeltype', ''))
            modelname = str(product_data.get('modelname', ''))
            version = str(product_data.get('version', ''))
            cpu = str(product_data.get('cpu', ''))
            gpu = str(product_data.get('gpu', ''))
            memory = str(product_data.get('memory', ''))
            storage = str(product_data.get('storage', ''))
            
            # 創建產品摘要
            summary_parts = []
            if modeltype and modeltype.strip() and modeltype.lower() != 'nan':
                summary_parts.append(f"型號系列: {modeltype}")
            if modelname and modelname.strip() and modelname.lower() != 'nan':
                summary_parts.append(f"產品名稱: {modelname}")
            if version and version.strip() and version.lower() != 'nan':
                summary_parts.append(f"版本: {version}")
            if cpu and cpu.strip() and cpu.lower() not in ['nan', 'no data']:
                summary_parts.append(f"處理器: {cpu[:100]}...")
            if gpu and gpu.strip() and gpu.lower() not in ['nan', 'no data']:
                summary_parts.append(f"顯示卡: {gpu[:100]}...")
            if memory and memory.strip() and memory.lower() not in ['nan', 'no data']:
                summary_parts.append(f"記憶體: {memory[:100]}...")
            if storage and storage.strip() and storage.lower() not in ['nan', 'no data']:
                summary_parts.append(f"儲存: {storage[:100]}...")
            
            parent_content = " | ".join(summary_parts)
            
            # 如果內容太長，進行截斷
            if len(parent_content) > self.chunk_config['max_parent_length']:
                parent_content = parent_content[:self.chunk_config['max_parent_length']] + "..."
            
            parent_chunk = {
                'chunk_id': f"parent_{modelname}_{hashlib.md5(str(product_data).encode()).hexdigest()[:8]}",
                'chunk_type': 'parent',
                'content': parent_content,
                'product_id': modelname,
                'modeltype': modeltype,
                'source': str(product_data.get('source_file', '')),
                'metadata': {
                    'cpu_summary': cpu[:200] if cpu and cpu.strip() and cpu.lower() not in ['nan', 'no data'] else '',
                    'gpu_summary': gpu[:200] if gpu and gpu.strip() and gpu.lower() not in ['nan', 'no data'] else '',
                    'memory_summary': memory[:200] if memory and memory.strip() and memory.lower() not in ['nan', 'no data'] else '',
                    'storage_summary': storage[:200] if storage and storage.strip() and storage.lower() not in ['nan', 'no data'] else ''
                }
            }
            
            return parent_chunk
            
        except Exception as e:
            logger.error(f"創建Parent Chunk失敗: {e}")
            raise
    
    def _create_performance_chunk(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建效能規格Chunk"""
        try:
            performance_fields = ['cpu', 'gpu', 'memory', 'storage', 'thermal']
            content_parts = []
            
            for field in performance_fields:
                value = product_data.get(field, '')
                if value and str(value).strip() and str(value).lower() != 'no data':
                    content_parts.append(f"{field.upper()}: {value}")
            
            if not content_parts:
                return None
            
            content = " | ".join(content_parts)
            if len(content) > self.chunk_config['max_child_length']:
                content = content[:self.chunk_config['max_child_length']] + "..."
            
            return {
                'chunk_id': f"perf_{product_data.get('modelname', 'unknown')}_{hashlib.md5(content.encode()).hexdigest()[:8]}",
                'chunk_type': 'performance',
                'content': content,
                'product_id': product_data.get('modelname', ''),
                'modeltype': product_data.get('modeltype', ''),
                'source': product_data.get('source_file', ''),
                'parent_id': f"parent_{product_data.get('modelname', 'unknown')}_{hashlib.md5(str(product_data).encode()).hexdigest()[:8]}"
            }
            
        except Exception as e:
            logger.error(f"創建效能Chunk失敗: {e}")
            return None
    
    def _create_design_chunk(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建設計特徵Chunk"""
        try:
            design_fields = ['lcd', 'touchpanel', 'keyboard', 'webcamera', 'touchpad', 'fingerprint']
            content_parts = []
            
            for field in design_fields:
                value = product_data.get(field, '')
                if value and str(value).strip() and str(value).lower() != 'no data':
                    content_parts.append(f"{field.upper()}: {value}")
            
            if not content_parts:
                return None
            
            content = " | ".join(content_parts)
            if len(content) > self.chunk_config['max_child_length']:
                content = content[:self.chunk_config['max_child_length']] + "..."
            
            return {
                'chunk_id': f"design_{product_data.get('modelname', 'unknown')}_{hashlib.md5(content.encode()).hexdigest()[:8]}",
                'chunk_type': 'design',
                'content': content,
                'product_id': product_data.get('modelname', ''),
                'modeltype': product_data.get('modeltype', ''),
                'source': product_data.get('source_file', ''),
                'parent_id': f"parent_{product_data.get('modelname', 'unknown')}_{hashlib.md5(str(product_data).encode()).hexdigest()[:8]}"
            }
            
        except Exception as e:
            logger.error(f"創建設計Chunk失敗: {e}")
            return None
    
    def _create_connectivity_chunk(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建連接性Chunk"""
        try:
            connectivity_fields = ['iointerface', 'wireless', 'lan', 'bluetooth', 'lte', 'wifi', 'usb']
            content_parts = []
            
            for field in connectivity_fields:
                value = product_data.get(field, '')
                if value and str(value).strip() and str(value).lower() != 'no data':
                    content_parts.append(f"{field.upper()}: {value}")
            
            if not content_parts:
                return None
            
            content = " | ".join(content_parts)
            if len(content) > self.chunk_config['max_child_length']:
                content = content[:self.chunk_config['max_child_length']] + "..."
            
            return {
                'chunk_id': f"conn_{product_data.get('modelname', 'unknown')}_{hashlib.md5(content.encode()).hexdigest()[:8]}",
                'chunk_type': 'connectivity',
                'content': content,
                'product_id': product_data.get('modelname', ''),
                'modeltype': product_data.get('modeltype', ''),
                'source': product_data.get('source_file', ''),
                'parent_id': f"parent_{product_data.get('modelname', 'unknown')}_{hashlib.md5(str(product_data).encode()).hexdigest()[:8]}"
            }
            
        except Exception as e:
            logger.error(f"創建連接性Chunk失敗: {e}")
            return None
    
    def _create_business_chunk(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建商務特徵Chunk"""
        try:
            business_fields = ['softwareconfig', 'ai', 'accessory', 'certifications', 'pm', 'devtime']
            content_parts = []
            
            for field in business_fields:
                value = product_data.get(field, '')
                if value and str(value).strip() and str(value).lower() != 'no data':
                    content_parts.append(f"{field.upper()}: {value}")
            
            if not content_parts:
                return None
            
            content = " | ".join(content_parts)
            if len(content) > self.chunk_config['max_child_length']:
                content = content[:self.chunk_config['max_child_length']] + "..."
            
            return {
                'chunk_id': f"biz_{product_data.get('modelname', 'unknown')}_{hashlib.md5(content.encode()).hexdigest()[:8]}",
                'chunk_type': 'business',
                'content': content,
                'product_id': product_data.get('modelname', ''),
                'modeltype': product_data.get('modeltype', ''),
                'source': product_data.get('source_file', ''),
                'parent_id': f"parent_{product_data.get('modelname', 'unknown')}_{hashlib.md5(str(product_data).encode()).hexdigest()[:8]}"
            }
            
        except Exception as e:
            logger.error(f"創建商務Chunk失敗: {e}")
            return None
    
    def batch_create_chunks(self, products: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批次創建chunks
        
        Args:
            products: 產品資料列表
            
        Returns:
            (parent_chunks, child_chunks): 所有parent和child chunks
        """
        all_parent_chunks = []
        all_child_chunks = []
        
        logger.info(f"開始批次處理 {len(products)} 個產品")
        
        for i, product in enumerate(products, 1):
            try:
                logger.debug(f"處理產品 {i}/{len(products)}: {product.get('modelname', 'Unknown')}")
                
                parent_chunk, child_chunks = self.create_parent_child_chunks(product)
                all_parent_chunks.append(parent_chunk)
                all_child_chunks.extend(child_chunks)
                
                if i % 10 == 0:
                    logger.info(f"已處理 {i}/{len(products)} 個產品")
                    
            except Exception as e:
                logger.error(f"處理產品 {i} 失敗: {e}")
                continue
        
        logger.info(f"批次處理完成: {len(all_parent_chunks)} 個parent chunks, {len(all_child_chunks)} 個child chunks")
        
        return all_parent_chunks, all_child_chunks
    
    def get_stats(self) -> Dict[str, Any]:
        """取得處理統計資訊"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置統計資訊"""
        self.stats = {
            'total_products_processed': 0,
            'total_chunks_created': 0,
            'parent_chunks': 0,
            'child_chunks': 0,
            'processing_errors': 0
        }

def main():
    """測試函數"""
    chunker = NotebookParentChildChunker()
    
    # 測試資料
    test_product = {
        'modeltype': '27',
        'modelname': 'AB27',
        'version': 'Version: MP_v1.0',
        'cpu': 'Intel Core i5-12400',
        'gpu': 'Intel UHD Graphics 730',
        'memory': '16GB DDR4',
        'storage': '512GB NVMe SSD',
        'lcd': '15.6" FHD',
        'source_file': 'test.csv'
    }
    
    try:
        parent_chunk, child_chunks = chunker.create_parent_child_chunks(test_product)
        
        print("✅ Parent Chunk:")
        print(f"  ID: {parent_chunk['chunk_id']}")
        print(f"  Content: {parent_chunk['content'][:100]}...")
        
        print(f"\n✅ Child Chunks ({len(child_chunks)}):")
        for i, chunk in enumerate(child_chunks, 1):
            print(f"  {i}. {chunk['chunk_type']}: {chunk['content'][:80]}...")
        
        print(f"\n📊 統計資訊: {chunker.get_stats()}")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    main()
