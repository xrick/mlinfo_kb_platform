#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版澄清對話管理器
大幅減少澄清對話需求，優先提供即時有用回應
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

class EnhancedClarificationManager:
    """增強版澄清對話管理器 - 最小化澄清，最大化即時回應"""
    
    def __init__(self, templates_path: str = None):
        """
        初始化增強版澄清對話管理器
        
        Args:
            templates_path: 澄清問題模板文件路徑
        """
        self.templates_path = templates_path or "sales_rag_app/libs/services/sales_assistant/prompts/clarification_templates.json"
        self.clarification_templates = self._load_clarification_templates()
        self.active_conversations: Dict[str, ConversationState] = {}
        
        # 大幅提高信心度閾值，減少澄清觸發
        self.confidence_threshold = 0.15  # 從 0.6 降到 0.15
        self.min_clarification_threshold = 0.05  # 只有極低信心度才澄清
        
        logging.info("增強版澄清對話管理器初始化完成 - 最小化澄清模式")
    
    def _load_clarification_templates(self) -> Dict:
        """載入澄清問題模板"""
        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
                logging.info(f"成功載入澄清模板: {list(templates.get('clarification_templates', {}).keys())}")
                return templates
        except FileNotFoundError:
            logging.warning(f"澄清模板文件不存在: {self.templates_path}")
            return self._get_minimal_templates()
        except Exception as e:
            logging.error(f"載入澄清模板失敗: {e}")
            return self._get_minimal_templates()
    
    def _get_minimal_templates(self) -> Dict:
        """獲取最小澄清模板（很少使用）"""
        return {
            "clarification_templates": {
                "extreme_ambiguity": {
                    "question": "您的查詢比較簡短，為了提供更準確的建議，請問您主要關心什麼方面？",
                    "options": [
                        {"id": "performance", "label": "🚀 性能表現"},
                        {"id": "battery", "label": "🔋 電池續航"},
                        {"id": "portability", "label": "🎒 輕便攜帶"},
                        {"id": "general", "label": "📋 綜合比較"}
                    ]
                }
            }
        }
    
    def should_clarify_enhanced(self, intent_result: Dict, smart_context: Dict = None) -> bool:
        """
        增強版澄清判斷 - 大幅減少澄清需求
        
        Args:
            intent_result: 意圖檢測結果
            smart_context: 智能回應上下文
            
        Returns:
            是否需要澄清
        """
        try:
            confidence = intent_result.get("confidence_score", 0.0)
            primary_intent = intent_result.get("primary_intent", "general")
            matched_keywords = intent_result.get("matched_keywords", [])
            
            # 1. 如果有明確的意圖，不需要澄清
            if confidence > self.confidence_threshold:
                logging.info(f"信心度足夠 ({confidence:.3f} > {self.confidence_threshold})，不需要澄清")
                return False
            
            # 2. 如果有任何匹配的關鍵字，不需要澄清
            if matched_keywords:
                logging.info(f"有匹配關鍵字 ({len(matched_keywords)} 個)，不需要澄清")
                return False
            
            # 3. 如果智能上下文能夠生成有用回應，不需要澄清
            if smart_context:
                response_strategy = smart_context.get("response_strategy", "")
                if response_strategy != "general_recommendation":
                    logging.info(f"有明確回應策略 ({response_strategy})，不需要澄清")
                    return False
                
                recommended_models = smart_context.get("recommended_models", [])
                if recommended_models:
                    logging.info(f"有推薦型號 ({recommended_models})，不需要澄清")
                    return False
            
            # 4. 檢查是否為極度模糊的查詢
            original_query = smart_context.get("original_query", "") if smart_context else ""
            if self._is_extremely_ambiguous(original_query, intent_result):
                logging.info("查詢極度模糊，需要澄清")
                return True
            
            # 5. 預設不澄清，提供最佳猜測回應
            logging.info("預設不澄清，將提供基於推斷的回應")
            return False
            
        except Exception as e:
            logging.error(f"澄清判斷失敗: {e}")
            # 錯誤情況下也不澄清，避免中斷用戶體驗
            return False
    
    def _is_extremely_ambiguous(self, query: str, intent_result: Dict) -> bool:
        """
        判斷查詢是否極度模糊
        
        Args:
            query: 原始查詢
            intent_result: 意圖檢測結果
            
        Returns:
            是否極度模糊
        """
        if not query or len(query.strip()) < 3:
            return True
        
        # 極度簡短且無意義的查詢
        meaningless_queries = [
            "筆電", "電腦", "laptop", "推薦", "建議", "哪個", "什麼", "有嗎", 
            "好嗎", "如何", "怎樣", "?", "？", "幫忙", "謝謝"
        ]
        
        query_clean = query.strip().lower()
        if query_clean in meaningless_queries:
            return True
        
        # 檢查是否只包含停用詞
        stop_words = ["的", "是", "在", "有", "和", "或", "但", "就", "都", "很", "非常", "比較", "一些"]
        words = query_clean.split()
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 1]
        
        if len(meaningful_words) == 0:
            return True
        
        # 檢查意圖檢測結果
        confidence = intent_result.get("confidence_score", 0.0)
        matched_keywords = intent_result.get("matched_keywords", [])
        
        # 只有在完全沒有任何線索時才認為極度模糊
        if confidence < self.min_clarification_threshold and len(matched_keywords) == 0:
            return True
        
        return False
    
    def generate_smart_fallback_response(self, query: str, intent_result: Dict, smart_context: Dict = None) -> Dict:
        """
        生成智能後備回應，避免澄清
        
        Args:
            query: 原始查詢
            intent_result: 意圖檢測結果
            smart_context: 智能回應上下文
            
        Returns:
            智能後備回應
        """
        try:
            response_strategy = smart_context.get("response_strategy", "general_recommendation") if smart_context else "general_recommendation"
            recommended_models = smart_context.get("recommended_models", ["958", "839", "819"]) if smart_context else ["958", "839", "819"]
            priority_specs = smart_context.get("priority_specs", ["cpu", "gpu", "memory"]) if smart_context else ["cpu", "gpu", "memory"]
            
            # 根據策略生成回應
            if response_strategy == "comparison":
                return self._generate_comparison_response(recommended_models, priority_specs)
            elif response_strategy == "spec_comparison":
                primary_intent = intent_result.get("primary_intent", "general")
                return self._generate_spec_focused_response(primary_intent, recommended_models)
            elif response_strategy == "latest_products":
                return self._generate_latest_products_response()
            elif response_strategy == "scenario_recommendation":
                return self._generate_scenario_recommendation()
            else:
                return self._generate_general_recommendation_response(recommended_models)
                
        except Exception as e:
            logging.error(f"生成智能後備回應失敗: {e}")
            return self._generate_default_helpful_response()
    
    def _generate_comparison_response(self, models: List[str], priority_specs: List[str]) -> Dict:
        """生成比較回應"""
        return {
            "message_type": "smart_response",
            "response_type": "comparison",
            "answer_summary": f"根據您的查詢，以下是{', '.join(models)}系列的比較分析：",
            "recommended_action": "show_model_comparison",
            "target_models": models,
            "priority_specs": priority_specs,
            "helpful_context": "我們為您整理了重點規格比較，如需特定方面的詳細信息，請告訴我們。",
            "additional_suggestions": [
                "🔋 如果重視續航，推薦819系列",
                "🎮 如果用於遊戲，推薦958系列", 
                "⚖️ 如果要平衡性能，推薦839系列"
            ]
        }
    
    def _generate_spec_focused_response(self, spec_type: str, models: List[str]) -> Dict:
        """生成規格專注回應"""
        spec_descriptions = {
            "battery": "電池續航",
            "display": "螢幕顯示",
            "cpu": "處理器性能",
            "gpu": "顯卡性能", 
            "memory": "記憶體配置",
            "storage": "儲存容量",
            "portability": "重量便攜性"
        }
        
        spec_name = spec_descriptions.get(spec_type, "綜合性能")
        
        return {
            "message_type": "smart_response",
            "response_type": "spec_focused",
            "answer_summary": f"關於{spec_name}方面，以下是各系列的表現分析：",
            "recommended_action": "show_spec_comparison",
            "focus_spec": spec_type,
            "target_models": models,
            "helpful_context": f"我們已為您重點整理{spec_name}的詳細比較。",
            "additional_suggestions": self._get_spec_specific_suggestions(spec_type)
        }
    
    def _generate_latest_products_response(self) -> Dict:
        """生成最新產品回應"""
        return {
            "message_type": "smart_response", 
            "response_type": "latest_products",
            "answer_summary": "以下是我們目前的最新產品系列：",
            "recommended_action": "show_latest_models",
            "target_models": ["958", "839", "819"],
            "helpful_context": "所有系列都是最新配置，各有不同的特色和定位。",
            "additional_suggestions": [
                "🚀 958系列：最新高性能配置",
                "⚖️ 839系列：性能與價格平衡",
                "🏢 819系列：商務辦公優化"
            ]
        }
    
    def _generate_scenario_recommendation(self) -> Dict:
        """生成使用場景推薦"""
        return {
            "message_type": "smart_response",
            "response_type": "scenario_recommendation", 
            "answer_summary": "根據不同使用場景，我們為您推薦以下選擇：",
            "recommended_action": "show_scenario_models",
            "target_models": ["958", "839", "819"],
            "helpful_context": "每個系列都針對特定使用場景進行了優化。",
            "additional_suggestions": [
                "🎮 遊戲娛樂：958系列 - 高性能GPU和CPU",
                "💼 商務辦公：819系列 - 長續航和輕便設計",
                "📚 學習創作：839系列 - 性能與便攜的平衡",
                "🎨 專業創作：958系列 - 專業級顯卡和大記憶體"
            ]
        }
    
    def _generate_general_recommendation_response(self, models: List[str]) -> Dict:
        """生成一般推薦回應"""
        return {
            "message_type": "smart_response",
            "response_type": "general_recommendation",
            "answer_summary": "基於我們的產品特色，為您推薦以下選擇：",
            "recommended_action": "show_general_comparison",
            "target_models": models,
            "helpful_context": "我們為您整理了各系列的特色比較，幫助您做出最適合的選擇。",
            "additional_suggestions": [
                "💡 性能需求高：推薦958系列",
                "💰 預算考量：推薦839系列",
                "🔋 續航重要：推薦819系列",
                "❓ 不確定需求：可以看看綜合比較"
            ]
        }
    
    def _generate_default_helpful_response(self) -> Dict:
        """生成預設有用回應"""
        return {
            "message_type": "smart_response",
            "response_type": "helpful_default",
            "answer_summary": "我們有三個主要系列，各有不同特色：",
            "recommended_action": "show_all_series",
            "target_models": ["958", "839", "819"],
            "helpful_context": "每個系列都有其獨特優勢，我們可以根據您的具體需求提供詳細建議。",
            "additional_suggestions": [
                "🚀 958系列：頂級性能，適合遊戲和專業應用",
                "⚖️ 839系列：平衡配置，適合一般工作和輕度遊戲",
                "🏢 819系列：商務導向，優秀續航和便攜性",
                "📞 如有特定需求，歡迎進一步詢問"
            ]
        }
    
    def _get_spec_specific_suggestions(self, spec_type: str) -> List[str]:
        """獲取特定規格的建議"""
        suggestions_map = {
            "battery": [
                "🔋 819系列：8-10小時超長續航",
                "⚡ 839系列：6-8小時平衡續航",
                "🚀 958系列：5-7小時高性能續航"
            ],
            "display": [
                "🎮 958系列：144Hz高刷新率，適合遊戲",
                "💼 819系列：護眼螢幕，適合長時間工作",
                "📺 839系列：IPS面板，色彩準確"
            ],
            "cpu": [
                "🚀 958系列：Ryzen 7高性能處理器",
                "⚖️ 839系列：Ryzen 5平衡性能",
                "💼 819系列：節能處理器，續航優化"
            ],
            "gpu": [
                "🎮 958系列：高性能獨立顯卡",
                "📊 839系列：中階獨立顯卡", 
                "💼 819系列：整合顯卡，省電高效"
            ]
        }
        
        return suggestions_map.get(spec_type, [
            "💡 每個系列都有其特色優勢",
            "📊 可以查看詳細規格比較",
            "🤔 如有疑問歡迎進一步詢問"
        ])
    
    def should_clarify(self, intent_result: Dict, confidence_threshold: float = None) -> bool:
        """
        向後兼容的澄清判斷接口
        """
        return self.should_clarify_enhanced(intent_result, None)
    
    def start_clarification(self, query: str, intent_result: Dict) -> Tuple[str, ClarificationQuestion]:
        """
        開始澄清對話（只在極度必要時使用）
        """
        conversation_id = str(uuid.uuid4())
        
        # 創建極簡澄清問題
        question = ClarificationQuestion(
            question_id=str(uuid.uuid4()),
            template_name="extreme_ambiguity",
            question="您希望了解筆電的哪個方面？",
            question_type="single_choice",
            options=[
                {"id": "performance", "label": "🚀 性能表現", "description": "CPU、GPU等性能規格"},
                {"id": "battery", "label": "🔋 電池續航", "description": "續航時間和省電特性"},
                {"id": "portability", "label": "🎒 輕便攜帶", "description": "重量、尺寸等便攜性"},
                {"id": "general", "label": "📋 綜合比較", "description": "整體規格和推薦"}
            ],
            conversation_id=conversation_id,
            step=1
        )
        
        # 創建對話狀態
        conversation_state = ConversationState(
            conversation_id=conversation_id,
            user_query=query,
            current_step=1,
            total_steps=1,  # 只一步澄清
            clarification_history=[],
            collected_context={},
            confidence_threshold=self.confidence_threshold,
            flow_type="minimal_clarification",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.active_conversations[conversation_id] = conversation_state
        
        logging.info(f"開始最小澄清對話: {conversation_id}")
        return conversation_id, question
    
    def process_clarification_response(self, conversation_id: str, user_choice: str, user_input: str = "") -> Dict:
        """
        處理澄清回應（立即完成，不延續對話）
        """
        if conversation_id not in self.active_conversations:
            return {"action": "error", "message": "對話不存在"}
        
        conversation_state = self.active_conversations[conversation_id]
        
        # 立即完成澄清，生成增強意圖
        enhanced_intent = self._generate_enhanced_intent_from_choice(user_choice, conversation_state.user_query)
        
        # 清理對話狀態
        del self.active_conversations[conversation_id]
        
        return {
            "action": "complete",
            "enhanced_intent": enhanced_intent,
            "clarification_summary": f"用戶關注：{user_choice}",
            "conversation_id": conversation_id
        }
    
    def _generate_enhanced_intent_from_choice(self, choice: str, original_query: str) -> Dict:
        """根據澄清選擇生成增強意圖"""
        choice_mapping = {
            "performance": {
                "primary_intent": "cpu",
                "confidence_score": 0.8,
                "priority_specs": ["cpu", "gpu", "memory"],
                "recommended_models": ["958", "839"]
            },
            "battery": {
                "primary_intent": "battery", 
                "confidence_score": 0.8,
                "priority_specs": ["battery", "cpu"],
                "recommended_models": ["819", "839"]
            },
            "portability": {
                "primary_intent": "portability",
                "confidence_score": 0.8, 
                "priority_specs": ["structconfig", "battery"],
                "recommended_models": ["819"]
            },
            "general": {
                "primary_intent": "comparison",
                "confidence_score": 0.8,
                "priority_specs": ["cpu", "gpu", "memory", "battery"],
                "recommended_models": ["958", "839", "819"]
            }
        }
        
        enhanced = choice_mapping.get(choice, choice_mapping["general"])
        enhanced["original_query"] = original_query
        enhanced["enhanced_by_clarification"] = True
        
        return enhanced