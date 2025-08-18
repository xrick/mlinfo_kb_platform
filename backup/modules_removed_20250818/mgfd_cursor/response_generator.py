#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD ResponseGenerator 模組
實現回應格式化和前端渲染信息生成
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

class ResponseGenerator:
    """回應生成模組"""
    
    def __init__(self, config_loader):
        """
        初始化回應生成器
        
        Args:
            config_loader: 配置載入器
        """
        self.config_loader = config_loader
        self.logger = logging.getLogger(__name__)
    
    def generate_response(self, response_object: Dict[str, Any]) -> str:
        """
        生成最終回應
        
        Args:
            response_object: 回應物件
            
        Returns:
            格式化的JSON回應
        """
        try:
            # 格式化回應內容
            formatted_response = self._format_response_content(response_object)
            
            # 添加前端渲染信息
            frontend_info = self._add_frontend_info(response_object)
            
            # 合併回應信息
            final_response = {
                **formatted_response,
                **frontend_info
            }
            
            # 序列化為JSON
            json_response = json.dumps(final_response, ensure_ascii=False, indent=2)
            
            self.logger.info(f"生成回應: {response_object.get('action_type', 'unknown')}")
            return json_response
            
        except Exception as e:
            self.logger.error(f"生成回應失敗: {e}")
            return self._generate_error_response(str(e))
    
    def format_suggestions(self, slot_name: str, context: Dict[str, Any]) -> List[str]:
        """
        格式化建議選項
        
        Args:
            slot_name: 槽位名稱
            context: 上下文信息
            
        Returns:
            建議選項列表
        """
        try:
            # 根據槽位類型生成建議
            suggestions = self._get_slot_suggestions(slot_name, context)
            
            # 應用個性化配置
            personalized_suggestions = self._apply_personality(suggestions, context)
            
            return personalized_suggestions
            
        except Exception as e:
            self.logger.error(f"格式化建議失敗: {e}")
            return []
    
    def _format_response_content(self, response_object: Dict[str, Any]) -> Dict[str, Any]:
        """格式化回應內容"""
        action_type = response_object.get("action_type", "")
        content = response_object.get("content", "")
        
        # 根據動作類型格式化內容
        if action_type == "elicitation":
            return self._format_funnel_question_response(response_object)
        elif action_type == "recommendation":
            return self._format_recommendation_response(response_object)
        elif action_type == "clarification":
            return self._format_clarification_response(response_object)
        elif action_type == "interruption":
            return self._format_interruption_response(response_object)
        elif action_type == "special_case_response":
            return self._format_special_case_response(response_object)
        else:
            return self._format_generic_response(response_object)
    
    def _format_funnel_question_response(self, response_object: Dict[str, Any]) -> Dict[str, Any]:
        """格式化漏斗問題回應 - 生成結構化的選項界面"""
        target_slot = response_object.get("target_slot", "")
        content = response_object.get("content", "")
        
        # 生成funnel question結構
        funnel_question = self._generate_funnel_question(target_slot, response_object)
        
        return {
            "type": "funnel_question",
            "session_id": response_object.get("session_id", ""),
            "question": funnel_question,
            "context": {
                "original_query": response_object.get("original_query", ""),
                "detected_type": "slot_elicitation",
                "generation_time": datetime.now().isoformat()
            },
            "message": "請選擇最符合您需求的選項，我將為您提供更精準的協助。"
        }
    
    def _generate_funnel_question(self, target_slot: str, response_object: Dict[str, Any]) -> Dict[str, Any]:
        """生成漏斗問題的問題結構"""
        slot_questions = {
            "usage_purpose": {
                "question_text": "為了更精準地幫助您，請選擇您的主要使用目的：",
                "options": [
                    {
                        "option_id": "gaming",
                        "label": "🎮 遊戲娛樂",
                        "description": "我主要用來玩遊戲，需要良好的遊戲性能",
                        "route": "gaming_flow",
                        "keywords": ["遊戲", "gaming", "電競", "fps"],
                        "example_queries": ["玩遊戲的筆電", "電競筆電推薦"],
                        "flow_description": "專注於遊戲性能需求分析"
                    },
                    {
                        "option_id": "business",
                        "label": "💼 商務辦公",
                        "description": "我主要用來工作，處理文書、簡報等商務需求",
                        "route": "business_flow",
                        "keywords": ["工作", "商務", "辦公", "文書"],
                        "example_queries": ["辦公筆電", "商務用筆電推薦"],
                        "flow_description": "專注於辦公效率和穩定性"
                    },
                    {
                        "option_id": "student",
                        "label": "🎓 學習教育",
                        "description": "我主要用來學習，上課、做作業、研究等",
                        "route": "student_flow",
                        "keywords": ["學習", "上課", "作業", "學生"],
                        "example_queries": ["學生筆電", "適合學習的筆電"],
                        "flow_description": "專注於學習需求和性價比"
                    },
                    {
                        "option_id": "creative",
                        "label": "🎨 創作設計",
                        "description": "我主要用來創作，如設計、影片剪輯、程式開發等",
                        "route": "creative_flow",
                        "keywords": ["設計", "創作", "剪輯", "開發"],
                        "example_queries": ["設計師筆電", "創作者筆電推薦"],
                        "flow_description": "專注於創作工具性能需求"
                    }
                ]
            },
            "budget_range": {
                "question_text": "請選擇您的預算範圍：",
                "options": [
                    {
                        "option_id": "budget",
                        "label": "💰 經濟實惠",
                        "description": "2-3萬元左右，追求高性價比",
                        "route": "budget_flow",
                        "keywords": ["便宜", "經濟", "平價"],
                        "example_queries": ["便宜的筆電", "經濟實惠筆電"],
                        "flow_description": "專注於性價比選擇"
                    },
                    {
                        "option_id": "mid_range",
                        "label": "🏆 中等價位",
                        "description": "3-5萬元左右，平衡性能與價格",
                        "route": "mid_range_flow",
                        "keywords": ["中等", "平衡", "適中"],
                        "example_queries": ["中價位筆電", "平衡性能筆電"],
                        "flow_description": "專注於性能平衡選擇"
                    },
                    {
                        "option_id": "premium",
                        "label": "💎 高階選擇",
                        "description": "5萬元以上，追求高性能表現",
                        "route": "premium_flow",
                        "keywords": ["高級", "高端", "頂級"],
                        "example_queries": ["高階筆電", "頂級性能筆電"],
                        "flow_description": "專注於高性能需求"
                    }
                ]
            },
            "performance_priority": {
                "question_text": "請選擇您最重視的性能方面：",
                "options": [
                    {
                        "option_id": "cpu",
                        "label": "⚡ 處理速度",
                        "description": "重視處理器性能，快速運算和多工處理",
                        "route": "cpu_priority_flow",
                        "keywords": ["速度", "處理器", "快速"],
                        "example_queries": ["快速的筆電", "處理器強的筆電"],
                        "flow_description": "專注於CPU性能選擇"
                    },
                    {
                        "option_id": "gpu",
                        "label": "🎯 圖形性能",
                        "description": "重視顯示卡性能，遊戲和圖形處理",
                        "route": "gpu_priority_flow",
                        "keywords": ["顯卡", "圖形", "遊戲性能"],
                        "example_queries": ["顯卡強的筆電", "圖形性能筆電"],
                        "flow_description": "專注於GPU性能選擇"
                    },
                    {
                        "option_id": "battery",
                        "label": "🔋 電池續航",
                        "description": "重視電池壽命，長時間使用不插電",
                        "route": "battery_priority_flow",
                        "keywords": ["電池", "續航", "省電"],
                        "example_queries": ["電池持久的筆電", "續航力強筆電"],
                        "flow_description": "專注於電池續航選擇"
                    }
                ]
            }
        }
        
        # 獲取對應槽位的問題定義，如果沒有則生成通用問題
        if target_slot in slot_questions:
            question_data = slot_questions[target_slot]
        else:
            question_data = {
                "question_text": f"請提供關於 {target_slot} 的更多信息：",
                "options": [
                    {
                        "option_id": "general_option",
                        "label": "🔍 一般選擇",
                        "description": "我需要更多指導來決定",
                        "route": "general_flow",
                        "keywords": [],
                        "example_queries": [],
                        "flow_description": "通用選擇流程"
                    }
                ]
            }
        
        return {
            "question_id": f"slot_{target_slot}",
            "question_text": question_data["question_text"],
            "options": question_data["options"]
        }
    
    def _format_elicitation_response(self, response_object: Dict[str, Any]) -> Dict[str, Any]:
        """格式化信息收集回應"""
        content = response_object.get("content", "")
        target_slot = response_object.get("target_slot", "")
        suggestions = response_object.get("suggestions", [])
        
        return {
            "type": "elicitation",
            "content": content,
            "target_slot": target_slot,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat(),
            "confidence": response_object.get("confidence", 0.8)
        }
    
    def _format_recommendation_response(self, response_object: Dict[str, Any]) -> Dict[str, Any]:
        """格式化推薦回應"""
        content = response_object.get("content", "")
        recommendations = response_object.get("recommendations", [])
        
        # 格式化推薦產品
        formatted_recommendations = []
        for rec in recommendations:
            formatted_rec = {
                "id": rec.get("id", ""),
                "name": rec.get("name", ""),
                "brand": rec.get("brand", ""),
                "price": rec.get("price", ""),
                "features": rec.get("features", []),
                "reason": rec.get("reason", ""),
                "image_url": rec.get("image_url", ""),
                "product_url": rec.get("product_url", "")
            }
            formatted_recommendations.append(formatted_rec)
        
        return {
            "type": "recommendation",
            "content": content,
            "recommendations": formatted_recommendations,
            "timestamp": datetime.now().isoformat(),
            "confidence": response_object.get("confidence", 0.9)
        }
    
    def _format_clarification_response(self, response_object: Dict[str, Any]) -> Dict[str, Any]:
        """格式化澄清回應"""
        content = response_object.get("content", "")
        
        return {
            "type": "clarification",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "confidence": response_object.get("confidence", 0.7)
        }
    
    def _format_interruption_response(self, response_object: Dict[str, Any]) -> Dict[str, Any]:
        """格式化中斷回應"""
        content = response_object.get("content", "")
        
        return {
            "type": "interruption",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "confidence": response_object.get("confidence", 0.9),
            "reset_session": True
        }
    
    def _format_generic_response(self, response_object: Dict[str, Any]) -> Dict[str, Any]:
        """格式化通用回應"""
        content = response_object.get("content", "")
        
        return {
            "type": "generic",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "confidence": response_object.get("confidence", 0.5)
        }
    
    def _add_frontend_info(self, response_object: Dict[str, Any]) -> Dict[str, Any]:
        """添加前端渲染信息"""
        action_type = response_object.get("action_type", "")
        
        frontend_info = {
            "render_type": "text",
            "show_suggestions": False,
            "show_recommendations": False,
            "show_buttons": False,
            "auto_scroll": True
        }
        
        # 根據動作類型設置前端渲染選項
        if action_type == "elicitation":
            frontend_info.update({
                "show_suggestions": True,
                "show_buttons": True,
                "button_type": "suggestion"
            })
        elif action_type == "recommendation":
            frontend_info.update({
                "show_recommendations": True,
                "show_buttons": True,
                "button_type": "product"
            })
        elif action_type == "clarification":
            frontend_info.update({
                "show_buttons": True,
                "button_type": "clarification"
            })
        
        return frontend_info
    
    def _get_slot_suggestions(self, slot_name: str, context: Dict[str, Any]) -> List[str]:
        """獲取槽位建議選項"""
        # 根據槽位類型返回建議
        slot_suggestions = {
            "usage_purpose": ["遊戲", "商務工作", "學習", "創作設計", "一般使用"],
            "budget_range": ["2-3萬", "3-4萬", "4-5萬", "5萬以上"],
            "brand_preference": ["華碩", "宏碁", "聯想", "惠普", "戴爾", "蘋果"],
            "performance_features": ["快速開機", "輕便攜帶", "高效能", "安靜運行", "長效電池"],
            "portability_need": ["超輕便", "平衡型", "桌面替代"]
        }
        
        return slot_suggestions.get(slot_name, [])
    
    def _apply_personality(self, suggestions: List[str], context: Dict[str, Any]) -> List[str]:
        """應用個性化配置"""
        # 這裡可以根據用戶偏好或對話風格調整建議
        # 目前直接返回原始建議
        return suggestions
    
    def _generate_error_response(self, error_message: str) -> str:
        """生成錯誤回應"""
        error_response = {
            "type": "error",
            "content": "抱歉，系統遇到了一些問題。請稍後再試。",
            "error": error_message,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.0,
            "render_type": "text",
            "show_suggestions": False,
            "show_recommendations": False,
            "show_buttons": False,
            "auto_scroll": True
        }
        
        return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    def generate_stream_response(self, response_object: Dict[str, Any]) -> str:
        """
        生成串流回應格式
        
        Args:
            response_object: 回應物件
            
        Returns:
            串流格式的回應
        """
        try:
            # 格式化回應內容
            formatted_response = self._format_response_content(response_object)
            
            # 添加前端渲染信息
            frontend_info = self._add_frontend_info(response_object)
            
            # 合併回應信息
            final_response = {
                **formatted_response,
                **frontend_info
            }
            
            # 生成串流格式
            stream_response = f"data: {json.dumps(final_response, ensure_ascii=False)}\n\n"
            
            return stream_response
            
        except Exception as e:
            self.logger.error(f"生成串流回應失敗: {e}")
            error_response = self._generate_error_response(str(e))
            return f"data: {error_response}\n\n"
    
    def format_chat_history(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化對話歷史
        
        Args:
            chat_history: 原始對話歷史
            
        Returns:
            格式化後的對話歷史
        """
        formatted_history = []
        
        for message in chat_history:
            formatted_message = {
                "role": message.get("role", "unknown"),
                "content": message.get("content", ""),
                "timestamp": message.get("timestamp", ""),
                "type": message.get("type", "text"),
                "suggestions": message.get("suggestions", []),
                "recommendations": message.get("recommendations", [])
            }
            formatted_history.append(formatted_message)
        
        return formatted_history
    
    def _format_special_case_response(self, response_object: Dict[str, Any]) -> Dict[str, Any]:
        """格式化特殊案例回應"""
        case_id = response_object.get("case_id", "")
        content = response_object.get("content", "")
        funnel_question = response_object.get("funnel_question", {})
        
        # 基本回應結構
        formatted_response = {
            "type": "special_case",
            "case_id": case_id,
            "session_id": response_object.get("session_id", ""),
            "content": content,
            "confidence": response_object.get("confidence", 0.8),
            "timestamp": datetime.now().isoformat()
        }
        
        # 如果有漏斗問題，添加到回應中
        if funnel_question:
            formatted_response["funnel_question"] = funnel_question
            formatted_response["type"] = "funnel_question"
            formatted_response["message"] = "請選擇最符合您需求的選項，我將為您提供更精準的協助。"
        
        # 檢查是否是循環打破案例
        if response_object.get("loop_breaking", False):
            formatted_response["loop_breaking"] = True
            formatted_response["message"] = "我注意到我們可能在重複相同的問題。讓我換個方式來幫助您："
        
        # 添加後續問題（如果存在）
        if "follow_up_questions" in response_object:
            formatted_response["follow_up_questions"] = response_object["follow_up_questions"]
        
        # 添加專門標準（如果存在）
        if "specialized_criteria" in response_object:
            formatted_response["specialized_criteria"] = response_object["specialized_criteria"]
        
        return formatted_response
