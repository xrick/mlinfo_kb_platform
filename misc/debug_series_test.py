#!/usr/bin/env python3
import re

def debug_series_patterns(query: str):
    print(f"🔍 調試查詢: '{query}'")
    
    series_patterns = [
        r'\b(819|839|958)\s*系列',           # 819系列、958系列
        r'\b(819|839|958)\s*機型',           # 819機型、958機型  
        r'\b(819|839|958)\s*款',             # 819款、958款
        r'\b(819|839|958)\s*型號',           # 819型號、958型號
        r'比較\s*(819|839|958)\s*系列',      # 比較819系列
        r'(819|839|958)\s*系列.*比較',       # 819系列...比較
        r'(819|839|958)\s*系列.*哪款',       # 819系列哪款
        r'(819|839|958)\s*系列.*機型',       # 819系列機型
    ]
    
    for i, pattern in enumerate(series_patterns, 1):
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            print(f"  ✅ 模式 {i}: {pattern} -> 匹配: '{match.group()}'")
        else:
            print(f"  ❌ 模式 {i}: {pattern} -> 無匹配")

queries = [
    "比較958系列哪款筆記型電腦更適合遊戲？",
    "請比較839系列機型的電池續航力比較？", 
    "請比較819系列顯示螢幕規格有什麼不同？"
]

for query in queries:
    debug_series_patterns(query)
    print()