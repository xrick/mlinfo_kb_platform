"""
Stat_Manager.py - 對話狀態機管理器

根據 Mermaid 圖表實現的狀態機：
stateDiagram-v2
[*] --> User
User --> System
System --> User
System --> DataQuery
DataQuery --> User
System -->[*]

功能：
- 管理用戶和AI之間的對話狀態
- 處理狀態轉換邏輯
- 記錄對話歷史
- 提供狀態查詢接口
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import logging
from datetime import datetime
import json


class ChatState(Enum):
    """對話狀態枚舉"""
    INITIAL = "initial"      # 初始狀態 [*]
    USER = "user"           # 用戶狀態
    SYSTEM = "system"       # 系統處理狀態
    DATA_QUERY = "data_query"  # 數據查詢狀態
    FINAL = "final"         # 結束狀態 [*]


class StateTransition:
    """狀態轉換類，定義轉換規則和條件"""
    
    def __init__(self, 
                 from_state: ChatState, 
                 to_state: ChatState,
                 condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
                 action: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
                 description: str = ""):
        """
        初始化狀態轉換
        
        Args:
            from_state: 起始狀態
            to_state: 目標狀態
            condition: 轉換條件函數
            action: 轉換時執行的動作
            description: 轉換描述
        """
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition
        self.action = action
        self.description = description
    
    def can_execute(self, context: Dict[str, Any]) -> bool:
        """
        檢查是否可以執行轉換
        
        Args:
            context: 當前上下文
            
        Returns:
            bool: 是否可以執行轉換
        """
        if self.condition is None:
            return True
        return self.condition(context)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行轉換動作
        
        Args:
            context: 當前上下文
            
        Returns:
            Dict[str, Any]: 更新後的上下文
        """
        if self.action:
            return self.action(context)
        return context


class ChatEvent:
    """聊天事件類，表示觸發狀態轉換的事件"""
    
    def __init__(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        """
        初始化聊天事件
        
        Args:
            event_type: 事件類型
            data: 事件數據
        """
        self.event_type = event_type
        self.data = data or {}
        self.timestamp = datetime.now()


class StatManager:
    """
    狀態管理器 - 實現對話狀態機
    
    管理用戶和AI之間的對話流程，根據預定義的狀態轉換規則
    處理各種聊天事件並維護對話上下文
    """
    
    def __init__(self, session_id: str = None):
        """
        初始化狀態管理器
        
        Args:
            session_id: 會話ID，用於識別不同的對話會話
        """
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_state = ChatState.INITIAL
        self.context: Dict[str, Any] = {
            "session_id": self.session_id,
            "start_time": datetime.now(),
            "user_messages": [],
            "system_responses": [],
            "data_queries": [],
            "conversation_history": []
        }
        
        # 初始化轉換規則
        self.transitions: List[StateTransition] = []
        self._setup_transitions()
        
        # 設置日誌
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"狀態管理器初始化完成 - 會話ID: {self.session_id}")
    
    def _setup_transitions(self):
        """設置狀態轉換規則"""
        
        # [*] --> User (初始狀態到用戶狀態)
        self.transitions.append(StateTransition(
            ChatState.INITIAL, 
            ChatState.USER,
            description="開始對話，等待用戶輸入"
        ))
        
        # User --> System (用戶輸入到系統處理)
        self.transitions.append(StateTransition(
            ChatState.USER, 
            ChatState.SYSTEM,
            condition=lambda ctx: ctx.get('user_input') is not None,
            action=self._process_user_input,
            description="處理用戶輸入"
        ))
        
        # System --> User (系統回應到用戶)
        self.transitions.append(StateTransition(
            ChatState.SYSTEM, 
            ChatState.USER,
            condition=lambda ctx: ctx.get('direct_response') is True,
            action=self._generate_system_response,
            description="生成系統回應"
        ))
        
        # System --> DataQuery (系統需要查詢數據)
        self.transitions.append(StateTransition(
            ChatState.SYSTEM, 
            ChatState.DATA_QUERY,
            condition=lambda ctx: ctx.get('needs_data_query') is True,
            action=self._execute_data_query,
            description="執行數據查詢"
        ))
        
        # DataQuery --> User (數據查詢結果返回給用戶)
        self.transitions.append(StateTransition(
            ChatState.DATA_QUERY, 
            ChatState.USER,
            action=self._process_data_results,
            description="處理數據查詢結果"
        ))
        
        # System --> [*] (系統結束對話)
        self.transitions.append(StateTransition(
            ChatState.SYSTEM, 
            ChatState.FINAL,
            condition=lambda ctx: ctx.get('end_conversation') is True,
            action=self._end_conversation,
            description="結束對話"
        ))
    
    def _process_user_input(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理用戶輸入的動作
        
        Args:
            context: 當前上下文
            
        Returns:
            Dict[str, Any]: 更新後的上下文
        """
        user_input = context.get('user_input', '')
        context['user_messages'].append({
            'timestamp': datetime.now(),
            'message': user_input
        })
        context['conversation_history'].append({
            'timestamp': datetime.now(),
            'type': 'user',
            'content': user_input
        })
        
        self.logger.info(f"處理用戶輸入: {user_input[:50]}...")
        return context
    
    def _generate_system_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成系統回應的動作
        
        Args:
            context: 當前上下文
            
        Returns:
            Dict[str, Any]: 更新後的上下文
        """
        # 這裡可以整合LLM管理器來生成回應
        response = f"系統回應: {context.get('user_input', '')}"
        context['system_responses'].append({
            'timestamp': datetime.now(),
            'response': response
        })
        context['conversation_history'].append({
            'timestamp': datetime.now(),
            'type': 'system',
            'content': response
        })
        
        self.logger.info(f"生成系統回應: {response[:50]}...")
        return context
    
    def _execute_data_query(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行數據查詢的動作
        
        Args:
            context: 當前上下文
            
        Returns:
            Dict[str, Any]: 更新後的上下文
        """
        query = context.get('data_query', '')
        context['data_queries'].append({
            'timestamp': datetime.now(),
            'query': query,
            'results': f"查詢結果: {query}"
        })
        
        self.logger.info(f"執行數據查詢: {query[:50]}...")
        return context
    
    def _process_data_results(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理數據查詢結果的動作
        
        Args:
            context: 當前上下文
            
        Returns:
            Dict[str, Any]: 更新後的上下文
        """
        # 處理查詢結果並準備回應
        context['data_processed'] = True
        context['direct_response'] = True
        
        self.logger.info("處理數據查詢結果完成")
        return context
    
    def _end_conversation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        結束對話的動作
        
        Args:
            context: 當前上下文
            
        Returns:
            Dict[str, Any]: 更新後的上下文
        """
        context['end_time'] = datetime.now()
        context['conversation_ended'] = True
        
        self.logger.info("對話結束")
        return context
    
    def _log_state_change(self, from_state: ChatState, to_state: ChatState, reason: str = ""):
        """
        記錄狀態變化
        
        Args:
            from_state: 起始狀態
            to_state: 目標狀態
            reason: 變化原因
        """
        log_entry = {
            'timestamp': datetime.now(),
            'from_state': from_state.value,
            'to_state': to_state.value,
            'reason': reason
        }
        
        self.context['conversation_history'].append({
            'timestamp': datetime.now(),
            'type': 'state_change',
            'content': f"狀態變化: {from_state.value} -> {to_state.value} ({reason})"
        })
        
        self.logger.info(f"狀態變化: {from_state.value} -> {to_state.value} ({reason})")
    
    def get_current_state(self) -> ChatState:
        """
        獲取當前狀態
        
        Returns:
            ChatState: 當前狀態
        """
        return self.current_state
    
    def get_context(self) -> Dict[str, Any]:
        """
        獲取當前上下文
        
        Returns:
            Dict[str, Any]: 當前上下文的副本
        """
        return self.context.copy()
    
    def update_context(self, updates: Dict[str, Any]):
        """
        更新上下文
        
        Args:
            updates: 要更新的內容
        """
        self.context.update(updates)
        self.logger.debug(f"上下文已更新: {updates}")
    
    def process_event(self, event: ChatEvent) -> bool:
        """
        處理事件並可能觸發狀態轉換
        
        Args:
            event: 要處理的事件
            
        Returns:
            bool: 是否觸發了狀態轉換
        """
        self.logger.debug(f"處理事件: {event.event_type} (當前狀態: {self.current_state.value})")
        
        # 更新上下文
        self.context.update(event.data)
        
        # 查找適用的轉換
        for transition in self.transitions:
            if transition.from_state == self.current_state:
                if transition.can_execute(self.context):
                    # 執行轉換
                    old_state = self.current_state
                    self.context = transition.execute(self.context)
                    self.current_state = transition.to_state
                    
                    self._log_state_change(
                        old_state, 
                        self.current_state, 
                        f"事件: {event.event_type}, 轉換: {transition.description}"
                    )
                    
                    return True
        
        self.logger.debug(f"未找到適用的事件轉換: {event.event_type}")
        return False
    
    def transition_to(self, target_state: ChatState, reason: str = "手動轉換") -> bool:
        """
        手動轉換到指定狀態
        
        Args:
            target_state: 目標狀態
            reason: 轉換原因
            
        Returns:
            bool: 轉換是否成功
        """
        # 檢查是否存在有效的轉換路徑
        for transition in self.transitions:
            if transition.from_state == self.current_state and transition.to_state == target_state:
                old_state = self.current_state
                self.context = transition.execute(self.context)
                self.current_state = target_state
                
                self._log_state_change(old_state, self.current_state, reason)
                return True
        
        self.logger.warning(f"無法轉換到狀態 {target_state.value}")
        return False
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        獲取對話摘要
        
        Returns:
            Dict[str, Any]: 對話摘要信息
        """
        return {
            'session_id': self.session_id,
            'current_state': self.current_state.value,
            'start_time': self.context.get('start_time'),
            'end_time': self.context.get('end_time'),
            'user_message_count': len(self.context.get('user_messages', [])),
            'system_response_count': len(self.context.get('system_responses', [])),
            'data_query_count': len(self.context.get('data_queries', [])),
            'conversation_ended': self.context.get('conversation_ended', False)
        }
    
    def reset_conversation(self):
        """重置對話狀態"""
        self.current_state = ChatState.INITIAL
        self.context = {
            "session_id": self.session_id,
            "start_time": datetime.now(),
            "user_messages": [],
            "system_responses": [],
            "data_queries": [],
            "conversation_history": []
        }
        self.logger.info("對話狀態已重置")
    
    def export_conversation_log(self, file_path: str = None) -> str:
        """
        導出對話日誌
        
        Args:
            file_path: 導出文件路徑，如果為None則自動生成
            
        Returns:
            str: 導出的文件路徑
        """
        if file_path is None:
            file_path = f"conversation_log_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        log_data = {
            'session_id': self.session_id,
            'conversation_summary': self.get_conversation_summary(),
            'conversation_history': self.context.get('conversation_history', []),
            'export_time': datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"對話日誌已導出到: {file_path}")
        return file_path


# 使用示例和測試函數
def create_test_conversation():
    """
    創建測試對話示例
    
    演示如何使用狀態管理器處理完整的對話流程
    """
    print("=== 狀態管理器測試對話 ===")
    
    # 創建狀態管理器
    stat_manager = StatManager("test_session_001")
    
    # 模擬用戶輸入事件
    user_event = ChatEvent("user_input", {
        "user_input": "我想查詢筆電規格",
        "direct_response": False,
        "needs_data_query": True
    })
    
    print(f"初始狀態: {stat_manager.get_current_state().value}")
    
    # 處理用戶輸入
    if stat_manager.process_event(user_event):
        print(f"處理用戶輸入後狀態: {stat_manager.get_current_state().value}")
    
    # 模擬數據查詢事件
    data_event = ChatEvent("data_query_complete", {
        "data_query": "查詢筆電規格",
        "data_results": "找到相關筆電規格信息"
    })
    
    if stat_manager.process_event(data_event):
        print(f"數據查詢完成後狀態: {stat_manager.get_current_state().value}")
    
    # 模擬系統回應事件
    response_event = ChatEvent("generate_response", {
        "direct_response": True
    })
    
    if stat_manager.process_event(response_event):
        print(f"生成回應後狀態: {stat_manager.get_current_state().value}")
    
    # 顯示對話摘要
    summary = stat_manager.get_conversation_summary()
    print(f"對話摘要: {summary}")
    
    return stat_manager


if __name__ == "__main__":
    # 運行測試
    test_manager = create_test_conversation()
