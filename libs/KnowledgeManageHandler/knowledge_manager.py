#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知識管理器
負責管理和處理各種知識庫
"""

import json
import logging
import sqlite3
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import pandas as pd


class KnowledgeManager:
    """
    知識管理器
    負責管理和處理各種知識庫，包括數據庫、文件、向量存儲等
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化知識管理器
        
        Args:
            base_path: 基礎路徑，默認為專案根目錄
        """
        self.logger = logging.getLogger(__name__)
        
        # 設定基礎路徑
        if base_path is None:
            self.base_path = Path(__file__).resolve().parents[2]
        else:
            self.base_path = Path(base_path)
        
        # 知識庫配置
        self.knowledge_bases = {}
        
        # 初始化默認知識庫
        self._initialize_default_knowledge_bases()
        
        self.logger.info(f"知識管理器初始化完成，基礎路徑: {self.base_path}")
    
    def _initialize_default_knowledge_bases(self):
        """初始化默認知識庫"""
        try:
            # 銷售規格知識庫
            sales_specs_db = self.base_path / "db" / "sales_specs.db"
            if sales_specs_db.exists():
                self.knowledge_bases["sales_specs"] = {
                    "type": "sqlite",
                    "path": str(sales_specs_db),
                    "description": "銷售規格數據庫"
                }
            
            # 歷史記錄知識庫
            history_db = self.base_path / "db" / "history.db"
            if history_db.exists():
                self.knowledge_bases["history"] = {
                    "type": "sqlite",
                    "path": str(history_db),
                    "description": "歷史記錄數據庫"
                }
            
            # 語義銷售規格知識庫
            semantic_db = self.base_path / "semantic_sales_spec.db"
            if semantic_db.exists():
                self.knowledge_bases["semantic_sales_spec"] = {
                    "type": "sqlite",
                    "path": str(semantic_db),
                    "description": "語義銷售規格數據庫"
                }
            
            self.logger.info(f"初始化了 {len(self.knowledge_bases)} 個知識庫")
            
        except Exception as e:
            self.logger.error(f"初始化默認知識庫失敗: {e}")
    
    def add_knowledge_base(self, name: str, kb_type: str, path: str, description: str = ""):
        """
        添加知識庫
        
        Args:
            name: 知識庫名稱
            kb_type: 知識庫類型
            path: 知識庫路徑
            description: 描述
        """
        try:
            self.knowledge_bases[name] = {
                "type": kb_type,
                "path": path,
                "description": description
            }
            self.logger.info(f"添加知識庫: {name} ({kb_type})")
        except Exception as e:
            self.logger.error(f"添加知識庫失敗 {name}: {e}")
    
    def remove_knowledge_base(self, name: str):
        """
        移除知識庫
        
        Args:
            name: 知識庫名稱
        """
        try:
            if name in self.knowledge_bases:
                del self.knowledge_bases[name]
                self.logger.info(f"移除知識庫: {name}")
            else:
                self.logger.warning(f"知識庫不存在: {name}")
        except Exception as e:
            self.logger.error(f"移除知識庫失敗 {name}: {e}")
    
    def list_knowledge_bases(self) -> List[str]:
        """
        列出所有知識庫
        
        Returns:
            知識庫名稱列表
        """
        return list(self.knowledge_bases.keys())
    
    def get_knowledge_base_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        獲取知識庫信息
        
        Args:
            name: 知識庫名稱
            
        Returns:
            知識庫信息字典
        """
        return self.knowledge_bases.get(name)
    
    def query_sqlite_knowledge_base(self, kb_name: str, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        查詢 SQLite 知識庫
        
        Args:
            kb_name: 知識庫名稱
            query: SQL 查詢語句
            
        Returns:
            查詢結果列表
        """
        try:
            kb_info = self.knowledge_bases.get(kb_name)
            if not kb_info or kb_info["type"] != "sqlite":
                self.logger.error(f"知識庫不存在或類型不匹配: {kb_name}")
                return None
            
            db_path = kb_info["path"]
            if not Path(db_path).exists():
                self.logger.error(f"數據庫文件不存在: {db_path}")
                return None
            
            # 執行查詢
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query)
                
                # 獲取結果
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    row_dict = dict(row)
                    results.append(row_dict)
                
                self.logger.info(f"查詢知識庫 {kb_name} 成功，返回 {len(results)} 條記錄")
                return results
                
        except Exception as e:
            self.logger.error(f"查詢知識庫失敗 {kb_name}: {e}")
            return None
    
    def query_sales_specs(self, model_name: Optional[str] = None, 
                         model_type: Optional[str] = None,
                         limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        查詢銷售規格
        
        Args:
            model_name: 型號名稱
            model_type: 型號類型
            limit: 限制結果數量
            
        Returns:
            規格數據列表
        """
        try:
            # 構建查詢條件
            conditions = []
            params = []
            
            if model_name:
                conditions.append("modelname LIKE ?")
                params.append(f"%{model_name}%")
            
            if model_type:
                conditions.append("modeltype = ?")
                params.append(model_type)
            
            # 構建 SQL 查詢
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"""
                SELECT * FROM specs 
                WHERE {where_clause}
                LIMIT {limit}
            """
            
            # 執行查詢
            kb_info = self.knowledge_bases.get("sales_specs")
            if not kb_info:
                self.logger.error("銷售規格知識庫不存在")
                return None
            
            with sqlite3.connect(kb_info["path"]) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    row_dict = dict(row)
                    results.append(row_dict)
                
                self.logger.info(f"查詢銷售規格成功，返回 {len(results)} 條記錄")
                return results
                
        except Exception as e:
            self.logger.error(f"查詢銷售規格失敗: {e}")
            return None
    
    def search_semantic_knowledge_base(self, query: str, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        語義搜索知識庫
        
        Args:
            query: 搜索查詢
            limit: 限制結果數量
            
        Returns:
            搜索結果列表
        """
        try:
            # 這裡可以實現語義搜索邏輯
            # 目前使用基本的文本搜索
            kb_info = self.knowledge_bases.get("semantic_sales_spec")
            if not kb_info:
                self.logger.error("語義銷售規格知識庫不存在")
                return None
            
            # 簡單的文本搜索實現
            search_query = f"""
                SELECT * FROM specs 
                WHERE modelname LIKE ? OR modeltype LIKE ? OR cpu LIKE ? OR gpu LIKE ?
                LIMIT {limit}
            """
            
            search_term = f"%{query}%"
            params = [search_term, search_term, search_term, search_term]
            
            with sqlite3.connect(kb_info["path"]) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(search_query, params)
                
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    row_dict = dict(row)
                    results.append(row_dict)
                
                self.logger.info(f"語義搜索成功，返回 {len(results)} 條記錄")
                return results
                
        except Exception as e:
            self.logger.error(f"語義搜索失敗: {e}")
            return None
    
    def get_knowledge_base_schema(self, kb_name: str) -> Optional[List[str]]:
        """
        獲取知識庫結構
        
        Args:
            kb_name: 知識庫名稱
            
        Returns:
            字段名稱列表
        """
        try:
            kb_info = self.knowledge_bases.get(kb_name)
            if not kb_info or kb_info["type"] != "sqlite":
                self.logger.error(f"知識庫不存在或類型不匹配: {kb_name}")
                return None
            
            with sqlite3.connect(kb_info["path"]) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(specs)")
                
                columns = []
                for row in cursor.fetchall():
                    columns.append(row[1])  # 列名
                
                self.logger.info(f"獲取知識庫結構成功: {kb_name}，共 {len(columns)} 個字段")
                return columns
                
        except Exception as e:
            self.logger.error(f"獲取知識庫結構失敗 {kb_name}: {e}")
            return None
    
    def get_knowledge_base_stats(self, kb_name: str) -> Optional[Dict[str, Any]]:
        """
        獲取知識庫統計信息
        
        Args:
            kb_name: 知識庫名稱
            
        Returns:
            統計信息字典
        """
        try:
            kb_info = self.knowledge_bases.get(kb_name)
            if not kb_info or kb_info["type"] != "sqlite":
                self.logger.error(f"知識庫不存在或類型不匹配: {kb_name}")
                return None
            
            with sqlite3.connect(kb_info["path"]) as conn:
                cursor = conn.cursor()
                
                # 獲取記錄總數
                cursor.execute("SELECT COUNT(*) FROM specs")
                total_records = cursor.fetchone()[0]
                
                # 獲取唯一型號數量
                cursor.execute("SELECT COUNT(DISTINCT modelname) FROM specs")
                unique_models = cursor.fetchone()[0]
                
                # 獲取型號類型數量
                cursor.execute("SELECT COUNT(DISTINCT modeltype) FROM specs")
                unique_types = cursor.fetchone()[0]
                
                # 獲取文件大小
                file_size = Path(kb_info["path"]).stat().st_size
                
                stats = {
                    "total_records": total_records,
                    "unique_models": unique_models,
                    "unique_types": unique_types,
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "last_updated": datetime.now().isoformat()
                }
                
                self.logger.info(f"獲取知識庫統計成功: {kb_name}")
                return stats
                
        except Exception as e:
            self.logger.error(f"獲取知識庫統計失敗 {kb_name}: {e}")
            return None
    
    def export_knowledge_base(self, kb_name: str, format: str = "json", 
                            output_path: Optional[str] = None) -> bool:
        """
        導出知識庫
        
        Args:
            kb_name: 知識庫名稱
            format: 導出格式 (json, csv, excel)
            output_path: 輸出路徑
            
        Returns:
            是否成功
        """
        try:
            kb_info = self.knowledge_bases.get(kb_name)
            if not kb_info or kb_info["type"] != "sqlite":
                self.logger.error(f"知識庫不存在或類型不匹配: {kb_name}")
                return False
            
            # 查詢所有數據
            results = self.query_sqlite_knowledge_base(kb_name, "SELECT * FROM specs")
            if not results:
                self.logger.error(f"查詢知識庫數據失敗: {kb_name}")
                return False
            
            # 設定輸出路徑
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.base_path / "exports" / f"{kb_name}_{timestamp}.{format}"
            
            # 確保輸出目錄存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 根據格式導出
            if format == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            
            elif format == "csv":
                df = pd.DataFrame(results)
                df.to_csv(output_path, index=False, encoding='utf-8')
            
            elif format == "excel":
                df = pd.DataFrame(results)
                df.to_excel(output_path, index=False)
            
            else:
                self.logger.error(f"不支援的導出格式: {format}")
                return False
            
            self.logger.info(f"導出知識庫成功: {kb_name} -> {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"導出知識庫失敗 {kb_name}: {e}")
            return False
    
    def backup_knowledge_base(self, kb_name: str) -> bool:
        """
        備份知識庫
        
        Args:
            kb_name: 知識庫名稱
            
        Returns:
            是否成功
        """
        try:
            kb_info = self.knowledge_bases.get(kb_name)
            if not kb_info or kb_info["type"] != "sqlite":
                self.logger.error(f"知識庫不存在或類型不匹配: {kb_name}")
                return False
            
            source_path = Path(kb_info["path"])
            if not source_path.exists():
                self.logger.error(f"源文件不存在: {source_path}")
                return False
            
            # 創建備份路徑
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.base_path / "backups" / "knowledge_bases"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_path = backup_dir / f"{kb_name}_{timestamp}.db"
            
            # 複製文件
            import shutil
            shutil.copy2(source_path, backup_path)
            
            self.logger.info(f"備份知識庫成功: {kb_name} -> {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"備份知識庫失敗 {kb_name}: {e}")
            return False
