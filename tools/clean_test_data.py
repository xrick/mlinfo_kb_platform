#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理測試資料工具
處理資料庫中的測試資料和格式不一致問題
"""

import sys
import duckdb
from pathlib import Path
from datetime import datetime

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import DB_PATH

def backup_database():
    """備份資料庫"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = project_root / "tools/backups" / f"sales_specs_backup_{timestamp}.db"
    backup_path.parent.mkdir(exist_ok=True)
    
    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ 資料庫已備份到: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ 備份失敗: {e}")
        return False

def analyze_data_issues():
    """分析資料品質問題"""
    conn = duckdb.connect(str(DB_PATH))
    try:
        print("🔍 分析資料品質問題...\n")
        
        # 1. 檢查測試資料
        print("1. 測試資料:")
        test_data = conn.execute("""
            SELECT modeltype, modelname, COUNT(*) as count
            FROM specs 
            WHERE modelname = 'Test Model' OR modelname LIKE '%test%' OR modelname LIKE '%Test%'
            GROUP BY modeltype, modelname
            ORDER BY modeltype, modelname
        """).fetchall()
        
        if test_data:
            for row in test_data:
                print(f"   {row[0]} | {row[1]} | {row[2]} 筆")
        else:
            print("   無測試資料")
        
        # 2. 檢查空值或異常值
        print("\n2. 空值或異常值:")
        null_data = conn.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN modelname IS NULL OR modelname = '' THEN 1 END) as null_modelname,
                COUNT(CASE WHEN modeltype IS NULL OR modeltype = '' THEN 1 END) as null_modeltype
            FROM specs
        """).fetchall()[0]
        
        print(f"   總記錄數: {null_data[0]}")
        print(f"   modelname空值: {null_data[1]}")
        print(f"   modeltype空值: {null_data[2]}")
        
        # 3. 檢查格式不一致
        print("\n3. modelname格式分析:")
        format_analysis = conn.execute("""
            SELECT 
                CASE 
                    WHEN modelname LIKE 'Model Name: %' THEN 'Model Name: 前綴'
                    WHEN modelname LIKE '%: %' THEN '包含冒號'
                    WHEN modelname = 'Test Model' THEN '測試資料'
                    ELSE '正常格式'
                END as format_type,
                COUNT(*) as count
            FROM specs 
            GROUP BY 1
            ORDER BY count DESC
        """).fetchall()
        
        for row in format_analysis:
            print(f"   {row[0]}: {row[1]} 筆")
        
        # 4. 檢查重複的modeltype下是否有不同格式
        print("\n4. 各系列的modelname格式:")
        series_analysis = conn.execute("""
            SELECT modeltype, modelname
            FROM specs 
            ORDER BY modeltype, modelname
        """).fetchall()
        
        current_type = None
        for row in series_analysis:
            if row[0] != current_type:
                current_type = row[0]
                print(f"   {current_type}:")
            print(f"     - {row[1]}")
            
    finally:
        conn.close()

def clean_test_data():
    """清理測試資料"""
    conn = duckdb.connect(str(DB_PATH))
    try:
        print("\n🧹 清理測試資料...")
        
        # 先查看要刪除的記錄數
        count_before = conn.execute("""
            SELECT COUNT(*) FROM specs 
            WHERE modelname = 'Test Model'
        """).fetchall()[0][0]
        
        if count_before > 0:
            # 刪除明顯的測試資料
            conn.execute("""
                DELETE FROM specs 
                WHERE modelname = 'Test Model'
            """)
            
            print(f"✅ 已刪除 {count_before} 筆測試資料")
        else:
            print("未發現需要刪除的測試資料")
        
    except Exception as e:
        print(f"❌ 清理失敗: {e}")
    finally:
        conn.close()

def normalize_modelname_format():
    """統一modelname格式，移除Model Name:前綴"""
    conn = duckdb.connect(str(DB_PATH))
    try:
        print("\n🔧 統一modelname格式...")
        
        # 查看需要處理的記錄
        to_update = conn.execute("""
            SELECT modelname FROM specs 
            WHERE modelname LIKE 'Model Name: %'
        """).fetchall()
        
        if to_update:
            print(f"發現 {len(to_update)} 筆需要更新格式的記錄")
            
            # DuckDB使用REPLACE函數替代REGEXP_REPLACE
            conn.execute("""
                UPDATE specs 
                SET modelname = REPLACE(modelname, 'Model Name: ', '')
                WHERE modelname LIKE 'Model Name: %'
            """)
            
            print(f"✅ 已更新 {len(to_update)} 筆記錄的格式")
        else:
            print("未發現需要格式化的記錄")
        
    except Exception as e:
        print(f"❌ 格式化失敗: {e}")
    finally:
        conn.close()

def verify_cleanup():
    """驗證清理結果"""
    conn = duckdb.connect(str(DB_PATH))
    try:
        print("\n✅ 驗證清理結果...")
        
        # 檢查各系列的記錄數
        series_count = conn.execute("""
            SELECT modeltype, COUNT(*) as count, 
                   GROUP_CONCAT(DISTINCT modelname, ', ') as models
            FROM specs 
            GROUP BY modeltype 
            ORDER BY modeltype
        """).fetchall()
        
        print("各系列記錄統計:")
        for row in series_count:
            print(f"  {row[0]}: {row[1]} 筆 -> {row[2]}")
        
        # 檢查是否還有測試資料
        test_remaining = conn.execute("""
            SELECT COUNT(*) FROM specs 
            WHERE modelname = 'Test Model' OR modelname LIKE '%test%'
        """).fetchall()[0][0]
        
        if test_remaining == 0:
            print("✅ 所有測試資料已清理完成")
        else:
            print(f"⚠️  仍有 {test_remaining} 筆測試資料")
            
    finally:
        conn.close()

def main():
    print("🔧 資料庫清理工具")
    print("=" * 50)
    
    # 1. 備份資料庫
    if not backup_database():
        print("❌ 備份失敗，終止清理作業")
        return
    
    # 2. 分析資料問題
    analyze_data_issues()
    
    # 3. 詢問是否繼續清理
    print("\n" + "=" * 50)
    response = input("是否繼續清理資料？(y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        # 4. 清理測試資料
        clean_test_data()
        
        # 5. 統一格式
        normalize_modelname_format()
        
        # 6. 驗證結果
        verify_cleanup()
        
        print("\n🎉 資料清理完成！")
    else:
        print("❌ 清理作業已取消")

if __name__ == '__main__':
    main()