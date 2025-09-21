#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test suite for the APX819 search fix
Tests multiple scenarios to ensure robustness
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from libs.KnowledgeManageHandler.knowledge_manager import KnowledgeManager

def test_comprehensive_search_scenarios():
    """Test multiple search scenarios to validate the fix"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        # Initialize knowledge manager
        logger.info("🔧 Initializing KnowledgeManager...")
        km = KnowledgeManager()

        # Test scenarios
        test_cases = [
            {
                "name": "Original APX819 dual-channel RAM query",
                "query": "Does APX819 support dual-channel RAM configuration?",
                "expected_modeltype": "819"
            },
            {
                "name": "APX819 without specific feature query",
                "query": "Tell me about APX819 specifications",
                "expected_modeltype": "819"
            },
            {
                "name": "APX839 comparison (should still work)",
                "query": "Does APX839 support dual-channel RAM configuration?",
                "expected_modeltype": "839"
            },
            {
                "name": "Multiple product codes",
                "query": "Compare APX819 and APX839 memory specifications",
                "expected_modeltypes": ["819", "839"]
            },
            {
                "name": "Gaming query without product codes (original semantic search)",
                "query": "What are the best gaming laptops for high-end games?",
                "expected_semantic_only": True
            },
            {
                "name": "Product code with lowercase",
                "query": "does apx819 have good performance?",
                "expected_modeltype": "819"
            }
        ]

        results = []

        for test_case in test_cases:
            logger.info(f"\n🧪 Testing: {test_case['name']}")
            logger.info(f"📝 Query: '{test_case['query']}'")

            result = km.search_product_data(test_case['query'])

            test_result = {
                "name": test_case['name'],
                "query": test_case['query'],
                "status": result.get("status"),
                "success": False,
                "details": ""
            }

            if result.get("status") == "success":
                products = result.get("products", [])
                matched_keys = result.get("matched_keys", [])
                detected_codes = result.get("detected_product_codes", [])

                logger.info(f"✅ Status: {result.get('status')}")
                logger.info(f"🔍 Detected codes: {detected_codes}")
                logger.info(f"🔑 Matched keys: {matched_keys}")
                logger.info(f"📊 Products found: {len(products)}")

                # Check if expected modeltype is found
                if "expected_modeltype" in test_case:
                    expected_type = test_case["expected_modeltype"]
                    if expected_type in matched_keys:
                        test_result["success"] = True
                        test_result["details"] = f"Found expected modeltype {expected_type}"
                        logger.info(f"🎯 SUCCESS: Found expected modeltype {expected_type}")
                    else:
                        test_result["details"] = f"Expected modeltype {expected_type} not found in {matched_keys}"
                        logger.warning(f"❌ FAIL: Expected modeltype {expected_type} not found")

                elif "expected_modeltypes" in test_case:
                    expected_types = test_case["expected_modeltypes"]
                    found_types = [t for t in expected_types if t in matched_keys]
                    if len(found_types) == len(expected_types):
                        test_result["success"] = True
                        test_result["details"] = f"Found all expected modeltypes {expected_types}"
                        logger.info(f"🎯 SUCCESS: Found all expected modeltypes {expected_types}")
                    else:
                        missing = [t for t in expected_types if t not in matched_keys]
                        test_result["details"] = f"Missing modeltypes {missing} from {expected_types}"
                        logger.warning(f"❌ PARTIAL: Missing modeltypes {missing}")

                elif test_case.get("expected_semantic_only"):
                    if len(matched_keys) > 0:
                        test_result["success"] = True
                        test_result["details"] = f"Semantic search returned {len(matched_keys)} modeltypes"
                        logger.info(f"🎯 SUCCESS: Semantic search working, found {len(matched_keys)} modeltypes")
                    else:
                        test_result["details"] = "No semantic search results"
                        logger.warning("❌ FAIL: No semantic search results")

                # Show some sample products
                for i, product in enumerate(products[:3], 1):
                    logger.info(f"  {i}. {product.get('modeltype', 'N/A')} - {product.get('modelname', 'Unknown')}")

            else:
                logger.error(f"❌ Search failed: {result.get('status')} - {result.get('error', 'Unknown error')}")
                test_result["details"] = f"Search failed: {result.get('error', 'Unknown')}"

            results.append(test_result)

        # Summary
        logger.info(f"\n📋 TEST SUMMARY")
        logger.info(f"{'='*60}")
        passed = sum(1 for r in results if r["success"])
        total = len(results)

        for result in results:
            status_icon = "✅" if result["success"] else "❌"
            logger.info(f"{status_icon} {result['name']}: {result['details']}")

        logger.info(f"{'='*60}")
        logger.info(f"🎯 PASSED: {passed}/{total} tests")

        if passed == total:
            logger.info("🚀 ALL TESTS PASSED! The APX819 search fix is working correctly.")
        else:
            logger.warning(f"⚠️  {total - passed} test(s) failed. Review the issues above.")

        return passed == total

    except Exception as e:
        logger.error(f"💥 Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_comprehensive_search_scenarios()
    exit(0 if success else 1)