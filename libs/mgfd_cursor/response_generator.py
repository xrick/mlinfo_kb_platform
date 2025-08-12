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
            return self._format_elicitation_response(response_object)
        elif action_type == "recommendation":
            return self._format_recommendation_response(response_object)
        elif action_type == "clarification":
            return self._format_clarification_response(response_object)
        elif action_type == "interruption":
            return self._format_interruption_response(response_object)
        else:
            return self._format_generic_response(response_object)
    
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
