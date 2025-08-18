#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt處理器 - 整合基礎Prompt規則與Think-then-Act原則
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

class PromptProcessor:
    """Prompt處理器 - 實現Think-then-Act和基礎規則"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 基礎Prompt規則（來自MGFD_Foundmental_Prompt_v1_old.txt）
        self.fundamental_rules = {
            "think_then_act": True,
            "focus_on_query": True,
            "company_data_only": True,
            "no_speculation": True,
            "data_insufficient_handling": True,
            "professional_tone": True
        }
        
        # 回應建議格式
        self.response_format = {
            "概括回答": "1-2行精準對焦核心需求",
            "詳細說明": "產品特點/功能說明 → 使用情境/步驟 → 加值建議",
            "清單格式": "簡明清單或表格呈現要點",
            "客服提示": "資訊不足時提供客服聯絡"
        }
    
    def process_with_think_then_act(self, user_input: str, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用Think-then-Act原則處理用戶輸入
        
        Args:
            user_input: 用戶輸入
            current_context: 當前對話上下文
            
        Returns:
            處理結果
        """
        try:
            # Think階段：理解和分析
            think_result = self._think_phase(user_input, current_context)
            
            # Act階段：生成回應
            act_result = self._act_phase(think_result)
            
            return {
                "success": True,
                "think_phase": think_result,
                "act_phase": act_result,
                "final_response": act_result.get("response", ""),
                "confidence": act_result.get("confidence", 0.5)
            }
            
        except Exception as e:
            self.logger.error(f"Think-then-Act處理失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "final_response": "處理失敗，請重新輸入。"
            }
    
    def _think_phase(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Think階段：分析用戶意圖和需求"""
        analysis = {
            "user_intent": self._analyze_user_intent(user_input),
            "key_requirements": self._extract_key_requirements(user_input),
            "context_relevance": self._assess_context_relevance(user_input, context),
            "data_availability": self._check_data_availability(user_input),
            "response_strategy": self._determine_response_strategy(user_input, context)
        }
        
        self.logger.debug(f"Think階段分析完成: {analysis}")
        return analysis
    
    def _act_phase(self, think_result: Dict[str, Any]) -> Dict[str, Any]:
        """Act階段：基於分析生成回應"""
        response_strategy = think_result.get("response_strategy", "general")
        
        if response_strategy == "product_recommendation":
            return self._generate_product_response(think_result)
        elif response_strategy == "slot_collection":
            return self._generate_question_response(think_result)
        elif response_strategy == "information_clarification":
            return self._generate_clarification_response(think_result)
        else:
            return self._generate_general_response(think_result)
    
    def _analyze_user_intent(self, user_input: str) -> str:
        """分析用戶意圖"""
        user_lower = user_input.lower()
        
        # 產品推薦意圖
        if any(word in user_lower for word in ["推薦", "介紹", "建議", "適合", "筆電", "電腦"]):
            return "product_recommendation"
        
        # 規格詢問意圖
        elif any(word in user_lower for word in ["規格", "配置", "cpu", "gpu", "記憶體", "螢幕"]):
            return "specification_inquiry"
        
        # 比較意圖
        elif any(word in user_lower for word in ["比較", "差異", "哪個好", "選擇"]):
            return "product_comparison"
        
        # 問題回答意圖（選項A/B/C等）
        elif any(char in user_lower for char in ["a)", "b)", "c)", "d)", "e)"]) or user_input.strip().upper() in ["A", "B", "C", "D", "E", "F", "G"]:
            return "option_selection"
        
        return "general_inquiry"
    
    def _extract_key_requirements(self, user_input: str) -> Dict[str, Any]:
        """提取關鍵需求"""
        requirements = {}
        user_lower = user_input.lower()
        
        # 用途需求
        if any(word in user_lower for word in ["遊戲", "gaming"]):
            requirements["usage"] = "gaming"
        elif any(word in user_lower for word in ["辦公", "文書", "office"]):
            requirements["usage"] = "office"
        elif any(word in user_lower for word in ["設計", "創作", "修圖"]):
            requirements["usage"] = "creative"
        
        # 便攜性需求
        if any(word in user_lower for word in ["攜帶", "輕便", "輕薄", "方便帶"]):
            requirements["portability"] = "high"
        elif any(word in user_lower for word in ["桌面", "固定", "不移動"]):
            requirements["portability"] = "low"
        
        # 預算需求
        if any(word in user_lower for word in ["便宜", "經濟", "省錢"]):
            requirements["budget"] = "low"
        elif any(word in user_lower for word in ["高端", "頂級", "不在乎錢"]):
            requirements["budget"] = "high"
        
        return requirements
    
    def _assess_context_relevance(self, user_input: str, context: Dict[str, Any]) -> float:
        """評估上下文相關性"""
        if not context:
            return 0.0
        
        # 檢查是否在funnel chat中
        if context.get("funnel_mode", False):
            return 0.8
        
        # 檢查是否有之前的槽位
        if context.get("filled_slots"):
            return 0.6
        
        return 0.3
    
    def _check_data_availability(self, user_input: str) -> Dict[str, Any]:
        """檢查數據可用性"""
        # 簡化實現：假設公司產品數據都可用
        return {
            "product_data": True,
            "specification_data": True,
            "comparison_data": True,
            "confidence": 0.9
        }
    
    def _determine_response_strategy(self, user_input: str, context: Dict[str, Any]) -> str:
        """決定回應策略"""
        user_intent = self._analyze_user_intent(user_input)
        
        # 如果在funnel chat中，傾向於繼續收集槽位
        if context.get("funnel_mode", False):
            if user_intent == "option_selection":
                return "slot_collection"
            elif context.get("awaiting_prompt_response", False):
                return "slot_collection"
        
        # 根據意圖決定策略
        if user_intent == "product_recommendation":
            return "product_recommendation"
        elif user_intent == "specification_inquiry":
            return "information_provision"
        elif user_intent == "option_selection":
            return "slot_collection"
        else:
            return "general"
    
    def _generate_product_response(self, think_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成產品推薦回應"""
        return {
            "response_type": "product_recommendation",
            "response": "基於您的需求，我來為您推薦合適的筆電產品。",
            "action_needed": "trigger_funnel_chat",
            "confidence": 0.8
        }
    
    def _generate_question_response(self, think_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成問題回應"""
        return {
            "response_type": "slot_collection", 
            "response": "了解了您的回答。",
            "action_needed": "process_slot_value",
            "confidence": 0.9
        }
    
    def _generate_clarification_response(self, think_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成澄清回應"""
        return {
            "response_type": "clarification",
            "response": "不好意思，可以請您詳細說明一下嗎？",
            "action_needed": "seek_clarification",
            "confidence": 0.6
        }
    
    def _generate_general_response(self, think_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成一般回應"""
        return {
            "response_type": "general",
            "response": "感謝您的提問。基於公司產品資料庫，我來為您提供協助。",
            "action_needed": "provide_general_help",
            "confidence": 0.7
        }
    
    def format_response_with_rules(self, response_content: str, response_type: str = "general") -> str:
        """
        根據基礎規則格式化回應
        
        Args:
            response_content: 回應內容
            response_type: 回應類型
            
        Returns:
            格式化後的回應
        """
        try:
            # 應用專業語調
            if self.fundamental_rules["professional_tone"]:
                # 確保禮貌和專業
                if not any(greeting in response_content for greeting in ["您好", "感謝", "請問"]):
                    response_content = f"感謝您的提問。{response_content}"
            
            # 應用回應格式建議
            if response_type == "product_recommendation":
                # 產品推薦格式
                formatted = f"**產品推薦建議**\n\n{response_content}"
                
                # 添加客服提示
                if self.fundamental_rules["data_insufficient_handling"]:
                    formatted += "\n\n如需更詳細的產品資訊，建議您直接聯絡客服人員取得最即時且完整的協助。"
                
                return formatted
            
            elif response_type == "slot_collection":
                # 槽位收集格式 - 保持簡潔
                return response_content
            
            else:
                # 一般格式
                return response_content
            
        except Exception as e:
            self.logger.error(f"回應格式化失敗: {e}")
            return response_content
    
    def validate_response_against_rules(self, response: str) -> Dict[str, Any]:
        """
        根據基礎規則驗證回應
        
        Args:
            response: 待驗證的回應
            
        Returns:
            驗證結果
        """
        validation = {
            "valid": True,
            "violations": [],
            "suggestions": []
        }
        
        # 檢查是否只使用公司數據
        if self.fundamental_rules["company_data_only"]:
            if any(term in response.lower() for term in ["據說", "可能", "應該", "大概"]):
                validation["violations"].append("可能包含推測性內容")
                validation["suggestions"].append("確保所有信息都來自公司產品資料庫")
        
        # 檢查是否有專業語調
        if self.fundamental_rules["professional_tone"]:
            if not any(polite in response for polite in ["您", "請", "感謝", "歡迎"]):
                validation["suggestions"].append("建議使用更禮貌的語調")
        
        # 檢查資訊不足處理
        if "不知道" in response or "不確定" in response:
            if "客服" not in response:
                validation["suggestions"].append("資訊不足時建議提及客服聯絡")
        
        validation["valid"] = len(validation["violations"]) == 0
        return validation