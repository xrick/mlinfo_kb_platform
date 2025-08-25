#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回應生成器
負責生成各種類型的回應
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime


class ResponseGenerator:
    """
    回應生成器
    負責生成各種類型的回應，包括文本、JSON、HTML等
    """
    
    def __init__(self):
        """初始化回應生成器"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("回應生成器初始化完成")
    
    def generate_text_response(self, content: str, **kwargs) -> str:
        """
        生成文本回應
        
        Args:
            content: 回應內容
            **kwargs: 額外參數
            
        Returns:
            格式化的文本回應
        """
        try:
            # 基本文本回應
            response = content
            
            # 添加時間戳（如果需要）
            if kwargs.get('include_timestamp', False):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                response = f"[{timestamp}] {response}"
            
            # 添加前綴（如果需要）
            if 'prefix' in kwargs:
                response = f"{kwargs['prefix']} {response}"
            
            # 添加後綴（如果需要）
            if 'suffix' in kwargs:
                response = f"{response} {kwargs['suffix']}"
            
            return response
            
        except Exception as e:
            self.logger.error(f"生成文本回應失敗: {e}")
            return f"回應生成失敗: {str(e)}"
    
    def generate_json_response(self, data: Dict[str, Any], **kwargs) -> str:
        """
        生成 JSON 回應
        
        Args:
            data: 回應數據
            **kwargs: 額外參數
            
        Returns:
            JSON 格式的回應
        """
        try:
            # 添加元數據
            response_data = {
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            # 添加額外字段
            for key, value in kwargs.items():
                if key not in response_data:
                    response_data[key] = value
            
            return json.dumps(response_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"生成 JSON 回應失敗: {e}")
            error_response = {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
            return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    def generate_error_response(self, error_message: str, error_code: str = "UNKNOWN_ERROR") -> str:
        """
        生成錯誤回應
        
        Args:
            error_message: 錯誤訊息
            error_code: 錯誤代碼
            
        Returns:
            錯誤回應
        """
        try:
            error_data = {
                "error": {
                    "message": error_message,
                    "code": error_code,
                    "timestamp": datetime.now().isoformat()
                },
                "status": "error"
            }
            
            return json.dumps(error_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"生成錯誤回應失敗: {e}")
            return f"錯誤回應生成失敗: {str(e)}"
    
    def generate_success_response(self, data: Any, message: str = "操作成功") -> str:
        """
        生成成功回應
        
        Args:
            data: 回應數據
            message: 成功訊息
            
        Returns:
            成功回應
        """
        try:
            success_data = {
                "data": data,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            return json.dumps(success_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"生成成功回應失敗: {e}")
            return self.generate_error_response(f"成功回應生成失敗: {str(e)}")
    
    def generate_stream_response(self, content_generator, **kwargs) -> str:
        """
        生成串流回應
        
        Args:
            content_generator: 內容生成器
            **kwargs: 額外參數
            
        Returns:
            串流回應格式
        """
        try:
            # 這裡可以實現串流回應的邏輯
            # 目前返回基本格式
            return f"data: {json.dumps({'content': 'stream_response'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            self.logger.error(f"生成串流回應失敗: {e}")
            return f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    def format_markdown_response(self, content: str, **kwargs) -> str:
        """
        格式化 Markdown 回應
        
        Args:
            content: 原始內容
            **kwargs: 額外參數
            
        Returns:
            格式化的 Markdown 回應
        """
        try:
            # 基本 Markdown 格式化
            formatted_content = content
            
            # 添加標題（如果需要）
            if 'title' in kwargs:
                formatted_content = f"# {kwargs['title']}\n\n{formatted_content}"
            
            # 添加代碼塊（如果需要）
            if 'code_block' in kwargs:
                formatted_content += f"\n\n```\n{kwargs['code_block']}\n```"
            
            # 添加表格（如果需要）
            if 'table_data' in kwargs:
                table_data = kwargs['table_data']
                if isinstance(table_data, list) and len(table_data) > 0:
                    # 生成表格
                    table_content = self._generate_markdown_table(table_data)
                    formatted_content += f"\n\n{table_content}"
            
            return formatted_content
            
        except Exception as e:
            self.logger.error(f"格式化 Markdown 回應失敗: {e}")
            return f"Markdown 格式化失敗: {str(e)}"
    
    def _generate_markdown_table(self, data: List[Dict[str, Any]]) -> str:
        """
        生成 Markdown 表格
        
        Args:
            data: 表格數據
            
        Returns:
            Markdown 表格字符串
        """
        try:
            if not data:
                return ""
            
            # 獲取列標題
            headers = list(data[0].keys())
            
            # 生成表頭
            table = "| " + " | ".join(headers) + " |\n"
            table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
            
            # 生成數據行
            for row in data:
                row_values = [str(row.get(header, "")) for header in headers]
                table += "| " + " | ".join(row_values) + " |\n"
            
            return table
            
        except Exception as e:
            self.logger.error(f"生成 Markdown 表格失敗: {e}")
            return f"表格生成失敗: {str(e)}"
    
    def generate_html_response(self, content: str, **kwargs) -> str:
        """
        生成 HTML 回應
        
        Args:
            content: 內容
            **kwargs: 額外參數
            
        Returns:
            HTML 格式的回應
        """
        try:
            # 基本 HTML 結構
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{kwargs.get('title', '回應')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .content {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .timestamp {{ color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="content">
        {content}
    </div>
    <div class="timestamp">
        生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </div>
</body>
</html>
            """
            
            return html.strip()
            
        except Exception as e:
            self.logger.error(f"生成 HTML 回應失敗: {e}")
            return f"<html><body><p>HTML 生成失敗: {str(e)}</p></body></html>"
