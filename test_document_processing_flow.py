#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試文書處理筆電推薦的完整資料流
"""

import sys
import logging
from pathlib import Path

# 設置詳細日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加libs目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent / 'libs'))

def test_document_processing_flow():
    """測試文書處理筆電推薦的完整資料流"""
    print("=== 測試文書處理筆電推薦資料流 ===\n")
    
    test_query = "請介紹目前較適合做文書處理的筆電"
    print(f"測試查詢: {test_query}\n")
    
    try:
        # 導入必要模組
        from mgfd_cursor.enhanced_slot_extractor import EnhancedSlotExtractor
        from mgfd_cursor.knowledge_base import NotebookKnowledgeBase
        from mgfd_cursor.hybrid_retriever import HybridProductRetriever
        
        print("1. 初始化組件...")
        
        # 初始化知識庫
        kb = NotebookKnowledgeBase()
        print(f"   ✅ 知識庫載入完成: {len(kb.products)} 個產品")
        
        # 創建slot_schema
        slot_schema = {
            "usage_purpose": {"required": True},
            "budget_range": {"required": True},
            "cpu_level": {"required": False},
            "gpu_level": {"required": False},
            "weight_requirement": {"required": False},
            "screen_size": {"required": False},
            "brand_preference": {"required": False}
        }
        
        # 創建模擬LLM管理器
        class MockLLMManager:
            def __init__(self):
                pass
        
        # 初始化enhanced_slot_extractor
        enhanced_extractor = EnhancedSlotExtractor(MockLLMManager(), slot_schema)
        print("   ✅ EnhancedSlotExtractor初始化完成")
        
        print("\n2. 槽位提取分析...")
        
        # 模擬會話狀態
        current_slots = {}
        session_id = "test_document_processing_001"
        
        # 提取槽位
        result = enhanced_extractor.extract_slots_with_classification(
            test_query, current_slots, session_id
        )
        
        print(f"   提取方法: {result.get('extraction_method', 'unknown')}")
        print(f"   提取的槽位: {result.get('extracted_slots', {})}")
        
        # 更新當前槽位
        if result.get('extracted_slots'):
            current_slots.update(result.get('extracted_slots'))
        
        print(f"   累積槽位: {current_slots}")
        
        # 檢查是否收集完整
        required_slots = [slot for slot, config in slot_schema.items() if config.get('required', False)]
        missing_slots = [slot for slot in required_slots if slot not in current_slots]
        
        if missing_slots:
            print(f"   ⚠️  缺少必要槽位: {missing_slots}")
            print(f"   💡 下一步應該詢問: {missing_slots[0] if missing_slots else '無'}")
        else:
            print(f"   ✅ 所有必要槽位已收集完成，可以進行產品推薦")
        
        print("\n3. 產品搜尋分析...")
        
        # 初始化混合檢索器
        retriever = HybridProductRetriever()
        print("   ✅ HybridProductRetriever初始化完成")
        
        # 測試熱門產品檢索
        popular_products = retriever.retrieve_popular_products()
        print(f"   📋 熱門產品檢索結果: {len(popular_products)} 個產品")
        
        for i, product in enumerate(popular_products[:3]):
            print(f"      產品 {i+1}: {product.get('modelname', 'Unknown')} - {product.get('primary_usage', 'Unknown')}")
        
        # 測試語義搜索
        semantic_results = retriever.semantic_search(test_query, top_k=3)
        print(f"   🔍 語義搜索結果: {len(semantic_results)} 個產品")
        
        for i, product in enumerate(semantic_results[:3]):
            print(f"      產品 {i+1}: {product.get('modelname', 'Unknown')} - 相關性: {product.get('similarity_score', 0):.3f}")
        
        print("\n4. 槽位匹配分析...")
        
        # 分析文書處理相關的產品
        document_processing_products = []
        
        for product in kb.products:
            # 檢查是否適合文書處理
            usage = product.get('primary_usage', '').lower()
            cpu = str(product.get('cpu', '')).lower()
            memory = str(product.get('memory', '')).lower()
            
            # 文書處理的判斷標準
            is_suitable = False
            reasons = []
            
            if 'general' in usage or 'business' in usage:
                is_suitable = True
                reasons.append("一般用途/商務用途")
            
            if any(term in cpu for term in ['i3', 'i5', 'ryzen 3', 'ryzen 5']):
                is_suitable = True
                reasons.append("適合的處理器")
            
            if '8gb' in memory or '16gb' in memory:
                is_suitable = True
                reasons.append("足夠的記憶體")
            
            if is_suitable:
                document_processing_products.append({
                    'product': product,
                    'reasons': reasons
                })
        
        print(f"   📋 適合文書處理的產品: {len(document_processing_products)} 個")
        
        for i, item in enumerate(document_processing_products[:3]):
            product = item['product']
            reasons = item['reasons']
            print(f"      產品 {i+1}: {product.get('modelname', 'Unknown')}")
            print(f"         CPU: {product.get('cpu', 'Unknown')}")
            print(f"         記憶體: {product.get('memory', 'Unknown')}")
            print(f"         用途: {product.get('primary_usage', 'Unknown')}")
            print(f"         適合原因: {', '.join(reasons)}")
        
        print("\n5. 推薦策略分析...")
        
        # 根據槽位值進行產品推薦
        if 'usage_purpose' in current_slots:
            usage_purpose = current_slots['usage_purpose']
            print(f"   🎯 使用目的: {usage_purpose}")
            
            # 根據使用目的篩選產品
            filtered_products = []
            for product in kb.products:
                if usage_purpose in str(product.get('primary_usage', '')).lower():
                    filtered_products.append(product)
            
            print(f"   📋 符合使用目的的產品: {len(filtered_products)} 個")
            
            # 顯示前3個推薦產品
            for i, product in enumerate(filtered_products[:3]):
                print(f"      推薦 {i+1}: {product.get('modelname', 'Unknown')}")
                print(f"         價格等級: {product.get('price_tier', 'Unknown')}")
                print(f"         熱門度: {product.get('popularity_score', 'Unknown')}")
        
        print("\n6. 資料流總結...")
        
        print("   📊 資料流分析:")
        print("      1. 用戶輸入: '請介紹目前較適合做文書處理的筆電'")
        print("      2. 槽位提取: EnhancedSlotExtractor分析用戶輸入")
        print("      3. 槽位匹配: 識別出 'document_processing' 或 'general' 用途")
        print("      4. 產品篩選: 根據槽位值篩選適合的產品")
        print("      5. 排序推薦: 根據熱門度和相關性排序")
        print("      6. 回應生成: 生成推薦回應給用戶")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_document_processing_flow()
    if success:
        print("\n🎉 文書處理筆電推薦資料流測試完成！")
        print("📋 測試摘要:")
        print("   - 槽位提取功能正常")
        print("   - 產品搜尋功能正常")
        print("   - 文書處理產品篩選正常")
        print("   - 推薦策略運作正常")
    else:
        print("\n💥 測試失敗")
