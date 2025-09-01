#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI遷移測試腳本
驗證MGFD系統從Flask遷移到FastAPI後的所有功能
"""

import sys
import os
import json
import asyncio
import requests
import time
from pathlib import Path

# 添加項目根目錄到路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 配置日誌
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 測試配置
BASE_URL = "http://localhost:8001"
API_BASE_URL = f"{BASE_URL}/api/mgfd"

class FastAPITester:
    """FastAPI遷移測試器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {}
    
    def test_health_check(self):
        """測試健康檢查端點"""
        try:
            logger.info("🧪 測試健康檢查端點...")
            response = self.session.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 健康檢查成功: {data}")
                self.test_results["health_check"] = True
                return True
            else:
                logger.error(f"❌ 健康檢查失敗: {response.status_code}")
                self.test_results["health_check"] = False
                return False
        except Exception as e:
            logger.error(f"❌ 健康檢查異常: {e}")
            self.test_results["health_check"] = False
            return False
    
    def test_system_status(self):
        """測試系統狀態端點"""
        try:
            logger.info("🧪 測試系統狀態端點...")
            response = self.session.get(f"{BASE_URL}/status")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 系統狀態檢查成功: {data}")
                self.test_results["system_status"] = True
                return True
            else:
                logger.error(f"❌ 系統狀態檢查失敗: {response.status_code}")
                self.test_results["system_status"] = False
                return False
        except Exception as e:
            logger.error(f"❌ 系統狀態檢查異常: {e}")
            self.test_results["system_status"] = False
            return False
    
    def test_mgfd_health(self):
        """測試MGFD健康檢查端點"""
        try:
            logger.info("🧪 測試MGFD健康檢查端點...")
            response = self.session.get(f"{API_BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ MGFD健康檢查成功: {data}")
                self.test_results["mgfd_health"] = True
                return True
            else:
                logger.error(f"❌ MGFD健康檢查失敗: {response.status_code}")
                self.test_results["mgfd_health"] = False
                return False
        except Exception as e:
            logger.error(f"❌ MGFD健康檢查異常: {e}")
            self.test_results["mgfd_health"] = False
            return False
    
    def test_mgfd_status(self):
        """測試MGFD系統狀態端點"""
        try:
            logger.info("🧪 測試MGFD系統狀態端點...")
            response = self.session.get(f"{API_BASE_URL}/status")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ MGFD系統狀態檢查成功: {data}")
                self.test_results["mgfd_status"] = True
                return True
            else:
                logger.error(f"❌ MGFD系統狀態檢查失敗: {response.status_code}")
                self.test_results["mgfd_status"] = False
                return False
        except Exception as e:
            logger.error(f"❌ MGFD系統狀態檢查異常: {e}")
            self.test_results["mgfd_status"] = False
            return False
    
    def test_chat_endpoint(self):
        """測試聊天端點"""
        try:
            logger.info("🧪 測試聊天端點...")
            
            # 測試數據
            test_data = {
                "message": "我想買一台筆電",
                "session_id": "test_session_fastapi",
                "stream": False
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/chat",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 聊天端點測試成功: {data}")
                self.test_results["chat_endpoint"] = True
                return True
            else:
                logger.error(f"❌ 聊天端點測試失敗: {response.status_code} - {response.text}")
                self.test_results["chat_endpoint"] = False
                return False
        except Exception as e:
            logger.error(f"❌ 聊天端點測試異常: {e}")
            self.test_results["chat_endpoint"] = False
            return False
    
    def test_session_management(self):
        """測試會話管理端點"""
        try:
            logger.info("🧪 測試會話管理端點...")
            session_id = "test_session_management"
            
            # 測試獲取會話狀態
            response = self.session.get(f"{API_BASE_URL}/session/{session_id}")
            logger.info(f"會話狀態檢查: {response.status_code}")
            
            # 測試重置會話
            response = self.session.post(f"{API_BASE_URL}/session/{session_id}/reset")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 會話管理測試成功: {data}")
                self.test_results["session_management"] = True
                return True
            else:
                logger.error(f"❌ 會話管理測試失敗: {response.status_code}")
                self.test_results["session_management"] = False
                return False
        except Exception as e:
            logger.error(f"❌ 會話管理測試異常: {e}")
            self.test_results["session_management"] = False
            return False
    
    def test_chat_history(self):
        """測試對話歷史端點"""
        try:
            logger.info("🧪 測試對話歷史端點...")
            session_id = "test_session_history"
            
            response = self.session.get(f"{API_BASE_URL}/session/{session_id}/history?limit=10")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 對話歷史測試成功: {data}")
                self.test_results["chat_history"] = True
                return True
            else:
                logger.error(f"❌ 對話歷史測試失敗: {response.status_code}")
                self.test_results["chat_history"] = False
                return False
        except Exception as e:
            logger.error(f"❌ 對話歷史測試異常: {e}")
            self.test_results["chat_history"] = False
            return False
    
    def test_api_documentation(self):
        """測試API文檔端點"""
        try:
            logger.info("🧪 測試API文檔端點...")
            
            # 測試Swagger UI
            response = self.session.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                logger.info("✅ Swagger UI文檔可訪問")
            else:
                logger.warning(f"⚠️ Swagger UI文檔訪問失敗: {response.status_code}")
            
            # 測試ReDoc
            response = self.session.get(f"{BASE_URL}/redoc")
            if response.status_code == 200:
                logger.info("✅ ReDoc文檔可訪問")
            else:
                logger.warning(f"⚠️ ReDoc文檔訪問失敗: {response.status_code}")
            
            # 測試OpenAPI JSON
            response = self.session.get(f"{BASE_URL}/openapi.json")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ OpenAPI JSON可訪問，版本: {data.get('info', {}).get('version', 'unknown')}")
                self.test_results["api_documentation"] = True
                return True
            else:
                logger.error(f"❌ OpenAPI JSON訪問失敗: {response.status_code}")
                self.test_results["api_documentation"] = False
                return False
        except Exception as e:
            logger.error(f"❌ API文檔測試異常: {e}")
            self.test_results["api_documentation"] = False
            return False
    
    def test_error_handling(self):
        """測試錯誤處理"""
        try:
            logger.info("🧪 測試錯誤處理...")
            
            # 測試無效的會話ID
            response = self.session.get(f"{API_BASE_URL}/session/invalid_session_id")
            if response.status_code == 404:
                logger.info("✅ 404錯誤處理正常")
            else:
                logger.warning(f"⚠️ 404錯誤處理異常: {response.status_code}")
            
            # 測試無效的聊天請求
            invalid_data = {"message": ""}  # 空消息
            response = self.session.post(
                f"{API_BASE_URL}/chat",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 422:
                logger.info("✅ 422驗證錯誤處理正常")
            else:
                logger.warning(f"⚠️ 422驗證錯誤處理異常: {response.status_code}")
            
            self.test_results["error_handling"] = True
            return True
        except Exception as e:
            logger.error(f"❌ 錯誤處理測試異常: {e}")
            self.test_results["error_handling"] = False
            return False
    
    def test_performance(self):
        """測試性能"""
        try:
            logger.info("🧪 測試性能...")
            
            start_time = time.time()
            
            # 發送多個請求測試性能
            for i in range(5):
                test_data = {
                    "message": f"測試消息 {i}",
                    "session_id": f"perf_test_session_{i}",
                    "stream": False
                }
                
                response = self.session.post(
                    f"{API_BASE_URL}/chat",
                    json=test_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.warning(f"⚠️ 性能測試請求 {i} 失敗: {response.status_code}")
            
            end_time = time.time()
            total_time = end_time - start_time
            
            logger.info(f"✅ 性能測試完成，總時間: {total_time:.2f}秒")
            self.test_results["performance"] = True
            return True
        except Exception as e:
            logger.error(f"❌ 性能測試異常: {e}")
            self.test_results["performance"] = False
            return False
    
    def run_all_tests(self):
        """運行所有測試"""
        logger.info("🚀 開始FastAPI遷移測試")
        logger.info("=" * 60)
        
        # 運行所有測試
        tests = [
            ("健康檢查", self.test_health_check),
            ("系統狀態", self.test_system_status),
            ("MGFD健康檢查", self.test_mgfd_health),
            ("MGFD系統狀態", self.test_mgfd_status),
            ("聊天端點", self.test_chat_endpoint),
            ("會話管理", self.test_session_management),
            ("對話歷史", self.test_chat_history),
            ("API文檔", self.test_api_documentation),
            ("錯誤處理", self.test_error_handling),
            ("性能測試", self.test_performance),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                logger.error(f"❌ {test_name}測試執行失敗: {e}")
                self.test_results[test_name.lower().replace(" ", "_")] = False
        
        # 輸出測試結果
        logger.info("=" * 60)
        logger.info("📊 FastAPI遷移測試結果總結")
        logger.info("=" * 60)
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ 通過" if result else "❌ 失敗"
            logger.info(f"{test_name:25} {status}")
            if result:
                passed += 1
        
        logger.info("=" * 60)
        logger.info(f"總計: {passed}/{total} 個測試通過")
        
        if passed == total:
            logger.info("🎉 所有測試通過！FastAPI遷移成功！")
            return True
        else:
            logger.error(f"⚠️  {total - passed} 個測試失敗，需要檢查")
            return False


def main():
    """主函數"""
    # 檢查服務器是否運行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            logger.error("❌ 服務器未運行或無法訪問")
            logger.info("請先啟動服務器: python main.py")
            return False
    except requests.exceptions.RequestException:
        logger.error("❌ 無法連接到服務器")
        logger.info("請先啟動服務器: python main.py")
        return False
    
    # 運行測試
    tester = FastAPITester()
    success = tester.run_all_tests()
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
