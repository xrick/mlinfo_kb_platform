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
        
    def _get_default_csv_path(self) -> Path:
        """獲取默認CSV路徑 - 修復版，指向真實產品資料目錄"""
        base_path = Path(__file__).parent.parent.parent
        data_dir = base_path / "data" / "raw" / "EM_New TTL_241104_AllTransformedToGoogleSheet"
        return data_dir
    
    def load_products(self) -> List[Dict[str, Any]]:
        """載入產品數據 - 修復版，支援多CSV檔案載入"""
        try:
            data_dir = Path(self.csv_path)
            
            if not data_dir.exists():
                self.logger.warning(f"產品資料目錄不存在: {data_dir}，使用示例數據")
                return self._get_sample_products()
            
            # 載入所有 *_result.csv 檔案
            csv_files = list(data_dir.glob("*_result.csv"))
            
            if not csv_files:
                self.logger.warning(f"在 {data_dir} 中找不到 *_result.csv 檔案，使用示例數據")
                return self._get_sample_products()
            
            all_products = []
            
            for csv_file in csv_files:
                try:
                    self.logger.info(f"載入產品檔案: {csv_file.name}")
                    df = pd.read_csv(csv_file)
                    
                    # 清理和驗證數據
                    products = df.to_dict(orient='records')
                    validated_products = self._validate_and_enrich_products(products)
                    
                    all_products.extend(validated_products)
                    self.logger.info(f"從 {csv_file.name} 載入了 {len(validated_products)} 個有效產品")
                    
                except Exception as e:
                    self.logger.error(f"載入檔案 {csv_file} 失敗: {e}")
                    continue
            
            if all_products:
                self.logger.info(f"總共成功載入 {len(all_products)} 個公司產品")
                return all_products
            else:
                self.logger.warning("無法載入任何有效產品，使用示例數據")
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
    
    def _validate_and_enrich_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """驗證和豐富化產品數據"""
        enriched_products = []
        
        for product in products:
            try:
                # 基本欄位驗證
                if not self._validate_product_fields(product):
                    continue
                
                # 豐富化產品數據
                enriched_product = self._enrich_product_data(product)
                enriched_products.append(enriched_product)
                
            except Exception as e:
                self.logger.debug(f"處理產品數據時發生錯誤: {e}")
                continue
        
        return enriched_products
    
    def _validate_product_fields(self, product: Dict[str, Any]) -> bool:
        """驗證產品必要欄位"""
        required_fields = ['modeltype', 'modelname']
        
        for field in required_fields:
            if not product.get(field):
                return False
        
        return True
    
    def _enrich_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """豐富化產品數據，添加計算字段"""
        enriched = product.copy()
        
        # 計算熱門度評分
        enriched['popularity_score'] = self._calculate_popularity_score(product)
        
        # 分類價格等級
        enriched['price_tier'] = self._categorize_price_tier(product)
        
        # 推斷主要用途
        enriched['primary_usage'] = self._infer_primary_usage(product)
        
        # 識別目標用戶
        enriched['target_users'] = self._identify_target_users(product)
        
        # 提取關鍵特色
        enriched['key_features'] = self._extract_key_features(product)
        
        return enriched
    
    def _calculate_popularity_score(self, product: Dict[str, Any]) -> float:
        """計算產品熱門度評分"""
        score = 5.0  # 基礎分數
        
        try:
            # 基於CPU等級
            cpu = product.get('cpu', '').lower()
            if any(term in cpu for term in ['i7', 'i9', 'ryzen 7', 'ryzen 9']):
                score += 1.5
            elif any(term in cpu for term in ['i5', 'ryzen 5']):
                score += 1.0
            
            # 基於GPU
            gpu = product.get('gpu', '').lower()
            if any(term in gpu for term in ['rtx', 'gtx', 'radeon']):
                score += 1.5
            
            # 基於記憶體
            memory = product.get('memory', '').lower()
            if '16gb' in memory or '32gb' in memory:
                score += 1.0
            elif '8gb' in memory:
                score += 0.5
            
            # 基於型號系列
            modeltype = product.get('modeltype', '')
            if modeltype in ['819', '839', '958']:
                score += 0.5
            
            return min(score, 10.0)  # 最高10分
        except Exception:
            return 5.0
    
    def _categorize_price_tier(self, product: Dict[str, Any]) -> str:
        """分類價格等級"""
        modeltype = product.get('modeltype', '')
        
        if modeltype in ['958']:
            return 'premium'
        elif modeltype in ['819']:
            return 'mid_range'
        elif modeltype in ['839']:
            return 'budget'
        else:
            return 'standard'
    
    def _infer_primary_usage(self, product: Dict[str, Any]) -> str:
        """推斷主要用途"""
        cpu = product.get('cpu', '').lower()
        gpu = product.get('gpu', '').lower()
        
        # 遊戲用途判斷
        if any(term in gpu for term in ['rtx', 'gtx']) and any(term in cpu for term in ['i7', 'i9', 'ryzen 7']):
            return 'gaming'
        
        # 商務用途判斷
        if 'business' in product.get('certifications', '').lower():
            return 'business'
        
        # 創作用途判斷
        if any(term in cpu for term in ['i7', 'i9']) and 'radeon' in gpu:
            return 'creative'
        
        return 'general'
    
    def _identify_target_users(self, product: Dict[str, Any]) -> List[str]:
        """識別目標用戶群"""
        users = []
        usage = self._infer_primary_usage(product)
        
        if usage == 'gaming':
            users.extend(['gamers', 'enthusiasts'])
        elif usage == 'business':
            users.extend(['professionals', 'enterprises'])
        elif usage == 'creative':
            users.extend(['creators', 'designers'])
        else:
            users.extend(['students', 'general_users'])
        
        return users
    
    def _extract_key_features(self, product: Dict[str, Any]) -> List[str]:
        """提取產品關鍵特色"""
        features = []
        
        try:
            # 基於CPU特色
            cpu = product.get('cpu', '').lower()
            if any(term in cpu for term in ['i7', 'i9', 'ryzen 7', 'ryzen 9']):
                features.append("高效能處理器")
            elif any(term in cpu for term in ['i5', 'ryzen 5']):
                features.append("均衡效能")
            
            # 基於GPU特色
            gpu = product.get('gpu', '').lower()
            if any(term in gpu for term in ['rtx', 'gtx', 'radeon']):
                features.append("獨立顯卡")
            
            # 基於記憶體特色
            memory = product.get('memory', '').lower()
            if any(term in memory for term in ['16gb', '32gb']):
                features.append("大容量記憶體")
            
            # 基於儲存特色
            storage = product.get('storage', '').lower()
            if 'nvme' in storage:
                features.append("NVMe超高速儲存")
            elif 'ssd' in storage:
                features.append("SSD高速儲存")
            
            # 基於顯示器特色
            lcd = product.get('lcd', '').lower()
            if 'fhd' in lcd and '144hz' in lcd:
                features.append("高刷新率螢幕")
            elif 'fhd' in lcd:
                features.append("全高清顯示")
            
            # 基於電池特色
            battery = product.get('battery', '').lower()
            if any(term in battery for term in ['55wh', '65wh', '90wh']):
                features.append("長效電池")
            
            # 基於重量特色
            weight_info = product.get('structconfig', '').lower()
            if '1.8' in weight_info or '1860' in weight_info:
                features.append("輕薄設計")
            
            return features[:3] if features else ["高品質", "可靠穩定"]
            
        except Exception:
            return ["高品質", "可靠穩定"]
