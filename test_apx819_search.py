#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify APX819 search fix
Tests the increased Milvus search limit to ensure APX819 is captured
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from libs.KnowledgeManageHandler.knowledge_manager import KnowledgeManager

def test_apx819_search():
    """Test the APX819 dual-channel RAM query"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        # Initialize knowledge manager
        logger.info("🔧 Initializing KnowledgeManager...")
        km = KnowledgeManager()

        # Test query that should return APX819
        query = "Does APX819 support dual-channel RAM configuration?"
        logger.info(f"🔍 Testing query: '{query}'")

        # Execute search with increased limit
        result = km.search_product_data(query)

        # Analyze results
        if result.get("status") == "success":
            products = result.get("products", [])
            matched_keys = result.get("matched_keys", [])

            logger.info(f"✅ Search successful!")
            logger.info(f"📊 Total products found: {len(products)}")
            logger.info(f"🔑 Matched keys (modeltypes): {matched_keys}")

            # Check if APX819 is found
            apx819_found = False
            for product in products:
                modeltype = str(product.get('modeltype', ''))
                if modeltype == '819':
                    apx819_found = True
                    logger.info(f"🎯 APX819 FOUND! Model: {product.get('modelname', 'Unknown')}")
                    logger.info(f"   RAM info: {product.get('memory', 'N/A')}")
                    break

            if not apx819_found:
                logger.warning(f"❌ APX819 NOT FOUND in results")
                logger.info("Found modeltypes: " + str([p.get('modeltype') for p in products]))

            # Show top 5 results for analysis
            logger.info("📋 Top 5 results:")
            for i, product in enumerate(products[:5], 1):
                logger.info(f"  {i}. {product.get('modeltype', 'N/A')} - {product.get('modelname', 'Unknown')}")

        else:
            logger.error(f"❌ Search failed: {result.get('status')} - {result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_apx819_search()