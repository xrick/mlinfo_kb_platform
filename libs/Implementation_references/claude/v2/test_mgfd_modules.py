"""
MGFD 模組測試文件
測試 MGFDKernel 和 UserInputHandler 的功能
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加模組路徑
sys.path.append(str(Path(__file__).parent))

from MGFDKernel import MGFDKernel
from UserInputHandler import UserInputHandler

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_user_input_handler():
    """測試 UserInputHandler 功能"""
    print("\n" + "="*50)
    print("測試 UserInputHandler")
    print("="*50)
    
    handler = UserInputHandler()
    
    # 測試用例
    test_cases = [
        {
            "message": "你好，我想買一台筆電",
            "expected_intent": "greet",
            "description": "基本問候"
        },
        {
            "message": "我想找一台用來工作的筆電",
            "expected_intent": "ask_recommendation",
            "description": "工作用途推薦"
        },
        {
            "message": "預算大概3萬到4萬之間",
            "expected_intent": "provide_info",
            "description": "價格範圍信息"
        },
        {
            "message": "比較輕便的，重量不要太重",
            "expected_intent": "provide_info",
            "description": "重量要求"
        },
        {
            "message": "螢幕尺寸大概15寸左右",
            "expected_intent": "provide_info",
            "description": "螢幕尺寸"
        },
        {
            "message": "華碩品牌的筆電",
            "expected_intent": "provide_info",
            "description": "品牌偏好"
        },
        {
            "message": "用來玩遊戲的，GPU效能要好一點",
            "expected_intent": "provide_info",
            "description": "遊戲用途和GPU要求"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n測試 {i}: {test_case['description']}")
        print(f"輸入: {test_case['message']}")
        
        # 模擬上下文
        context = {
            "session_id": "test_session",
            "slots": {},
            "stage": "INIT"
        }
        
        # 解析輸入
        result = await handler.parse(test_case['message'], context)
        
        print(f"意圖: {result['intent']}")
        print(f"槽位更新: {result['slots_update']}")
        print(f"控制指令: {result['control']}")
        print(f"置信度: {result['confidence']:.2f}")
        print(f"錯誤: {result['errors']}")
        
        # 驗證結果
        if result['intent'] == test_case['expected_intent']:
            print("✅ 意圖識別正確")
        else:
            print(f"❌ 意圖識別錯誤，期望: {test_case['expected_intent']}")
        
        if result['slots_update']:
            print("✅ 槽位抽取成功")
        else:
            print("⚠️ 未抽取到槽位")


async def test_mgfd_kernel():
    """測試 MGFDKernel 功能"""
    print("\n" + "="*50)
    print("測試 MGFDKernel")
    print("="*50)
    
    # 創建 UserInputHandler 實例
    user_input_handler = UserInputHandler()
    
    # 創建 MGFDKernel 實例
    kernel = MGFDKernel()
    
    # 設置 UserInputHandler
    kernel.set_user_input_handler(user_input_handler)
    
    # 測試用例
    test_cases = [
        {
            "message": "你好，我想買筆電",
            "description": "基本問候和需求"
        },
        {
            "message": "我想找一台工作用的筆電，預算3萬左右",
            "description": "完整需求描述"
        },
        {
            "message": "比較輕便的，15寸螢幕",
            "description": "具體規格要求"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n測試 {i}: {test_case['description']}")
        print(f"輸入: {test_case['message']}")
        
        # 處理消息
        result = await kernel.process_message("test_session", test_case['message'])
        
        print(f"回應類型: {result.get('type', 'unknown')}")
        print(f"回應內容: {result.get('message', 'N/A')}")
        print(f"會話ID: {result.get('session_id', 'N/A')}")
        
        if result.get('success') is False:
            print(f"❌ 處理失敗: {result.get('error', '未知錯誤')}")
        else:
            print("✅ 處理成功")


async def test_keywords_extraction():
    """測試基於 default_keywords.json 的詞彙捕捉"""
    print("\n" + "="*50)
    print("測試 default_keywords.json 詞彙捕捉")
    print("="*50)
    
    handler = UserInputHandler()
    
    # 測試 default_keywords.json 中的關鍵詞
    keyword_test_cases = [
        {
            "message": "我想要一台用途是工作的筆電",
            "expected_slots": ["usage_purpose"],
            "description": "用途關鍵詞"
        },
        {
            "message": "預算大概4萬到5萬之間",
            "expected_slots": ["price_range"],
            "description": "預算關鍵詞"
        },
        {
            "message": "重量要輕便一點",
            "expected_slots": ["weight"],
            "description": "重量關鍵詞"
        },
        {
            "message": "攜帶性要好，容易攜帶",
            "expected_slots": ["portability"],
            "description": "攜帶性關鍵詞"
        },
        {
            "message": "CPU效能要強一點",
            "expected_slots": ["cpu_performance"],
            "description": "CPU效能關鍵詞"
        },
        {
            "message": "GPU效能要好，用來玩遊戲",
            "expected_slots": ["gpu_performance"],
            "description": "GPU效能關鍵詞"
        },
        {
            "message": "螢幕尺寸15寸",
            "expected_slots": ["screen_size"],
            "description": "螢幕尺寸關鍵詞"
        },
        {
            "message": "品牌要華碩的",
            "expected_slots": ["brand"],
            "description": "品牌關鍵詞"
        },
        {
            "message": "要有觸控螢幕",
            "expected_slots": ["touch_screen"],
            "description": "觸控螢幕關鍵詞"
        }
    ]
    
    for i, test_case in enumerate(keyword_test_cases, 1):
        print(f"\n測試 {i}: {test_case['description']}")
        print(f"輸入: {test_case['message']}")
        
        context = {"session_id": "test_session", "slots": {}, "stage": "INIT"}
        result = await handler.parse(test_case['message'], context)
        
        extracted_slots = list(result['slots_update'].keys())
        print(f"抽取的槽位: {extracted_slots}")
        
        # 驗證是否抽取到期望的槽位
        expected_slots = test_case['expected_slots']
        matched_slots = [slot for slot in expected_slots if slot in extracted_slots]
        
        if matched_slots:
            print(f"✅ 成功抽取期望槽位: {matched_slots}")
        else:
            print(f"❌ 未抽取到期望槽位: {expected_slots}")


async def test_system_status():
    """測試系統狀態功能"""
    print("\n" + "="*50)
    print("測試系統狀態")
    print("="*50)
    
    kernel = MGFDKernel()
    
    # 獲取系統狀態
    status = await kernel.get_system_status()
    
    print(f"系統狀態: {status.get('success', False)}")
    if status.get('system_status'):
        system_info = status['system_status']
        print(f"Redis 狀態: {system_info.get('redis', 'unknown')}")
        print(f"模組狀態: {system_info.get('modules', {})}")
        print(f"版本: {system_info.get('version', 'unknown')}")


async def main():
    """主測試函數"""
    print("開始 MGFD 模組測試")
    print("="*50)
    
    try:
        # 測試 UserInputHandler
        await test_user_input_handler()
        
        # 測試 keywords.json 詞彙捕捉
        await test_keywords_extraction()
        
        # 測試 MGFDKernel
        await test_mgfd_kernel()
        
        # 測試系統狀態
        await test_system_status()
        
        print("\n" + "="*50)
        print("所有測試完成")
        print("="*50)
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}", exc_info=True)
        print(f"❌ 測試失敗: {e}")


if __name__ == "__main__":
    asyncio.run(main())
