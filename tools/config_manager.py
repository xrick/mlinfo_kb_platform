#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Manager CLI
統一管理sales assistant配置檔案的命令列工具
"""

import os
import sys
import json
import argparse
from pathlib import Path
from tabulate import tabulate
from typing import Dict, Any, List
import subprocess

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 設定檔路徑
ENTITY_PATTERNS_PATH = project_root / "libs/services/sales_assistant/prompts/entity_patterns.json"
QUERY_KEYWORDS_PATH = project_root / "libs/services/sales_assistant/prompts/query_keywords.json"
BACKUP_DIR = project_root / "tools/backups"

class ConfigManager:
    """統一配置管理器"""
    
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(exist_ok=True)
        
        self.config_files = {
            'entity_patterns': ENTITY_PATTERNS_PATH,
            'query_keywords': QUERY_KEYWORDS_PATH
        }
    
    def _load_config(self, config_type: str) -> Dict[str, Any]:
        """載入指定類型的配置"""
        if config_type not in self.config_files:
            return {}
        
        try:
            with open(self.config_files[config_type], 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 載入 {config_type} 配置失敗: {e}")
            return {}
    
    def status(self):
        """顯示配置檔案狀態"""
        print("🔍 Sales Assistant 配置檔案狀態:\n")
        
        table_data = []
        for config_name, config_path in self.config_files.items():
            if config_path.exists():
                try:
                    data = self._load_config(config_name)
                    size = config_path.stat().st_size
                    
                    if config_name == 'entity_patterns':
                        entity_count = len(data.get('entity_patterns', {}))
                        status = f"✅ {entity_count} 個實體類型"
                    elif config_name == 'query_keywords':
                        intent_count = len(data.get('intent_keywords', {}))
                        status = f"✅ {intent_count} 個意圖"
                    else:
                        status = "✅ 存在"
                    
                    table_data.append([
                        config_name,
                        str(config_path),
                        f"{size} bytes",
                        status
                    ])
                except Exception as e:
                    table_data.append([
                        config_name,
                        str(config_path),
                        "錯誤",
                        f"❌ {str(e)[:50]}..."
                    ])
            else:
                table_data.append([
                    config_name,
                    str(config_path),
                    "不存在",
                    "❌ 檔案不存在"
                ])
        
        headers = ['配置類型', '檔案路徑', '大小', '狀態']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def sync_modeltypes(self):
        """同步數據庫中的modeltype到配置檔案"""
        print("🔄 同步數據庫中的modeltype到配置檔案...")
        
        try:
            # 從數據庫獲取modeltype
            from config import DB_PATH
            import duckdb
            
            conn = duckdb.connect(str(DB_PATH))
            result = conn.execute('SELECT DISTINCT modeltype FROM specs ORDER BY modeltype').fetchall()
            conn.close()
            
            modeltypes = [row[0] for row in result]
            print(f"📋 從數據庫獲取到的modeltype: {modeltypes}")
            
            # 更新entity_patterns.json
            entity_data = self._load_config('entity_patterns')
            if 'entity_patterns' in entity_data and 'MODEL_TYPE' in entity_data['entity_patterns']:
                # 構建新的pattern
                pattern = f"\\\\b(?:{'|'.join(modeltypes)})\\\\b"
                entity_data['entity_patterns']['MODEL_TYPE']['patterns'] = [pattern]
                entity_data['entity_patterns']['MODEL_TYPE']['examples'] = modeltypes
                
                # 儲存更新
                self._create_backup('entity_patterns')
                with open(ENTITY_PATTERNS_PATH, 'w', encoding='utf-8') as f:
                    json.dump(entity_data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 已更新 entity_patterns.json 中的 MODEL_TYPE 模式")
                print(f"🎯 新模式: {pattern}")
            
            return True
            
        except Exception as e:
            print(f"❌ 同步失敗: {e}")
            return False
    
    def validate_all(self):
        """驗證所有配置檔案"""
        print("🔍 驗證所有配置檔案...\n")
        
        all_valid = True
        
        # 驗證entity_patterns
        print("1. 驗證 entity_patterns.json:")
        result = subprocess.run([
            sys.executable, 
            str(project_root / "tools/entity_manager.py"), 
            "validate"
        ], capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ entity_patterns.json 驗證通過")
        else:
            print("❌ entity_patterns.json 驗證失敗")
            print(result.stdout)
            all_valid = False
        
        print()
        
        # 驗證query_keywords
        print("2. 驗證 query_keywords.json:")
        result = subprocess.run([
            sys.executable, 
            str(project_root / "tools/keywords_manager.py"), 
            "validate"
        ], capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ query_keywords.json 驗證通過")
        else:
            print("❌ query_keywords.json 驗證失敗")
            print(result.stdout)
            all_valid = False
        
        print()
        
        if all_valid:
            print("🎉 所有配置檔案驗證通過！")
        else:
            print("⚠️  部分配置檔案存在問題，請檢查上述錯誤訊息")
        
        return all_valid
    
    def backup_all(self):
        """備份所有配置檔案"""
        print("📋 備份所有配置檔案...")
        
        for config_name in self.config_files.keys():
            self._create_backup(config_name)
        
        print("✅ 備份完成")
    
    def _create_backup(self, config_type: str):
        """建立備份檔案"""
        if config_type not in self.config_files:
            print(f"❌ 未知配置類型: {config_type}")
            return
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{config_type}_{timestamp}.json"
        
        try:
            import shutil
            shutil.copy2(self.config_files[config_type], backup_file)
            print(f"📋 已建立備份: {backup_file}")
        except Exception as e:
            print(f"⚠️  建立 {config_type} 備份失敗: {e}")
    
    def list_backups(self):
        """列出所有備份檔案"""
        if not self.backup_dir.exists():
            print("❌ 備份目錄不存在")
            return
        
        backup_files = list(self.backup_dir.glob("*.json"))
        if not backup_files:
            print("📂 沒有找到備份檔案")
            return
        
        # 按修改時間排序
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        table_data = []
        for backup_file in backup_files:
            stat = backup_file.stat()
            from datetime import datetime
            mtime = datetime.fromtimestamp(stat.st_mtime)
            
            table_data.append([
                backup_file.name,
                f"{stat.st_size} bytes",
                mtime.strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        headers = ['備份檔案', '大小', '建立時間']
        print("\n📋 備份檔案列表:")
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def restore_backup(self, backup_file: str):
        """從備份檔案還原配置"""
        backup_path = self.backup_dir / backup_file
        if not backup_path.exists():
            print(f"❌ 備份檔案不存在: {backup_file}")
            return False
        
        # 判斷配置類型
        config_type = None
        for ct in self.config_files.keys():
            if backup_file.startswith(ct):
                config_type = ct
                break
        
        if not config_type:
            print(f"❌ 無法識別備份檔案類型: {backup_file}")
            return False
        
        try:
            # 建立當前配置的備份
            self._create_backup(config_type)
            
            # 還原備份
            import shutil
            shutil.copy2(backup_path, self.config_files[config_type])
            print(f"✅ 已從 {backup_file} 還原 {config_type} 配置")
            return True
            
        except Exception as e:
            print(f"❌ 還原失敗: {e}")
            return False
    
    def summary(self):
        """顯示配置摘要"""
        print("📊 Sales Assistant 配置摘要:\n")
        
        # Entity Patterns 摘要
        entity_data = self._load_config('entity_patterns')
        entity_patterns = entity_data.get('entity_patterns', {})
        
        print("🎯 實體模式 (Entity Patterns):")
        for entity_type, config in entity_patterns.items():
            pattern_count = len(config.get('patterns', []))
            example_count = len(config.get('examples', []))
            print(f"  • {entity_type}: {pattern_count} 個模式, {example_count} 個範例")
        
        print()
        
        # Query Keywords 摘要
        keywords_data = self._load_config('query_keywords')
        intent_keywords = keywords_data.get('intent_keywords', {})
        
        print("🔍 查詢關鍵字 (Query Keywords):")
        total_keywords = 0
        for intent_name, config in intent_keywords.items():
            keyword_count = len(config.get('keywords', []))
            total_keywords += keyword_count
            print(f"  • {intent_name}: {keyword_count} 個關鍵字")
        
        print(f"\n📈 總計: {len(entity_patterns)} 個實體類型, {len(intent_keywords)} 個意圖, {total_keywords} 個關鍵字")
    
    def export_config(self, format: str = 'json'):
        """匯出完整配置"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            export_data = {}
            for config_name in self.config_files.keys():
                export_data[config_name] = self._load_config(config_name)
            
            filename = f"sales_assistant_config_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 已匯出完整配置到 {filename}")
        
        elif format == 'summary':
            filename = f"config_summary_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                # 重定向stdout到檔案
                import io
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                
                self.summary()
                
                sys.stdout = old_stdout
                f.write(buffer.getvalue())
            
            print(f"✅ 已匯出配置摘要到 {filename}")

def main():
    parser = argparse.ArgumentParser(description='Sales Assistant 配置管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # status 命令
    subparsers.add_parser('status', help='顯示配置檔案狀態')
    
    # sync 命令
    subparsers.add_parser('sync', help='同步數據庫中的modeltype到配置檔案')
    
    # validate 命令
    subparsers.add_parser('validate', help='驗證所有配置檔案')
    
    # backup 命令
    subparsers.add_parser('backup', help='備份所有配置檔案')
    
    # list-backups 命令
    subparsers.add_parser('list-backups', help='列出所有備份檔案')
    
    # restore 命令
    restore_parser = subparsers.add_parser('restore', help='從備份還原配置')
    restore_parser.add_argument('backup_file', help='備份檔案名稱')
    
    # summary 命令
    subparsers.add_parser('summary', help='顯示配置摘要')
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='匯出配置')
    export_parser.add_argument('--format', choices=['json', 'summary'], default='json', help='匯出格式')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = ConfigManager()
    
    if args.command == 'status':
        manager.status()
    
    elif args.command == 'sync':
        manager.sync_modeltypes()
    
    elif args.command == 'validate':
        manager.validate_all()
    
    elif args.command == 'backup':
        manager.backup_all()
    
    elif args.command == 'list-backups':
        manager.list_backups()
    
    elif args.command == 'restore':
        manager.restore_backup(args.backup_file)
    
    elif args.command == 'summary':
        manager.summary()
    
    elif args.command == 'export':
        manager.export_config(args.format)

if __name__ == '__main__':
    main()