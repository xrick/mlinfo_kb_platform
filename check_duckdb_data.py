#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 semantic_sales_spec.db 資料庫中的所有資料
"""

import duckdb
import pandas as pd
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 資料庫檔案路徑
DB_FILE = "db/semantic_sales_spec.db"

def connect_to_duckdb():
    """連接到 DuckDB 資料庫"""
    try:
        logger.info(f"嘗試連接到 DuckDB: {DB_FILE}")
        con = duckdb.connect(database=DB_FILE, read_only=True)
        logger.info("✅ 成功連接到 DuckDB")
        return con
    except Exception as e:
        logger.error(f"❌ 連接 DuckDB 失敗: {e}")
        return None

def list_all_tables(con):
    """列出所有表格"""
    try:
        tables = con.execute("SHOW TABLES").fetchall()
        logger.info(f"資料庫中的所有表格: {[table[0] for table in tables]}")
        return [table[0] for table in tables]
    except Exception as e:
        logger.error(f"列出表格時發生錯誤: {e}")
        return []

def get_table_info(con, table_name):
    """獲取表格資訊"""
    try:
        # 獲取表格結構
        schema = con.execute(f"DESCRIBE {table_name}").fetchall()
        logger.info(f"表格 '{table_name}' 的結構:")
        for col in schema:
            logger.info(f"  - {col[0]}: {col[1]}")
        
        # 獲取記錄數量
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        logger.info(f"表格 '{table_name}' 的記錄數量: {count}")
        
        return schema, count
    except Exception as e:
        logger.error(f"獲取表格 '{table_name}' 資訊時發生錯誤: {e}")
        return None, 0

def show_table_data(con, table_name, limit=10):
    """顯示表格資料（限制顯示數量）"""
    try:
        # 獲取前幾筆資料
        data = con.execute(f"SELECT * FROM {table_name} LIMIT {limit}").fetchdf()
        logger.info(f"表格 '{table_name}' 的前 {limit} 筆資料:")
        print(f"\n=== {table_name} 表格資料 ===")
        print(data.to_string(index=False))
        
        # 獲取總記錄數
        total_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        logger.info(f"表格 '{table_name}' 總共有 {total_count} 筆記錄")
        
        return data, total_count
    except Exception as e:
        logger.error(f"顯示表格 '{table_name}' 資料時發生錯誤: {e}")
        return None, 0

def show_table_sample(con, table_name, sample_size=5):
    """顯示表格的隨機樣本"""
    try:
        data = con.execute(f"SELECT * FROM {table_name} ORDER BY RANDOM() LIMIT {sample_size}").fetchdf()
        logger.info(f"表格 '{table_name}' 的隨機樣本 ({sample_size} 筆):")
        print(f"\n=== {table_name} 隨機樣本 ===")
        print(data.to_string(index=False))
        return data
    except Exception as e:
        logger.error(f"獲取表格 '{table_name}' 樣本時發生錯誤: {e}")
        return None

def main():
    """主函數"""
    logger.info("=== 檢查 semantic_sales_spec.db 資料庫 ===")
    
    # 連接到資料庫
    con = connect_to_duckdb()
    if not con:
        return
    
    try:
        # 列出所有表格
        logger.info("--- 列出所有表格 ---")
        tables = list_all_tables(con)
        
        if not tables:
            logger.warning("資料庫中沒有表格")
            return
        
        # 檢查每個表格
        for table_name in tables:
            logger.info(f"\n--- 檢查表格: {table_name} ---")
            
            # 獲取表格資訊
            schema, count = get_table_info(con, table_name)
            
            if count > 0:
                # 顯示表格資料（如果記錄數少於20，顯示全部；否則顯示前10筆）
                if count <= 20:
                    show_table_data(con, table_name, limit=count)
                else:
                    show_table_data(con, table_name, limit=10)
                    # 額外顯示一些隨機樣本
                    show_table_sample(con, table_name, sample_size=5)
            else:
                logger.info(f"表格 '{table_name}' 沒有資料")
        
        # 總結
        logger.info("\n=== 檢查結果總結 ===")
        total_tables = len(tables)
        logger.info(f"資料庫中共有 {total_tables} 個表格")
        for table_name in tables:
            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            logger.info(f"  - {table_name}: {count} 筆記錄")
            
    except Exception as e:
        logger.error(f"檢查資料庫時發生錯誤: {e}")
    finally:
        # 關閉連接
        con.close()
        logger.info("已關閉 DuckDB 連接")

if __name__ == "__main__":
    main()
