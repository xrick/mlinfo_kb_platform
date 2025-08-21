#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
筆電規格資料查詢腳本
提供多種查詢方式來搜尋和顯示筆電規格資料
"""

import sqlite3
import argparse
from pathlib import Path
from typing import List, Dict, Any

class NotebookSpecQuery:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """連接到資料庫"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"❌ 連接資料庫失敗: {e}")
            return False
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """取得資料庫統計資訊"""
        try:
            # 總記錄數
            self.cursor.execute('SELECT COUNT(*) FROM notebook_specs')
            total_records = self.cursor.fetchone()[0]
            
            # 各型號記錄數
            self.cursor.execute('''
                SELECT modeltype, COUNT(*) as count 
                FROM notebook_specs 
                GROUP BY modeltype 
                ORDER BY count DESC
            ''')
            modeltype_counts = dict(self.cursor.fetchall())
            
            # 各版本記錄數
            self.cursor.execute('''
                SELECT version, COUNT(*) as count 
                FROM notebook_specs 
                GROUP BY version 
                ORDER BY count DESC
                LIMIT 10
            ''')
            version_counts = dict(self.cursor.fetchall())
            
            return {
                'total_records': total_records,
                'modeltype_counts': modeltype_counts,
                'version_counts': version_counts
            }
        except Exception as e:
            print(f"❌ 取得統計資訊失敗: {e}")
            return {}
    
    def search_by_modeltype(self, modeltype: str) -> List[Dict[str, Any]]:
        """根據型號類型搜尋"""
        try:
            self.cursor.execute('''
                SELECT modeltype, version, modelname, mainboard, cpu, gpu, memory, storage, source_file
                FROM notebook_specs 
                WHERE modeltype LIKE ? 
                ORDER BY version, modelname
            ''', (f'%{modeltype}%',))
            
            columns = [desc[0] for desc in self.cursor.description]
            rows = []
            for row in self.cursor.fetchall():
                rows.append(dict(zip(columns, row)))
            
            return rows
        except Exception as e:
            print(f"❌ 搜尋失敗: {e}")
            return []
    
    def search_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """根據關鍵字搜尋（在主要欄位中搜尋）"""
        try:
            self.cursor.execute('''
                SELECT modeltype, version, modelname, mainboard, cpu, gpu, memory, storage, source_file
                FROM notebook_specs 
                WHERE modeltype LIKE ? OR version LIKE ? OR modelname LIKE ? OR cpu LIKE ? OR gpu LIKE ?
                ORDER BY modeltype, version
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
            
            columns = [desc[0] for desc in self.cursor.description]
            rows = []
            for row in self.cursor.fetchall():
                rows.append(dict(zip(columns, row)))
            
            return rows
        except Exception as e:
            print(f"❌ 搜尋失敗: {e}")
            return []
    
    def get_detailed_spec(self, record_id: int) -> Dict[str, Any]:
        """取得詳細規格"""
        try:
            self.cursor.execute('''
                SELECT * FROM notebook_specs WHERE id = ?
            ''', (record_id,))
            
            columns = [desc[0] for desc in self.cursor.description]
            row = self.cursor.fetchone()
            
            if row:
                return dict(zip(columns, row))
            else:
                return {}
        except Exception as e:
            print(f"❌ 取得詳細規格失敗: {e}")
            return {}
    
    def list_all_models(self, limit: int = 50) -> List[Dict[str, Any]]:
        """列出所有型號（限制數量）"""
        try:
            self.cursor.execute('''
                SELECT id, modeltype, version, modelname, source_file
                FROM notebook_specs 
                ORDER BY modeltype, version, modelname
                LIMIT ?
            ''', (limit,))
            
            columns = [desc[0] for desc in self.cursor.description]
            rows = []
            for row in self.cursor.fetchall():
                rows.append(dict(zip(columns, row)))
            
            return rows
        except Exception as e:
            print(f"❌ 列出型號失敗: {e}")
            return []
    
    def display_results(self, results: List[Dict[str, Any]], title: str = "搜尋結果"):
        """顯示搜尋結果"""
        if not results:
            print(f"📭 {title}: 沒有找到符合的結果")
            return
        
        print(f"\n📋 {title} ({len(results)} 筆):")
        print("=" * 100)
        
        for i, result in enumerate(results, 1):
            print(f"{i:2d}. 型號: {result.get('modeltype', 'N/A')}")
            print(f"    版本: {result.get('version', 'N/A')}")
            print(f"    名稱: {result.get('modelname', 'N/A')}")
            if 'mainboard' in result:
                print(f"    主機板: {result.get('mainboard', 'N/A')}")
            if 'cpu' in result:
                print(f"    CPU: {result.get('cpu', 'N/A')[:80]}...")
            if 'gpu' in result:
                print(f"    GPU: {result.get('gpu', 'N/A')[:80]}...")
            if 'memory' in result:
                print(f"    記憶體: {result.get('memory', 'N/A')[:80]}...")
            if 'storage' in result:
                print(f"    儲存: {result.get('storage', 'N/A')[:80]}...")
            if 'source_file' in result:
                print(f"    來源: {result.get('source_file', 'N/A')}")
            print("-" * 100)

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='筆電規格資料查詢工具')
    parser.add_argument('--db', default='db/nb_spec_0250821v1.db', help='資料庫路徑')
    parser.add_argument('--stats', action='store_true', help='顯示資料庫統計資訊')
    parser.add_argument('--list', action='store_true', help='列出所有型號')
    parser.add_argument('--modeltype', help='根據型號類型搜尋')
    parser.add_argument('--keyword', help='根據關鍵字搜尋')
    parser.add_argument('--detail', type=int, help='顯示指定ID的詳細規格')
    parser.add_argument('--limit', type=int, default=50, help='限制顯示數量')
    
    args = parser.parse_args()
    
    # 檢查資料庫是否存在
    if not Path(args.db).exists():
        print(f"❌ 資料庫不存在: {args.db}")
        return
    
    # 建立查詢器
    query = NotebookSpecQuery(args.db)
    
    if not query.connect():
        return
    
    try:
        if args.stats:
            # 顯示統計資訊
            stats = query.get_database_stats()
            if stats:
                print("📊 資料庫統計資訊:")
                print(f"總記錄數: {stats['total_records']}")
                print("\n各型號記錄數:")
                for modeltype, count in stats['modeltype_counts'].items():
                    print(f"  {modeltype}: {count} 筆")
                print("\n各版本記錄數:")
                for version, count in stats['version_counts'].items():
                    print(f"  {version}: {count} 筆")
        
        elif args.list:
            # 列出所有型號
            models = query.list_all_models(args.limit)
            query.display_results(models, f"所有型號 (限制 {args.limit} 筆)")
        
        elif args.modeltype:
            # 根據型號類型搜尋
            results = query.search_by_modeltype(args.modeltype)
            query.display_results(results, f"型號類型 '{args.modeltype}' 的搜尋結果")
        
        elif args.keyword:
            # 根據關鍵字搜尋
            results = query.search_by_keyword(args.keyword)
            query.display_results(results, f"關鍵字 '{args.keyword}' 的搜尋結果")
        
        elif args.detail:
            # 顯示詳細規格
            spec = query.get_detailed_spec(args.detail)
            if spec:
                print(f"📋 詳細規格 (ID: {args.detail}):")
                print("=" * 80)
                for key, value in spec.items():
                    if value:  # 只顯示有值的欄位
                        print(f"{key:20s}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
            else:
                print(f"❌ 找不到ID為 {args.detail} 的記錄")
        
        else:
            # 預設顯示統計資訊
            stats = query.get_database_stats()
            if stats:
                print("📊 資料庫統計資訊:")
                print(f"總記錄數: {stats['total_records']}")
                print("\n各型號記錄數:")
                for modeltype, count in stats['modeltype_counts'].items():
                    print(f"  {modeltype}: {count} 筆")
            
            print("\n💡 使用方式:")
            print("  python scripts/query_nb_specs.py --stats          # 顯示統計資訊")
            print("  python scripts/query_nb_specs.py --list           # 列出所有型號")
            print("  python scripts/query_nb_specs.py --modeltype 27   # 搜尋型號27")
            print("  python scripts/query_nb_specs.py --keyword AMD    # 搜尋關鍵字AMD")
            print("  python scripts/query_nb_specs.py --detail 1      # 顯示ID=1的詳細規格")
    
    finally:
        query.close()

if __name__ == "__main__":
    main()

