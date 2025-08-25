import asyncio
import uuid
import time
from typing import Dict, Any, List
from dataclasses import asdict

# =====================================
# MGFD完整工作流程示例：Case-1實現
# =====================================

class MGFDWorkflowExample:
    """MGFD系統完整工作流程示例"""
    
    def __init__(self):
        self.kernel = MGFDKernel()
        self.session_contexts = {}
    
    async def handle_user_request(self, user_input: str, session_id: str) -> Dict[str, Any]:
        """處理用戶請求的完整流程"""
        
        # 步驟1：初始化會話上下文
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = self.kernel.create_standard_context(session_id)
        
        context = self.session_contexts[session_id]
        context["raw_user_input"] = user_input
        context["workflow_trace"] = []  # 用於追蹤整個流程
        
        try:
            # 步驟2：用戶輸入分析
            analysis_result = await self._step_user_input_analysis(context)
            if analysis_result.status != ActionStatus.SUCCESS:
                return self._create_error_response("輸入分析失敗", analysis_result.message)
            
            # 步驟3：意圖識別和槽位提取
            intent_result = await self._step_intent_extraction(context) 
            if intent_result.status != ActionStatus.SUCCESS:
                return self._create_error_response("意圖識別失敗", intent_result.message)
            
            # 步驟4：檢查是否需要槽位補充
            if self._needs_slot_filling(context):
                return await self._step_slot_filling_conversation(context)
            
            # 步驟5：知識庫搜索
            search_result = await self._step_knowledge_search(context)
            if search_result.status != ActionStatus.SUCCESS:
                return self._create_error_response("知識搜索失敗", search_result.message)
            
            # 步驟6：提示工程和響應生成
            response_result = await self._step_response_generation(context)
            if response_result.status != ActionStatus.SUCCESS:
                return self._create_error_response("響應生成失敗", response_result.message)
            
            # 步驟7：狀態更新
            await self._step_state_update(context)
            
            return {
                "success": True,
                "response": context.get("final_response"),
                "ui_elements": context.get("ui_elements"),
                "session_id": session_id,
                "workflow_trace": context["workflow_trace"]
            }
            
        except Exception as e:
            return self._create_error_response("系統錯誤", str(e))
    
    async def _step_user_input_analysis(self, context: Dict[str, Any]) -> ActionResult:
        """步驟1：用戶輸入分析"""
        start_time = time.time()
        context["workflow_trace"].append("開始用戶輸入分析")
        
        # 創建UserInputHandler請求消息
        request_payload = UserInputHandlerProtocol.create_input_analysis_request(
            context["raw_user_input"], 
            context["session_id"]
        )
        
        message = MGFDMessage(
            message_id=str(uuid.uuid4()),
            message_type=MGFDMessageType.USER_INPUT_REQUEST,
            sender_module="MGFDKernel",
            receiver_module="UserInputHandler", 
            timestamp=time.time(),
            payload=request_payload,
            correlation_id=context["session_id"]
        )
        
        # 模擬UserInputHandler響應
        mock_response = {
            "status": "success",
            "data": {
                "parsed_input": context["raw_user_input"],
                "language": "zh-TW",
                "input_type": "product_inquiry",
                "preprocessing_applied": ["normalization", "tokenization"]
            }
        }
        
        # 更新上下文
        context.update(mock_response["data"])
        context["workflow_trace"].append(f"輸入分析完成 - {time.time() - start_time:.3f}s")
        
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data=mock_response["data"],
            execution_time=time.time() - start_time
        )
    
    async def _step_intent_extraction(self, context: Dict[str, Any]) -> ActionResult:
        """步驟2：意圖提取和實體識別"""
        start_time = time.time()
        context["workflow_trace"].append("開始意圖提取")
        
        # 模擬NLP處理結果
        mock_nlp_result = {
            "intent": "laptop_recommendation_request",
            "confidence": 0.92,
            "entities": [
                {"type": "PRODUCT", "value": "筆電", "start": 6, "end": 8},
                {"type": "REQUIREMENT", "value": "新出的", "start": 2, "end": 5}
            ],
            "extracted_slots": {
                "product_category": "筆電",
                "requirement_type": "最新產品",
                "budget": None,  # 需要後續收集
                "usage_scenario": None  # 需要後續收集
            }
        }
        
        # 更新上下文
        context.update(mock_nlp_result)
        context["workflow_trace"].append(f"意圖提取完成 - 意圖: {mock_nlp_result['intent']}")
        
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data=mock_nlp_result,
            execution_time=time.time() - start_time
        )
    
    def _needs_slot_filling(self, context: Dict[str, Any]) -> bool:
        """檢查是否需要槽位補充"""
        slots = context.get("extracted_slots", {})
        required_slots = ["product_category", "budget", "usage_scenario"]
        
        missing_slots = [slot for slot in required_slots if not slots.get(slot)]
        context["missing_slots"] = missing_slots
        
        return len(missing_slots) > 0
    
    async def _step_slot_filling_conversation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """步驟3：槽位補充對話"""
        context["workflow_trace"].append("進入槽位補充對話")
        
        missing_slots = context["missing_slots"]
        next_slot = missing_slots[0]
        
        # 生成槽位收集問題
        slot_questions = {
            "budget": "請問您的預算範圍是多少？",
            "usage_scenario": "請問您主要用這台筆電做什麼用途？（例如：辦公、遊戲、設計等）"
        }
        
        question = slot_questions.get(next_slot, f"請提供 {next_slot} 的相關信息")
        
        return {
            "success": True,
            "response": question,
            "ui_elements": {
                "type": "slot_collection",
                "required_slot": next_slot,
                "progress": {
                    "completed": len(context["extracted_slots"]) - len(missing_slots),
                    "total": len(context["extracted_slots"])
                }
            },
            "session_id": context["session_id"],
            "requires_user_response": True
        }
    
    async def _step_knowledge_search(self, context: Dict[str, Any]) -> ActionResult:
        """步驟4：知識庫語義搜索"""
        start_time = time.time()
        context["workflow_trace"].append("開始知識庫搜索")
        
        # 構建搜索請求
        search_request = KnowledgeManagementHandlerProtocol.create_chunking_search_request(
            query=f"推薦{context['extracted_slots']['product_category']}",
            slots=context["extracted_slots"]
        )
        
        # 模擬Parent-Child Chunking搜索結果
        mock_search_results = [
            {
                "product_id": "LAPTOP_2024_001",
                "product_name": "MacBook Pro 14\" M3",
                "similarity_score": 0.94,
                "chunk_info": {
                    "chunk_type": "parent",
                    "chunk_id": "PARENT_LAPTOP_001",
                    "child_chunks": ["CHILD_PERFORMANCE_001", "CHILD_DESIGN_001"]
                },
                "matching_reasons": [
                    "符合最新產品要求",
                    "高效能處理器",
                    "專業級設計"
                ],
                "specifications": {
                    "processor": "Apple M3 Pro",
                    "memory": "18GB",
                    "storage": "512GB SSD",
                    "display": "14.2吋 Liquid Retina XDR",
                    "price": "NT$ 69,900"
                }
            },
            {
                "product_id": "LAPTOP_2024_002", 
                "product_name": "ASUS ROG Zephyrus G14",
                "similarity_score": 0.89,
                "chunk_info": {
                    "chunk_type": "child", 
                    "chunk_id": "CHILD_GAMING_002",
                    "parent_chunk": "PARENT_LAPTOP_002"
                },
                "matching_reasons": [
                    "2024年新款",
                    "遊戲效能優異", 
                    "便攜性佳"
                ],
                "specifications": {
                    "processor": "AMD Ryzen 9 7940HS",
                    "memory": "32GB",
                    "storage": "1TB SSD",
                    "graphics": "NVIDIA RTX 4060",
                    "price": "NT$ 59,900"
                }
            }
        ]
        
        # 更新上下文
        context["search_results"] = mock_search_results
        context["total_matches"] = len(mock_search_results)
        context["workflow_trace"].append(f"搜索完成 - 找到 {len(mock_search_results)} 個相關產品")
        
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={"search_results": mock_search_results},
            execution_time=time.time() - start_time
        )
    
    async def _step_response_generation(self, context: Dict[str, Any]) -> ActionResult:
        """步驟5：響應生成"""
        start_time = time.time()
        context["workflow_trace"].append("開始響應生成")
        
        # 選擇適當的提示模板
        prompt_request = PromptManagementHandlerProtocol.create_prompt_selection_request(
            context=context,
            intent=context["intent"]
        )
        
        # 模擬選中的提示模板
        selected_prompt = """
        根據用戶的需求，為以下筆電產品生成專業的推薦說明：
        - 重點突出產品特色和優勢
        - 說明為什麼適合用戶需求  
        - 提供清晰的規格對比
        - 語調要專業友善
        """
        
        # 生成響應內容
        response_content = self._generate_product_recommendation_response(
            context["search_results"], 
            context["extracted_slots"]
        )
        
        # 生成UI元素
        ui_elements = {
            "type": "product_recommendation",
            "products": [
                {
                    "id": result["product_id"],
                    "name": result["product_name"],
                    "image_url": f"/images/{result['product_id']}.jpg",
                    "key_specs": result["specifications"],
                    "similarity_score": result["similarity_score"],
                    "recommendation_reasons": result["matching_reasons"]
                }
                for result in context["search_results"]
            ],
            "follow_up_questions": [
                "需要了解更詳細的規格嗎？",
                "想看其他價格區間的選擇嗎？",
                "有什麼具體的使用需求要討論？"
            ]
        }
        
        # 更新上下文
        context["final_response"] = response_content
        context["ui_elements"] = ui_elements
        context["workflow_trace"].append(f"響應生成完成 - {time.time() - start_time:.3f}s")
        
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={"response": response_content, "ui_elements": ui_elements},
            execution_time=time.time() - start_time
        )
    
    def _generate_product_recommendation_response(self, search_results: List[Dict], slots: Dict[str, Any]) -> str:
        """生成產品推薦響應內容"""
        response = "根據您對最新筆電的需求，我為您推薦以下幾款產品：\n\n"
        
        for i, product in enumerate(search_results, 1):
            response += f"**{i}. {product['product_name']}**\n"
            response += f"價格：{product['specifications']['price']}\n"
            response += f"推薦理由：{', '.join(product['matching_reasons'])}\n"
            response += f"相似度：{product['similarity_score']:.1%}\n\n"
            
            response += "主要規格：\n"
            for key, value in product['specifications'].items():
                if key != 'price':
                    response += f"- {key.title()}: {value}\n"
            response += "\n---\n\n"
        
        response += "這些產品都是2024年的最新款，您可以根據預算和使用需求選擇。需要我詳細介紹哪一款嗎？"
        
        return response
    
    async def _step_state_update(self, context: Dict[str, Any]) -> ActionResult:
        """步驟6：狀態更新"""
        start_time = time.time()
        context["workflow_trace"].append("更新狀態管理")
        
        # 更新會話狀態到Redis（模擬）
        state_update_request = StateManagementHandlerProtocol.create_state_transition_request(
            current_state="DataQuery",
            trigger="search_completed", 
            context=context
        )
        
        # 模擬狀態更新響應
        context["current_state"] = "User"  # 回到等待用戶響應狀態
        context["last_action"] = "product_recommendation_generated"
        context["workflow_trace"].append("狀態更新完成")
        
        return ActionResult(
            status=ActionStatus.SUCCESS,
            data={"new_state": "User"},
            execution_time=time.time() - start_time
        )
    
    def _create_error_response(self, error_type: str, error_message: str) -> Dict[str, Any]:
        """創建錯誤響應"""
        return {
            "success": False,
            "error": {
                "type": error_type,
                "message": error_message,
                "timestamp": time.time()
            },
            "response": f"抱歉，處理您的請求時遇到問題：{error_message}",
            "ui_elements": {
                "type": "error",
                "retry_available": True
            }
        }

# =====================================
# 使用範例
# =====================================

async def demo_mgfd_workflow():
    """演示MGFD完整工作流程"""
    workflow = MGFDWorkflowExample()
    
    print("=== MGFD SalesRAG 系統工作流程演示 ===\n")
    
    # 模擬用戶請求
    user_input = "請介紹目前新出的筆電"
    session_id = str(uuid.uuid4())
    
    print(f"用戶輸入: {user_input}")
    print(f"會話ID: {session_id}\n")
    
    # 執行工作流程
    result = await workflow.handle_user_request(user_input, session_id)
    
    if result["success"]:
        print("✅ 處理成功！")
        print(f"\n系統響應:\n{result['response']}\n")
        
        print("📊 UI元素:")
        ui_elements = result["ui_elements"]
        if ui_elements["type"] == "product_recommendation":
            print(f"- 推薦產品數量: {len(ui_elements['products'])}")
            for product in ui_elements["products"]:
                print(f"  * {product['name']} (相似度: {product['similarity_score']:.1%})")
        
        print(f"\n🔍 工作流程追蹤:")
        for i, step in enumerate(result["workflow_trace"], 1):
            print(f"  {i}. {step}")
    else:
        print("❌ 處理失敗！")
        print(f"錯誤: {result['error']['message']}")

# 運行演示
if __name__ == "__main__":
    asyncio.run(demo_mgfd_workflow())