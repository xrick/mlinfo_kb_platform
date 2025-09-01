"""
回應生成處理器 - 主類別
整合策略工廠和所有回應生成功能
"""

import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from .ResponseStrategyFactory import ResponseStrategyFactory
from .ResponseStrategy import ResponseStrategy, ResponseType
from .strategies.FunnelQuestionStrategy import FunnelQuestionStrategy
from .strategies.RecommendationStrategy import RecommendationStrategy
from .strategies.ElicitationStrategy import ElicitationStrategy
from .strategies.GeneralResponseStrategy import GeneralResponseStrategy
from .utils.MarkdownTableGenerator import MarkdownTableGenerator
from .utils.ResponseQualityEvaluator import ResponseQualityEvaluator
from .utils.ResponseTemplateManager import ResponseTemplateManager


class ResponseGenHandler:
    """回應生成處理器主類別"""
    
    def __init__(self) -> None:
        """初始化回應生成器"""
        self.logger = logging.getLogger(__name__)
        
        # 設置日誌級別
        self.logger.setLevel(logging.INFO)
        
        # 初始化核心組件
        try:
            self.strategy_factory = ResponseStrategyFactory()
            self.table_generator = MarkdownTableGenerator()
            self.quality_evaluator = ResponseQualityEvaluator()
            self.template_manager = ResponseTemplateManager()
            
            # 註冊策略
            self._register_strategies()
            
            # 載入回應模板
            self.response_templates = self._load_response_templates()
            
            self.logger.info("ResponseGenHandler 初始化完成")
            
        except Exception as e:
            self.logger.error(f"ResponseGenHandler 初始化失敗: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _register_strategies(self) -> None:
        """註冊所有策略"""
        try:
            # 註冊各種回應策略
            self.strategy_factory.register_strategy(FunnelQuestionStrategy())
            self.strategy_factory.register_strategy(RecommendationStrategy())
            self.strategy_factory.register_strategy(ElicitationStrategy())
            self.strategy_factory.register_strategy(GeneralResponseStrategy())
            
            self.logger.info("所有策略註冊完成")
        except Exception as e:
            self.logger.error(f"註冊策略時發生錯誤: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _load_response_templates(self) -> Dict[str, str]:
        """載入回應模板"""
        try:
            # 基本模板，實際應用中可以從文件載入
            templates = {
                "funnel_intro": "歡迎使用筆電購物助手！讓我幫您找到最適合的筆電。",
                "general_greeting": "您好！我是您的筆電購物助手，有什麼可以幫您的嗎？",
                "error_message": "抱歉，我遇到了一些問題。請稍後再試。",
                "clarification_request": "請您提供更多細節，這樣我才能給您更準確的建議。"
            }
            return templates
        except Exception as e:
            self.logger.error(f"載入回應模板時發生錯誤: {e}")
            return {"error": "模板載入失敗"}
    
    # 標準動作合約實作
    async def generate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成回應 - 主要入口點（標準動作合約）
        
        Args:
            context: 當前上下文
            
        Returns:
            生成的回應字典
        """
        start_time = datetime.now()
        session_id = context.get('session_id', 'unknown')
        
        try:
            self.logger.info(f"開始生成回應 - 會話: {session_id}")
            self.logger.debug(f"上下文內容: {context}")
            
            # 1. 選擇適當的策略
            strategy = self._select_strategy(context)
            
            # 2. 預處理上下文
            processed_context = self._preprocess_context(strategy, context)
            
            # 3. 生成回應
            response = self._generate_response(strategy, processed_context)
            
            # 4. 後處理回應
            final_response = self._postprocess_response(strategy, response, processed_context)
            
            # 5. 品質評估（可選）
            if context.get("enable_quality_evaluation", True):
                final_response = self._evaluate_quality(final_response, context)
            
            # 6. 前端格式適配
            final_response = self._adapt_frontend_format(final_response)
            
            # 7. 記錄執行時間
            execution_time = (datetime.now() - start_time).total_seconds()
            final_response["execution_time"] = execution_time
            
            self.logger.info(f"回應生成完成 - 會話: {session_id}, 策略: {strategy.strategy_name}, 執行時間: {execution_time:.3f}秒")
            return final_response
            
        except Exception as e:
            self.logger.error(f"生成回應時發生錯誤 - 會話: {session_id}: {e}")
            self.logger.error(traceback.format_exc())
            return self._create_error_response(context, str(e))
    
    def _select_strategy(self, context: Dict[str, Any]) -> ResponseStrategy:
        """選擇適當的策略"""
        try:
            strategy = self.strategy_factory.get_best_strategy(context)
            
            # 驗證策略是否適合
            if not self.strategy_factory.validate_strategy(strategy, context):
                self.logger.warning(f"策略 {strategy.strategy_name} 不適合當前上下文")
                # 使用通用策略作為備選
                strategy = self.strategy_factory.get_strategy("general")
                if not strategy:
                    raise ValueError("沒有可用的通用策略")
            
            self.logger.debug(f"選擇策略: {strategy.strategy_name}")
            return strategy
            
        except Exception as e:
            self.logger.error(f"選擇策略時發生錯誤: {e}")
            raise
    
    def _preprocess_context(self, strategy: ResponseStrategy, context: Dict[str, Any]) -> Dict[str, Any]:
        """預處理上下文"""
        try:
            processed_context = strategy.preprocess_context(context)
            self.logger.debug(f"上下文預處理完成")
            return processed_context
        except Exception as e:
            self.logger.error(f"預處理上下文時發生錯誤: {e}")
            return context
    
    def _generate_response(self, strategy: ResponseStrategy, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成回應"""
        try:
            response = strategy.generate_response(context)
            self.logger.debug(f"策略 {strategy.strategy_name} 生成回應完成")
            return response
        except Exception as e:
            self.logger.error(f"生成回應時發生錯誤: {e}")
            raise
    
    def _postprocess_response(self, strategy: ResponseStrategy, response: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """後處理回應"""
        try:
            final_response = strategy.postprocess_response(response, context)
            final_response["timestamp"] = datetime.now().isoformat()
            
            # 驗證回應格式
            if not self._validate_response_format(final_response):
                self.logger.warning("回應格式驗證失敗，使用錯誤回應")
                final_response = self._create_error_response(context)
            
            self.logger.debug(f"回應後處理完成")
            return final_response
        except Exception as e:
            self.logger.error(f"後處理回應時發生錯誤: {e}")
            return self._create_error_response(context, str(e))
    
    def _evaluate_quality(self, response: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """評估回應品質"""
        try:
            quality_result = self.quality_evaluator.evaluate_response(response, context)
            response["quality_evaluation"] = quality_result
            
            # 記錄品質評估結果
            overall_score = quality_result.get("overall_score", 0.0)
            self.logger.info(f"回應品質評估完成，總分: {overall_score:.2f}")
            
            return response
        except Exception as e:
            self.logger.error(f"評估回應品質時發生錯誤: {e}")
            return response
    
    def register_strategy(self, strategy: ResponseStrategy) -> None:
        """
        註冊新的回應策略
        
        Args:
            strategy: 要註冊的策略實例
        """
        try:
            self.strategy_factory.register_strategy(strategy)
            self.logger.info(f"註冊新策略: {strategy.strategy_name}")
        except Exception as e:
            self.logger.error(f"註冊策略時發生錯誤: {e}")
            raise
    
    def get_available_strategies(self) -> Dict[str, Any]:
        """
        獲取所有可用策略的信息
        
        Returns:
            策略信息字典
        """
        try:
            strategies = self.strategy_factory.get_available_strategies()
            return {
                "total_strategies": len(strategies),
                "strategies": strategies
            }
        except Exception as e:
            self.logger.error(f"獲取策略信息時發生錯誤: {e}")
            return {"total_strategies": 0, "strategies": [], "error": str(e)}
    
    def generate_markdown_table(
        self, 
        data: Dict[str, Any], 
        table_name: str = "",
        style_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成 Markdown 表格
        
        Args:
            data: 表格數據
            table_name: 表格名稱
            style_config: 樣式配置
        
        Returns:
            Markdown 表格字符串
        """
        try:
            return self.table_generator.generate_table(data, table_name, style_config)
        except Exception as e:
            self.logger.error(f"生成 Markdown 表格時發生錯誤: {e}")
            return f"表格生成失敗: {str(e)}"
    
    def generate_comparison_table(
        self, 
        comparison_data: list, 
        product_names: list,
        table_name: str = "產品比較表"
    ) -> str:
        """
        生成產品比較表格
        
        Args:
            comparison_data: 比較數據
            product_names: 產品名稱列表
            table_name: 表格名稱
        
        Returns:
            Markdown 比較表格字符串
        """
        try:
            return self.table_generator.generate_comparison_table(comparison_data, product_names, table_name)
        except Exception as e:
            self.logger.error(f"生成比較表格時發生錯誤: {e}")
            return f"比較表格生成失敗: {str(e)}"
    
    def generate_recommendation_table(
        self, 
        recommendations: list, 
        table_name: str = "推薦產品"
    ) -> str:
        """
        生成推薦產品表格
        
        Args:
            recommendations: 推薦產品列表
            table_name: 表格名稱
        
        Returns:
            Markdown 推薦表格字符串
        """
        try:
            return self.table_generator.generate_recommendation_table(recommendations, table_name)
        except Exception as e:
            self.logger.error(f"生成推薦表格時發生錯誤: {e}")
            return f"推薦表格生成失敗: {str(e)}"
    
    def evaluate_response_quality(
        self, 
        response: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        評估回應品質
        
        Args:
            response: 回應字典
            context: 當前上下文
        
        Returns:
            品質評估結果
        """
        try:
            return self.quality_evaluator.evaluate_response(response, context)
        except Exception as e:
            self.logger.error(f"評估回應品質時發生錯誤: {e}")
            return {"error": f"品質評估失敗: {str(e)}"}
    
    def render_template(
        self, 
        template_name: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        渲染模板
        
        Args:
            template_name: 模板名稱
            context: 渲染上下文
        
        Returns:
            渲染後的內容
        """
        try:
            return self.template_manager.render_template(template_name, context)
        except Exception as e:
            self.logger.error(f"渲染模板時發生錯誤: {e}")
            return f"模板渲染失敗: {str(e)}"
    
    def _validate_response_format(self, response: Dict[str, Any]) -> bool:
        """
        驗證回應格式
        
        Args:
            response: 回應字典
            
        Returns:
            格式是否有效
        """
        try:
            # 檢查必要字段
            required_fields = ["type", "message"]
            if not all(field in response for field in required_fields):
                return False
            
            # 檢查回應類型是否有效
            valid_types = [rt.value for rt in ResponseType]
            if response["type"] not in valid_types:
                return False
            
            # 檢查消息是否為空
            if not response["message"] or not response["message"].strip():
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"驗證回應格式時發生錯誤: {e}")
            return False
    
    def _create_error_response(self, context: Dict[str, Any], error_message: str = "系統錯誤") -> Dict[str, Any]:
        """
        創建錯誤回應
        
        Args:
            context: 當前上下文
            error_message: 錯誤消息
            
        Returns:
            錯誤回應字典
        """
        try:
            return {
                "type": "general",
                "message": f"抱歉，{error_message}。請稍後再試。",
                "session_id": context.get("session_id", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "error": True,
                "error_message": error_message
            }
        except Exception as e:
            self.logger.error(f"創建錯誤回應時發生錯誤: {e}")
            return {
                "type": "general",
                "message": "系統發生嚴重錯誤，請聯繫技術支援。",
                "error": True
            }
    
    def _adapt_frontend_format(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        適配前端期望的格式
        
        Args:
            response: 原始回應
        
        Returns:
            適配後的回應
        """
        try:
            adapted_response = {
                "type": response.get("type", "general"),
                "message": response.get("message", ""),
                "session_id": response.get("session_id"),
                "timestamp": response.get("timestamp", datetime.now().isoformat())
            }
            
            # 根據回應類型添加特定字段
            if response.get("type") == "funnel_question":
                adapted_response.update({
                    "question": response.get("question"),
                    "options": response.get("options", []),
                    "question_message": response.get("question_message", "")
                })
            elif response.get("type") == "recommendation":
                adapted_response.update({
                    "recommendations": response.get("recommendations", []),
                    "comparison_table": response.get("comparison_table"),
                    "summary": response.get("recommendation_summary")
                })
            elif response.get("type") == "elicitation":
                adapted_response.update({
                    "elicitation_type": response.get("elicitation_type"),
                    "missing_info": response.get("missing_info", [])
                })
            
            # 保留其他字段
            for key, value in response.items():
                if key not in adapted_response:
                    adapted_response[key] = value
            
            return adapted_response
        except Exception as e:
            self.logger.error(f"適配前端格式時發生錯誤: {e}")
            return response
    
    def get_template(self, template_name: str) -> str:
        """
        獲取回應模板
        
        Args:
            template_name: 模板名稱
            
        Returns:
            模板內容
        """
        try:
            return self.response_templates.get(template_name, "")
        except Exception as e:
            self.logger.error(f"獲取模板時發生錯誤: {e}")
            return ""
    
    def add_template(self, template_name: str, template_content: str) -> None:
        """
        添加新的回應模板
        
        Args:
            template_name: 模板名稱
            template_content: 模板內容
        """
        try:
            self.response_templates[template_name] = template_content
            self.logger.info(f"添加新模板: {template_name}")
        except Exception as e:
            self.logger.error(f"添加模板時發生錯誤: {e}")
            raise
    
    def remove_template(self, template_name: str) -> bool:
        """
        移除回應模板
        
        Args:
            template_name: 模板名稱
            
        Returns:
            是否成功移除
        """
        try:
            if template_name in self.response_templates:
                del self.response_templates[template_name]
                self.logger.info(f"移除模板: {template_name}")
                return True
            else:
                self.logger.warning(f"模板不存在: {template_name}")
                return False
        except Exception as e:
            self.logger.error(f"移除模板時發生錯誤: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        獲取系統狀態
        
        Returns:
            系統狀態字典
        """
        try:
            return {
                "module_name": "ResponseGenHandler",
                "status": "active",
                "available_strategies": len(self.strategy_factory.strategies),
                "available_templates": len(self.response_templates),
                "table_generator_status": "active",
                "quality_evaluator_status": "active",
                "template_manager_status": "active",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"獲取系統狀態時發生錯誤: {e}")
            return {
                "module_name": "ResponseGenHandler",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_component_info(self) -> Dict[str, Any]:
        """
        獲取組件信息
        
        Returns:
            組件信息字典
        """
        try:
            return {
                "strategy_factory": {
                    "available_strategies": self.strategy_factory.get_available_strategies(),
                    "total_strategies": len(self.strategy_factory.strategies)
                },
                "table_generator": {
                    "status": "active",
                    "converter_status": "active"
                },
                "quality_evaluator": {
                    "status": "active",
                    "evaluation_weights": self.quality_evaluator.evaluation_weights
                },
                "template_manager": {
                    "status": "active",
                    "available_templates": self.template_manager.get_available_templates(),
                    "total_templates": len(self.template_manager.templates)
                }
            }
        except Exception as e:
            self.logger.error(f"獲取組件信息時發生錯誤: {e}")
            return {"error": str(e)}
