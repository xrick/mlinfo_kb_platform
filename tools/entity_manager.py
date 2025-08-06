#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entity Patterns Manager CLI
管理 entity_patterns.json 設定檔的命令列工具
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from tabulate import tabulate
from typing import Dict, Any, List

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 設定檔路徑
ENTITY_PATTERNS_PATH = project_root / "libs/services/sales_assistant/prompts/entity_patterns.json"
BACKUP_DIR = project_root / "tools/backups"

class EntityPatternsManager:
    """實體模式管理器"""
    
    def __init__(self):
        self.patterns_path = ENTITY_PATTERNS_PATH
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(exist_ok=True)
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, Any]:
        """載入實體模式設定"""
        try:
            with open(self.patterns_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('entity_patterns', {})
        except Exception as e:
            print(f"❌ 載入設定檔失敗: {e}")
            return {}
    
    def _save_patterns(self, backup: bool = True) -> bool:
        """儲存實體模式設定"""
        try:
            if backup:
                self._create_backup()
            
            data = {"entity_patterns": self.patterns}
            with open(self.patterns_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 儲存設定檔失敗: {e}")
            return False
    
    def _create_backup(self):
        """建立備份檔案"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"entity_patterns_{timestamp}.json"
        
        try:
            import shutil
            shutil.copy2(self.patterns_path, backup_file)
            print(f"📋 已建立備份: {backup_file}")
        except Exception as e:
            print(f"⚠️  建立備份失敗: {e}")
    
    def list_entities(self):
        """列出所有實體類型"""
        if not self.patterns:
            print("❌ 沒有找到實體模式設定")
            return
        
        table_data = []
        for entity_type, config in self.patterns.items():
            patterns = config.get('patterns', [])
            description = config.get('description', '')
            examples = config.get('examples', [])
            
            table_data.append([
                entity_type,
                description,
                len(patterns),
                len(examples),
                ', '.join(examples[:3]) + ('...' if len(examples) > 3 else '')
            ])
        
        headers = ['實體類型', '描述', '模式數量', '範例數量', '範例預覽']
        print("\n📋 實體模式列表:")
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def show_entity(self, entity_type: str):
        """顯示特定實體類型的詳細資訊"""
        if entity_type not in self.patterns:
            print(f"❌ 實體類型 '{entity_type}' 不存在")
            available = ', '.join(self.patterns.keys())
            print(f"📋 可用的實體類型: {available}")
            return
        
        config = self.patterns[entity_type]
        print(f"\n🔍 實體類型: {entity_type}")
        print(f"📝 描述: {config.get('description', '無描述')}")
        
        patterns = config.get('patterns', [])
        print(f"\n🎯 模式 ({len(patterns)} 個):")
        for i, pattern in enumerate(patterns, 1):
            print(f"  {i}. {pattern}")
        
        examples = config.get('examples', [])
        if examples:
            print(f"\n💡 範例 ({len(examples)} 個):")
            for i, example in enumerate(examples, 1):
                print(f"  {i}. {example}")
    
    def add_entity(self, entity_type: str, description: str, patterns: List[str], examples: List[str] = None):
        """新增實體類型"""
        if entity_type in self.patterns:
            print(f"❌ 實體類型 '{entity_type}' 已存在")
            return False
        
        # 驗證正則表達式模式
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as e:
                print(f"❌ 無效的正則表達式模式 '{pattern}': {e}")
                return False
        
        self.patterns[entity_type] = {
            "patterns": patterns,
            "description": description,
            "examples": examples or []
        }
        
        if self._save_patterns():
            print(f"✅ 已新增實體類型 '{entity_type}'")
            return True
        return False
    
    def update_entity(self, entity_type: str, field: str, value: Any):
        """更新實體類型的特定欄位"""
        if entity_type not in self.patterns:
            print(f"❌ 實體類型 '{entity_type}' 不存在")
            return False
        
        valid_fields = ['description', 'patterns', 'examples']
        if field not in valid_fields:
            print(f"❌ 無效的欄位 '{field}'。有效欄位: {', '.join(valid_fields)}")
            return False
        
        # 特殊處理patterns欄位的正則表達式驗證
        if field == 'patterns':
            if isinstance(value, str):
                value = [value]
            for pattern in value:
                try:
                    re.compile(pattern)
                except re.error as e:
                    print(f"❌ 無效的正則表達式模式 '{pattern}': {e}")
                    return False
        
        self.patterns[entity_type][field] = value
        
        if self._save_patterns():
            print(f"✅ 已更新實體類型 '{entity_type}' 的 {field}")
            return True
        return False
    
    def delete_entity(self, entity_type: str):
        """刪除實體類型"""
        if entity_type not in self.patterns:
            print(f"❌ 實體類型 '{entity_type}' 不存在")
            return False
        
        del self.patterns[entity_type]
        
        if self._save_patterns():
            print(f"✅ 已刪除實體類型 '{entity_type}'")
            return True
        return False
    
    def add_pattern(self, entity_type: str, pattern: str):
        """為實體類型新增模式"""
        if entity_type not in self.patterns:
            print(f"❌ 實體類型 '{entity_type}' 不存在")
            return False
        
        # 驗證正則表達式
        try:
            re.compile(pattern)
        except re.error as e:
            print(f"❌ 無效的正則表達式模式 '{pattern}': {e}")
            return False
        
        if pattern in self.patterns[entity_type]['patterns']:
            print(f"❌ 模式 '{pattern}' 已存在")
            return False
        
        self.patterns[entity_type]['patterns'].append(pattern)
        
        if self._save_patterns():
            print(f"✅ 已為 '{entity_type}' 新增模式 '{pattern}'")
            return True
        return False
    
    def remove_pattern(self, entity_type: str, pattern: str):
        """從實體類型移除模式"""
        if entity_type not in self.patterns:
            print(f"❌ 實體類型 '{entity_type}' 不存在")
            return False
        
        patterns = self.patterns[entity_type]['patterns']
        if pattern not in patterns:
            print(f"❌ 模式 '{pattern}' 不存在")
            return False
        
        patterns.remove(pattern)
        
        if self._save_patterns():
            print(f"✅ 已從 '{entity_type}' 移除模式 '{pattern}'")
            return True
        return False
    
    def add_example(self, entity_type: str, example: str):
        """為實體類型新增範例"""
        if entity_type not in self.patterns:
            print(f"❌ 實體類型 '{entity_type}' 不存在")
            return False
        
        examples = self.patterns[entity_type].setdefault('examples', [])
        if example in examples:
            print(f"❌ 範例 '{example}' 已存在")
            return False
        
        examples.append(example)
        
        if self._save_patterns():
            print(f"✅ 已為 '{entity_type}' 新增範例 '{example}'")
            return True
        return False
    
    def test_pattern(self, pattern: str, test_text: str):
        """測試正則表達式模式"""
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            matches = list(regex.finditer(test_text))
            
            print(f"\n🧪 測試模式: {pattern}")
            print(f"📝 測試文本: {test_text}")
            print(f"🎯 找到 {len(matches)} 個匹配:")
            
            for i, match in enumerate(matches, 1):
                print(f"  {i}. '{match.group()}' (位置: {match.start()}-{match.end()})")
            
            if not matches:
                print("  (無匹配)")
                
        except re.error as e:
            print(f"❌ 無效的正則表達式: {e}")
    
    def validate_config(self):
        """驗證設定檔的有效性"""
        print("🔍 驗證實體模式設定...")
        
        errors = []
        warnings = []
        
        for entity_type, config in self.patterns.items():
            # 檢查必要欄位
            if 'patterns' not in config:
                errors.append(f"實體類型 '{entity_type}' 缺少 'patterns' 欄位")
                continue
            
            if not config['patterns']:
                warnings.append(f"實體類型 '{entity_type}' 沒有定義任何模式")
            
            # 驗證正則表達式
            for pattern in config['patterns']:
                try:
                    re.compile(pattern)
                except re.error as e:
                    errors.append(f"實體類型 '{entity_type}' 的模式 '{pattern}' 無效: {e}")
        
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
    parser = argparse.ArgumentParser(description='實體模式管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    subparsers.add_parser('list', help='列出所有實體類型')
    
    # show 命令
    show_parser = subparsers.add_parser('show', help='顯示特定實體類型')
    show_parser.add_argument('entity_type', help='實體類型名稱')
    
    # add 命令
    add_parser = subparsers.add_parser('add', help='新增實體類型')
    add_parser.add_argument('entity_type', help='實體類型名稱')
    add_parser.add_argument('description', help='描述')
    add_parser.add_argument('patterns', nargs='+', help='正則表達式模式')
    add_parser.add_argument('--examples', nargs='*', help='範例')
    
    # update 命令
    update_parser = subparsers.add_parser('update', help='更新實體類型')
    update_parser.add_argument('entity_type', help='實體類型名稱')
    update_parser.add_argument('field', choices=['description', 'patterns', 'examples'], help='要更新的欄位')
    update_parser.add_argument('value', nargs='+', help='新值')
    
    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='刪除實體類型')
    delete_parser.add_argument('entity_type', help='實體類型名稱')
    
    # add-pattern 命令
    add_pattern_parser = subparsers.add_parser('add-pattern', help='新增模式到實體類型')
    add_pattern_parser.add_argument('entity_type', help='實體類型名稱')
    add_pattern_parser.add_argument('pattern', help='正則表達式模式')
    
    # remove-pattern 命令
    remove_pattern_parser = subparsers.add_parser('remove-pattern', help='從實體類型移除模式')
    remove_pattern_parser.add_argument('entity_type', help='實體類型名稱')
    remove_pattern_parser.add_argument('pattern', help='正則表達式模式')
    
    # add-example 命令
    add_example_parser = subparsers.add_parser('add-example', help='新增範例到實體類型')
    add_example_parser.add_argument('entity_type', help='實體類型名稱')
    add_example_parser.add_argument('example', help='範例文字')
    
    # test 命令
    test_parser = subparsers.add_parser('test', help='測試正則表達式模式')
    test_parser.add_argument('pattern', help='正則表達式模式')
    test_parser.add_argument('text', help='測試文字')
    
    # validate 命令
    subparsers.add_parser('validate', help='驗證設定檔')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = EntityPatternsManager()
    
    if args.command == 'list':
        manager.list_entities()
    
    elif args.command == 'show':
        manager.show_entity(args.entity_type)
    
    elif args.command == 'add':
        manager.add_entity(args.entity_type, args.description, args.patterns, args.examples)
    
    elif args.command == 'update':
        value = args.value[0] if len(args.value) == 1 else args.value
        manager.update_entity(args.entity_type, args.field, value)
    
    elif args.command == 'delete':
        manager.delete_entity(args.entity_type)
    
    elif args.command == 'add-pattern':
        manager.add_pattern(args.entity_type, args.pattern)
    
    elif args.command == 'remove-pattern':
        manager.remove_pattern(args.entity_type, args.pattern)
    
    elif args.command == 'add-example':
        manager.add_example(args.entity_type, args.example)
    
    elif args.command == 'test':
        manager.test_pattern(args.pattern, args.text)
    
    elif args.command == 'validate':
        manager.validate_config()

if __name__ == '__main__':
    main()