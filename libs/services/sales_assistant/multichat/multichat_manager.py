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
    
    def should_activate_multichat(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        判斷是否應該啟動多輪對話，並識別查詢場景類型
        
        Args:
            query: 使用者查詢
            
        Returns:
            (是否應該啟動多輪對話, 場景類型)
            場景類型可能為: "business", "gaming", "creation", "study", "general" 或 None
        """
        try:
            # 檢查觸發關鍵字
            vague_keywords = self.trigger_keywords.get("vague_queries", [])
            comparison_keywords = self.trigger_keywords.get("comparison_queries", [])
            
            logging.info(f"觸發關鍵字載入狀態 - 模糊查詢: {len(vague_keywords)} 個, 比較查詢: {len(comparison_keywords)} 個")
            logging.info(f"正在檢查查詢: '{query}'")
            
            query_lower = query.lower()
            
            # 場景識別關鍵詞
            business_keywords = ["商務", "辦公", "工作", "企業", "商用", "業務", "職場", "公司", 
                               "文書處理", "文書", "處理", "office", "business", "工作用", "上班", 
                               "會議", "報告", "簡報", "excel", "word", "ppt", "專業工作"]
            gaming_keywords = ["遊戲", "gaming", "電競", "遊戲用", "玩遊戲", "game", "fps", "moba", 
                             "顯卡", "gpu", "高畫質", "高效能遊戲"]
            creation_keywords = ["創作", "設計", "繪圖", "影片編輯", "剪輯", "photoshop", "3d建模", 
                               "渲染", "creator", "design", "創意", "美工"]
            study_keywords = ["學習", "學生", "讀書", "課業", "上課", "study", "student", "教育", 
                            "大學生", "高中生", "研究", "論文"]
            
            # 識別場景類型
            detected_scenario = None
            if any(keyword in query_lower for keyword in business_keywords):
                detected_scenario = "business"
            elif any(keyword in query_lower for keyword in gaming_keywords):
                detected_scenario = "gaming"
            elif any(keyword in query_lower for keyword in creation_keywords):
                detected_scenario = "creation"
            elif any(keyword in query_lower for keyword in study_keywords):
                detected_scenario = "study"
            else:
                detected_scenario = "general"
            
            # 優先檢查比較查詢關鍵字（避免被模糊查詢攔截）
            for keyword in comparison_keywords:
                if keyword in query_lower:
                    # 檢查是否為具體系列比較（如819系列、958系列等）
                    if self._is_series_comparison(query):
                        logging.info(f"檢測到系列比較查詢，應直接執行比較: {keyword}")
                        return False, None  # 不觸發多輪對話，直接執行比較
                    elif not self._has_specific_models(query):
                        logging.info(f"檢測到模糊比較查詢: {keyword}, 場景類型: {detected_scenario}")
                        return True, detected_scenario
            
            # 檢查模糊查詢關鍵字
            for keyword in vague_keywords:
                if keyword in query_lower:
                    logging.info(f"檢測到模糊查詢關鍵字: {keyword}, 場景類型: {detected_scenario}")
                    return True, detected_scenario
            
            # 檢查是否包含使用場景描述但沒有具體機型
            scenario_keywords = ["適合", "用於", "專門", "主要", "需要", "想要", "希望", "打算"]
            if any(keyword in query_lower for keyword in scenario_keywords) and not self._has_specific_models(query):
                logging.info(f"檢測到使用場景查詢，啟動引導，場景類型: {detected_scenario}")
                return True, detected_scenario
            
            return False, None
            
        except Exception as e:
            logging.error(f"判斷是否啟動多輪對話時發生錯誤: {e}")
            return False, None
    
    def _has_specific_models(self, query: str) -> bool:
        """檢查查詢是否包含具體的機型（而非系列）"""
        # 具體機型模式：完整的機型名稱，如 AG958, APX958, NB819-A 等
        # 排除純系列號碼（819, 839, 958）的匹配
        specific_model_patterns = [
            r'[A-Z]{2,3}\d{3}',  # 如 AG958, APX958, NB819 等
            r'i[3579]-\d+',      # 如 i7-1234 等具體CPU型號
            r'Ryzen\s+[579]\s+\d+',  # 如 Ryzen 7 5800H 等具體CPU型號
        ]
        
        # 檢查是否包含具體機型名稱
        for pattern in specific_model_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logging.info(f"檢測到具體機型模式: {pattern}")
                return True
        
        # 檢查是否包含常見的機型名稱關鍵字組合
        # 例如：「AG958 和 APX958 的比較」這類具體機型比較
        model_mention_patterns = [
            r'[A-Z]{1,3}\d{3}[A-Z]*[-\s]*[A-Z]*\d*',  # 完整機型名稱
        ]
        
        for pattern in model_mention_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches and len(matches) >= 1:  # 至少提到一個具體機型
                # 驗證是否為有效的機型名稱格式（不只是系列號碼）
                valid_models = [m for m in matches if len(m) > 3 and not re.match(r'^\d{3}$', m)]
                if valid_models:
                    logging.info(f"檢測到具體機型名稱: {valid_models}")
                    return True
        
        logging.info("未檢測到具體機型，判定為系列或模糊查詢")
        return False
    
    def _is_series_comparison(self, query: str) -> bool:
        """檢查是否為系列比較查詢（如819系列、958系列等）"""
        # 明確的系列比較模式：直接要求比較特定系列的機型
        definitive_series_comparison_patterns = [
            r'比較\s*(819|839|958)\s*系列',      # 比較819系列
            r'(819|839|958)\s*系列.*比較.*規格',  # 819系列比較規格
            r'(819|839|958)\s*系列.*比較.*性能',  # 819系列比較性能
            r'(819|839|958)\s*系列.*比較.*差異',  # 819系列比較差異
            r'(819|839|958)\s*系列.*比較.*不同',  # 819系列比較不同
            r'(819|839|958)\s*系列.*有什麼不同',  # 819系列有什麼不同
            r'(819|839|958)\s*系列.*差異',       # 819系列差異
            r'(819|839|958)\s*系列.*顯示.*比較', # 819系列顯示比較
            r'(819|839|958)\s*系列.*螢幕.*比較', # 819系列螢幕比較
        ]
        
        for pattern in definitive_series_comparison_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logging.info(f"檢測到明確系列比較模式: {pattern}")
                return True
        
        # 排除模糊詢問類型的查詢（如"有哪些"、"可以"等）
        ambiguous_question_patterns = [
            r'有哪些.*比較',     # 有哪些...比較
            r'可以.*比較',       # 可以...比較
            r'能夠.*比較',       # 能夠...比較
            r'比較.*哪些',       # 比較...哪些
        ]
        
        for pattern in ambiguous_question_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logging.info(f"檢測到模糊詢問模式，不視為系列比較: {pattern}")
                return False
        
        # 額外檢查：嚴格的數字系列+比較關鍵字組合（排除模糊詢問）
        if re.search(r'\b(819|839|958)\b', query):
            comparison_keywords = ["比較", "差別", "不同", "差異"]
            for keyword in comparison_keywords:
                if keyword in query.lower():
                    # 確認不包含具體機型名稱且不是模糊詢問
                    if not self._has_specific_models(query) and not any(
                        ambiguous in query for ambiguous in ["哪些", "可以", "能夠", "有什麼"]
                    ):
                        logging.info("檢測到嚴格的數字系列+比較關鍵字組合")
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