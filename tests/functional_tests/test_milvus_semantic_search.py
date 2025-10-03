#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Milvus 向量搜索和 Parent-Child Chunking 功能測試程式
測試不同查詢字串的搜索效果
"""

import sys
import os
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import logging
from datetime import datetime
from libs.KnowledgeManageHandler.knowledge_manager import KnowledgeManager

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MilvusSearchTester:
    """Milvus 搜索功能測試器"""
    
    def __init__(self):
        """初始化測試器"""
        self.km = None
        self.test_queries = [
            "輕便筆電推薦",
            "高效能遊戲筆電", 
            "商務用筆記型電腦",
            "平價學生筆電",
            "創意設計筆電",
            "長續航力筆電",
            "觸控螢幕筆電",
            "2合1變形筆電",
            "小尺寸筆電",
            "大螢幕筆電"
        ]
        
    def initialize_knowledge_manager(self):
        """初始化知識管理器"""
        try:
            logger.info("=== 初始化知識管理器 ===")
            self.km = KnowledgeManager()
            logger.info("知識管理器初始化完成")
            
            # 檢查各組件狀態
            milvus_status = self.km.get_milvus_status()
            llm_status = self.km.get_llm_status()
            
            logger.info(f"Milvus 狀態: {milvus_status.get('milvus_available', False)}")
            logger.info(f"LLM 狀態: {llm_status.get('llm_available', False)}")
            
            return True
            
        except Exception as e:
            logger.error(f"知識管理器初始化失敗: {e}")
            return False
    
    def test_milvus_connection(self):
        """測試 Milvus 連接和集合狀態"""
        try:
            logger.info("=== 測試 Milvus 連接 ===")
            
            status = self.km.get_milvus_status()
            
            print(f"Milvus 可用: {status.get('milvus_available', False)}")
            print(f"Milvus 查詢器已初始化: {status.get('milvus_query_initialized', False)}")
            
            if status.get('collection_name'):
                print(f"Collection 名稱: {status['collection_name']}")
                print(f"Collection 已載入: {status.get('collection_loaded', False)}")
                print(f"Schema 字段數: {status.get('schema_fields', 0)}")
                print(f"字段名稱: {status.get('field_names', [])}")
            
            return status.get('milvus_query_initialized', False)
            
        except Exception as e:
            logger.error(f"測試 Milvus 連接失敗: {e}")
            return False
    
    def test_basic_semantic_search(self, query: str, top_k: int = 3):
        """測試基本語義搜索"""
        try:
            logger.info(f"--- 基本語義搜索: '{query}' ---")
            
            results = self.km.milvus_semantic_search(query, top_k=top_k)
            
            if results:
                print(f"✅ 找到 {len(results)} 個結果:")
                for i, result in enumerate(results, 1):
                    print(f"  結果 {i}:")
                    print(f"    Chunk ID: {result['chunk_id']}")
                    print(f"    產品 ID: {result['product_id']}")
                    print(f"    Chunk 類型: {result['chunk_type']}")
                    print(f"    相似度: {result['similarity_score']:.3f}")
                    print(f"    內容: {result['content'][:100]}...")
                    print("")
            else:
                print("❌ 未找到相關結果")
            
            return results
            
        except Exception as e:
            logger.error(f"基本語義搜索失敗: {e}")
            return None
    
    def test_parent_child_retrieval(self, query: str):
        """測試 Parent-Child Chunking 檢索"""
        try:
            logger.info(f"--- Parent-Child 檢索: '{query}' ---")
            
            results = self.km.parent_child_retrieval(query, child_top_k=5, parent_top_k=2)
            
            if results:
                print(f"✅ Parent-Child 檢索結果:")
                print(f"  子chunks數量: {results['total_child_chunks']}")
                print(f"  父documents數量: {results['total_parent_docs']}")
                
                # 顯示最相關的子chunks
                print("  最相關的子chunks:")
                for i, child in enumerate(results['child_chunks'][:3], 1):
                    print(f"    {i}. 產品ID: {child['product_id']}, 相似度: {child['similarity_score']:.3f}")
                    print(f"       內容: {child['content'][:80]}...")
                
                # 顯示對應的父documents
                if results['parent_documents']:
                    print("  對應的父documents:")
                    for parent in results['parent_documents']:
                        print(f"    產品ID: {parent['product_id']}")
                        print(f"    內容: {parent['content'][:100]}...")
            else:
                print("❌ 未找到相關結果")
            
            return results
            
        except Exception as e:
            logger.error(f"Parent-Child 檢索失敗: {e}")
            return None
    
    def test_hybrid_search(self, query: str):
        """測試混合搜索（僅向量檢索，無 LLM）"""
        try:
            logger.info(f"--- 混合搜索（無 LLM）: '{query}' ---")

            results = self.km.hybrid_search(query, use_parent_child=True, top_k=3)
            
            if results:
                print(f"✅ 混合搜索結果:")
                print(f"  搜索方法: {results['search_method']}")
                print(f"  查詢: {results['query']}")
                
                if results['search_results']:
                    search_data = results['search_results']
                    if isinstance(search_data, dict) and 'child_chunks' in search_data:
                        print(f"  找到 {search_data['total_child_chunks']} 個相關片段")
                    
                # 顯示截斷的上下文（原先為 LLM 用）
                ctx = results.get('context_used', '')
                if ctx:
                    print("  使用的上下文片段:")
                    print(f"    {ctx[:300]}...")
            else:
                print("❌ 混合搜索失敗")
            
            return results
            
        except Exception as e:
            logger.error(f"混合搜索失敗: {e}")
            return None
    
    def test_different_chunk_types(self, query: str):
        """測試不同的chunk類型搜索"""
        try:
            logger.info(f"--- 測試不同 Chunk 類型: '{query}' ---")
            
            # 測試僅搜索child chunks
            child_results = self.km.milvus_semantic_search(query, top_k=3, chunk_type_filter="child")
            print(f"Child chunks 結果數量: {len(child_results) if child_results else 0}")
            
            # 測試僅搜索parent documents
            parent_results = self.km.milvus_semantic_search(query, top_k=3, chunk_type_filter="parent")
            print(f"Parent documents 結果數量: {len(parent_results) if parent_results else 0}")
            
            # 測試不過濾chunk類型
            all_results = self.km.milvus_semantic_search(query, top_k=5)
            print(f"全部結果數量: {len(all_results) if all_results else 0}")
            
            if all_results:
                chunk_types = [r['chunk_type'] for r in all_results]
                print(f"Chunk類型分布: {set(chunk_types)}")
            
            return {
                'child_results': child_results,
                'parent_results': parent_results,
                'all_results': all_results
            }
            
        except Exception as e:
            logger.error(f"測試不同chunk類型失敗: {e}")
            return None
    
    def run_comprehensive_test(self):
        """執行全面的測試"""
        try:
            logger.info("=== 開始全面測試 ===")
            
            # 1. 初始化
            if not self.initialize_knowledge_manager():
                logger.error("知識管理器初始化失敗，結束測試")
                return
            
            # 2. 測試連接
            if not self.test_milvus_connection():
                logger.error("Milvus 連接測試失敗，結束測試")
                return
            
            # 3. 對每個測試查詢進行測試
            for i, query in enumerate(self.test_queries, 1):
                print(f"\n{'='*60}")
                print(f"測試查詢 {i}/{len(self.test_queries)}: {query}")
                print(f"{'='*60}")
                
                # 基本語義搜索
                basic_results = self.test_basic_semantic_search(query)
                
                # Parent-Child 檢索
                if basic_results:
                    pc_results = self.test_parent_child_retrieval(query)
                    
                    # 混合搜索（無 LLM，只對前幾個查詢測試以節省時間）
                    if i <= 3:
                        hybrid_results = self.test_hybrid_search(query)
                
                # 測試不同chunk類型（只對第一個查詢詳細測試）
                if i == 1:
                    chunk_type_results = self.test_different_chunk_types(query)
                
                # 為避免過於頻繁查詢，添加短暫延遲
                import time
                time.sleep(1)
            
            logger.info("=== 全面測試完成 ===")
            
        except Exception as e:
            logger.error(f"全面測試過程發生錯誤: {e}")
    
    def run_single_query_test(self, query: str):
        """對單一查詢進行詳細測試"""
        try:
            logger.info(f"=== 單一查詢詳細測試: '{query}' ===")
            
            # 初始化
            if not self.initialize_knowledge_manager():
                return
            
            if not self.test_milvus_connection():
                return
            
            print(f"\n對查詢 '{query}' 進行詳細測試:")
            print("-" * 50)
            
            # 1. 基本語義搜索
            basic_results = self.test_basic_semantic_search(query, top_k=5)
            
            # 2. Parent-Child 檢索
            pc_results = self.test_parent_child_retrieval(query)
            
            # 3. 混合搜索（無 LLM）
            hybrid_results = self.test_hybrid_search(query)
            
            # 4. 不同chunk類型測試
            chunk_type_results = self.test_different_chunk_types(query)
            
            logger.info("單一查詢測試完成")
            
        except Exception as e:
            logger.error(f"單一查詢測試失敗: {e}")


def main():
    """主函數"""
    tester = MilvusSearchTester()
    
    # 檢查命令列參數
    if len(sys.argv) > 1:
        # 如果提供了查詢參數，進行單一查詢測試
        query = " ".join(sys.argv[1:])
        tester.run_single_query_test(query)
    else:
        # 否則進行全面測試
        print("開始進行 Milvus 語義搜索功能全面測試...")
        print("如需測試特定查詢，請使用: python test_milvus_semantic_search.py \"您的查詢\"")
        print("")
        
        tester.run_comprehensive_test()


if __name__ == "__main__":
    main()
