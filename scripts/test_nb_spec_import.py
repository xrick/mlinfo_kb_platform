#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試筆電規格資料匯入功能
"""

import sqlite3
import os
from pathlib import Path

def test_database_creation():
    """測試資料庫建立"""
    db_path = "db/nb_spec_0250821v1.db"
    
    # 如果資料庫已存在，先刪除
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"已刪除舊的資料庫: {db_path}")
    
    try:
        # 建立資料庫連接
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 建立主要規格資料表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notebook_specs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modeltype TEXT NOT NULL,
                version TEXT,
                modelname TEXT,
                mainboard TEXT,
                devtime TEXT,
                pm TEXT,
                structconfig TEXT,
                lcd TEXT,
                touchpanel TEXT,
                iointerface TEXT,
                ledind TEXT,
                powerbutton TEXT,
                keyboard TEXT,
                webcamera TEXT,
                touchpad TEXT,
                fingerprint TEXT,
                audio TEXT,
                battery TEXT,
                cpu TEXT,
                gpu TEXT,
                memory TEXT,
                lcdconnector TEXT,
                storage TEXT,
                wifislot TEXT,
                thermal TEXT,
                tpm TEXT,
                rtc TEXT,
                wireless TEXT,
                lan TEXT,
                lte TEXT,
                bluetooth TEXT,
                softwareconfig TEXT,
                ai TEXT,
                accessory TEXT,
                certifications TEXT,
                source_file TEXT NOT NULL,
                import_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                content_hash TEXT,
                UNIQUE(modeltype, version, modelname, content_hash)
            )
        ''')
        
        # 建立匯入記錄表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS import_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                total_rows INTEGER DEFAULT 0,
                imported_rows INTEGER DEFAULT 0,
                skipped_rows INTEGER DEFAULT 0,
                error_rows INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                error_message TEXT,
                import_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 建立索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_modeltype ON notebook_specs(modeltype)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_version ON notebook_specs(version)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_modelname ON notebook_specs(modelname)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_file ON notebook_specs(source_file)')
        
        conn.commit()
        print(f"✅ 資料庫 {db_path} 建立成功")
        
        # 檢查資料表結構
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 建立的資料表: {[table[0] for table in tables]}")
        
        # 檢查欄位
        cursor.execute("PRAGMA table_info(notebook_specs)")
        columns = cursor.fetchall()
        print(f"📊 notebook_specs 欄位數: {len(columns)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 建立資料庫失敗: {e}")
        return False

def test_csv_files_exist():
    """測試CSV檔案是否存在"""
    csv_dir = Path("data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet")
    
    if not csv_dir.exists():
        print(f"❌ CSV目錄不存在: {csv_dir}")
        return False
    
    csv_files = list(csv_dir.glob('*.csv'))
    if not csv_files:
        print(f"❌ 在目錄 {csv_dir} 中未找到CSV檔案")
        return False
    
    print(f"✅ 找到 {len(csv_files)} 個CSV檔案:")
    for csv_file in csv_files:
        print(f"  📄 {csv_file.name}")
    
    return True

def test_sample_csv_reading():
    """測試讀取樣本CSV檔案"""
    csv_dir = Path("data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet")
    csv_files = list(csv_dir.glob('*.csv'))
    
    if not csv_files:
        print("❌ 沒有CSV檔案可測試")
        return False
    
    # 測試第一個CSV檔案
    sample_file = csv_files[0]
    print(f"📖 測試讀取檔案: {sample_file.name}")
    
    try:
        import csv
        with open(sample_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            print(f"✅ CSV標題欄位: {len(headers)} 個")
            print(f"📋 欄位名稱: {headers}")
            
            # 讀取前3行資料
            rows = []
            for i, row in enumerate(reader):
                if i < 3:
                    rows.append(row)
                else:
                    break
            
            print(f"📊 前3行資料:")
            for i, row in enumerate(rows):
                print(f"  第{i+1}行: modeltype={row.get('modeltype', 'N/A')}, "
                      f"version={row.get('version', 'N/A')[:30]}...")
            
            return True
            
    except Exception as e:
        print(f"❌ 讀取CSV檔案失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🧪 開始測試筆電規格資料匯入功能")
    print("=" * 60)
    
    # 測試1: 檢查CSV檔案
    print("\n1️⃣ 測試CSV檔案存在性")
    if not test_csv_files_exist():
        print("❌ CSV檔案測試失敗，無法繼續")
        return
    
    # 測試2: 建立資料庫
    print("\n2️⃣ 測試資料庫建立")
    if not test_database_creation():
        print("❌ 資料庫建立測試失敗，無法繼續")
        return
    
    # 測試3: 讀取樣本CSV
    print("\n3️⃣ 測試CSV檔案讀取")
    if not test_sample_csv_reading():
        print("❌ CSV讀取測試失敗")
        return
    
    print("\n" + "=" * 60)
    print("🎉 所有測試通過！可以執行匯入腳本了")
    print("\n💡 執行匯入腳本:")
    print("   python scripts/import_nb_specs.py")

if __name__ == "__main__":
    main()

