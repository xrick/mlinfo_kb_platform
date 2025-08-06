#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckDB CLI查詢工具
用於查詢和探索sales_specs.db中的筆電規格資料
"""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import duckdb
from tabulate import tabulate
import pandas as pd


class DuckDBQueryCLI:
    """DuckDB查詢CLI工具類"""

    def __init__(self, db_path: str):
        """
        初始化DuckDB查詢工具
        
        Args:
            db_path: DuckDB資料庫檔案路徑
        """
        self.db_path = db_path
        self.conn = None
        
    def connect(self) -> bool:
        """
        連接到DuckDB資料庫
        
        Returns:
            是否連接成功
        """
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ 錯誤：找不到資料庫檔案 '{self.db_path}'")
                return False
            
            # 使用read_only模式確保安全
            self.conn = duckdb.connect(self.db_path, read_only=True)
            print(f"✅ 成功連接到DuckDB: {self.db_path}")
            return True
            
        except Exception as e:
            print(f"❌ 連接DuckDB失敗: {e}")
            return False
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def execute_query(self, query: str, params: tuple = ()) -> Optional[List[Tuple]]:
        """
        執行SQL查詢
        
        Args:
            query: SQL查詢語句
            params: 查詢參數
            
        Returns:
            查詢結果或None（如果出錯）
        """
        if not self.conn:
            print("❌ 資料庫未連接")
            return None
            
        try:
            if params:
                result = self.conn.execute(query, params).fetchall()
            else:
                result = self.conn.execute(query).fetchall()
                
            return result
            
        except Exception as e:
            print(f"❌ 查詢執行失敗: {e}")
            print(f"   SQL: {query}")
            return None
    
    def get_table_info(self) -> Dict[str, Any]:
        """
        獲取資料庫表格資訊
        
        Returns:
            表格資訊字典
        """
        info = {}
        
        # 獲取所有表格
        tables_result = self.execute_query("SHOW TABLES")
        if not tables_result:
            return info
        
        tables = [row[0] for row in tables_result]
        info['tables'] = tables
        
        # 獲取每個表格的詳細資訊
        for table in tables:
            table_info = {}
            
            # 獲取欄位資訊
            columns_result = self.execute_query(f"DESCRIBE {table}")
            if columns_result:
                columns = []
                for col in columns_result:
                    columns.append({
                        'name': col[0],
                        'type': col[1],
                        'nullable': col[2] if len(col) > 2 else None
                    })
                table_info['columns'] = columns
                table_info['column_count'] = len(columns)
            
            # 獲取記錄數
            count_result = self.execute_query(f"SELECT COUNT(*) FROM {table}")
            if count_result:
                table_info['row_count'] = count_result[0][0]
            
            info[table] = table_info
        
        return info
    
    def show_info(self):
        """顯示資料庫基本資訊"""
        print("\n🗃️  DuckDB資料庫資訊")
        print("=" * 50)
        print(f"資料庫路徑: {self.db_path}")
        
        info = self.get_table_info()
        if not info:
            print("❌ 無法獲取資料庫資訊")
            return
        
        print(f"資料庫大小: {self._get_file_size(self.db_path)}")
        print(f"包含表格數: {len(info.get('tables', []))}")
        
        for table_name in info.get('tables', []):
            table_info = info.get(table_name, {})
            row_count = table_info.get('row_count', 0)
            col_count = table_info.get('column_count', 0)
            print(f"  📊 {table_name}: {row_count:,} 筆記錄, {col_count} 個欄位")
    
    def show_schema(self, table_name: str = 'specs'):
        """
        顯示表格結構
        
        Args:
            table_name: 表格名稱
        """
        print(f"\n📋 表格 '{table_name}' 結構")
        print("=" * 60)
        
        columns_result = self.execute_query(f"DESCRIBE {table_name}")
        if not columns_result:
            print(f"❌ 無法獲取表格 '{table_name}' 的結構")
            return
        
        # 準備表格資料
        table_data = []
        for i, col in enumerate(columns_result, 1):
            table_data.append([
                i,
                col[0],  # column name
                col[1],  # data type
                "Yes" if len(col) > 2 and col[2] else "No"  # nullable
            ])
        
        print(tabulate(
            table_data,
            headers=["#", "欄位名稱", "資料型別", "可為空"],
            tablefmt="grid"
        ))
        
        # 顯示記錄數統計
        count_result = self.execute_query(f"SELECT COUNT(*) FROM {table_name}")
        if count_result:
            print(f"\n📈 總記錄數: {count_result[0][0]:,}")
    
    def list_records(self, table_name: str = 'specs', limit: int = 10, offset: int = 0, 
                    columns: List[str] = None):
        """
        列出記錄
        
        Args:
            table_name: 表格名稱
            limit: 限制筆數
            offset: 偏移量
            columns: 指定顯示的欄位
        """
        print(f"\n📝 表格 '{table_name}' 記錄 (顯示 {offset+1}-{offset+limit})")
        print("=" * 80)
        
        # 建構查詢
        if columns:
            cols_str = ", ".join(columns)
        else:
            cols_str = "*"
        
        query = f"SELECT {cols_str} FROM {table_name} LIMIT {limit} OFFSET {offset}"
        result = self.execute_query(query)
        
        if not result:
            print("❌ 查詢失敗")
            return
        
        if not result:
            print("📭 沒有找到記錄")
            return
        
        # 獲取欄位名稱
        if columns:
            headers = columns
        else:
            columns_result = self.execute_query(f"DESCRIBE {table_name}")
            headers = [col[0] for col in columns_result] if columns_result else []
        
        # 顯示結果
        print(tabulate(result, headers=headers, tablefmt="grid", maxcolwidths=30))
        print(f"\n📊 顯示了 {len(result)} 筆記錄")
    
    def show_model(self, model_name: str, table_name: str = 'specs'):
        """
        顯示特定型號的詳細資訊
        
        Args:
            model_name: 型號名稱
            table_name: 表格名稱
        """
        print(f"\n🔍 型號 '{model_name}' 詳細資訊")
        print("=" * 60)
        
        query = f"SELECT * FROM {table_name} WHERE modelname = ?"
        result = self.execute_query(query, (model_name,))
        
        if not result:
            print("❌ 查詢失敗")
            return
        
        if not result:
            print(f"📭 找不到型號 '{model_name}'")
            return
        
        # 獲取欄位名稱
        columns_result = self.execute_query(f"DESCRIBE {table_name}")
        if not columns_result:
            print("❌ 無法獲取欄位資訊")
            return
        
        headers = [col[0] for col in columns_result]
        
        # 垂直顯示詳細資訊
        for record in result:
            print(f"\n📋 記錄 {result.index(record) + 1}:")
            for i, value in enumerate(record):
                field_name = headers[i] if i < len(headers) else f"欄位{i+1}"
                display_value = value if value is not None and value != '' else "N/A"
                print(f"  {field_name:15}: {display_value}")
        
        print(f"\n✅ 找到 {len(result)} 筆匹配記錄")
    
    def search_records(self, keyword: str, table_name: str = 'specs', limit: int = 20):
        """
        搜尋包含關鍵字的記錄
        
        Args:
            keyword: 搜尋關鍵字
            table_name: 表格名稱
            limit: 限制結果數量
        """
        print(f"\n🔎 搜尋關鍵字 '{keyword}' (限制 {limit} 筆)")
        print("=" * 60)
        
        # 獲取所有欄位名稱
        columns_result = self.execute_query(f"DESCRIBE {table_name}")
        if not columns_result:
            print("❌ 無法獲取欄位資訊")
            return
        
        columns = [col[0] for col in columns_result]
        
        # 建構搜尋條件 - 在所有欄位中搜尋
        conditions = []
        for col in columns:
            conditions.append(f"{col} LIKE ?")
        
        where_clause = " OR ".join(conditions)
        query = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT {limit}"
        
        # 為每個欄位準備參數
        params = tuple(f"%{keyword}%" for _ in columns)
        
        result = self.execute_query(query, params)
        
        if result is None:
            print("❌ 搜尋失敗")
            return
        
        if not result:
            print(f"📭 沒有找到包含 '{keyword}' 的記錄")
            return
        
        # 顯示主要欄位的搜尋結果
        main_columns = ['modelname', 'modeltype', 'cpu', 'memory', 'storage', 'lcd']
        available_columns = [col for col in main_columns if col in columns]
        
        # 提取指定欄位的資料
        main_col_indices = [columns.index(col) for col in available_columns]
        filtered_result = []
        for row in result:
            filtered_row = [row[i] for i in main_col_indices]
            filtered_result.append(filtered_row)
        
        print(tabulate(
            filtered_result,
            headers=available_columns,
            tablefmt="grid",
            maxcolwidths=25
        ))
        
        print(f"\n✅ 找到 {len(result)} 筆匹配記錄")
        
        if len(result) == limit:
            print(f"💡 結果已限制為 {limit} 筆，可能還有更多匹配記錄")
    
    def get_column_stats(self, column_name: str, table_name: str = 'specs'):
        """
        獲取欄位統計資訊
        
        Args:
            column_name: 欄位名稱
            table_name: 表格名稱
        """
        print(f"\n📊 欄位 '{column_name}' 統計資訊")
        print("=" * 50)
        
        # 檢查欄位是否存在
        columns_result = self.execute_query(f"DESCRIBE {table_name}")
        if not columns_result:
            print("❌ 無法獲取表格結構")
            return
        
        available_columns = [col[0] for col in columns_result]
        if column_name not in available_columns:
            print(f"❌ 欄位 '{column_name}' 不存在")
            print(f"可用欄位: {', '.join(available_columns)}")
            return
        
        # 基本統計
        stats_queries = [
            ("記錄總數", f"SELECT COUNT(*) FROM {table_name}"),
            ("非空值數", f"SELECT COUNT({column_name}) FROM {table_name}"),
            ("空值數", f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NULL OR {column_name} = ''"),
            ("唯一值數", f"SELECT COUNT(DISTINCT {column_name}) FROM {table_name}")
        ]
        
        print("基本統計:")
        for stat_name, query in stats_queries:
            result = self.execute_query(query)
            if result:
                print(f"  {stat_name}: {result[0][0]:,}")
        
        # 前10個最常見的值
        print(f"\n'{column_name}' 前10個最常見的值:")
        top_values_query = f"""
        SELECT {column_name}, COUNT(*) as count 
        FROM {table_name} 
        WHERE {column_name} IS NOT NULL AND {column_name} != ''
        GROUP BY {column_name} 
        ORDER BY count DESC 
        LIMIT 10
        """
        
        result = self.execute_query(top_values_query)
        if result:
            table_data = [[i+1, value, count] for i, (value, count) in enumerate(result)]
            print(tabulate(
                table_data,
                headers=["排名", "值", "出現次數"],
                tablefmt="grid"
            ))
        else:
            print("❌ 無法獲取統計資料")
    
    def execute_sql(self, sql: str):
        """
        執行自定義SQL查詢
        
        Args:
            sql: SQL查詢語句
        """
        print(f"\n🛠️  執行SQL查詢")
        print("=" * 50)
        print(f"SQL: {sql}")
        print("-" * 50)
        
        result = self.execute_query(sql)
        
        if result is None:
            print("❌ 查詢執行失敗")
            return
        
        if not result:
            print("📭 查詢結果為空")
            return
        
        # 嘗試獲取欄位名稱（這對某些查詢可能不可用）
        try:
            # 獲取查詢的欄位名稱（僅對簡單SELECT查詢有效）
            description = self.conn.description if hasattr(self.conn, 'description') else None
            if description:
                headers = [col[0] for col in description]
            else:
                headers = [f"列{i+1}" for i in range(len(result[0]) if result else 0)]
        except:
            headers = [f"列{i+1}" for i in range(len(result[0]) if result else 0)]
        
        # 顯示結果
        print(tabulate(result, headers=headers, tablefmt="grid", maxcolwidths=30))
        print(f"\n✅ 查詢完成，返回 {len(result)} 筆記錄")
    
    def export_data(self, output_file: str, query: str = None, table_name: str = 'specs', 
                   format: str = 'csv'):
        """
        匯出資料
        
        Args:
            output_file: 輸出檔案路徑
            query: 自定義查詢（可選）
            table_name: 表格名稱
            format: 輸出格式 ('csv' 或 'json')
        """
        print(f"\n💾 匯出資料到 {output_file}")
        print("=" * 50)
        
        # 使用自定義查詢或預設查詢
        if query:
            sql_query = query
        else:
            sql_query = f"SELECT * FROM {table_name}"
        
        result = self.execute_query(sql_query)
        
        if result is None:
            print("❌ 資料查詢失敗")
            return
        
        if not result:
            print("📭 沒有資料可匯出")
            return
        
        try:
            if format.lower() == 'csv':
                # 對於自定義查詢，嘗試從查詢結果推斷欄位名稱
                if query:
                    # 簡單的欄位名稱推斷 - 提取SELECT後面的欄位
                    try:
                        select_part = query.upper().split('SELECT')[1].split('FROM')[0]
                        if '*' in select_part:
                            # 如果是SELECT *，獲取表格的所有欄位
                            columns_result = self.execute_query(f"DESCRIBE {table_name}")
                            headers = [col[0] for col in columns_result] if columns_result else []
                        else:
                            # 簡單解析欄位名稱（去除AS別名等）
                            fields = [field.strip().split(' AS ')[-1].split(' ')[-1] for field in select_part.split(',')]
                            headers = [field.strip() for field in fields]
                    except:
                        # 如果解析失敗，使用通用名稱
                        headers = [f"欄位{i+1}" for i in range(len(result[0]) if result else 0)]
                else:
                    # 獲取表格的所有欄位名稱
                    columns_result = self.execute_query(f"DESCRIBE {table_name}")
                    headers = [col[0] for col in columns_result] if columns_result else []
                
                # 確保headers數量與結果欄位數量匹配
                if result and len(headers) != len(result[0]):
                    headers = [f"欄位{i+1}" for i in range(len(result[0]))]
                
                # 使用pandas匯出CSV
                df = pd.DataFrame(result, columns=headers)
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                
            elif format.lower() == 'json':
                # 獲取欄位名稱
                columns_result = self.execute_query(f"DESCRIBE {table_name}")
                if columns_result:
                    headers = [col[0] for col in columns_result]
                else:
                    headers = [f"欄位{i+1}" for i in range(len(result[0]))]
                
                # 轉換為字典列表
                data = []
                for row in result:
                    record = {}
                    for i, value in enumerate(row):
                        record[headers[i]] = value
                    data.append(record)
                
                # 匯出JSON
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            else:
                print(f"❌ 不支援的格式: {format}")
                return
            
            print(f"✅ 成功匯出 {len(result)} 筆記錄到 {output_file}")
            
        except Exception as e:
            print(f"❌ 匯出失敗: {e}")
    
    def _get_file_size(self, file_path: str) -> str:
        """獲取檔案大小的人類可讀格式"""
        try:
            size_bytes = os.path.getsize(file_path)
            
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f} TB"
            
        except:
            return "未知"


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="DuckDB CLI查詢工具 - 用於查詢筆電規格資料庫",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
使用範例:
  %(prog)s info                          # 顯示資料庫基本資訊
  %(prog)s schema                        # 顯示表格結構
  %(prog)s list --limit 5                # 列出前5筆記錄
  %(prog)s show "AHP819: FP7R2"          # 顯示特定型號詳細資訊
  %(prog)s search "Ryzen"                # 搜尋包含Ryzen的記錄
  %(prog)s stats cpu                     # 顯示CPU欄位統計
  %(prog)s sql "SELECT modelname, cpu FROM specs LIMIT 5"  # 執行自定義SQL
  %(prog)s export output.csv             # 匯出所有資料為CSV
  %(prog)s export output.json --format json  # 匯出所有資料為JSON
        """
    )
    
    parser.add_argument(
        '--db-path',
        default='../db/sales_specs.db',
        help='DuckDB資料庫檔案路徑 (預設: db/sales_specs.db)'
    )
    
    parser.add_argument(
        '--table',
        default='specs',
        help='表格名稱 (預設: specs)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # info命令
    info_parser = subparsers.add_parser('info', help='顯示資料庫基本資訊')
    
    # schema命令
    schema_parser = subparsers.add_parser('schema', help='顯示表格結構')
    
    # list命令
    list_parser = subparsers.add_parser('list', help='列出記錄')
    list_parser.add_argument('--limit', type=int, default=10, help='限制筆數 (預設: 10)')
    list_parser.add_argument('--offset', type=int, default=0, help='偏移量 (預設: 0)')
    list_parser.add_argument('--columns', nargs='+', help='指定顯示欄位')
    
    # show命令
    show_parser = subparsers.add_parser('show', help='顯示特定型號詳細資訊')
    show_parser.add_argument('model', help='型號名稱')
    
    # search命令
    search_parser = subparsers.add_parser('search', help='搜尋記錄')
    search_parser.add_argument('keyword', help='搜尋關鍵字')
    search_parser.add_argument('--limit', type=int, default=20, help='限制結果數量 (預設: 20)')
    
    # stats命令
    stats_parser = subparsers.add_parser('stats', help='顯示欄位統計資訊')
    stats_parser.add_argument('column', help='欄位名稱')
    
    # sql命令
    sql_parser = subparsers.add_parser('sql', help='執行自定義SQL查詢')
    sql_parser.add_argument('query', help='SQL查詢語句')
    
    # export命令
    export_parser = subparsers.add_parser('export', help='匯出資料')
    export_parser.add_argument('output', help='輸出檔案路徑')
    export_parser.add_argument('--query', help='自定義查詢 (可選)')
    export_parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='輸出格式 (預設: csv)')
    
    args = parser.parse_args()
    
    # 檢查依賴
    try:
        import duckdb
        import tabulate
        import pandas
    except ImportError as e:
        print(f"❌ 缺少必要套件: {e}")
        print("請執行: pip install duckdb tabulate pandas")
        sys.exit(1)
    
    # 如果沒有指定命令，顯示幫助
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 初始化CLI工具
    cli = DuckDBQueryCLI(args.db_path)
    
    if not cli.connect():
        sys.exit(1)
    
    try:
        # 執行對應命令
        if args.command == 'info':
            cli.show_info()
            
        elif args.command == 'schema':
            cli.show_schema(args.table)
            
        elif args.command == 'list':
            cli.list_records(
                table_name=args.table,
                limit=args.limit,
                offset=args.offset,
                columns=args.columns
            )
            
        elif args.command == 'show':
            cli.show_model(args.model, args.table)
            
        elif args.command == 'search':
            cli.search_records(args.keyword, args.table, args.limit)
            
        elif args.command == 'stats':
            cli.get_column_stats(args.column, args.table)
            
        elif args.command == 'sql':
            cli.execute_sql(args.query)
            
        elif args.command == 'export':
            cli.export_data(
                output_file=args.output,
                query=args.query,
                table_name=args.table,
                format=args.format
            )
    
    finally:
        cli.close()


if __name__ == '__main__':
    main()