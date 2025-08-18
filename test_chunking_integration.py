#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Chunking整合後的搜尋功能
"""

import sys
import os
import json
import logging
from typing import Dict, Any

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_chunking_integration():
    """測試Chunking整合功能"""
    print("=" * 80)
    print("MGFD Chunking整合測試")
    print("=" * 80)
    
    try:
        # 步驟1：測試NotebookKnowledgeBase初始化
        print("\n步驟1：測試NotebookKnowledgeBase整合chunking初始化")
        
        from libs.mgfd_cursor.knowledge_base import NotebookKnowledgeBase
        
        print("- 初始化知識庫（包含chunking引擎）...")
        kb = NotebookKnowledgeBase()
        
        # 檢查chunking相關屬性
        print(f"- Chunking引擎狀態: {'✅ 正常' if hasattr(kb, 'chunking_engine') else '❌ 缺失'}")
        print(f"- 產品數量: {len(kb.products)}")
        
        if hasattr(kb, 'parent_chunks') and hasattr(kb, 'child_chunks'):
            print(f"- 父分塊數量: {len(kb.parent_chunks)}")
            print(f"- 子分塊數量: {len(kb.child_chunks)}")
            print(f"- 嵌入向量數量: {len(kb.chunk_embeddings)}")
        
        # 步驟2：測試Case-1槽位搜尋
        print("\n步驟2：測試Case-1槽位搜尋")
        
        case_1_slots = {
            "usage_purpose": "document_processing",
            "portability": "light"
        }
        
        print(f"- 測試槽位: {case_1_slots}")
        search_results = kb.search_products(case_1_slots)
        
        print(f"- 搜尋結果數量: {len(search_results)}")
        
        if search_results:
            print("\n前3個搜尋結果:")
            for i, product in enumerate(search_results[:3], 1):
                print(f"\n  {i}. {product.get('modelname', 'Unknown')}")
                print(f"     型號: {product.get('modeltype', 'N/A')}")
                print(f"     CPU: {product.get('cpu', 'N/A')[:50]}...")
                
                # 顯示chunking特有的資訊
                if 'similarity_score' in product:
                    print(f"     相似度: {product['similarity_score']:.2%}")
                if 'match_reasons' in product:
                    print(f"     匹配原因: {', '.join(product['match_reasons'])}")
                if 'match_type' in product:
                    print(f"     匹配類型: {product['match_type']}")
        
        # 步驟3：測試其他搜尋場景
        print("\n步驟3：測試其他搜尋場景")
        
        test_scenarios = [
            {
                "name": "高效能遊戲需求",
                "slots": {"usage_purpose": "gaming", "budget_range": "premium"}
            },
            {
                "name": "經濟實惠辦公",
                "slots": {"usage_purpose": "document_processing", "budget_range": "budget"}
            },
            {
                "name": "便攜商務",
                "slots": {"portability": "frequent", "weight_requirement": "light"}
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n  測試場景: {scenario['name']}")
            print(f"  槽位: {scenario['slots']}")
            
            results = kb.search_products(scenario['slots'])
            print(f"  結果數量: {len(results)}")
            
            if results:
                top_result = results[0]
                print(f"  最佳匹配: {top_result.get('modelname', 'Unknown')}")
                if 'similarity_score' in top_result:
                    print(f"  相似度: {top_result['similarity_score']:.2%}")
        
        # 步驟4：測試統計資訊
        print("\n步驟4：測試系統統計")
        
        if hasattr(kb, 'get_chunking_stats'):
            stats = kb.get_chunking_stats()
            print("- Chunking統計:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        # 步驟5：測試搜尋性能
        print("\n步驟5：測試搜尋性能")
        
        import time
        
        # 測試多次搜尋的平均時間
        test_slots = {"usage_purpose": "document_processing", "portability": "light"}
        search_times = []
        
        for _ in range(5):
            start_time = time.time()
            kb.search_products(test_slots)
            end_time = time.time()
            search_times.append(end_time - start_time)
        
        avg_time = sum(search_times) / len(search_times)
        print(f"- 平均搜尋時間: {avg_time:.3f}秒")
        print(f"- 搜尋時間範圍: {min(search_times):.3f}s - {max(search_times):.3f}s")
        
        print("\n" + "=" * 80)
        print("✅ Chunking整合測試完成！")
        print("=" * 80)
        
        # 保存測試結果
        test_results = {
            "test_name": "Chunking Integration Test",
            "knowledge_base_stats": stats if 'stats' in locals() else {},
            "case_1_results_count": len(search_results),
            "average_search_time": avg_time,
            "test_scenarios": len(test_scenarios),
            "all_scenarios_working": all(kb.search_products(s['slots']) for s in test_scenarios)
        }
        
        with open("docs/MGFD_System_Design/My_MGFD_Design/v0.3/chunking_integration_test_results.json", 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        print(f"測試結果已保存到: chunking_integration_test_results.json")
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chunking_integration()
    sys.exit(0 if success else 1)