#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澄清對話管理器
負責處理用戶意圖不明確時的澄清對話流程
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ConversationState:
    """對話狀態"""
    conversation_id: str
    user_query: str
    current_step: int
    total_steps: int
    clarification_history: List[Dict]
    collected_context: Dict
    confidence_threshold: float
    flow_type: str
    created_at: str
    updated_at: str

@dataclass
class ClarificationQuestion:
    """澄清問題"""
    question_id: str
    template_name: str
    question: str
    question_type: str
    options: List[Dict]
    conversation_id: str
    step: int

@dataclass 
class ClarificationResponse:
    """澄清回應"""
    response_id: str
    question_id: str
    user_choice: str
    user_input: str
    conversation_id: str
    timestamp: str

class ClarificationManager:
    """澄清對話管理器"""
    
    def __init__(self, templates_path: str = None):
        """
        初始化澄清對話管理器
        
        Args:
            templates_path: 澄清問題模板文件路徑
        """
        self.templates_path = templates_path or "sales_rag_app/libs/services/sales_assistant/prompts/clarification_templates.json"
        self.clarification_templates = self._load_clarification_templates()
        self.active_conversations: Dict[str, ConversationState] = {}
        self.confidence_threshold = 0.6  # 默認信心度閾值
        
        logging.info("澄清對話管理器初始化完成")
    
    def _load_clarification_templates(self) -> Dict:
        """載入澄清問題模板"""
        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
                logging.info(f"成功載入澄清模板: {list(templates.get('clarification_templates', {}).keys())}")
                return templates
        except FileNotFoundError:
            logging.error(f"澄清模板文件不存在: {self.templates_path}")
            return self._get_default_templates()
        except Exception as e:
            logging.error(f"載入澄清模板失敗: {e}")
            return self._get_default_templates()
    
    def _get_default_templates(self) -> Dict:
        """獲取預設澄清模板"""
        return {
            "clarification_templates": {
                "usage_scenario": {
                    "question": "請問您的主要使用場景是什麼？",
                    "options": [
                        {"id": "gaming", "label": "🎮 遊戲娛樂"},
                        {"id": "business", "label": "💼 商務辦公"},
                        {"id": "creation", "label": "🎨 設計創作"},
                        {"id": "study", "label": "📚 學習研究"}
                    ]
                }
            }
        }
    
    def should_clarify(self, intent_result: Dict, confidence_threshold: float = None) -> bool:
        """
        判斷是否需要進行澄清對話
        
        Args:
            intent_result: 意圖檢測結果
            confidence_threshold: 信心度閾值
            
        Returns:
            是否需要澄清
        """
        try:
            threshold = confidence_threshold or self.confidence_threshold
            confidence_score = intent_result.get("confidence_score", 0.0)
            primary_intent = intent_result.get("primary_intent", "general")
            
            # 條件1: 信心度低於閾值
            if confidence_score < threshold:
                logging.info(f"信心度 {confidence_score:.2f} 低於閾值 {threshold}，需要澄清")
                return True
            
            # 條件2: 檢測到一般意圖
            if primary_intent == "general":
                logging.info("檢測到一般意圖，需要澄清")
                return True
            
            # 條件3: 沒有檢測到任何實體
            entities = intent_result.get("entities", [])
            if not entities:
                logging.info("未檢測到任何實體，需要澄清")
                return True
            
            # 條件4: 意圖衝突（多個高信心度意圖）
            high_confidence_intents = intent_result.get("high_confidence_intents", [])
            if len(high_confidence_intents) > 2:
                logging.info(f"檢測到多個意圖衝突 ({len(high_confidence_intents)} 個)，需要澄清")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"判斷是否需要澄清時發生錯誤: {e}")
            return True  # 出錯時傾向於澄清
    
    def start_clarification(self, query: str, intent_result: Dict) -> Tuple[str, ClarificationQuestion]:
        """
        開始澄清對話流程
        
        Args:
            query: 用戶原始查詢
            intent_result: 意圖檢測結果
            
        Returns:
            (conversation_id, clarification_question)
        """
        try:
            conversation_id = str(uuid.uuid4())
            
            # 決定澄清流程類型
            flow_type = self._determine_clarification_flow(intent_result)
            
            # 創建對話狀態
            conversation_state = ConversationState(
                conversation_id=conversation_id,
                user_query=query,
                current_step=1,
                total_steps=self._get_flow_total_steps(flow_type),
                clarification_history=[],
                collected_context={
                    "original_intent_result": intent_result,
                    "flow_type": flow_type
                },
                confidence_threshold=self.confidence_threshold,
                flow_type=flow_type,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            self.active_conversations[conversation_id] = conversation_state
            
            # 生成第一個澄清問題
            clarification_question = self._generate_clarification_question(conversation_state)
            
            logging.info(f"開始澄清對話: {conversation_id}, 流程類型: {flow_type}")
            return conversation_id, clarification_question
            
        except Exception as e:
            logging.error(f"開始澄清對話時發生錯誤: {e}")
            raise
    
    def _determine_clarification_flow(self, intent_result: Dict) -> str:
        """
        根據意圖結果決定澄清流程類型
        
        Args:
            intent_result: 意圖檢測結果
            
        Returns:
            澄清流程類型
        """
        primary_intent = intent_result.get("primary_intent", "general")
        intent_type = intent_result.get("primary_intent_type", "base")
        
        # 根據主要意圖決定流程
        if primary_intent == "comparison" or "comparison" in primary_intent:
            return "comparison_inquiry"
        elif primary_intent in ["cpu", "gpu", "memory", "storage"] or intent_type == "sub":
            return "performance_inquiry"
        elif primary_intent == "latest" or "latest" in primary_intent:
            return "latest_inquiry"
        else:
            return "general_inquiry"
    
    def _get_flow_total_steps(self, flow_type: str) -> int:
        """獲取流程總步數"""
        flow_configs = self.clarification_templates.get("clarification_flows", {})
        flow_config = flow_configs.get(flow_type, {})
        steps = flow_config.get("steps", [])
        return len([step for step in steps if step.get("required", True)])
    
    def _generate_clarification_question(self, conversation_state: ConversationState) -> ClarificationQuestion:
        """
        生成澄清問題
        
        Args:
            conversation_state: 對話狀態
            
        Returns:
            澄清問題
        """
        try:
            flow_type = conversation_state.flow_type
            current_step = conversation_state.current_step
            
            # 獲取流程配置
            flow_configs = self.clarification_templates.get("clarification_flows", {})
            flow_config = flow_configs.get(flow_type, {})
            steps = flow_config.get("steps", [])
            
            # 找到當前步驟
            current_step_config = None
            for step_config in steps:
                if step_config.get("step") == current_step:
                    current_step_config = step_config
                    break
            
            if not current_step_config:
                # 如果沒有找到配置，使用預設模板
                template_name = "usage_scenario"
            else:
                template_name = current_step_config.get("template", "usage_scenario")
            
            # 獲取模板
            templates = self.clarification_templates.get("clarification_templates", {})
            template = templates.get(template_name, {})
            
            if not template:
                raise ValueError(f"找不到澄清模板: {template_name}")
            
            # 創建澄清問題
            question_id = str(uuid.uuid4())
            clarification_question = ClarificationQuestion(
                question_id=question_id,
                template_name=template_name,
                question=template.get("question", "請選擇您的需求"),
                question_type=template.get("question_type", "single_choice"),
                options=template.get("options", []),
                conversation_id=conversation_state.conversation_id,
                step=current_step
            )
            
            return clarification_question
            
        except Exception as e:
            logging.error(f"生成澄清問題時發生錯誤: {e}")
            raise
    
    def process_clarification_response(self, conversation_id: str, user_choice: str, 
                                     user_input: str = "") -> Dict:
        """
        處理用戶的澄清回應
        
        Args:
            conversation_id: 對話ID
            user_choice: 用戶選擇的選項ID
            user_input: 用戶額外輸入
            
        Returns:
            處理結果
        """
        try:
            if conversation_id not in self.active_conversations:
                raise ValueError(f"找不到對話: {conversation_id}")
            
            conversation_state = self.active_conversations[conversation_id]
            
            # 記錄澄清回應
            clarification_response = ClarificationResponse(
                response_id=str(uuid.uuid4()),
                question_id="",  # 這裡可以後續完善
                user_choice=user_choice,
                user_input=user_input,
                conversation_id=conversation_id,
                timestamp=datetime.now().isoformat()
            )
            
            # 更新對話歷史
            conversation_state.clarification_history.append({
                "step": conversation_state.current_step,
                "user_choice": user_choice,
                "user_input": user_input,
                "timestamp": clarification_response.timestamp
            })
            
            # 更新收集到的上下文
            self._update_collected_context(conversation_state, user_choice, user_input)
            
            # 判斷是否需要下一步澄清
            next_action = self._determine_next_action(conversation_state)
            
            # 更新對話狀態
            conversation_state.updated_at = datetime.now().isoformat()
            
            if next_action == "continue":
                # 繼續下一步澄清
                conversation_state.current_step += 1
                next_question = self._generate_clarification_question(conversation_state)
                
                return {
                    "action": "continue",
                    "conversation_id": conversation_id,
                    "next_question": next_question,
                    "current_step": conversation_state.current_step,
                    "total_steps": conversation_state.total_steps
                }
            
            elif next_action == "complete":
                # 澄清完成，生成增強的意圖結果
                enhanced_intent = self._generate_enhanced_intent(conversation_state)
                
                # 移除活躍對話
                del self.active_conversations[conversation_id]
                
                return {
                    "action": "complete",
                    "conversation_id": conversation_id,
                    "enhanced_intent": enhanced_intent,
                    "clarification_summary": self._generate_clarification_summary(conversation_state)
                }
            
            else:
                raise ValueError(f"未知的下一步動作: {next_action}")
                
        except Exception as e:
            logging.error(f"處理澄清回應時發生錯誤: {e}")
            raise
    
    def _update_collected_context(self, conversation_state: ConversationState, 
                                 user_choice: str, user_input: str):
        """更新收集到的上下文資訊"""
        current_step = conversation_state.current_step
        
        # 根據步驟和選擇更新上下文
        if current_step == 1:
            conversation_state.collected_context["usage_scenario"] = user_choice
        elif current_step == 2:
            conversation_state.collected_context["budget_range"] = user_choice
        elif current_step == 3:
            conversation_state.collected_context["specific_requirements"] = user_choice
        
        # 保存額外輸入
        if user_input:
            conversation_state.collected_context[f"step_{current_step}_input"] = user_input
    
    def _determine_next_action(self, conversation_state: ConversationState) -> str:
        """決定下一步動作"""
        # 簡單邏輯：如果達到總步數或收集到足夠資訊就完成
        if conversation_state.current_step >= conversation_state.total_steps:
            return "complete"
        
        # 檢查是否收集到足夠的關鍵資訊
        collected_context = conversation_state.collected_context
        if "usage_scenario" in collected_context and collected_context["usage_scenario"] != "no_preference":
            # 如果已確定使用場景且不是無偏好，可能可以提前結束
            if conversation_state.flow_type == "general_inquiry" and conversation_state.current_step >= 1:
                return "complete"
        
        return "continue"
    
    def _generate_enhanced_intent(self, conversation_state: ConversationState) -> Dict:
        """生成增強的意圖結果"""
        original_intent = conversation_state.collected_context.get("original_intent_result", {})
        collected_context = conversation_state.collected_context
        
        # 基於澄清結果增強意圖
        enhanced_intent = original_intent.copy()
        enhanced_intent["clarification_enhanced"] = True
        enhanced_intent["confidence_score"] = 0.9  # 澄清後信心度提高
        
        # 根據使用場景更新主要意圖
        usage_scenario = collected_context.get("usage_scenario")
        if usage_scenario:
            if usage_scenario == "gaming":
                enhanced_intent["primary_intent"] = "gaming_gpu"
                enhanced_intent["priority_specs"] = ["gpu", "cpu", "memory"]
            elif usage_scenario == "business":
                enhanced_intent["primary_intent"] = "energy_efficient_cpu"
                enhanced_intent["priority_specs"] = ["cpu", "battery", "structconfig"]
            elif usage_scenario == "creation":
                enhanced_intent["primary_intent"] = "professional_gpu"
                enhanced_intent["priority_specs"] = ["gpu", "cpu", "memory", "storage"]
            elif usage_scenario == "study":
                enhanced_intent["primary_intent"] = "long_battery"
                enhanced_intent["priority_specs"] = ["cpu", "battery", "structconfig"]
        
        # 添加澄清上下文
        enhanced_intent["clarification_context"] = collected_context
        
        return enhanced_intent
    
    def _generate_clarification_summary(self, conversation_state: ConversationState) -> str:
        """生成澄清對話總結"""
        collected_context = conversation_state.collected_context
        history = conversation_state.clarification_history
        
        summary_parts = []
        
        # 使用場景
        usage_scenario = collected_context.get("usage_scenario")
        if usage_scenario:
            scenario_labels = {
                "gaming": "遊戲娛樂",
                "business": "商務辦公", 
                "creation": "設計創作",
                "study": "學習研究"
            }
            summary_parts.append(f"使用場景：{scenario_labels.get(usage_scenario, usage_scenario)}")
        
        # 預算範圍
        budget_range = collected_context.get("budget_range")
        if budget_range:
            budget_labels = {
                "economy": "經濟型",
                "mid_range": "中階型",
                "premium": "高階型"
            }
            summary_parts.append(f"預算範圍：{budget_labels.get(budget_range, budget_range)}")
        
        # 特殊需求
        specific_requirements = collected_context.get("specific_requirements")
        if specific_requirements and specific_requirements != "no_specific":
            req_labels = {
                "large_screen": "大螢幕",
                "high_memory": "大記憶體",
                "fast_storage": "高速儲存",
                "rich_ports": "豐富接口"
            }
            summary_parts.append(f"特殊需求：{req_labels.get(specific_requirements, specific_requirements)}")
        
        if summary_parts:
            return f"根據您的澄清回應，我了解到您的需求：{' | '.join(summary_parts)}"
        else:
            return "感謝您提供的額外資訊，這將幫助我為您提供更精準的推薦。"
    
    def get_conversation_state(self, conversation_id: str) -> Optional[ConversationState]:
        """獲取對話狀態"""
        return self.active_conversations.get(conversation_id)
    
    def cleanup_expired_conversations(self, hours: int = 24):
        """清理過期的對話"""
        try:
            current_time = datetime.now()
            expired_ids = []
            
            for conv_id, state in self.active_conversations.items():
                created_time = datetime.fromisoformat(state.created_at)
                if (current_time - created_time).total_seconds() > hours * 3600:
                    expired_ids.append(conv_id)
            
            for conv_id in expired_ids:
                del self.active_conversations[conv_id]
                logging.info(f"清理過期對話: {conv_id}")
                
        except Exception as e:
            logging.error(f"清理過期對話時發生錯誤: {e}")