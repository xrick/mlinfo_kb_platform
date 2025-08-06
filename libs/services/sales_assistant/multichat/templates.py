#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
對話模板管理
負責格式化多輪對話的問題和回應顯示
"""

from typing import Dict, List, Any
from datetime import datetime
from .models import ChatQuestion, FeatureOption, ConversationSession

class ChatTemplateManager:
    """對話模板管理器"""
    
    def __init__(self):
        """初始化模板管理器"""
        self.question_templates = self._get_question_templates()
        self.response_templates = self._get_response_templates()
    
    def _get_question_templates(self) -> Dict[str, str]:
        """獲取問題模板"""
        return {
            "multichat_question": """
🤖 **為了為您推薦最適合的筆電，我需要了解您的具體需求**

📋 **進度**: 第 {current_step} 步，共 {total_steps} 步

❓ **{question_text}**

請選擇最符合您需求的選項：

{options_text}

💡 *提示: 如果不確定，可以選擇「沒有偏好」，系統會根據其他條件為您推薦*
            """,
            
            "option_format": "**{index}** - {label}\n   {description}",
            
            "progress_bar": "📊 進度: {progress_bar} ({current}/{total})",
            
            "session_start": """
🚀 **開始多輪對話引導**

您的問題是：「{user_query}」

我將通過幾個簡單的問題來了解您的具體需求，幫您找到最適合的筆電機型。

{first_question}
            """,
            
            "session_complete": """
✅ **需求收集完成！**

根據您提供的偏好，我已經了解您的需求：

{preferences_summary}

現在讓我為您搜尋符合條件的筆電機型...
            """
        }
    
    def _get_response_templates(self) -> Dict[str, str]:
        """獲取回應模板"""
        return {
            "choice_received": "✅ 收到您的選擇：**{choice_label}**",
            
            "next_question": """
{choice_confirmation}

{next_question}
            """,
            
            "preferences_item": "• **{feature_name}**: {selected_option}",
            
            "error_message": "❌ 處理您的回應時發生錯誤，請重新選擇或聯繫支援。",
            
            "invalid_choice": "⚠️ 無效的選擇，請選擇 1-{max_options} 之間的數字。",
            
            "session_timeout": "⏰ 會話已超時，請重新開始對話。"
        }
    
    def format_question(self, question: ChatQuestion, current_step: int, total_steps: int) -> str:
        """
        格式化問題顯示
        
        Args:
            question: 對話問題
            current_step: 當前步驟
            total_steps: 總步驟數
            
        Returns:
            格式化的問題文字
        """
        try:
            # 格式化選項
            options_text = ""
            for i, option in enumerate(question.options, 1):
                option_text = self.question_templates["option_format"].format(
                    index=i,
                    label=option.label,
                    description=option.description
                )
                options_text += option_text + "\n"
            
            # 生成進度條
            progress_bar = self._generate_progress_bar(current_step, total_steps)
            
            # 格式化完整問題  
            formatted_question = self.question_templates["multichat_question"].format(
                current_step=current_step,
                total_steps=total_steps,
                question_text=question.question_text,
                options_text=options_text.strip(),
                progress_bar=progress_bar
            )
            
            return formatted_question.strip()
            
        except Exception as e:
            return f"格式化問題時發生錯誤: {e}"
    
    def format_session_start(self, user_query: str, first_question: str) -> str:
        """
        格式化會話開始訊息
        
        Args:
            user_query: 使用者原始查詢
            first_question: 第一個問題
            
        Returns:
            格式化的開始訊息
        """
        return self.question_templates["session_start"].format(
            user_query=user_query,
            first_question=first_question
        )
    
    def format_choice_confirmation(self, choice_label: str) -> str:
        """
        格式化選擇確認訊息
        
        Args:
            choice_label: 選擇的選項標籤
            
        Returns:
            確認訊息
        """
        return self.response_templates["choice_received"].format(
            choice_label=choice_label
        )
    
    def format_next_question_response(self, choice_label: str, next_question: str) -> str:
        """
        格式化下一個問題的回應
        
        Args:
            choice_label: 使用者選擇的標籤
            next_question: 下一個問題
            
        Returns:
            格式化的回應
        """
        choice_confirmation = self.format_choice_confirmation(choice_label)
        
        return self.response_templates["next_question"].format(
            choice_confirmation=choice_confirmation,
            next_question=next_question
        )
    
    def format_session_complete(self, preferences_summary: Dict[str, Dict]) -> str:
        """
        格式化會話完成訊息
        
        Args:
            preferences_summary: 偏好總結
            
        Returns:
            完成訊息
        """
        # 格式化偏好列表
        preferences_text = ""
        for feature_id, pref_data in preferences_summary.items():
            if pref_data["selected_option"] not in ["沒有偏好", "沒有特殊需求", "彈性選擇"]:
                pref_item = self.response_templates["preferences_item"].format(
                    feature_name=pref_data["feature_name"],
                    selected_option=pref_data["selected_option"]
                )
                preferences_text += pref_item + "\n"
        
        if not preferences_text:
            preferences_text = "• 您選擇讓系統根據整體需求為您推薦"
        
        return self.question_templates["session_complete"].format(
            preferences_summary=preferences_text.strip()
        )
    
    def format_error_message(self, error_type: str = "general") -> str:
        """
        格式化錯誤訊息
        
        Args:
            error_type: 錯誤類型
            
        Returns:
            錯誤訊息
        """
        if error_type == "invalid_choice":
            return self.response_templates["invalid_choice"]
        elif error_type == "session_timeout":
            return self.response_templates["session_timeout"]
        else:
            return self.response_templates["error_message"]
    
    def _generate_progress_bar(self, current: int, total: int, width: int = 10) -> str:
        """
        生成進度條顯示
        
        Args:
            current: 當前進度
            total: 總進度
            width: 進度條寬度
            
        Returns:
            進度條字串
        """
        try:
            if total == 0:
                return "▓" * width
            
            filled = int((current / total) * width)
            empty = width - filled
            
            progress_bar = "▓" * filled + "▒" * empty
            percentage = int((current / total) * 100)
            
            return f"{progress_bar} {percentage}%"
            
        except Exception:
            return "▒" * width
    
    def format_option_list(self, options: List[FeatureOption]) -> str:
        """
        格式化選項列表
        
        Args:
            options: 選項列表
            
        Returns:
            格式化的選項文字
        """
        options_text = ""
        for i, option in enumerate(options, 1):
            option_text = self.question_templates["option_format"].format(
                index=i,
                label=option.label,
                description=option.description
            )
            options_text += option_text + "\n"
        
        return options_text.strip()
    
    def get_option_by_number(self, options: List[FeatureOption], choice_number: str) -> FeatureOption:
        """
        根據選擇編號獲取選項
        
        Args:
            options: 選項列表
            choice_number: 選擇的編號（字串）
            
        Returns:
            對應的選項
        """
        try:
            index = int(choice_number) - 1
            if 0 <= index < len(options):
                return options[index]
            else:
                raise ValueError(f"選項編號超出範圍: {choice_number}")
        except ValueError:
            raise ValueError(f"無效的選項編號: {choice_number}")
    
    def create_multichat_response_data(self, 
                                     action: str,
                                     session_id: str,
                                     **kwargs) -> Dict[str, Any]:
        """
        建立標準的多輪對話回應資料
        
        Args:
            action: 動作類型 ("start", "continue", "complete", "error")
            session_id: 會話ID
            **kwargs: 額外資料
            
        Returns:
            回應資料字典
        """
        base_response = {
            "message_type": "multichat_response",
            "action": action,
            "session_id": session_id,
            "timestamp": str(datetime.now().isoformat())
        }
        
        base_response.update(kwargs)
        return base_response