#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試RAG系統初始化
"""

import sys
from pathlib import Path

# 添加libs目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent / 'libs'))

def test_rag_system():
    """測試RAG系統初始化"""
    print("=== 測試RAG系統初始化 ===\n")
    
    try:
        # 測試hybrid_retriever初始化
        from mgfd_cursor.hybrid_retriever import HybridProductRetriever
        from mgfd_cursor.chunking import ProductChunkingEngine
        
        print("1. 初始化分塊引擎...")
        chunking_engine = ProductChunkingEngine()
        
        print("2. 初始化混合檢索器...")
        retriever = HybridProductRetriever(chunking_engine)
        
        print("3. 測試熱門產品檢索...")
        popular_products = retriever.retrieve_popular_products()
        
        print(f"   檢索到 {len(popular_products)} 個熱門產品")
        
        if popular_products:
            print("4. 檢查前3個熱門產品:")
            for i, product in enumerate(popular_products[:3]):
                print(f"   產品 {i+1}:")
                print(f"     ID: {product.get('id', 'N/A')}")
                print(f"     modelname: {product.get('modelname', 'N/A')}")
                print(f"     modeltype: {product.get('modeltype', 'N/A')}")
                print(f"     popularity_score: {product.get('popularity_score', 'N/A')}")
                print(f"     primary_usage: {product.get('primary_usage', 'N/A')}")
                print(f"     price_tier: {product.get('price_tier', 'N/A')}")
                print()
        else:
            print("❌ 沒有檢索到熱門產品")
            return False
        
        print("5. 測試語義搜索...")
        search_results = retriever.semantic_search("遊戲筆電", top_k=3)
        print(f"   語義搜索結果: {len(search_results)} 個產品")
        
        print("\n✅ RAG系統初始化測試完成")
        return True
        
    except Exception as e:
        print(f"❌ RAG系統測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_system()
    if success:
        print("\n🎉 RAG系統初始化成功！")
    else:
        print("\n💥 RAG系統初始化失敗")
