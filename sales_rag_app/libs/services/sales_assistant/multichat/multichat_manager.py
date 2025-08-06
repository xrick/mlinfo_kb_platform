#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多輪對話管理器
負責管理基於NB特點的多輪對話流程，導引使用者從模糊需求到明確規格
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from .models import (
    NBFeature, FeatureOption, FeatureResponse, 
    ChatChain, ConversationSession, ChatQuestion,
    FeatureType, ResponseType, generate_id
)
from .gen_chat import ChatGenerator

class MultichatManager:
    """多輪對話管理器"""
    
    def __init__(self, features_config_path: str = None):
        """
        初始化多輪對話管理器
        
        Args:
            features_config_path: NB特點配置檔案路徑
        """
        self.features_config_path = features_config_path or self._get_default_features_path()
        self.features_config = self._load_features_config()
        self.nb_features = self._parse_nb_features()
        self.trigger_keywords = self.features_config.get("trigger_keywords", {})
        
        # 初始化對話鍊生成器
        self.chat_generator = ChatGenerator(features_config_path)
        
        # 活躍的對話會話
        self.active_sessions: Dict[str, ConversationSession] = {}
        
        logging.info(f"多輪對話管理器初始化完成，支援 {len(self.nb_features)} 個特點")
    
    def _get_default_features_path(self) -> str:
        """獲取預設特點配置路徑"""
        return str(Path(__file__).parent / "nb_features.json")
    
    def _load_features_config(self) -> Dict:
        """載入NB特點配置"""
        try:
            with open(self.features_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logging.info(f"成功載入特點配置")
                return config
        except Exception as e:
            logging.error(f"載入特點配置失敗: {e}")
            return {}
    
    def _parse_nb_features(self) -> Dict[str, NBFeature]:
        """解析NB特點配置為物件"""
        features = {}
        nb_features_config = self.features_config.get("nb_features", {})
        
        for feature_id, config in nb_features_config.items():
            try:
                # 解析選項
                options = []
                for opt_config in config.get("options", []):
                    option = FeatureOption(
                        option_id=opt_config["option_id"],
                        label=opt_config["label"],
                        description=opt_config["description"],
                        keywords=opt_config.get("keywords", []),
                        db_filter=opt_config.get("db_filter", {})
                    )
                    options.append(option)
                
                # 建立NBFeature物件
                feature = NBFeature(
                    feature_id=feature_id,
                    feature_type=FeatureType(config["feature_type"]),
                    name=config["name"],
                    description=config["description"],
                    question_template=config["question_template"],
                    response_type=ResponseType(config["response_type"]),
                    options=options,
                    keywords=config.get("keywords", []),
                    priority=config.get("priority", 1),
                    required=config.get("required", True)
                )
                features[feature_id] = feature
                
            except Exception as e:
                logging.error(f"解析特點 {feature_id} 失敗: {e}")
        
        return features
    
    def should_activate_multichat(self, query: str, intent_result: Dict = None) -> bool:
        """
        判斷是否應該啟動多輪對話
        
        Args:
            query: 使用者查詢
            intent_result: 意圖檢測結果
            
        Returns:
            是否應該啟動多輪對話
        """
        try:
            # 檢查觸發關鍵字
            vague_keywords = self.trigger_keywords.get("vague_queries", [])
            comparison_keywords = self.trigger_keywords.get("comparison_queries", [])
            
            query_lower = query.lower()
            
            # 檢查模糊查詢關鍵字
            for keyword in vague_keywords:
                if keyword in query_lower:
                    logging.info(f"檢測到模糊查詢關鍵字: {keyword}")
                    return True
            
            # 檢查比較查詢關鍵字（某些情況下也需要引導）
            for keyword in comparison_keywords:
                if keyword in query_lower and not self._has_specific_models(query):
                    logging.info(f"檢測到模糊比較查詢: {keyword}")
                    return True
            
            # 檢查意圖結果的信心度
            if intent_result:
                confidence = intent_result.get("confidence_score", 1.0)
                if confidence < 0.5:
                    logging.info(f"意圖信心度過低: {confidence}")
                    return True
                
                # 檢查是否為一般意圖
                primary_intent = intent_result.get("primary_intent", "")
                if primary_intent in ["general", "unclear", "specifications"]:
                    logging.info(f"檢測到需要澄清的意圖: {primary_intent}")
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"判斷是否啟動多輪對話時發生錯誤: {e}")
            return False
    
    def _has_specific_models(self, query: str) -> bool:
        """檢查查詢是否包含具體的機型"""
        # 這裡可以擴展檢查邏輯，判斷是否提到具體機型
        model_patterns = [r'\d{3}', r'[A-Z]{2,3}\d{3}', r'i[3579]', r'Ryzen']
        for pattern in model_patterns:
            if re.search(pattern, query):
                return True
        return False
    
    def start_multichat_flow(self, query: str, user_context: Dict = None, strategy: str = "random") -> Tuple[str, ChatQuestion]:
        """
        開始多輪對話流程
        
        Args:
            query: 使用者原始查詢
            user_context: 使用者上下文資訊
            strategy: 對話鍊生成策略
            
        Returns:
            (session_id, first_question)
        """
        try:
            # 生成對話鍊
            if user_context and "usage_scenario" in user_context:
                chat_chain = self.chat_generator.get_chain_by_scenario(user_context["usage_scenario"])
            else:
                chat_chain = self.chat_generator.get_random_chain(strategy)
            
            # 建立對話會話
            session_id = generate_id()
            session = ConversationSession(
                session_id=session_id,
                user_query=query,
                chat_chain=chat_chain,
                current_step=0,
                total_steps=len(chat_chain.features_order),
                collected_responses=[],
                session_state=user_context or {},
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                is_complete=False
            )
            
            # 儲存活躍會話
            self.active_sessions[session_id] = session
            
            # 生成第一個問題
            first_question = self._generate_next_question(session)
            
            logging.info(f"開始多輪對話: {session_id}, 對話鍊: {' -> '.join(chat_chain.features_order)}")
            return session_id, first_question
            
        except Exception as e:
            logging.error(f"開始多輪對話流程失敗: {e}")
            raise
    
    def _generate_next_question(self, session: ConversationSession) -> ChatQuestion:
        """
        生成下一個問題
        
        Args:
            session: 對話會話
            
        Returns:
            對話問題
        """
        try:
            current_feature_id = session.chat_chain.features_order[session.current_step]
            feature = self.nb_features[current_feature_id]
            
            # 轉換選項格式
            options = []
            for nb_option in feature.options:
                option = FeatureOption(
                    option_id=nb_option.option_id,
                    label=nb_option.label,
                    description=nb_option.description,
                    keywords=nb_option.keywords,
                    db_filter=nb_option.db_filter
                )
                options.append(option)
            
            question = ChatQuestion(
                question_id=generate_id(),
                session_id=session.session_id,
                feature=feature,
                step=session.current_step + 1,
                question_text=feature.question_template,
                options=options,
                created_at=datetime.now().isoformat()
            )
            
            return question
            
        except Exception as e:
            logging.error(f"生成問題失敗: {e}")
            raise
    
    def process_feature_response(self, session_id: str, user_choice: str, user_input: str = "") -> Dict:
        """
        處理使用者對特點的回應
        
        Args:
            session_id: 會話ID
            user_choice: 使用者選擇的選項ID
            user_input: 使用者額外輸入
            
        Returns:
            處理結果
        """
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"找不到會話: {session_id}")
            
            session = self.active_sessions[session_id]
            current_feature_id = session.chat_chain.features_order[session.current_step]
            
            # 建立回應記錄
            response = FeatureResponse(
                response_id=generate_id(),
                feature_id=current_feature_id,
                feature_type=FeatureType(current_feature_id),
                user_choice=user_choice,
                user_input=user_input,
                confidence=1.0,
                timestamp=datetime.now().isoformat()
            )
            
            # 儲存回應
            session.collected_responses.append(response)
            session.updated_at = datetime.now().isoformat()
            
            # 判斷下一步動作
            session.current_step += 1
            
            if session.current_step >= session.total_steps:
                # 對話完成
                session.is_complete = True
                enhanced_query = self._generate_enhanced_query(session)
                
                # 移除活躍會話
                del self.active_sessions[session_id]
                
                return {
                    "action": "complete",
                    "session_id": session_id,
                    "enhanced_query": enhanced_query,
                    "collected_preferences": self._summarize_preferences(session),
                    "db_filters": self._generate_db_filters(session)
                }
            else:
                # 繼續下一個問題
                next_question = self._generate_next_question(session)
                
                return {
                    "action": "continue",
                    "session_id": session_id,
                    "next_question": next_question,
                    "current_step": session.current_step,
                    "total_steps": session.total_steps,
                    "progress": f"{session.current_step}/{session.total_steps}"
                }
                
        except Exception as e:
            logging.error(f"處理特點回應失敗: {e}")
            raise
    
    def _generate_enhanced_query(self, session: ConversationSession) -> str:
        """
        基於收集的回應生成增強的查詢
        
        Args:
            session: 對話會話
            
        Returns:
            增強的查詢字串
        """
        try:
            preferences = []
            original_query = session.user_query
            
            for response in session.collected_responses:
                feature = self.nb_features[response.feature_id]
                
                # 找到對應的選項
                selected_option = None
                for option in feature.options:
                    if option.option_id == response.user_choice:
                        selected_option = option
                        break
                
                if selected_option and response.user_choice not in ["no_preference", "no_specific", "flexible"]:
                    preferences.append(f"{feature.name}: {selected_option.label.replace('🎮 ', '').replace('💼 ', '').replace('🎨 ', '').replace('📚 ', '').replace('🚀 ', '').replace('⚖️ ', '').replace('🔋 ', '').replace('🤷 ', '').replace('💻 ', '').replace('❓ ', '').replace('🧠 ', '').replace('💰 ', '').replace('🔧 ', '').replace('📦 ', '').replace('📁 ', '').replace('💾 ', '').replace('⚡ ', '').replace('📺 ', '').replace('🖥️ ', '').replace('💻 ', '').replace('🪶 ', '').replace('🎒 ', '').replace('🏠 ', '').replace('💎 ', '').replace('💳 ', '').replace('👑 ', '').replace('🤝 ', '')}")
            
            if preferences:
                enhanced_query = f"根據以下偏好條件：{' | '.join(preferences)}，{original_query}"
            else:
                enhanced_query = original_query
            
            return enhanced_query
            
        except Exception as e:
            logging.error(f"生成增強查詢失敗: {e}")
            return session.user_query
    
    def _summarize_preferences(self, session: ConversationSession) -> Dict:
        """
        總結使用者偏好
        
        Args:
            session: 對話會話
            
        Returns:
            偏好總結
        """
        summary = {}
        
        for response in session.collected_responses:
            feature = self.nb_features[response.feature_id]
            
            # 找到對應的選項
            selected_option = None
            for option in feature.options:
                if option.option_id == response.user_choice:
                    selected_option = option
                    break
            
            if selected_option:
                summary[response.feature_id] = {
                    "feature_name": feature.name,
                    "selected_option": selected_option.label,
                    "description": selected_option.description,
                    "user_input": response.user_input
                }
        
        return summary
    
    def _generate_db_filters(self, session: ConversationSession) -> Dict:
        """
        生成資料庫查詢篩選條件
        
        Args:
            session: 對話會話
            
        Returns:
            資料庫篩選條件
        """
        filters = {}
        
        for response in session.collected_responses:
            feature = self.nb_features[response.feature_id]
            
            # 找到對應的選項
            selected_option = None
            for option in feature.options:
                if option.option_id == response.user_choice:
                    selected_option = option
                    break
            
            if selected_option and selected_option.db_filter:
                filters.update(selected_option.db_filter)
        
        return filters
    
    def get_session_state(self, session_id: str) -> Optional[ConversationSession]:
        """
        獲取會話狀態
        
        Args:
            session_id: 會話ID
            
        Returns:
            會話狀態或None
        """
        return self.active_sessions.get(session_id)
    
    def cleanup_expired_sessions(self, hours: int = 24):
        """
        清理過期的會話
        
        Args:
            hours: 過期時間（小時）
        """
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                created_time = datetime.fromisoformat(session.created_at)
                if (current_time - created_time).total_seconds() > hours * 3600:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                logging.info(f"清理過期會話: {session_id}")
            
        except Exception as e:
            logging.error(f"清理過期會話失敗: {e}")
    
    def abort_session(self, session_id: str) -> bool:
        """
        中止會話
        
        Args:
            session_id: 會話ID
            
        Returns:
            是否成功中止
        """
        try:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logging.info(f"中止會話: {session_id}")
                return True
            return False
        except Exception as e:
            logging.error(f"中止會話失敗: {e}")
            return False