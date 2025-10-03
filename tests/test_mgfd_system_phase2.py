#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD系統階段2測試腳本
測試主控制器和API整合
"""

import sys
import os
import json
import redis
import logging
from pathlib import Path

# 添加項目根目錄到路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_redis_connection():
    """測試Redis連接"""
    try:
        client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        client.ping()
        logger.info("✅ Redis連接測試成功")
        return client
    except Exception as e:
        logger.error(f"❌ Redis連接測試失敗: {e}")
        return None

def test_mgfd_system_initialization():
    """測試MGFD系統初始化"""
    try:
        from libs.mgfd_cursor.mgfd_system import MGFDSystem
        
        redis_client = test_redis_connection()
        if not redis_client:
            logger.error("❌ 無法初始化MGFD系統：Redis連接失敗")
            return None
        
        mgfd_system = MGFDSystem(redis_client)
        logger.info("✅ MGFD系統初始化成功")
        return mgfd_system
    except Exception as e:
        logger.error(f"❌ MGFD系統初始化失敗: {e}")
        return None

def test_config_loader():
    """測試配置載入器"""
    try:
        from libs.mgfd_cursor.config_loader import ConfigLoader
        
        config_loader = ConfigLoader()
        
        # 測試載入各種配置
        slot_schema = config_loader.load_slot_schema()
        slot_synonyms = config_loader.load_slot_synonyms()
        personality_profiles = config_loader.load_personality_profiles()
        response_templates = config_loader.load_response_templates()
        think_prompts = config_loader.load_think_prompts()
        act_prompts = config_loader.load_act_prompts()
        
        logger.info("✅ 配置載入器測試成功")
        logger.info(f"   - 槽位模式: {len(slot_schema)} 個槽位")
        logger.info(f"   - 槽位同義詞: {len(slot_synonyms)} 個映射")
        logger.info(f"   - 個性配置: {len(personality_profiles.get('profiles', {}))} 個配置")
        logger.info(f"   - 回應模板: {len(response_templates.get('templates', {}))} 個模板")
        logger.info(f"   - Think提示詞: {len(think_prompts.get('think_prompts', {}))} 個提示詞")
        logger.info(f"   - Act提示詞: {len(act_prompts.get('act_prompts', {}))} 個提示詞")
        
        return config_loader
    except Exception as e:
        logger.error(f"❌ 配置載入器測試失敗: {e}")
        return None

def test_user_input_handler():
    """測試用戶輸入處理器"""
    try:
        from libs.UserInputHandler.UserInputHandler import UserInputHandler
        from libs.mgfd_cursor.llm_manager import MGFDLLMManager
        
        llm_manager = MGFDLLMManager()
        slot_schema = {
            "usage_purpose": {
                "description": "使用目的",
                "type": "string",
                "required": True,
                "options": ["gaming", "business", "study", "entertainment", "other"]
            },
            "budget_range": {
                "description": "預算範圍",
                "type": "string",
                "required": True,
                "options": ["low", "medium", "high", "premium"]
            }
        }
        
        handler = UserInputHandler(llm_manager, slot_schema)
        logger.info("✅ 用戶輸入處理器初始化成功")
        return handler
    except Exception as e:
        logger.error(f"❌ 用戶輸入處理器測試失敗: {e}")
        return None

def test_dialogue_manager():
    """測試對話管理器"""
    try:
        from libs.mgfd_cursor.dialogue_manager import DialogueManager
        from libs.mgfd_cursor.llm_manager import MGFDLLMManager
        
        llm_manager = MGFDLLMManager()
        slot_schema = {
            "usage_purpose": {
                "description": "使用目的",
                "type": "string",
                "required": True,
                "options": ["gaming", "business", "study", "entertainment", "other"]
            },
            "budget_range": {
                "description": "預算範圍",
                "type": "string",
                "required": True,
                "options": ["low", "medium", "high", "premium"]
            }
        }
        
        manager = DialogueManager(llm_manager, slot_schema)
        logger.info("✅ 對話管理器初始化成功")
        return manager
    except Exception as e:
        logger.error(f"❌ 對話管理器測試失敗: {e}")
        return None

def test_action_executor():
    """測試動作執行器"""
    try:
        from libs.mgfd_cursor.action_executor import ActionExecutor
        from libs.mgfd_cursor.llm_manager import MGFDLLMManager
        from libs.mgfd_cursor.config_loader import ConfigLoader
        
        llm_manager = MGFDLLMManager()
        config_loader = ConfigLoader()
        
        executor = ActionExecutor(llm_manager, config_loader)
        logger.info("✅ 動作執行器初始化成功")
        return executor
    except Exception as e:
        logger.error(f"❌ 動作執行器測試失敗: {e}")
        return None

def test_response_generator():
    """測試回應生成器"""
    try:
        from libs.ResponseGenHandler.ResponseGenHandler import ResponseGenHandler as ResponseGenerator
        from libs.mgfd_cursor.config_loader import ConfigLoader
        
        config_loader = ConfigLoader()
        
        generator = ResponseGenerator(config_loader)
        logger.info("✅ 回應生成器初始化成功")
        return generator
    except Exception as e:
        logger.error(f"❌ 回應生成器測試失敗: {e}")
        return None

def test_redis_state_manager():
    """測試Redis狀態管理器"""
    try:
        from libs.mgfd_cursor.redis_state_manager import RedisStateManager
        
        redis_client = test_redis_connection()
        if not redis_client:
            logger.error("❌ 無法測試Redis狀態管理器：Redis連接失敗")
            return None
        
        state_manager = RedisStateManager(redis_client)
        logger.info("✅ Redis狀態管理器初始化成功")
        return state_manager
    except Exception as e:
        logger.error(f"❌ Redis狀態管理器測試失敗: {e}")
        return None

def test_mgfd_system_integration():
    """測試MGFD系統整合"""
    try:
        mgfd_system = test_mgfd_system_initialization()
        if not mgfd_system:
            return False
        
        # 測試系統狀態
        status = mgfd_system.get_system_status()
        if status.get('success', False):
            logger.info("✅ MGFD系統狀態檢查成功")
            logger.info(f"   - Redis狀態: {status['system_status']['redis']}")
            logger.info(f"   - LLM狀態: {status['system_status']['llm']}")
            logger.info(f"   - 模組狀態: {status['system_status']['modules']}")
        else:
            logger.error("❌ MGFD系統狀態檢查失敗")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ MGFD系統整合測試失敗: {e}")
        return False

def test_api_routes():
    """測試API路由"""
    try:
        from api.mgfd_routes import mgfd_bp, mgfd_system
        
        if mgfd_system:
            logger.info("✅ MGFD API路由初始化成功")
            logger.info(f"   - Blueprint名稱: {mgfd_bp.name}")
            logger.info(f"   - 註冊的端點數量: {len(mgfd_bp.deferred_functions)}")
        else:
            logger.error("❌ MGFD API路由初始化失敗：系統未初始化")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ MGFD API路由測試失敗: {e}")
        return False

def run_all_tests():
    """運行所有測試"""
    logger.info("🚀 開始MGFD系統階段2測試")
    logger.info("=" * 50)
    
    test_results = {
        "redis_connection": False,
        "config_loader": False,
        "user_input_handler": False,
        "dialogue_manager": False,
        "action_executor": False,
        "response_generator": False,
        "redis_state_manager": False,
        "mgfd_system_integration": False,
        "api_routes": False
    }
    
    # 測試各個組件
    test_results["redis_connection"] = test_redis_connection() is not None
    test_results["config_loader"] = test_config_loader() is not None
    test_results["user_input_handler"] = test_user_input_handler() is not None
    test_results["dialogue_manager"] = test_dialogue_manager() is not None
    test_results["action_executor"] = test_action_executor() is not None
    test_results["response_generator"] = test_response_generator() is not None
    test_results["redis_state_manager"] = test_redis_state_manager() is not None
    test_results["mgfd_system_integration"] = test_mgfd_system_integration()
    test_results["api_routes"] = test_api_routes()
    
    # 輸出測試結果
    logger.info("=" * 50)
    logger.info("📊 測試結果總結")
    logger.info("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        logger.info(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    logger.info("=" * 50)
    logger.info(f"總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        logger.info("🎉 所有測試通過！階段2實現成功！")
        return True
    else:
        logger.error(f"⚠️  {total - passed} 個測試失敗，需要檢查")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
