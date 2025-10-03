#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Chunking Strategy模式
"""

import sys
import logging
from pathlib import Path

# 設置詳細日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加libs目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent / 'libs'))

def test_chunking_strategy():
    """測試Chunking Strategy模式"""
    print("=== 測試Chunking Strategy模式 ===\n")
    
    try:
        # 導入必要模組
        from mgfd_cursor.chunking import (
            ChunkingContext, 
            ChunkingStrategyType,
            ProductChunkingEngine,
            SemanticChunkingEngine
        )
        
        print("1. 測試Strategy模式導入...")
        print("   ✅ 成功導入ChunkingContext")
        print("   ✅ 成功導入ChunkingStrategyType")
        print("   ✅ 成功導入ProductChunkingEngine")
        print("   ✅ 成功導入SemanticChunkingEngine")
        
        print("\n2. 測試Parent-Child Strategy...")
        
        # 創建parent_child策略
        parent_child_engine = ProductChunkingEngine()
        print(f"   ✅ 成功創建Parent-Child引擎: {parent_child_engine.strategy_name}")
        print(f"   策略類型: {parent_child_engine.get_strategy_type().value}")
        print(f"   策略描述: {parent_child_engine.get_description()}")
        
        print("\n3. 測試Semantic Strategy...")
        
        # 創建semantic策略
        semantic_engine = SemanticChunkingEngine()
        print(f"   ✅ 成功創建Semantic引擎: {semantic_engine.strategy_name}")
        print(f"   策略類型: {semantic_engine.get_strategy_type().value}")
        print(f"   策略描述: {semantic_engine.get_description()}")
        
        print("\n4. 測試ChunkingContext...")
        
        # 創建context並設置策略
        context = ChunkingContext(parent_child_engine)
        print(f"   ✅ 成功創建ChunkingContext")
        
        # 添加semantic策略
        context.set_strategy(semantic_engine)
        print(f"   ✅ 成功添加Semantic策略")
        
        # 獲取可用策略
        available_strategies = context.get_available_strategies()
        print(f"   📋 可用策略數量: {len(available_strategies)}")
        for strategy in available_strategies:
            print(f"      - {strategy['strategy_name']}: {strategy['strategy_type'].value}")
        
        print("\n5. 測試策略切換...")
        
        # 切換到parent_child策略
        context.switch_strategy(ChunkingStrategyType.PARENT_CHILD)
        current_strategy = context.get_strategy()
        print(f"   ✅ 切換到Parent-Child策略: {current_strategy.strategy_name}")
        
        # 切換到semantic策略
        context.switch_strategy(ChunkingStrategyType.SEMANTIC)
        current_strategy = context.get_strategy()
        print(f"   ✅ 切換到Semantic策略: {current_strategy.strategy_name}")
        
        print("\n6. 測試產品分塊...")
        
        # 測試產品數據
        test_product = {
            "modeltype": "839",
            "modelname": "AKK839",
            "cpu": "Intel Core i3-1215U",
            "gpu": "Intel UHD Graphics",
            "memory": "4GB DDR4",
            "storage": "128GB SSD",
            "lcd": "14\" HD (1366x768)",
            "structconfig": "Budget Notebook, 1.6kg"
        }
        
        # 使用parent_child策略創建分塊
        context.switch_strategy(ChunkingStrategyType.PARENT_CHILD)
        parent_chunk, child_chunks = context.create_chunks(test_product)
        print(f"   ✅ Parent-Child策略創建分塊:")
        print(f"      Parent chunk: {parent_chunk['chunk_id']}")
        print(f"      Child chunks: {len(child_chunks)} 個")
        
        # 使用semantic策略創建分塊
        context.switch_strategy(ChunkingStrategyType.SEMANTIC)
        parent_chunk, child_chunks = context.create_chunks(test_product)
        print(f"   ✅ Semantic策略創建分塊:")
        print(f"      Parent chunk: {parent_chunk['chunk_id']}")
        print(f"      Child chunks: {len(child_chunks)} 個")
        
        print("\n7. 測試批量處理...")
        
        test_products = [test_product]
        
        # 批量處理
        all_parents, all_children = context.batch_create_chunks(test_products)
        print(f"   ✅ 批量處理完成:")
        print(f"      Parent chunks: {len(all_parents)} 個")
        print(f"      Child chunks: {len(all_children)} 個")
        
        print("\n8. 測試嵌入向量生成...")
        
        test_text = "這是一個測試文本"
        embedding = context.generate_embedding(test_text)
        print(f"   ✅ 嵌入向量生成成功:")
        print(f"      向量維度: {len(embedding)}")
        print(f"      向量類型: {type(embedding)}")
        
        print("\n9. 測試策略信息...")
        
        for strategy in available_strategies:
            print(f"   📋 {strategy['strategy_name']}:")
            print(f"      類型: {strategy['strategy_type'].value}")
            print(f"      描述: {strategy['description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chunking_strategy()
    if success:
        print("\n🎉 Chunking Strategy模式測試完成！")
        print("📋 測試摘要:")
        print("   - Strategy模式架構成功實作")
        print("   - Parent-Child和Semantic策略都正常工作")
        print("   - ChunkingContext可以動態切換策略")
        print("   - 所有分塊功能正常運作")
    else:
        print("\n💥 測試失敗")
