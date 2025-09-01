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
        """載入產品數據 - 強化版，支援多CSV檔案載入與錯誤恢復"""
        try:
            data_dir = Path(self.csv_path)
            
            # 檢查數據目錄存在性
            if not data_dir.exists():
                self.logger.warning(f"產品資料目錄不存在: {data_dir}")
                return self._handle_data_loading_failure("目錄不存在")
            
            if not data_dir.is_dir():
                self.logger.error(f"指定路徑不是目錄: {data_dir}")
                return self._handle_data_loading_failure("路徑錯誤")
            
            # 查找CSV檔案
            csv_files = list(data_dir.glob("*_result.csv"))
            
            if not csv_files:
                self.logger.warning(f"在 {data_dir} 中找不到 *_result.csv 檔案")
                # 嘗試查找其他可能的CSV檔案
                alternative_files = list(data_dir.glob("*.csv"))
                if alternative_files:
                    self.logger.info(f"發現 {len(alternative_files)} 個其他CSV檔案，嘗試載入")
                    csv_files = alternative_files[:5]  # 限制最多5個檔案
                else:
                    return self._handle_data_loading_failure("找不到CSV檔案")
            
            # 載入CSV檔案
            all_products = []
            successful_files = 0
            failed_files = 0
            
            for csv_file in csv_files:
                try:
                    self.logger.info(f"載入產品檔案: {csv_file.name}")
                    
                    # 檢查檔案可讀性
                    if not csv_file.exists() or csv_file.stat().st_size == 0:
                        self.logger.warning(f"檔案 {csv_file.name} 不存在或為空")
                        failed_files += 1
                        continue
                    
                    # 讀取CSV檔案
                    try:
                        df = pd.read_csv(csv_file, encoding='utf-8')
                    except UnicodeDecodeError:
                        # 嘗試其他編碼
                        self.logger.info(f"嘗試使用GBK編碼讀取 {csv_file.name}")
                        df = pd.read_csv(csv_file, encoding='gbk')
                    except pd.errors.EmptyDataError:
                        self.logger.warning(f"檔案 {csv_file.name} 無數據")
                        failed_files += 1
                        continue
                    except pd.errors.ParserError as e:
                        self.logger.error(f"解析檔案 {csv_file.name} 失敗: {e}")
                        failed_files += 1
                        continue
                    
                    # 檢查DataFrame有效性
                    if df.empty:
                        self.logger.warning(f"檔案 {csv_file.name} 沒有數據行")
                        failed_files += 1
                        continue
                    
                    # 驗證必要欄位
                    required_cols = ['modeltype', 'modelname']
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    if missing_cols:
                        self.logger.warning(f"檔案 {csv_file.name} 缺少必要欄位: {missing_cols}")
                        failed_files += 1
                        continue
                    
                    # 清理和驗證數據
                    products = df.to_dict(orient='records')
                    validated_products = self._validate_and_enrich_products(products)
                    
                    if validated_products:
                        all_products.extend(validated_products)
                        successful_files += 1
                        self.logger.info(f"從 {csv_file.name} 成功載入 {len(validated_products)} 個有效產品")
                    else:
                        self.logger.warning(f"檔案 {csv_file.name} 沒有有效產品數據")
                        failed_files += 1
                    
                except Exception as e:
                    self.logger.error(f"處理檔案 {csv_file.name} 時發生錯誤: {e}")
                    failed_files += 1
                    continue
            
            # 結果處理
            if all_products:
                self.logger.info(f"數據載入完成: 成功載入 {len(all_products)} 個產品 (成功檔案: {successful_files}, 失敗檔案: {failed_files})")
                return all_products
            else:
                self.logger.warning(f"無法從任何檔案載入有效產品數據 (處理檔案: {len(csv_files)}, 失敗檔案: {failed_files})")
                return self._handle_data_loading_failure("所有檔案載入失敗")
                
        except Exception as e:
            self.logger.error(f"載入產品數據過程中發生未預期錯誤: {e}")
            return self._handle_data_loading_failure(f"系統錯誤: {str(e)}")
    
    def _handle_data_loading_failure(self, reason: str) -> List[Dict[str, Any]]:
        """處理數據載入失敗的情況"""
        self.logger.error(f"數據載入失敗原因: {reason}")
        self.logger.info("啟用備案產品數據 - 確保系統繼續運行")
        
        # 記錄備案啟用事件
        try:
            from datetime import datetime
            failure_log = {
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "action": "使用備案產品數據",
                "products_count": 3
            }
            self.logger.warning(f"備案機制啟用: {failure_log}")
        except Exception:
            pass
        
        return self._get_sample_products()
    
    def _get_sample_products(self) -> List[Dict[str, Any]]:
        """獲取示例產品數據 - 修復版，僅包含公司產品"""
        self.logger.warning("使用備案產品數據 - 僅包含公司內部產品")
        return [
            {
                "modeltype": "819",
                "version": "MP_v1.6",
                "modelname": "AB819-S",
                "cpu": "Intel Core i5-12500H",
                "gpu": "Intel Iris Xe Graphics",
                "memory": "8GB DDR4",
                "storage": "256GB SSD",
                "lcd": "15.6\" FHD (1920x1080)",
                "battery": "50Wh",
                "wireless": "Wi-Fi 6",
                "bluetooth": "Bluetooth 5.1",
                "iointerface": "USB-A x2, USB-C x1, HDMI",
                "structconfig": "Commercial Notebook, 1.8kg",
                "popularity_score": 7.5,
                "price_tier": "mid_range",
                "primary_usage": "business",
                "target_users": ["professionals", "students"],
                "key_features": ["均衡效能", "輕薄設計", "全高清顯示"]
            },
            {
                "modeltype": "839",
                "version": "EVT_v1.0", 
                "modelname": "AKK839",
                "cpu": "Intel Core i3-1215U",
                "gpu": "Intel UHD Graphics",
                "memory": "4GB DDR4",
                "storage": "128GB SSD",
                "lcd": "14\" HD (1366x768)",
                "battery": "42Wh",
                "wireless": "Wi-Fi 5",
                "bluetooth": "Bluetooth 5.0",
                "iointerface": "USB-A x2, USB-C x1",
                "structconfig": "Budget Notebook, 1.6kg",
                "popularity_score": 6.0,
                "price_tier": "budget",
                "primary_usage": "general",
                "target_users": ["students", "general_users"],
                "key_features": ["經濟實惠", "輕便攜帶", "日常辦公"]
            },
            {
                "modeltype": "958",
                "version": "MP_v1.1",
                "modelname": "AG958",
                "cpu": "Intel Core i7-12700H",
                "gpu": "Intel Iris Xe Graphics",
                "memory": "16GB DDR4",
                "storage": "512GB SSD",
                "lcd": "15.6\" FHD (1920x1080) 144Hz",
                "battery": "65Wh",
                "wireless": "Wi-Fi 6E",
                "bluetooth": "Bluetooth 5.2",
                "iointerface": "USB-A x3, USB-C x2, HDMI, Ethernet",
                "structconfig": "Performance Notebook, 2.1kg",
                "popularity_score": 8.5,
                "price_tier": "premium",
                "primary_usage": "creative",
                "target_users": ["professionals", "creators"],
                "key_features": ["高效能處理器", "大容量記憶體", "高刷新率螢幕"]
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
                # 清理產品數據，移除前綴
                cleaned_product = self._clean_product_data(product)
                
                # 基本欄位驗證
                if not self._validate_product_fields(cleaned_product):
                    continue
                
                # 豐富化產品數據
                enriched_product = self._enrich_product_data(cleaned_product)
                enriched_products.append(enriched_product)
                
            except Exception as e:
                self.logger.debug(f"處理產品數據時發生錯誤: {e}")
                continue
        
        return enriched_products
    
    def _clean_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """清理產品數據，移除前綴"""
        cleaned = product.copy()
        
        # 清理modelname前綴
        if 'modelname' in cleaned:
            modelname = str(cleaned['modelname'])
            if 'Model Name:' in modelname:
                cleaned['modelname'] = modelname.replace('Model Name:', '').strip()
                self.logger.debug(f"清理modelname前綴: '{modelname}' -> '{cleaned['modelname']}'")
        
        # 清理version前綴
        if 'version' in cleaned:
            version = str(cleaned['version'])
            if 'Version:' in version:
                cleaned['version'] = version.replace('Version:', '').strip()
                self.logger.debug(f"清理version前綴: '{version}' -> '{cleaned['version']}'")
        
        # 清理mainboard前綴
        if 'mainboard' in cleaned:
            mainboard = str(cleaned['mainboard'])
            if 'MB Ver.:' in mainboard:
                cleaned['mainboard'] = mainboard.replace('MB Ver.:', '').strip()
                self.logger.debug(f"清理mainboard前綴: '{mainboard}' -> '{cleaned['mainboard']}'")
        
        return cleaned
    
    def _validate_product_fields(self, product: Dict[str, Any]) -> bool:
        """驗證產品必要欄位 - 強化版"""
        # 必要欄位檢查
        required_fields = ['modeltype', 'modelname']
        
        for field in required_fields:
            value = product.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                self.logger.debug(f"產品缺少必要欄位 {field} 或值為空")
                return False
        
        # 公司產品驗證 - 確保不是外部產品
        modelname = str(product.get('modelname', '')).strip()
        if not self._is_company_product(modelname):
            self.logger.debug(f"排除非公司產品: {modelname}")
            return False
        
        # 型號格式驗證
        modeltype = str(product.get('modeltype', '')).strip()
        if not self._is_valid_modeltype(modeltype):
            self.logger.debug(f"無效的型號格式: {modeltype}")
            return False
        
        return True
    
    def _is_company_product(self, modelname: str) -> bool:
        """檢查是否為公司產品"""
        if not modelname:
            return False
        
        # 清理前綴（以防萬一）
        if 'Model Name:' in modelname:
            modelname = modelname.replace('Model Name:', '').strip()
            
        modelname_lower = modelname.lower()
        
        # 公司產品前綴模式
        company_prefixes = ['ab', 'akk', 'ag', 'ac', 'apx', 'ast', 'ahp']  # 基於真實數據觀察
        
        # 檢查是否以公司前綴開頭
        for prefix in company_prefixes:
            if modelname_lower.startswith(prefix):
                return True
        
        # 排除明確的外部品牌
        external_brands = [
            'asus', 'rog', 'strix', 'lenovo', 'thinkpad', 
            'macbook', 'mac', 'hp', 'pavilion', 'acer', 
            'aspire', 'dell', 'surface', 'msi', 'razer'
        ]
        
        for brand in external_brands:
            if brand in modelname_lower:
                return False
        
        return True
    
    def _is_valid_modeltype(self, modeltype: str) -> bool:
        """檢查是否為有效的型號"""
        if not modeltype:
            return False
        
        # 基於實際數據，公司型號主要為數字，但也可能包含字母
        modeltype_clean = modeltype.strip()
        
        # 檢查是否為純數字
        try:
            int(modeltype_clean)
            return True
        except ValueError:
            # 如果不是純數字，檢查是否為數字+字母的組合（如AC01）
            if modeltype_clean and len(modeltype_clean) <= 10:
                return True
        
        return False
    
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
