# tools/keywords_manager.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Keywords Manager CLI
管理 query_keywords.json 設定檔的命令列工具
"""

import os
import sys
import json
import argparse
from pathlib import Path
from tabulate import tabulate
from typing import Dict, Any, List

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 設定檔路徑
QUERY_KEYWORDS_PATH = project_root / "libs/services/sales_assistant/prompts/query_keywords.json"
BACKUP_DIR = project_root / "tools/backups"

class QueryKeywordsManager:
    """查詢關鍵字管理器"""
    
    def __init__(self):
        self.keywords_path = QUERY_KEYWORDS_PATH
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(exist_ok=True)
        self.keywords = self._load_keywords()
    
    def _load_keywords(self) -> Dict[str, Any]:
        """載入查詢關鍵字設定"""
        try:
            with open(self.keywords_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('intent_keywords', {})
        except Exception as e:
            print(f"❌ 載入設定檔失敗: {e}")
            return {}
    
    def _save_keywords(self, backup: bool = True) -> bool:
        """儲存查詢關鍵字設定"""
        try:
            if backup:
                self._create_backup()
            
            data = {"intent_keywords": self.keywords}
            with open(self.keywords_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 儲存設定檔失敗: {e}")
            return False
    
    def _create_backup(self):
        """建立備份檔案"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"query_keywords_{timestamp}.json"
        
        try:
            import shutil
            shutil.copy2(self.keywords_path, backup_file)
            print(f"📋 已建立備份: {backup_file}")
        except Exception as e:
            print(f"⚠️  建立備份失敗: {e}")
    
    def list_intents(self):
        """列出所有意圖類型"""
        if not self.keywords:
            print("❌ 沒有找到查詢關鍵字設定")
            return
        
        table_data = []
        for intent_name, config in self.keywords.items():
            keywords = config.get('keywords', [])
            description = config.get('description', '')
            
            table_data.append([
                intent_name,
                description,
                len(keywords),
                ', '.join(keywords[:5]) + ('...' if len(keywords) > 5 else '')
            ])
        
        headers = ['意圖名稱', '描述', '關鍵字數量', '關鍵字預覽']
        print("\n📋 查詢意圖列表:")
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def show_intent(self, intent_name: str):
        """顯示特定意圖的詳細資訊"""
        if intent_name not in self.keywords:
            print(f"❌ 意圖 '{intent_name}' 不存在")
            available = ', '.join(self.keywords.keys())
            print(f"📋 可用的意圖: {available}")
            return
        
        config = self.keywords[intent_name]
        print(f"\n🔍 意圖: {intent_name}")
        print(f"📝 描述: {config.get('description', '無描述')}")
        
        keywords = config.get('keywords', [])
        print(f"\n🎯 關鍵字 ({len(keywords)} 個):")
        for i, keyword in enumerate(keywords, 1):
            print(f"  {i}. {keyword}")
    
    def add_intent(self, intent_name: str, description: str, keywords: List[str]):
        """新增意圖類型"""
        if intent_name in self.keywords:
            print(f"❌ 意圖 '{intent_name}' 已存在")
            return False
        
        self.keywords[intent_name] = {
            "keywords": keywords,
            "description": description
        }
        
        if self._save_keywords():
            print(f"✅ 已新增意圖 '{intent_name}'")
            return True
        return False
    
    def update_intent(self, intent_name: str, field: str, value: Any):
        """更新意圖的特定欄位"""
        if intent_name not in self.keywords:
            print(f"❌ 意圖 '{intent_name}' 不存在")
            return False
        
        valid_fields = ['description', 'keywords']
        if field not in valid_fields:
            print(f"❌ 無效的欄位 '{field}'。有效欄位: {', '.join(valid_fields)}")
            return False
        
        # 處理關鍵字列表
        if field == 'keywords' and isinstance(value, str):
            value = [value]
        
        self.keywords[intent_name][field] = value
        
        if self._save_keywords():
            print(f"✅ 已更新意圖 '{intent_name}' 的 {field}")
            return True
        return False
    
    def delete_intent(self, intent_name: str):
        """刪除意圖類型"""
        if intent_name not in self.keywords:
            print(f"❌ 意圖 '{intent_name}' 不存在")
            return False
        
        del self.keywords[intent_name]
        
        if self._save_keywords():
            print(f"✅ 已刪除意圖 '{intent_name}'")
            return True
        return False
    
    def add_keyword(self, intent_name: str, keyword: str):
        """為意圖新增關鍵字"""
        if intent_name not in self.keywords:
            print(f"❌ 意圖 '{intent_name}' 不存在")
            return False
        
        keywords = self.keywords[intent_name]['keywords']
        if keyword in keywords:
            print(f"❌ 關鍵字 '{keyword}' 已存在")
            return False
        
        keywords.append(keyword)
        
        if self._save_keywords():
            print(f"✅ 已為 '{intent_name}' 新增關鍵字 '{keyword}'")
            return True
        return False
    
    def remove_keyword(self, intent_name: str, keyword: str):
        """從意圖移除關鍵字"""
        if intent_name not in self.keywords:
            print(f"❌ 意圖 '{intent_name}' 不存在")
            return False
        
        keywords = self.keywords[intent_name]['keywords']
        if keyword not in keywords:
            print(f"❌ 關鍵字 '{keyword}' 不存在")
            return False
        
        keywords.remove(keyword)
        
        if self._save_keywords():
            print(f"✅ 已從 '{intent_name}' 移除關鍵字 '{keyword}'")
            return True
        return False
    
    def search_keyword(self, keyword: str):
        """搜尋包含特定關鍵字的意圖"""
        matches = []
        keyword_lower = keyword.lower()
        
        for intent_name, config in self.keywords.items():
            keywords = config.get('keywords', [])
            for kw in keywords:
                if keyword_lower in kw.lower():
                    matches.append((intent_name, kw))
        
        if matches:
            print(f"\n🔍 搜尋關鍵字 '{keyword}' 的結果:")
            table_data = []
            for intent_name, matched_keyword in matches:
                description = self.keywords[intent_name].get('description', '')
                table_data.append([intent_name, matched_keyword, description])
            
            headers = ['意圖', '匹配關鍵字', '描述']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
        else:
            print(f"❌ 沒有找到包含 '{keyword}' 的關鍵字")
    
    def test_query(self, query: str):
        """測試查詢文字會匹配到哪些意圖"""
        query_lower = query.lower()
        matches = []
        
        for intent_name, config in self.keywords.items():
            keywords = config.get('keywords', [])
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                confidence = len(matched_keywords) / len(keywords)
                matches.append((intent_name, matched_keywords, confidence))
        
        if matches:
            # 按信心度排序
            matches.sort(key=lambda x: x[2], reverse=True)
            
            print(f"\n🧪 查詢文字: '{query}'")
            print("🎯 匹配結果:")
            
            table_data = []
            for intent_name, matched_keywords, confidence in matches:
                description = self.keywords[intent_name].get('description', '')
                table_data.append([
                    intent_name,
                    f"{confidence:.2%}",
                    ', '.join(matched_keywords),
                    description
                ])
            
            headers = ['意圖', '信心度', '匹配關鍵字', '描述']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
        else:
            print(f"❌ 查詢 '{query}' 沒有匹配到任何意圖")
    
    def export_keywords(self, intent_name: str = None, format: str = 'txt'):
        """匯出關鍵字"""
        if intent_name:
            if intent_name not in self.keywords:
                print(f"❌ 意圖 '{intent_name}' 不存在")
                return
            data = {intent_name: self.keywords[intent_name]}
        else:
            data = self.keywords
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'txt':
            filename = f"keywords_export_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                for intent, config in data.items():
                    f.write(f"# {intent} - {config.get('description', '')}\n")
                    for keyword in config.get('keywords', []):
                        f.write(f"{keyword}\n")
                    f.write("\n")
        elif format == 'json':
            filename = f"keywords_export_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已匯出到 {filename}")
    
    def validate_config(self):
        """驗證設定檔的有效性"""
        print("🔍 驗證查詢關鍵字設定...")
        
        errors = []
        warnings = []
        
        for intent_name, config in self.keywords.items():
            # 檢查必要欄位
            if 'keywords' not in config:
                errors.append(f"意圖 '{intent_name}' 缺少 'keywords' 欄位")
                continue
            
            if not config['keywords']:
                warnings.append(f"意圖 '{intent_name}' 沒有定義任何關鍵字")
            
            # 檢查重複關鍵字
            keywords = config['keywords']
            if len(keywords) != len(set(keywords)):
                duplicates = [kw for kw in keywords if keywords.count(kw) > 1]
                warnings.append(f"意圖 '{intent_name}' 有重複關鍵字: {set(duplicates)}")
        
        # 檢查跨意圖的重複關鍵字
        all_keywords = {}
        for intent_name, config in self.keywords.items():
            for keyword in config.get('keywords', []):
                if keyword in all_keywords:
                    warnings.append(f"關鍵字 '{keyword}' 同時出現在 '{all_keywords[keyword]}' 和 '{intent_name}'")
                else:
                    all_keywords[keyword] = intent_name
        
        # 顯示結果
        if errors:
            print("❌ 發現錯誤:")
            for error in errors:
                print(f"  • {error}")
        
        if warnings:
            print("⚠️  警告:")
            for warning in warnings:
                print(f"  • {warning}")
        
        if not errors and not warnings:
            print("✅ 設定檔驗證通過")
        
        return len(errors) == 0

def main():
    parser = argparse.ArgumentParser(description='查詢關鍵字管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    subparsers.add_parser('list', help='列出所有意圖')
    
    # show 命令
    show_parser = subparsers.add_parser('show', help='顯示特定意圖')
    show_parser.add_argument('intent_name', help='意圖名稱')
    
    # add 命令
    add_parser = subparsers.add_parser('add', help='新增意圖')
    add_parser.add_argument('intent_name', help='意圖名稱')
    add_parser.add_argument('description', help='描述')
    add_parser.add_argument('keywords', nargs='+', help='關鍵字列表')
    
    # update 命令
    update_parser = subparsers.add_parser('update', help='更新意圖')
    update_parser.add_argument('intent_name', help='意圖名稱')
    update_parser.add_argument('field', choices=['description', 'keywords'], help='要更新的欄位')
    update_parser.add_argument('value', nargs='+', help='新值')
    
    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='刪除意圖')
    delete_parser.add_argument('intent_name', help='意圖名稱')
    
    # add-keyword 命令
    add_keyword_parser = subparsers.add_parser('add-keyword', help='新增關鍵字到意圖')
    add_keyword_parser.add_argument('intent_name', help='意圖名稱')
    add_keyword_parser.add_argument('keyword', help='關鍵字')
    
    # remove-keyword 命令
    remove_keyword_parser = subparsers.add_parser('remove-keyword', help='從意圖移除關鍵字')
    remove_keyword_parser.add_argument('intent_name', help='意圖名稱')
    remove_keyword_parser.add_argument('keyword', help='關鍵字')
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='搜尋關鍵字')
    search_parser.add_argument('keyword', help='要搜尋的關鍵字')
    
    # test 命令
    test_parser = subparsers.add_parser('test', help='測試查詢文字')
    test_parser.add_argument('query', help='查詢文字')
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='匯出關鍵字')
    export_parser.add_argument('--intent', help='特定意圖名稱（不指定則匯出全部）')
    export_parser.add_argument('--format', choices=['txt', 'json'], default='txt', help='匯出格式')
    
    # validate 命令
    subparsers.add_parser('validate', help='驗證設定檔')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = QueryKeywordsManager()
    
    if args.command == 'list':
        manager.list_intents()
    
    elif args.command == 'show':
        manager.show_intent(args.intent_name)
    
    elif args.command == 'add':
        manager.add_intent(args.intent_name, args.description, args.keywords)
    
    elif args.command == 'update':
        value = args.value[0] if len(args.value) == 1 else args.value
        manager.update_intent(args.intent_name, args.field, value)
    
    elif args.command == 'delete':
        manager.delete_intent(args.intent_name)
    
    elif args.command == 'add-keyword':
        manager.add_keyword(args.intent_name, args.keyword)
    
    elif args.command == 'remove-keyword':
        manager.remove_keyword(args.intent_name, args.keyword)
    
    elif args.command == 'search':
        manager.search_keyword(args.keyword)
    
    elif args.command == 'test':
        manager.test_query(args.query)
    
    elif args.command == 'export':
        manager.export_keywords(args.intent, args.format)
    
    elif args.command == 'validate':
        manager.validate_config()

if __name__ == '__main__':
    main()