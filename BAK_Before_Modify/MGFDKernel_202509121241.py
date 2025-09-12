# BAK_Before_Modify/MGFDKernel_202509121241.py
# BAK_Before_Modify/MGFDKernel.py
# libs/MGFDKernel.py
"""
MGFD 核心控制器 - 系統大腦及對外唯一介面
負責協調五大模組，管理對話流程，處理前端請求
後端處理完畢，回覆給前端的格式:
return {
        "success": True,
        "session_id": session_id,
        "message": "LLM Responses",
        "timestamp": datetime.now().isoformat()
        }
"""

import logging
import json
import redis
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

# 導入其他模組（待實作）
# from .UserInputHandler import UserInputHandler
# from .StateManageHandler import StateManagementHandler
# from .PromptManagementHandler import PromptManagementHandler
# from .KnowledgeManageHandler import KnowledgeManagementHandler
# from .ResponseGenHandler import ResponseGenHandler
from .UserInputHandler.UserInputHandler import UserInputHandler
from .UserInputHandler import CheckUtils
from .StateManageHandler.StateManagementHandler import StateManagementHandler
from .PromptManagementHandler import prompt_manager
from .KnowledgeManageHandler.knowledge_manager import KnowledgeManager
from .ResponseGenHandler import ResponseGenHandler
from dataclasses import dataclass
from .RAG.LLM.LLMInitializer import LLMInitializer
from langchain.prompts import PromptTemplate
import re
logger = logging.getLogger(__name__)

###setup debug
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

@dataclass
class StateStatus:
    keyword_matched: str
    keyword_not_matched: str
    need_data_query:str
    no_data_query:str
    default:str

@dataclass
class States:
    OnInit: str
    OnReceiveMsg: str
    OnResponseMsg: str
    OnGenFunnelChat: str
    OnGenMDContent: str
    OnDataQuery: str
    OnQueriedDataProcessing: str
    OnSendFront: str
    OnWaitMsg: str


class MGFDKernel:
    """
    MGFD 系統核心控制器
    職責：協調五大模組，管理對話流程，處理前端請求
    """
    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """
        初始化 MGFD 核心控制器 
        Args:
            redis_client: Redis 客戶端實例，用於會話狀態持久化
        """
        # 初始化知識管理器（包含 LLM 功能）
        self.knowledge_manager = KnowledgeManager()
        self.redis_client = redis_client
        self.config = self._load_config()
        
        #self.slot_schema = self._load_slot_schema()
        
        # Initialize states and state_status before state_machine to avoid AttributeError
        self.states = States(
            OnInit="OnInit",
            OnReceiveMsg="OnReceiveMsg",
            OnResponseMsg="OnResponseMsg",
            OnGenFunnelChat="OnGenFunnelChat",
            OnGenMDContent="OnGenMDContent",
            OnDataQuery="OnDataQuery",
            OnQueriedDataProcessing="OnQueriedDataProcessing",
            OnSendFront="OnSendFront",
            OnWaitMsg="OnWaitMsg"
        )
        self.state_status = StateStatus(
            keyword_matched="keyword_matched",
            keyword_not_matched="keyword_not_matched",
            need_data_query="need_data_query",
            no_data_query="no_data_query",
            default="default"
        )
        
        # Load state machine after state_status is initialized
        self.state_machine = self._load_state_machine()
        # Welcome Prompt
        self.welcome_prompt = self._load_welcome_prompt()
        self.prompt_using = """
            身為一名專業且親切的筆記型電腦銷售專家，你的任務是主動迎接進入賣場的客戶，並引導他們完成一段愉快且有效率的購物體驗。
            你的對話應遵循以下結構與原則：

            **1. 熱情開場與初步探索：**
            * 用溫暖且開放式的問候開始對話，例如：「您好，歡迎光臨！想找一台什麼樣的筆記型電腦呢？還是先隨意看看？」
            * 避免給予壓力，讓客戶感到輕鬆自在。

            **2. 引導式需求分析（核心任務）：**
            你的目標是透過精準提問，像偵探一樣拼湊出客戶的真實需求。請依序詢問以下關鍵問題，並根據客戶的回答追問細節：
            * **主要用途：** 「請問您買這台電腦，最主要是用來做什麼呢？例如是工作、上課、玩遊戲，還是單純上網追劇？」
            * **軟體與場景：**
                * （如果工作/上課）：「會常用到哪些比較特別的軟體嗎？像是剪輯影片、寫程式或跑數據分析？」
                * （如果玩遊戲）：「平常喜歡玩哪一種類型的遊戲呢？」
            * **便攜性與螢幕：** 「會經常需要把它帶出門嗎？對於螢幕大小或重量有沒有特別的偏好？」
            * **預算範圍：** 「方便請問一下您的預算大概是多少呢？我能更好地幫您篩選出CP值最高的選擇。」
            * **品牌與偏好：** 「過去有用過哪個品牌的電腦嗎？有沒有特別喜歡或不喜歡的品牌？」
            * **關鍵考量：** 「對您來說，一台理想的筆電，最不能妥協的功能是什麼？是效能、電池續航力，還是螢幕的畫質？」

            **3. 確認需求與提出方案：**
            * 在提問後，用一句話總結並確認客戶的需求。例如：「好的，所以我幫您整理一下，您需要一台方便攜帶、續航力長，主要用來文書處理和看影片，預算在三萬左右的筆電，對嗎？」
            * 根據確認後的需求，提出 2-3 款最符合的筆電選項。
            * 介紹每款筆電時，不要只講規格，要強調「它能為客戶帶來的好處」。例如，與其說「它有16GB RAM」，不如說「它有16GB的記憶體，所以您同時開很多網頁和文件都不會卡頓，非常順暢。」

            **4. 處理疑慮與完成銷售：**
            * 耐心回答客戶對推薦產品的任何問題。
            * 如果客戶猶豫不決，可以主動詢問：「這幾款您比較喜歡哪一台的設計呢？或是您還在意哪個部分，我再幫您說明？」
            * 最後，以親切的態度協助客戶完成購買流程或提供後續資訊。

            **互動準則：**
            * **語氣：** 始終保持專業、友善、耐心且充滿熱忱。
            * **目標：** 你的角色是「顧問」，不是「推銷員」。專注於解決客戶的問題，而非僅僅賣出最貴的商品。
            * **避免：** 不要使用過於深奧的技術術語，盡量用生活化的比喻來解釋。

            **嚴格遵守使用內部資料:**: 請絕對務必嚴格遵守公司產品資料都完全來自公司內部提供的各種資料，嚴格禁止出現競爭公司資料。

            **資料收集**:
            在你取得以下資料前，可以不斷重複詢問使用者，直到滿足資料收集完成。
            1. 用途
            1. 預算
            2. cpu規格
            3. gpu規格
            4. 筆電重量
            5. ssd容量
            6. 記憶體容量

        """
        # System-level prompt template (優化版 - 減少 70% Token 消耗)
        # 注意：這是不可變的模板，避免狀態污染
        self.SysPromptTemplate = """你是專業的筆電銷售顧問。根據以下產品資料回答客戶問題：

**產品資料：**
{product_data}

**客戶需求：**
{user_query}

**回應要求：**
1. 僅使用提供的產品資料，不得編造
2. 推薦 2-3 款最符合的產品
3. 用表格比較主要規格
4. 使用繁體中文，語氣專業友善
5. 無合適產品時回覆：「建議聯繫客服專家獲得協助」

**輸出格式：**
簡潔的 Markdown 格式，包含產品推薦和規格表格。"""
        # 宣告三層式prompt所需要的變數
        # self.product_data = None
        # self.prompt_using = None
        # self.answer = None
        # self.query = None
        # 宣告三層式Prompt

        # 初始化五大模組
        try:
            self.user_input_handler = UserInputHandler()
            self.prompt_manager = prompt_manager.get_global_prompt_manager()
            # knowledge_manager 已經在 __init__ 開頭初始化了
            self.response_generator = ResponseGenHandler()
            self.state_manager = StateManagementHandler(redis_client)
            logger.info("所有模組初始化成功")
            self.slot_schema = self.user_input_handler.slot_schema
        except Exception as e:
            logger.error(f"模組初始化失敗: {e}")
            # 如果初始化失敗，設置為 None
            self.user_input_handler = None
            self.prompt_manager = None
            self.knowledge_manager = None
            self.response_generator = None
            self.state_manager = None
        
        # 嘗試初始化 LLM（最小變更；失敗則保持回退機制）
        self.llm = None
        try:
            self.llm_initializer = LLMInitializer()
            self.llm = self.llm_initializer.get_llm()
            logger.info("LLM 初始化成功")
        except Exception as e:
            logger.warning(f"LLM 初始化失敗，將使用回退機制: {e}")
            self.llm_initializer = None
            self.llm = None
        # 若 Kernel 內未取得 LLM，且 KnowledgeManager 內已有 llm，可作讀取式備援
        try:
            if self.llm is None and getattr(self, 'knowledge_manager', None) is not None:
                km_llm = getattr(self.knowledge_manager, 'llm', None)
                if km_llm is not None:
                    self.llm = km_llm
                    logger.info("採用 KnowledgeManager 中的 LLM 作為備援")
        except Exception:
            # 安全保底，不阻斷初始化
            pass

        logger.info("MGFDKernel 初始化完成")
    
    def extract_markdown_tables(self, text: str) -> List[str]:
        """
        從文字中提取所有 Markdown 表格，並以 list 形式回傳。

        Args:
            text (str): 輸入的完整文字

        Returns:
            List[str]: 所有找到的 Markdown 表格，每個元素是一個字串
        """
        # 使用 regex 找出 markdown 表格
        table_pattern = re.compile(
            r"\|.*?\|\n\|[-:\s|]+\|\n(?:\|.*?\|\n?)+",
            re.DOTALL
        )
        tables = table_pattern.findall(text)
        return tables
    
    def _summarize_product_data(self, product_data: Dict[str, Any], max_products: int = 5) -> Dict[str, Any]:
        """
        摘要產品數據，只保留關鍵資訊以減少 Token 消耗
        
        Args:
            product_data: 原始產品數據
            max_products: 最大產品數量
            
        Returns:
            摘要後的產品數據
        """
        if not isinstance(product_data, dict) or not product_data.get("products"):
            return product_data
            
        products = product_data.get("products", [])
        
        # 限制產品數量到最相關的幾個
        products = products[:max_products]
        
        summarized_products = []
        for product in products:
            # 只保留關鍵規格，大幅減少數據量
            summarized_product = {
                "modeltype": product.get("modeltype", ""),
                "modelname": product.get("modelname", ""),
                "cpu_summary": self._extract_cpu_summary(product.get("cpu", "") or ""),
                "memory_summary": self._extract_memory_summary(product.get("memory", "") or ""),
                "lcd_summary": self._extract_lcd_summary(product.get("lcd", "") or ""),
                "battery_summary": self._extract_battery_summary(product.get("battery", "") or ""),
                "portability": self._assess_portability(product)
            }
            summarized_products.append(summarized_product)
        
        return {
            "query": product_data.get("query", ""),
            "status": product_data.get("status", ""),
            "count": len(summarized_products),
            "products": summarized_products,
            "note": f"已摘要為 {len(summarized_products)} 個主要產品規格"
        }
    
    def _extract_cpu_summary(self, cpu_text: str) -> str:
        """提取 CPU 關鍵資訊"""
        if not cpu_text:
            return "未提供 CPU 資訊"
        
        # 提取主要 CPU 型號和系列
        cpu_lines = cpu_text.split('\n')
        for line in cpu_lines:
            if any(keyword in line for keyword in ['Ryzen', 'AMD', 'Intel', 'Core']):
                return line.strip()[:100]  # 限制長度
        
        return cpu_text[:50] + "..." if len(cpu_text) > 50 else cpu_text
    
    def _extract_memory_summary(self, memory_text: str) -> str:
        """提取記憶體關鍵資訊"""
        if not memory_text:
            return "未提供記憶體資訊"
        
        # 尋找記憶體容量和類型
        import re
        ram_match = re.search(r'(\d+G[B]?|\d+GB|\d+TB)', memory_text)
        ddr_match = re.search(r'(DDR\d+|LPDDR\d+)', memory_text)
        
        summary_parts = []
        if ddr_match:
            summary_parts.append(ddr_match.group(1))
        if ram_match:
            summary_parts.append(f"最高 {ram_match.group(1)}")
        
        return " ".join(summary_parts) if summary_parts else memory_text[:50]
    
    def _extract_lcd_summary(self, lcd_text: str) -> str:
        """提取螢幕關鍵資訊"""
        if not lcd_text:
            return "未提供螢幕資訊"
        
        # 提取螢幕尺寸和解析度
        import re
        size_match = re.search(r'(\d+\.?\d*)"', lcd_text)
        resolution_match = re.search(r'(\d+\*\d+|\d+x\d+)', lcd_text)
        
        summary_parts = []
        if size_match:
            summary_parts.append(f"{size_match.group(1)}吋")
        if resolution_match:
            summary_parts.append(resolution_match.group(1))
        
        return " ".join(summary_parts) if summary_parts else lcd_text[:50]
    
    def _extract_battery_summary(self, battery_text: str) -> str:
        """提取電池關鍵資訊"""
        if not battery_text:
            return "未提供電池資訊"
        
        # 提取電池容量和續航力
        import re
        capacity_match = re.search(r'(\d+Wh)', battery_text)
        life_match = re.search(r'(\d+\s*[小時|Hours|Hour])', battery_text)
        
        summary_parts = []
        if capacity_match:
            summary_parts.append(capacity_match.group(1))
        if life_match:
            summary_parts.append(f"續航 {life_match.group(1)}")
        
        return " ".join(summary_parts) if summary_parts else "標準電池"
    
    def _assess_portability(self, product: Dict[str, Any]) -> str:
        """評估便攜性"""
        lcd = product.get("lcd", "") or ""  # 確保不是 None
        battery = product.get("battery", "") or ""  # 確保不是 None
        
        # 簡單的便攜性評估
        if any(size in lcd for size in ["11.6", "12", "13", "14"]):
            return "輕薄便攜"
        elif any(size in lcd for size in ["15.6", "16"]):
            return "標準尺寸"
        else:
            return "尺寸未知"
    
    # generate three-tier prompt
    def generate_three_tier_prompt(self,product_data=None, user_query=None):
        """生成三層式提示 - 修復版：避免模板狀態污染"""
        # 🔧 修復：每次都從乾淨的模板開始，避免狀態污染
        # 使用 str.replace 來避免 JSON 中的佔位符衝突
        result = self.SysPromptTemplate.replace("{product_data}", str(product_data))
        result = result.replace("{user_query}", str(user_query))
        return result
    #     """生成三層式提示"""
    #     return self.SysPrompt.format(product_data=None, prompt_using=self.prompt_using, 
    #                                  answer=self.answer, query=self.query)
    
    def _load_welcome_prompt(self) -> str:
        welcome_prompt = """
            角色：身為一名專業且親切的筆記型電腦銷售專家，你的任務是主動迎接進入賣場的客戶，並引導他們完成一段愉快且有效率的購物體驗。
            原則：
                1.從現在起，請你主動提出問題直到你有足夠資訊能夠回答客戶的問題。
            任務：
            1. 用溫暖且開放式的問候開始對話，例如：「您好，歡迎光臨！想找一台什麼樣的筆記型電腦呢？還是先隨意看看？」
            2. 避免給予壓力，讓客戶感到輕鬆自在。
            3. 透過精準提問，像偵探一樣拼湊出客戶的真實需求。
            4. 根據客戶的需求，提出 2-3 款最符合的筆電選項。
        """
        return welcome_prompt
    


    def _load_config(self) -> Dict[str, Any]:
        """載入系統配置"""
        try:
            config_path = Path(__file__).parent / "config" / "system_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 使用預設配置
                return {
                    "max_session_duration": 3600,  # 1小時
                    "max_slots_per_session": 20,
                    "default_response_timeout": 30,
                    "enable_streaming": True,
                    "log_level": "INFO"
                }
        except Exception as e:
            logger.error(f"載入配置失敗: {e}")
            return {}
    
    def _load_state_machine(self) -> Dict[str, Dict[str, Any]]:
        """載入狀態機定義"""
        try:
            state_machine = {
                "OnInit": {
                    "description": "狀態機初始化狀態",
                    "actions": ["GenerateWelcomePrompt"],
                    "next_states": {
                        self.state_status.keyword_matched: "OnResponseMsg",
                        self.state_status.keyword_not_matched: "OnGenFunnelChat"
                    }
                },
                "OnReceiveMsg": {
                    "description": "接收用戶消息狀態",
                    "actions": [
                        "ExtractKeyword",
                        "CompareSentence"
                    ],
                    "next_states": {
                        self.state_status.keyword_matched: "OnResponseMsg",
                        self.state_status.keyword_not_matched: "OnGenFunnelChat"
                    }
                },
                "OnResponseMsg": {
                    "description": "回應消息狀態",
                    "actions": [
                        "DataQuery",
                        "GenerateMDContent"
                    ],
                    "next_states": {
                        self.state_status.need_data_query: "OnDataQuery",
                        self.state_status.no_data_query: "OnGenFunnelChat"
                    }
                },
                "OnGenFunnelChat": {
                    "description": "生成漏斗式聊天狀態",
                    "actions": [
                        "Generate Messages to guide customers to our product"
                    ],
                    "next_states": {
                        self.state_status.default: "OnGenMDContent"
                    }
                },
                "OnGenMDContent": {
                    "description": "生成 Markdown 內容狀態",
                    "actions": [
                        "GenerateMDContent"
                    ],
                    "next_states": {
                        self.state_status.default: "OnGenMDContent"
                    }
                },
                "OnDataQuery": {
                    "description": "執行內部數據查詢狀態",
                    "actions": [
                        "DataQuery"
                    ],
                    "next_states": {
                        self.state_status.default: "OnQueriedDataProcessing"
                    }
                },
                "OnQueriedDataProcessing": {
                    "description": "查詢數據後處理狀態",
                    "actions": [
                        "DataPostprocessing"
                    ],
                    "next_states": {
                        self.state_status.default: "OnSendFront"
                    }
                },
                "OnSendFront": {
                    "description": "發送數據到前端狀態",
                    "actions": [
                        "SendDataToFront"
                    ],
                    "next_states": {
                        self.state_status.default: "OnWaitMsg"
                    }
                },
                "OnWaitMsg": {
                    "description": "等待下一條消息狀態",
                    "actions": [
                        "WaitNextMessage"
                    ],
                    "next_states": {
                        self.state_status.default: "OnReceiveMsg"
                    }
                }
            }
            logger.info(f"成功載入狀態機定義，包含 {len(state_machine)} 個狀態")
            return state_machine
        except Exception as e:
            logger.error(f"載入狀態機定義失敗: {e}")
            return {}
    
    async def process_message(
        self, 
        session_id: str, 
        message: str, 
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        處理用戶消息 - 主要入口點
        
        Args:
            session_id: 會話識別碼
            message: 用戶輸入消息
            stream: 是否使用串流回應
            
        Returns:
            包含回應內容的字典，格式對齊 mgfd_ai.js 期望
        """
        try:
            logger.info(f"處理消息 - 會話: {session_id}, 消息: {message}...")
            
            # 檢查模組是否已初始化
            if not self._check_modules_initialized():
                return self._create_error_response("系統模組未初始化")
            
            # 處理消息
            result = await self._process_message_internal(session_id, message)
            
            # 添加會話ID到回應
            result['session_id'] = session_id
            result['timestamp'] = datetime.now().isoformat()
            
            logger.info(f"消息處理完成 - 會話: {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"處理消息時發生錯誤: {e}", exc_info=True)
            return self._create_error_response(f"系統內部錯誤: {str(e)}")
    
    
    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        獲取會話狀態
        
        Args:
            session_id: 會話識別碼
            
        Returns:
            會話狀態字典
        """
        try:
            if not self.state_manager:
                return self._create_error_response("狀態管理器未初始化")
            
            # 暫時返回基本狀態，待 StateManagementHandler 實作
            return {
                "success": True,
                "session_id": session_id,
                "current_stage": "unknown",
                "filled_slots": {},
                "chat_history": [],
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"獲取會話狀態時發生錯誤: {e}", exc_info=True)
            return self._create_error_response(f"獲取會話狀態失敗: {str(e)}")
    
    async def reset_session(self, session_id: str) -> Dict[str, Any]:
        """
        重置會話
        
        Args:
            session_id: 會話識別碼
            
        Returns:
            重置結果字典
        """
        try:
            logger.info(f"重置會話: {session_id}")
            
            if not self.state_manager:
                return self._create_error_response("狀態管理器未初始化")
            
            # 暫時返回成功，待 StateManagementHandler 實作
            return {
                "success": True,
                "session_id": session_id,
                "message": "LLM Responses",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"重置會話時發生錯誤: {e}", exc_info=True)
            return self._create_error_response(f"重置會話失敗: {str(e)}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        獲取系統狀態
        
        Returns:
            系統狀態字典
        """
        try:
            modules_status = {
                "user_input_handler": self.user_input_handler is not None,
                "prompt_manager": self.prompt_manager is not None,
                "knowledge_manager": self.knowledge_manager is not None,
                "response_generator": self.response_generator is not None,
                "state_manager": self.state_manager is not None
            }
            
            redis_status = "connected" if self.redis_client and self.redis_client.ping() else "disconnected"
            
            return {
                "success": True,
                "system_status": {
                    "redis": redis_status,
                    "modules": modules_status,
                    "timestamp": datetime.now().isoformat(),
                    "version": "v2.0.0"
                }
            }
            
        except Exception as e:
            logger.error(f"獲取系統狀態時發生錯誤: {e}", exc_info=True)
            return self._create_error_response(f"獲取系統狀態失敗: {str(e)}")
    
    
    async def _process_message_internal(
        self, 
        session_id: str, 
        message: str #user input message
    ) -> Dict[str, Any]:
        """
        內部消息處理流程
        """
        # Step 1: 建立 context
        context = {
            "session_id": session_id,
            "user_message": message,
            "keyword": "nodata",
            "product_data": {},
            "timestamp": datetime.now().isoformat(),
            "state": self.states.OnReceiveMsg,
            "slots": {},
            "query_result": {},
            "previous_answer": str,
            "history": [],
            "control": {},
            "errors": [],
            "slot_schema": self.slot_schema,
            "config": self.config
        }
        
        # Step 2: 解析輸入（UserInputHandler）
        # 預設值，避免後續 NameError／KeyError
        slot_metadata = {}
        _product_data = {}
        if self.user_input_handler:
            slot_name, slot_metadata = await self.user_input_handler.parse_keyword(message)
            logger.info(f"***************************slot_name START*********************************: \n關鍵詞:\n{slot_name}")
        if slot_name:
            context.setdefault("slots", {}).update({slot_name: slot_metadata})
        else:
            context.setdefault("slots", {}).update({"": {}})
        
        # Step 3: 狀態機驅動（StateManager）
        if slot_metadata.get("ifDBSearch", True):
            context["state"] = self.states.OnDataQuery#"OnDataQuery"#
        else:
            context["state"] = self.states.OnGenFunnelChat#"OnGenFunnelChat"
        self.query = message

        # Step 4: 知識查詢（如需要）
        #需要加入knowledge_manager.search(context)
        #若ifDBSearch為True，則進行知識查詢，並將結果存入context["query_result"],
        #這是product_data
        if slot_metadata.get("ifDBSearch", True):
            # 直接進行與關鍵字相關的產品規格搜尋（以非阻塞方式在執行緒池執行）
            _product_data = await asyncio.to_thread(self.knowledge_manager.search_product_data, message)
            context['keyword'] = slot_name
            logging.info(f"知識查詢結果: {_product_data}")
            #進行
        #step 5: generate three-tier prompt and send prompt to LLM
        # 摘要產品數據以大幅減少 Token 消耗
        if _product_data and isinstance(_product_data, dict) and _product_data.get("products"):
            logger.info(f"原始產品數據包含 {len(_product_data.get('products', []))} 個產品")
            _product_data = self._summarize_product_data(_product_data, max_products=3)
            logger.info(f"摘要後產品數據包含 {len(_product_data.get('products', []))} 個產品")
        
        # 將 product_data 轉為 JSON 字串注入，降低模型誤判結構機率
        product_data_json = json.dumps(_product_data, ensure_ascii=False, indent=2)
        logger.info(f"產品資料 JSON 長度: {len(product_data_json)} (已優化)")
        logger.info(f"***************************產品資料START*********************************: \n產品資料:\n{product_data_json}")
        logger.info(f"***************************產品資料END***********************************\n")

        # 🔧 修復：使用局部變量避免狀態污染
        current_prompt = self.generate_three_tier_prompt(product_data=product_data_json, user_query=self.query)
        logger.info(f"***************************系統提示START********************************** \n{current_prompt}")
        logger.info(f"***************************系統提示END***********************************\n")
        #_product_data
        # # 將使用者查詢同時提供為 user_query，避免模板鍵名不一致導致 KeyError
        # 
        # self.SysPrompt = PromptTemplate(input_variables=["product_data", "user_query"], template=self.SysPrompt)
        # chain = self.SysPrompt | self.llm
        
        context['query_result'] = {"qry_result": _product_data}
        context['keyword'] = slot_name
        logging.info(f"product_data: {context['query_result']}")
        
        # Step 6: 生成回應（ResponseGenerator）
        # 若查無產品，直接回覆指定提示句；否則將 System Prompt 發送給 LLM
        llm_output = None
        try:
            no_products = (
                isinstance(_product_data, dict)
                and (
                    _product_data.get("status") in {"no_results", "no_spec_data", "no_database", "error"}
                    or not _product_data.get("products")
                )
            )
            # tables = []
            if no_products:
                llm_output = "目前尚未搜尋到符您需求的產品，是否進行不同規格產品的搜尋呢？"
            else:
                if hasattr(self, 'llm') and self.llm:
                    try:
                        # 使用 asyncio.wait_for 提供額外的超時保護（90秒，稍大於 LLM 的 request_timeout）
                        llm_output = await asyncio.wait_for(
                            asyncio.to_thread(self.llm.invoke, current_prompt),
                            timeout=90
                        )
                        ## format markdown tables
                        # tables = self.extract_markdown_tables(llm_output)
                        # if tables:
                        #     for table in tables:
                        #         llm_output = llm_output.replace(table, f"```markdown\n{table}\n```")
                        ## end of format markdown tables
                        if isinstance(llm_output, dict):
                            llm_output = llm_output.get('content') or json.dumps(llm_output, ensure_ascii=False)
                        if llm_output is not None and not isinstance(llm_output, str):
                            llm_output = str(llm_output)
                        logger.info(f"LLM 生成成功，長度: {len(llm_output) if llm_output else 0}")
                    except asyncio.TimeoutError:
                        logger.error("LLM 調用超時 (90秒)，回退至簡化回應")
                        llm_output = "抱歉，系統處理時間較長，我為您提供簡化的產品建議。根據您的需求「輕便容易攜帶」，我推薦以下輕薄筆電類型，詳細規格請聯繫客服專家獲得協助。"
                    except Exception as e:
                        logger.error(f"LLM 調用發生異常: {e}")
                        llm_output = "系統暫時無法生成詳細回應，建議聯繫客服專家以獲得產品推薦。"
                else:
                    logger.info("LLM 未初始化，跳過生成步驟，回退至資料字串")
        except Exception as e:
            logger.warning(f"LLM 生成失敗，回退至查詢資料: {e}")

        # step 7: format frontend response
        # presentation_data_prompt = """
        # *採用markdown格式輸出：請markdown syntax產生專業、簡潔、美觀的報告，讓使用者能夠清楚了解。
        # {product_data}
        # """.format(product_data=product_data_json)
        # 若有 llm_output 則優先使用，否則回傳查詢資料字串，避免前端顯示 [object Object]
        
        response_result = {
            "type": "general",
            "message": llm_output,
            "success": True
        }
        # # 若有 llm_output 則優先使用，否則回傳查詢資料字串，避免前端顯示 [object Object]
        # response_result = {
        #     "type": "general",
        #     "message": llm_output if llm_output else json.dumps(_product_data, ensure_ascii=False, indent=2),
        #     "success": True
        # }
        return response_result
        # if self.response_generator:
        #     response_result = await self.response_generator.generate(context)
        #     context.update(response_result)
            
        #     # 映射 ResponseGenHandler 的字段到 _format_frontend_response 期待的字段
        #     if response_result.get("type") == "funnel_question":
        #         context["current_question"] = response_result.get("current_question")
        #         context["question_options"] = response_result.get("question_options", [])
        #         context["question_message"] = response_result.get("message", "")
        # else:
        #     context.update({
        #         "response_type": "general",
        #         "message": "回應生成器未初始化"
        #     })
        
        # result = self._format_frontend_response(context)
        # logger.info(f"🔧 最終回應結果: {result}")
        # return result
    
    # async def _process_message_internal(
    #     self, 
    #     session_id: str, 
    #     message: str
    # ) -> Dict[str, Any]:
    #     """
    #     內部消息處理流程
        
    #     Args:
    #         session_id: 會話識別碼
    #         message: 用戶輸入消息
            
    #     Returns:
    #         處理結果字典
    #     """
    #     # Step 1: 建立 context
    #     context = await self._build_context(session_id, message)
        
    #     # Step 2: 解析輸入（UserInputHandler）
    #     if self.user_input_handler:
    #         input_result = await self.user_input_handler.parse(message, context)
    #         context.update(input_result)
    #     else:
    #         # 暫時使用基本解析
    #         context.update({
    #             "intent": "unknown",
    #             "slots_update": {},
    #             "control": {},
    #             "errors": [],
    #             "confidence": 0.0
    #         })
        
    #     # Step 3: 狀態機驅動（StateManager）
    #     if self.state_manager:
    #         state_result = await self.state_manager.process_state(context)
    #         context.update(state_result)
    #     else:
    #         # 暫時使用基本狀態處理
    #         context.update({
    #             "stage": "INIT",
    #             "needs_knowledge_search": False
    #         })
        
    #     # Step 4: 知識查詢（如需要）
    #     if context.get('needs_knowledge_search') and self.knowledge_manager:
    #         knowledge_result = await self.knowledge_manager.search(context)
    #         context.update(knowledge_result)
        
    #     # Step 5: 生成回應（ResponseGenerator）
    #     if self.response_generator:
    #         response_result = await self.response_generator.generate(context)
    #         context.update(response_result)
    #     else:
    #         # 暫時使用基本回應
    #         context.update({
    #             "response_type": "general",
    #             "response_message": "系統正在處理您的請求..."
    #         })
        
    #     # Step 6: 更新狀態
    #     if self.state_manager:
    #         await self.state_manager.update_session_state(session_id, context)
        
    #     return self._format_frontend_response(context)
    
    # async def _build_context(
    #     self, 
    #     session_id: str, 
    #     message: str
    # ) -> Dict[str, Any]:
    #     """
    #     建立處理上下文
        
    #     Args:
    #         session_id: 會話識別碼
    #         message: 用戶輸入消息
            
    #     Returns:
    #         上下文字典
    #     """
    #     # 獲取現有會話狀態
    #     session_state = {}
    #     if self.state_manager:
    #         session_state = await self.state_manager.get_session_state(session_id) or {}
        
    #     # 根據消息內容確定狀態
    #     if message and message.strip():
    #         current_state = "OnReceiveMsg"
    #     else:
    #         current_state = session_state.get("state", "OnWaitMsg")
        
    #     context = {
    #         "session_id": session_id,
    #         "user_message": message,
    #         "timestamp": datetime.now().isoformat(),
    #         "state": current_state,
    #         "slots": session_state.get("slots", {}),
    #         "history": session_state.get("history", []),
    #         "control": {},
    #         "errors": [],
    #         "slot_schema": self.slot_schema,
    #         "config": self.config
    #     }
        
    #     return context
    
    def _format_frontend_response(
        self, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        格式化前端回應
        
        Args:
            context: 處理上下文
            
        Returns:
            格式化後的回應字典
        """
        state = context.get('state', 'unknown')
        response_type = context.get('response_type', 'general')
        
        # 根據狀態和回應類型格式化
        if state == 'OnReceiveMsg':
            return {
                "success": True,
                "type": "funnel_start",
                "message": context.get('funnel_intro', '歡迎使用筆電購物助手！'),
                "session_id": context.get('session_id')
            }
        elif state == 'OnGenFunnelChat':
            return {
                "success": True,
                "type": "funnel_question",
                "question": {
                    "question_text": context.get('current_question'),
                    "options": context.get('question_options', [])
                },
                "session_id": context.get('session_id'),
                "message": context.get('question_message', '')
            }
        elif state == 'OnResponseMsg':
            return {
                "success": True,
                "type": "recommendation",
                "recommendations": context.get('recommendations', []),
                "comparison_table": context.get('comparison_table'),
                "summary": context.get('recommendation_summary'),
                "session_id": context.get('session_id')
            }
        elif state == 'OnGenMDContent':
            return {
                "success": True,
                "type": "elicitation",
                "message": context.get('elicitation_message'),
                "slots_needed": context.get('slots_needed', []),
                "session_id": context.get('session_id')
            }
        else:
            # 直接返回結構化格式，不要包裝成 stream_response
            return {
                "success": True,
                "type": "general",
                "message": context.get('message') or context.get('response_message', ''),
                "session_id": context.get('session_id')
            }
    
    def _check_modules_initialized(self) -> bool:
        """檢查模組是否已初始化"""
        # 只需要 UserInputHandler 已初始化即可進行基本處理
        return self.user_input_handler is not None
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """創建錯誤回應"""
        return {
            "success": False,
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
    
    def set_user_input_handler(self, handler):
        """設置用戶輸入處理器"""
        self.user_input_handler = handler
        logger.info("UserInputHandler 已設置")
    
    def set_prompt_manager(self, manager):
        """設置提示管理器"""
        self.prompt_manager = manager
        logger.info("PromptManagementHandler 已設置")
    
    def set_knowledge_manager(self, manager):
        """設置知識管理器"""
        self.knowledge_manager = manager
        logger.info("KnowledgeManagementHandler 已設置")
    
    def set_response_generator(self, generator):
        """設置回應生成器"""
        self.response_generator = generator
        logger.info("ResponseGenHandler 已設置")
    
    def set_state_manager(self, manager):
        """設置狀態管理器"""
        self.state_manager = manager
        logger.info("StateManagementHandler 已設置")
