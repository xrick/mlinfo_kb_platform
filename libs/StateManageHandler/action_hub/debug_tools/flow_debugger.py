"""
流程除錯工具
提供流程可視化和除錯能力
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional


# 設置日誌
logger = logging.getLogger(__name__)


class FlowDebugger:
    """流程除錯工具"""
    
    def __init__(self):
        """初始化除錯工具"""
        self.debug_session = {}
        self.execution_history = []
        logger.info("流程除錯工具初始化完成")
    
    def log_state_execution(self, state_id: str, state_config: Dict[str, Any], 
                           execution_context: Dict[str, Any]) -> None:
        """
        記錄狀態執行信息
        
        Args:
            state_id: 狀態 ID
            state_config: 狀態配置
            execution_context: 執行上下文
        """
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "state_id": state_id,
            "state_name": state_config.get("state_name", ""),
            "execution_order": state_config.get("execution_order", 0),
            "input_data": self._extract_input_data(state_config, execution_context),
            "output_data": self._extract_output_data(state_config, execution_context),
            "execution_time_ms": execution_context.get(f"{state_id.lower()}_execution_time", 0),
            "success": execution_context.get(f"{state_id.lower()}_completed", False),
            "error": execution_context.get("error", None),
            "session_id": execution_context.get("session_id", "unknown")
        }
        
        self.execution_history.append(execution_record)
        
        # 輸出除錯信息
        if self._should_log_debug_info(state_config):
            self._output_debug_info(execution_record)
    
    def generate_debug_report(self, session_id: str) -> Dict[str, Any]:
        """
        生成除錯報告
        
        Args:
            session_id: 會話 ID
            
        Returns:
            除錯報告
        """
        session_executions = [exec for exec in self.execution_history 
                            if exec.get("session_id") == session_id]
        
        if not session_executions:
            return {
                "session_id": session_id,
                "error": "找不到會話執行記錄",
                "timestamp": datetime.now().isoformat()
            }
        
        # 計算統計信息
        total_states = len(session_executions)
        successful_states = len([exec for exec in session_executions if exec["success"]])
        failed_states = total_states - successful_states
        
        # 計算性能摘要
        performance_summary = self._calculate_performance_summary(session_executions)
        
        # 生成錯誤摘要
        error_summary = self._generate_error_summary(session_executions)
        
        # 生成執行時間線
        execution_timeline = self._generate_execution_timeline(session_executions)
        
        return {
            "session_id": session_id,
            "total_states": total_states,
            "successful_states": successful_states,
            "failed_states": failed_states,
            "success_rate": successful_states / total_states if total_states > 0 else 0,
            "execution_timeline": execution_timeline,
            "performance_summary": performance_summary,
            "error_summary": error_summary,
            "debug_timestamp": datetime.now().isoformat()
        }
    
    def get_execution_history(self, session_id: str = None) -> List[Dict[str, Any]]:
        """
        獲取執行歷史
        
        Args:
            session_id: 會話 ID，如果為 None 則返回所有記錄
            
        Returns:
            執行歷史記錄
        """
        if session_id:
            return [exec for exec in self.execution_history if exec.get("session_id") == session_id]
        return self.execution_history.copy()
    
    def clear_execution_history(self, session_id: str = None):
        """
        清除執行歷史
        
        Args:
            session_id: 會話 ID，如果為 None 則清除所有記錄
        """
        if session_id:
            self.execution_history = [exec for exec in self.execution_history 
                                    if exec.get("session_id") != session_id]
            logger.info(f"已清除會話 {session_id} 的執行歷史")
        else:
            self.execution_history.clear()
            logger.info("已清除所有執行歷史")
    
    def export_debug_data(self, session_id: str, file_path: str) -> bool:
        """
        導出除錯數據到檔案
        
        Args:
            session_id: 會話 ID
            file_path: 導出檔案路徑
            
        Returns:
            是否成功導出
        """
        try:
            debug_report = self.generate_debug_report(session_id)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(debug_report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"除錯數據已導出到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"導出除錯數據失敗: {e}")
            return False
    
    def _extract_input_data(self, state_config: Dict[str, Any], 
                           execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """提取輸入數據"""
        input_data = {}
        
        # 根據狀態配置提取輸入數據
        if "input_schema" in state_config:
            input_schema = state_config["input_schema"]
            
            # 提取必需字段
            for field in input_schema.get("required", []):
                if field in execution_context:
                    input_data[field] = execution_context[field]
                else:
                    input_data[field] = "MISSING"
            
            # 提取可選字段
            for field in input_schema.get("optional", []):
                if field in execution_context:
                    input_data[field] = execution_context[field]
        
        return input_data
    
    def _extract_output_data(self, state_config: Dict[str, Any], 
                            execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """提取輸出數據"""
        output_data = {}
        
        # 根據狀態配置提取輸出數據
        if "output_schema" in state_config:
            output_schema = state_config["output_schema"]
            
            for field in output_schema.keys():
                if field in execution_context:
                    output_data[field] = execution_context[field]
        
        return output_data
    
    def _should_log_debug_info(self, state_config: Dict[str, Any]) -> bool:
        """判斷是否應該輸出除錯信息"""
        # 這裡可以根據配置決定是否輸出除錯信息
        return True
    
    def _output_debug_info(self, execution_record: Dict[str, Any]):
        """輸出除錯信息"""
        state_id = execution_record["state_id"]
        success = execution_record["success"]
        execution_time = execution_record["execution_time_ms"]
        
        if success:
            logger.debug(f"狀態 {state_id} 執行成功，耗時: {execution_time:.2f}ms")
        else:
            error = execution_record.get("error", "未知錯誤")
            logger.warning(f"狀態 {state_id} 執行失敗: {error}")
    
    def _calculate_performance_summary(self, session_executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算性能摘要"""
        if not session_executions:
            return {}
        
        execution_times = [exec.get("execution_time_ms", 0) for exec in session_executions]
        
        return {
            "total_execution_time_ms": sum(execution_times),
            "average_execution_time_ms": sum(execution_times) / len(execution_times) if execution_times else 0,
            "min_execution_time_ms": min(execution_times) if execution_times else 0,
            "max_execution_time_ms": max(execution_times) if execution_times else 0,
            "total_states": len(session_executions)
        }
    
    def _generate_error_summary(self, session_executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成錯誤摘要"""
        error_records = [exec for exec in session_executions if not exec["success"]]
        
        if not error_records:
            return {"error_count": 0, "errors": []}
        
        error_summary = {
            "error_count": len(error_records),
            "errors": []
        }
        
        for error_record in error_records:
            error_info = {
                "state_id": error_record["state_id"],
                "state_name": error_record["state_name"],
                "error": error_record.get("error", "未知錯誤"),
                "timestamp": error_record["timestamp"]
            }
            error_summary["errors"].append(error_info)
        
        return error_summary
    
    def _generate_execution_timeline(self, session_executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成執行時間線"""
        # 按執行順序排序
        sorted_executions = sorted(session_executions, key=lambda x: x.get("execution_order", 0))
        
        timeline = []
        for exec_record in sorted_executions:
            timeline_item = {
                "order": exec_record.get("execution_order", 0),
                "state_id": exec_record["state_id"],
                "state_name": exec_record["state_name"],
                "timestamp": exec_record["timestamp"],
                "execution_time_ms": exec_record.get("execution_time_ms", 0),
                "success": exec_record["success"],
                "error": exec_record.get("error", None)
            }
            timeline.append(timeline_item)
        
        return timeline
    
    def get_debug_statistics(self) -> Dict[str, Any]:
        """獲取除錯統計信息"""
        if not self.execution_history:
            return {"total_sessions": 0, "total_executions": 0}
        
        # 統計會話數量
        session_ids = set(exec.get("session_id") for exec in self.execution_history)
        
        # 統計總執行次數
        total_executions = len(self.execution_history)
        
        # 統計成功和失敗次數
        successful_executions = sum(1 for exec in self.execution_history if exec["success"])
        failed_executions = total_executions - successful_executions
        
        return {
            "total_sessions": len(session_ids),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "last_update": datetime.now().isoformat()
        }


# 導出主要類別
__all__ = ['FlowDebugger']
