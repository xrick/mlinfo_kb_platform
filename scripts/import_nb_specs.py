#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
筆電規格資料匯入腳本
將 data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet 中的所有CSV檔案
匯入到 nb_spec_0250821v1.db 資料庫中
"""

import os
import sqlite3
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/nb_spec_import.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NotebookSpecImporter:
    def __init__(self, csv_dir: str, db_path: str):
        self.csv_dir = Path(csv_dir)
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def create_database(self):
        """建立資料庫和資料表"""
        try:
            # 確保logs目錄存在
            os.makedirs('logs', exist_ok=True)
            
            # 建立資料庫連接
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # 建立主要規格資料表
            self.cursor.execute('''
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
            self.cursor.execute('''
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
            
            # 建立索引以提升查詢效能
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_modeltype ON notebook_specs(modeltype)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_version ON notebook_specs(version)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_modelname ON notebook_specs(modelname)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_file ON notebook_specs(source_file)')
            
            self.conn.commit()
            logger.info(f"資料庫 {self.db_path} 建立成功")
            
        except Exception as e:
            logger.error(f"建立資料庫失敗: {e}")
            raise
    
    def calculate_content_hash(self, row_data: Dict[str, Any]) -> str:
        """計算資料列的內容雜湊值，用於去重"""
        # 移除不需要的欄位
        exclude_fields = {'id', 'source_file', 'import_timestamp', 'content_hash'}
        content_str = '|'.join([
            str(row_data.get(k, '')) 
            for k in sorted(row_data.keys()) 
            if k not in exclude_fields
        ])
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()
    
    def clean_data(self, value: str) -> str:
        """清理資料值"""
        if value is None:
            return ''
        # 移除BOM字元和多餘的空白和換行
        cleaned = str(value).strip().replace('\ufeff', '').replace('\n', ' ').replace('\r', ' ')
        # 將多個空白合併為單一空白
        cleaned = ' '.join(cleaned.split())
        return cleaned
    
    def import_csv_file(self, csv_file: Path) -> Dict[str, Any]:
        """匯入單一CSV檔案"""
        result = {
            'filename': csv_file.name,
            'total_rows': 0,
            'imported_rows': 0,
            'skipped_rows': 0,
            'error_rows': 0,
            'status': 'success',
            'error_message': None
        }
        
        try:
            logger.info(f"開始處理檔案: {csv_file.name}")
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, 1):
                    result['total_rows'] += 1
                    
                    try:
                        # 清理資料
                        cleaned_row = {k: self.clean_data(v) for k, v in row.items()}
                        
                        # 計算內容雜湊值
                        content_hash = self.calculate_content_hash(cleaned_row)
                        
                        # 檢查是否已存在相同內容的記錄
                        self.cursor.execute('''
                            SELECT id FROM notebook_specs 
                            WHERE modeltype = ? AND version = ? AND modelname = ? AND content_hash = ?
                        ''', (
                            cleaned_row.get('modeltype', ''),
                            cleaned_row.get('version', ''),
                            cleaned_row.get('modelname', ''),
                            content_hash
                        ))
                        
                        if self.cursor.fetchone():
                            result['skipped_rows'] += 1
                            continue
                        
                        # 插入新記錄
                        self.cursor.execute('''
                            INSERT INTO notebook_specs (
                                modeltype, version, modelname, mainboard, devtime, pm,
                                structconfig, lcd, touchpanel, iointerface, ledind,
                                powerbutton, keyboard, webcamera, touchpad, fingerprint,
                                audio, battery, cpu, gpu, memory, lcdconnector,
                                storage, wifislot, thermal, tpm, rtc, wireless,
                                lan, lte, bluetooth, softwareconfig, ai, accessory,
                                certifications, source_file, content_hash
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            cleaned_row.get('modeltype', ''),
                            cleaned_row.get('version', ''),
                            cleaned_row.get('modelname', ''),
                            cleaned_row.get('mainboard', ''),
                            cleaned_row.get('devtime', ''),
                            cleaned_row.get('pm', ''),
                            cleaned_row.get('structconfig', ''),
                            cleaned_row.get('lcd', ''),
                            cleaned_row.get('touchpanel', ''),
                            cleaned_row.get('iointerface', ''),
                            cleaned_row.get('ledind', ''),
                            cleaned_row.get('powerbutton', ''),
                            cleaned_row.get('keyboard', ''),
                            cleaned_row.get('webcamera', ''),
                            cleaned_row.get('touchpad', ''),
                            cleaned_row.get('fingerprint', ''),
                            cleaned_row.get('audio', ''),
                            cleaned_row.get('battery', ''),
                            cleaned_row.get('cpu', ''),
                            cleaned_row.get('gpu', ''),
                            cleaned_row.get('memory', ''),
                            cleaned_row.get('lcdconnector', ''),
                            cleaned_row.get('storage', ''),
                            cleaned_row.get('wifislot', ''),
                            cleaned_row.get('thermal', ''),
                            cleaned_row.get('tpm', ''),
                            cleaned_row.get('rtc', ''),
                            cleaned_row.get('wireless', ''),
                            cleaned_row.get('lan', ''),
                            cleaned_row.get('lte', ''),
                            cleaned_row.get('bluetooth', ''),
                            cleaned_row.get('softwareconfig', ''),
                            cleaned_row.get('ai', ''),
                            cleaned_row.get('accessory', ''),
                            cleaned_row.get('certifications', ''),
                            csv_file.name,
                            content_hash
                        ))
                        
                        result['imported_rows'] += 1
                        
                        # 每100筆提交一次
                        if result['imported_rows'] % 100 == 0:
                            self.conn.commit()
                            logger.info(f"{csv_file.name}: 已處理 {result['imported_rows']} 筆資料")
                    
                    except Exception as e:
                        result['error_rows'] += 1
                        logger.error(f"處理第 {row_num} 行時發生錯誤: {e}")
                        continue
                
                # 最終提交
                self.conn.commit()
                
                # 記錄匯入結果
                self.cursor.execute('''
                    INSERT INTO import_logs (
                        filename, total_rows, imported_rows, skipped_rows, 
                        error_rows, status, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result['filename'], result['total_rows'], result['imported_rows'],
                    result['skipped_rows'], result['error_rows'], result['status'],
                    result['error_message']
                ))
                self.conn.commit()
                
                logger.info(f"檔案 {csv_file.name} 處理完成: "
                          f"總計 {result['total_rows']} 行, "
                          f"匯入 {result['imported_rows']} 行, "
                          f"跳過 {result['skipped_rows']} 行, "
                          f"錯誤 {result['error_rows']} 行")
                
        except Exception as e:
            result['status'] = 'error'
            result['error_message'] = str(e)
            logger.error(f"處理檔案 {csv_file.name} 時發生錯誤: {e}")
            
            # 記錄錯誤到資料庫
            self.cursor.execute('''
                INSERT INTO import_logs (
                    filename, total_rows, imported_rows, skipped_rows, 
                    error_rows, status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['filename'], result['total_rows'], result['imported_rows'],
                result['skipped_rows'], result['error_rows'], result['status'],
                result['error_message']
            ))
            self.conn.commit()
        
        return result
    
    def import_all_csv_files(self) -> List[Dict[str, Any]]:
        """匯入所有CSV檔案"""
        csv_files = list(self.csv_dir.glob('*.csv'))
        csv_files.sort()  # 按檔名排序
        
        if not csv_files:
            logger.warning(f"在目錄 {self.csv_dir} 中未找到CSV檔案")
            return []
        
        logger.info(f"找到 {len(csv_files)} 個CSV檔案")
        
        results = []
        total_imported = 0
        total_skipped = 0
        total_errors = 0
        
        for i, csv_file in enumerate(csv_files, 1):
            logger.info(f"處理進度: {i}/{len(csv_files)} - {csv_file.name}")
            
            result = self.import_csv_file(csv_file)
            results.append(result)
            
            total_imported += result['imported_rows']
            total_skipped += result['skipped_rows']
            total_errors += result['error_rows']
            
            # 顯示進度
            progress = (i / len(csv_files)) * 100
            logger.info(f"整體進度: {progress:.1f}%")
        
        # 顯示總計結果
        logger.info("=" * 60)
        logger.info("匯入完成！總計結果:")
        logger.info(f"處理檔案數: {len(csv_files)}")
        logger.info(f"總匯入筆數: {total_imported}")
        logger.info(f"總跳過筆數: {total_skipped}")
        logger.info(f"總錯誤筆數: {total_errors}")
        logger.info("=" * 60)
        
        return results
    
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
            
            # 匯入記錄
            self.cursor.execute('SELECT * FROM import_logs ORDER BY import_timestamp DESC LIMIT 10')
            recent_imports = self.cursor.fetchall()
            
            return {
                'total_records': total_records,
                'modeltype_counts': modeltype_counts,
                'recent_imports': recent_imports
            }
            
        except Exception as e:
            logger.error(f"取得資料庫統計資訊失敗: {e}")
            return {}
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            logger.info("資料庫連接已關閉")

def main():
    """主函數"""
    # 設定路徑
    csv_directory = "data/raw/EM_New TTL_241104_AllTransformedToGoogleSheet"
    database_path = "db/nb_spec_0250821v1.db"
    
    # 檢查CSV目錄是否存在
    if not os.path.exists(csv_directory):
        logger.error(f"CSV目錄不存在: {csv_directory}")
        return
    
    importer = None
    try:
        # 建立匯入器
        importer = NotebookSpecImporter(csv_directory, database_path)
        
        # 建立資料庫
        importer.create_database()
        
        # 匯入所有CSV檔案
        results = importer.import_all_csv_files()
        
        # 顯示統計資訊
        stats = importer.get_database_stats()
        if stats:
            logger.info("資料庫統計資訊:")
            logger.info(f"總記錄數: {stats['total_records']}")
            logger.info("各型號記錄數:")
            for modeltype, count in stats['modeltype_counts'].items():
                logger.info(f"  {modeltype}: {count} 筆")
        
        logger.info("匯入作業完成！")
        
    except Exception as e:
        logger.error(f"匯入作業失敗: {e}")
        raise
    
    finally:
        if importer:
            importer.close()

if __name__ == "__main__":
    main()
