"""
MGFD 核心控制器 - 系統大腦及對外唯一介面
負責協調五大模組，管理對話流程，處理前端請求
"""

import logging
import json
import redis
from typing import Dict, Any, Optional, List
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
logger = logging.getLogger(__name__)

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
        self.slot_schema = self._load_slot_schema()
        
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
        # System-level prompt
        self.SysPrompt = (
            "1.Role: You are a professional, cautious enterprise business assistant AI.\n"
            "2.Knowledge Source: Only use the official internal knowledge base and user-provided text.\n"
            "3.Prohibited: No fabrication, guessing, or using external knowledge.\n"
            "4.Thinking Rule: Plan internally first (not shown), then generate the reply.\n"
            "5.Response Format:\n\t- Executive Summary: 1–3 sentences with the direct answer\n\t- Detailed Breakdown: Features → Usage → Recommendations\n\t- Closing Guidance: Customer service note or next-step prompt\n"
            "6.Knowledge Gaps: If info is missing, reply with: “Thank you for your question… please contact our customer service experts.”\n"
            "7.Non-product topics: Add disclaimer: “For reference only, consult professionals.”\n"
            "8.Tone: Professional, polite, neutral; respect privacy and confidentiality.\n"
            """
            9.Context: 
                product data:
                ```text
                    {product_data}
                ```
                prompt using:
                ```text
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
                ```
                
                user_query:
                ```text
                    {user_query}
                ```
            """
            "10.If {product_data} is empty, display “Product Data: None”.\n"
        )
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
        except Exception as e:
            logger.error(f"模組初始化失敗: {e}")
            # 如果初始化失敗，設置為 None
            self.user_input_handler = None
            self.prompt_manager = None
            self.knowledge_manager = None
            self.response_generator = None
            self.state_manager = None
        
        logger.info("MGFDKernel 初始化完成")
    # generate three-tier prompt
    def generate_three_tier_prompt(self):
        """生成三層式提示"""
        return self.SysPrompt.format(product_data=self.product_data, prompt_using=self.prompt_using, 
                                     answer=self.answer, query=self.query)
    
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
            logger.info(f"處理消息 - 會話: {session_id}, 消息: {message[:50]}...")
            
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
        if self.user_input_handler:
            slot_name, slot_metadata = await self.user_input_handler.parse_keyword(message)
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
        if slot_metadata["ifDBSearch"]:
            
            logging.info(f"先查詢產品資料: {context['query_result']}")
            #search_product_data
            _product_data = await self.search_product_data(message)
            #next step: generate three-tier prompt
            self.SysPrompt = self.SysPrompt.format(product_data=_product_data,
                                                   query=context["user_message"])
            context['query_result'] = {"qry_result":_product_data}
            context['keyword'] = "data"
            logging.info(f"知識查詢結果: {context['query_result']}")
            #進行
            
        
        # Step 6: 生成回應（ResponseGenerator）
        # 先手動生成回應傳回前端
        # if self.
        response_result = {
            "type": "general",
            "message": _product_data,
            "success": True
        }
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
