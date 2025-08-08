#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 知識庫管理系統
"""

import json
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

class NotebookKnowledgeBase:
    """筆記型電腦知識庫管理"""
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        初始化知識庫
        
        Args:
            csv_path: 產品CSV文件路徑
        """
        self.logger = logging.getLogger(__name__)
        self.csv_path = csv_path or self._get_default_csv_path()
        self.products = self.load_products()
        
    def _get_default_csv_path(self) -> str:
        """獲取默認CSV路徑"""
        return str(Path(__file__).parent.parent.parent / "data" / "raw" / "notebook_products.csv")
    
    def load_products(self) -> List[Dict[str, Any]]:
        """載入產品數據"""
        try:
            if Path(self.csv_path).exists():
                df = pd.read_csv(self.csv_path)
                products = df.to_dict(orient='records')
                self.logger.info(f"成功載入 {len(products)} 個產品")
                return products
            else:
                self.logger.warning(f"產品文件不存在: {self.csv_path}，使用示例數據")
                return self._get_sample_products()
        except Exception as e:
            self.logger.error(f"載入產品數據失敗: {e}")
            return self._get_sample_products()
    
    def _get_sample_products(self) -> List[Dict[str, Any]]:
        """獲取示例產品數據"""
        return [
            {
                "id": "NB001",
                "name": "ASUS ROG Strix G15",
                "brand": "asus",
                "series": "ROG",
                "usage_purpose": ["gaming", "creative"],
                "price_range": "premium",
                "cpu": "AMD Ryzen 7 5800H",
                "gpu": "NVIDIA RTX 3060",
                "ram": "16GB",
                "storage": "512GB SSD",
                "display": "15.6\" FHD 144Hz",
                "weight": "2.3kg",
                "battery": "90Wh",
                "description": "專為遊戲設計的高性能筆電，適合重度遊戲和創意工作"
            },
            {
                "id": "NB002", 
                "name": "Lenovo ThinkPad X1 Carbon",
                "brand": "lenovo",
                "series": "ThinkPad",
                "usage_purpose": ["business", "general"],
                "price_range": "luxury",
                "cpu": "Intel Core i7-1165G7",
                "gpu": "Intel Iris Xe",
                "ram": "16GB",
                "storage": "1TB SSD",
                "display": "14\" 4K UHD",
                "weight": "1.1kg",
                "battery": "57Wh",
                "description": "商務精英首選，輕薄便攜，性能穩定"
            },
            {
                "id": "NB003",
                "name": "Acer Aspire 5",
                "brand": "acer", 
                "series": "Aspire",
                "usage_purpose": ["student", "general"],
                "price_range": "budget",
                "cpu": "AMD Ryzen 5 5500U",
                "gpu": "AMD Radeon Graphics",
                "ram": "8GB",
                "storage": "256GB SSD",
                "display": "15.6\" FHD",
                "weight": "1.8kg",
                "battery": "48Wh",
                "description": "性價比之選，適合學生和一般使用"
            },
            {
                "id": "NB004",
                "name": "MacBook Pro 14",
                "brand": "apple",
                "series": "MacBook Pro", 
                "usage_purpose": ["creative", "business"],
                "price_range": "luxury",
                "cpu": "Apple M1 Pro",
                "gpu": "Apple M1 Pro GPU",
                "ram": "16GB",
                "storage": "512GB SSD",
                "display": "14\" Liquid Retina XDR",
                "weight": "1.6kg",
                "battery": "70Wh",
                "description": "創意專業人士的理想選擇，性能強勁，顯示效果出色"
            },
            {
                "id": "NB005",
                "name": "HP Pavilion Gaming",
                "brand": "hp",
                "series": "Pavilion",
                "usage_purpose": ["gaming", "student"],
                "price_range": "mid_range",
                "cpu": "Intel Core i5-10300H",
                "gpu": "NVIDIA GTX 1650",
                "ram": "8GB",
                "storage": "512GB SSD",
                "display": "15.6\" FHD 144Hz",
                "weight": "2.2kg",
                "battery": "52.5Wh",
                "description": "中端遊戲筆電，平衡性能與價格"
            }
        ]
    
    def filter_products(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根據用戶偏好過濾產品
        
        Args:
            preferences: 用戶偏好字典
            
        Returns:
            過濾後的產品列表
        """
        filtered_products = self.products.copy()
        
        # 根據使用目的過濾
        if "usage_purpose" in preferences:
            purpose = preferences["usage_purpose"]
            filtered_products = [
                p for p in filtered_products 
                if purpose in p.get("usage_purpose", [])
            ]
        
        # 根據預算範圍過濾
        if "budget_range" in preferences:
            budget = preferences["budget_range"]
            filtered_products = [
                p for p in filtered_products 
                if p.get("price_range") == budget
            ]
        
        # 根據品牌偏好過濾
        if "brand_preference" in preferences:
            brand = preferences["brand_preference"]
            filtered_products = [
                p for p in filtered_products 
                if p.get("brand") == brand
            ]
        
        # 根據便攜性需求過濾
        if "portability_need" in preferences:
            portability = preferences["portability_need"]
            if portability == "ultra_portable":
                filtered_products = [
                    p for p in filtered_products 
                    if float(p.get("weight", "3").replace("kg", "")) < 1.5
                ]
            elif portability == "desktop_replacement":
                filtered_products = [
                    p for p in filtered_products 
                    if float(p.get("weight", "1").replace("kg", "")) > 2.0
                ]
        
        return filtered_products
    
    def semantic_search(self, query: str) -> List[Dict[str, Any]]:
        """
        語義搜索相關產品
        
        Args:
            query: 搜索查詢
            
        Returns:
            相關產品列表
        """
        query_lower = query.lower()
        relevant_products = []
        
        for product in self.products:
            score = 0
            
            # 檢查產品名稱
            if query_lower in product.get("name", "").lower():
                score += 3
            
            # 檢查品牌
            if query_lower in product.get("brand", "").lower():
                score += 2
            
            # 檢查描述
            if query_lower in product.get("description", "").lower():
                score += 1
            
            # 檢查使用目的
            for purpose in product.get("usage_purpose", []):
                if query_lower in purpose.lower():
                    score += 2
            
            if score > 0:
                relevant_products.append((product, score))
        
        # 按相關性排序
        relevant_products.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in relevant_products]
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """根據ID獲取產品"""
        for product in self.products:
            if product.get("id") == product_id:
                return product
        return None
    
    def get_products_by_brand(self, brand: str) -> List[Dict[str, Any]]:
        """根據品牌獲取產品"""
        return [p for p in self.products if p.get("brand") == brand]
    
    def get_products_by_price_range(self, price_range: str) -> List[Dict[str, Any]]:
        """根據價格範圍獲取產品"""
        return [p for p in self.products if p.get("price_range") == price_range]
