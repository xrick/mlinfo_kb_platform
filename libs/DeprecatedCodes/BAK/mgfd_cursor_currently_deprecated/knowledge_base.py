#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD 知識庫管理系統 - 整合Chunking搜尋核心
"""

import json
import logging
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 導入chunking模組
from .chunking import ProductChunkingEngine, ChunkingContext, ChunkingStrategyType

# 導入產品評分引擎
from .product_scoring_engine import ProductScoringEngine

class NotebookKnowledgeBase:
    """筆記型電腦知識庫管理 - 整合Chunking搜尋核心"""
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        初始化知識庫
        
        Args:
            csv_path: 產品CSV文件路徑
        """
        self.logger = logging.getLogger(__name__)
        self.csv_path = csv_path or self._get_default_csv_path()
        self.products = self.load_products()
        
        # 初始化chunking引擎 - 搜尋核心
        self.logger.info("初始化Chunking搜尋引擎...")
        self.chunking_engine = ProductChunkingEngine()
        self.chunking_context = ChunkingContext(self.chunking_engine)
        
        # 初始化產品評分引擎
        self.logger.info("初始化產品評分引擎...")
        self.scoring_engine = ProductScoringEngine()
        
        # 產品分塊儲存
        self.parent_chunks = []
        self.child_chunks = []
        self.chunk_embeddings = []
        self.embedding_index = {}  # chunk_id -> embedding index mapping
        
        # 初始化分塊數據
        if self.products:
            self._initialize_chunks()
        
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
    
    def search_products(self, slots: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根據槽位搜索產品 - 使用Chunking語義搜尋核心 + 多因子評分
        
        Args:
            slots: 已收集的槽位信息
            
        Returns:
            按評分排序的匹配產品列表
        """
        try:
            self.logger.info(f"使用增強評分引擎搜索產品: {slots}")
            
            # 第一步：語義搜尋獲取候選產品
            search_query = self._build_search_query(slots)
            candidate_products = []
            
            if search_query:
                # 使用chunking語義搜尋
                semantic_results = self._semantic_search_with_chunking(search_query, top_k=15)
                if semantic_results:
                    candidate_products = self._convert_chunks_to_products(semantic_results, slots)
                    self.logger.info(f"語義搜尋找到 {len(candidate_products)} 個候選產品")
            
            # 如果語義搜尋結果不足，使用傳統搜尋補充
            if len(candidate_products) < 5:
                fallback_products = self._fallback_search(slots)
                # 合併結果，去重
                seen_ids = {p.get("modeltype", "") for p in candidate_products}
                for product in fallback_products:
                    if product.get("modeltype", "") not in seen_ids and len(candidate_products) < 10:
                        candidate_products.append(product)
                        seen_ids.add(product.get("modeltype", ""))
                self.logger.info(f"傳統搜尋補充後共 {len(candidate_products)} 個候選產品")
            
            # 第二步：使用多因子評分系統對所有候選產品評分
            if candidate_products:
                scored_products = self.scoring_engine.batch_score_products(candidate_products, slots)
                
                # 整合評分結果到產品信息中
                final_results = []
                for product, score_result in scored_products:
                    enhanced_product = product.copy()
                    enhanced_product.update({
                        "recommendation_score": score_result["total_score"],
                        "score_breakdown": score_result["dimension_scores"],
                        "recommendation_reason": score_result["evaluation_summary"],
                        "match_confidence": "高" if score_result["total_score"] >= 75 else "中" if score_result["total_score"] >= 50 else "低"
                    })
                    final_results.append(enhanced_product)
                
                self.logger.info(f"完成多因子評分，返回 {len(final_results)} 個評分產品")
                return final_results
            else:
                self.logger.warning("無候選產品，返回默認推薦")
                return self._get_default_recommendations(slots)
                
        except Exception as e:
            self.logger.error(f"增強搜尋失敗: {e}")
            return self._fallback_search(slots)
    
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
    
    def reinitialize_chunks(self):
        """重新初始化分塊 - 用於數據更新後"""
        if hasattr(self, 'chunking_engine') and self.products:
            self.logger.info("重新初始化產品分塊...")
            self._initialize_chunks()

    # === Chunking 與語義搜尋實作 ===
    def _initialize_chunks(self) -> None:
        """基於當前產品集建立 parent/child 分塊與向量索引"""
        try:
            parent_chunks, child_chunks = self.chunking_engine.batch_create_chunks(self.products)
            self.parent_chunks = parent_chunks
            self.child_chunks = child_chunks

            # 僅對有 embedding 的 chunks 建立對齊陣列
            all_chunks = self.parent_chunks + self.child_chunks
            self.embedded_chunks: List[Dict[str, Any]] = []
            embeddings: List[List[float]] = []
            self.embedding_index = {}

            for idx, ch in enumerate(all_chunks):
                emb = ch.get("embedding")
                if isinstance(emb, list) and len(emb) > 0:
                    self.embedded_chunks.append(ch)
                    embeddings.append(emb)
                    self.embedding_index[ch["chunk_id"]] = len(embeddings) - 1

            if embeddings:
                self.chunk_embeddings = np.array(embeddings, dtype=np.float32)
            else:
                self.chunk_embeddings = np.zeros((0, 384), dtype=np.float32)

            self.logger.info(
                f"完成產品分塊初始化：parents={len(self.parent_chunks)}, children={len(self.child_chunks)}, embedded={len(self.embedded_chunks)}"
            )
        except Exception as e:
            self.logger.error(f"初始化分塊失敗: {e}")
            self.parent_chunks = []
            self.child_chunks = []
            self.embedded_chunks = []
            self.chunk_embeddings = np.zeros((0, 384), dtype=np.float32)
            self.embedding_index = {}

    def _build_search_query(self, slots: Dict[str, Any]) -> str:
        """將槽位轉換為語義查詢字串"""
        if not slots:
            return ""

        parts: List[str] = []
        usage = slots.get("usage_purpose") or slots.get("primary_usage")
        if usage:
            parts.append(f"用途:{usage}")
        budget = slots.get("budget_range") or slots.get("price_tier")
        if budget:
            parts.append(f"預算:{budget}")
        screen = slots.get("screen_size")
        if screen:
            parts.append(f"螢幕:{screen}吋")
        port = slots.get("portability") or slots.get("portability_need")
        if port:
            parts.append(f"便攜:{port}")
        brand = slots.get("brand_preference")
        if brand and brand != "no_preference":
            parts.append(f"品牌:{brand}")
        special = slots.get("special_requirement")
        if special:
            parts.append(f"需求:{special}")

        return "，".join(parts)

    def _semantic_search_with_chunking(self, query: str, top_k: int = 10, min_score: float = 0.30) -> List[Dict[str, Any]]:
        """對 query 進行語義檢索，返回相似的 chunk 結果集合

        Returns: List[{ 'chunk': chunk_dict, 'score': float }]
        """
        if not query or self.chunk_embeddings.shape[0] == 0:
            return []

        try:
            query_vec = self.chunking_engine.generate_embedding(query)
            query_vec_np = np.array(query_vec, dtype=np.float32).reshape(1, -1)
            scores = cosine_similarity(query_vec_np, self.chunk_embeddings)[0]

            # 取得 top_k 指標
            top_indices = np.argsort(scores)[::-1][:top_k]

            # 對應回已嵌入的 chunks
            results: List[Dict[str, Any]] = []
            for idx in top_indices:
                score = float(scores[idx])
                if score < min_score:
                    continue
                if 0 <= idx < len(self.embedded_chunks):
                    results.append({
                        "chunk": self.embedded_chunks[idx],
                        "score": score,
                    })
            return results
        except Exception as e:
            self.logger.error(f"語義搜尋計算失敗: {e}")
            return []

    def _convert_chunks_to_products(self, chunk_results: List[Dict[str, Any]], slots: Dict[str, Any]) -> List[Dict[str, Any]]:
        """將 chunk 相似結果彙整為產品清單，去重並附上匹配資訊"""
        if not chunk_results:
            return []

        # 建立 modeltype -> product 的索引
        product_map: Dict[str, Dict[str, Any]] = {}
        for p in self.products:
            key = str(p.get("modeltype", ""))
            if key:
                product_map[key] = p

        seen_products = set()
        aggregated: List[Dict[str, Any]] = []

        for item in chunk_results:
            chunk = item.get("chunk", {})
            score = item.get("score", 0.0)
            product_id = str(chunk.get("product_id", ""))
            if not product_id or product_id in seen_products:
                continue

            base_product = product_map.get(product_id)
            if not base_product:
                continue

            product_entry = base_product.copy()
            product_entry["similarity_score"] = max(0.0, min(1.0, float(score)))

            # 匹配原因：基於 chunk 類型與 metadata 簡化產生
            match_reasons: List[str] = []
            chunk_type = chunk.get("chunk_type", "")
            meta = chunk.get("metadata", {}) or {}
            if chunk_type == "child_performance":
                if meta.get("cpu_tier"):
                    match_reasons.append(f"CPU:{meta.get('cpu_tier')}")
                if meta.get("gpu_tier"):
                    match_reasons.append(f"GPU:{meta.get('gpu_tier')}")
            elif chunk_type == "child_design":
                if meta.get("screen_size_category"):
                    match_reasons.append(f"尺寸:{meta.get('screen_size_category')}")
                if meta.get("portability_score"):
                    match_reasons.append("便攜性佳")
            elif chunk_type == "child_business":
                if meta.get("security_level"):
                    match_reasons.append("商務安全")
            elif chunk_type == "child_connectivity":
                if meta.get("connectivity_score"):
                    match_reasons.append("連接性豐富")
            else:
                # parent chunk 或未知類型
                primary_usage = meta.get("primary_usage") or product_entry.get("primary_usage")
                if primary_usage:
                    match_reasons.append(f"用途:{primary_usage}")

            if not match_reasons:
                match_reasons.append("與您的需求語義相似")

            product_entry["match_reasons"] = match_reasons
            aggregated.append(product_entry)
            seen_products.add(product_id)

            if len(aggregated) >= 10:
                break

        # 依相似度排序
        aggregated.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
        return aggregated

    def _get_default_recommendations(self, slots: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        當無候選產品時提供默認推薦
        
        Args:
            slots: 用戶需求槽位
            
        Returns:
            默認推薦產品列表，包含評分信息
        """
        try:
            self.logger.info(f"提供默認推薦，基於槽位: {slots}")
            
            # 選擇最佳的示例產品
            default_products = self.products[:3] if self.products else self._get_sample_products()
            
            # 對默認產品進行評分
            scored_defaults = self.scoring_engine.batch_score_products(default_products, slots)
            
            # 整合評分結果
            final_defaults = []
            for product, score_result in scored_defaults:
                enhanced_product = product.copy()
                enhanced_product.update({
                    "recommendation_score": score_result["total_score"],
                    "score_breakdown": score_result["dimension_scores"],
                    "recommendation_reason": score_result["evaluation_summary"],
                    "match_confidence": "中",
                    "is_default_recommendation": True
                })
                final_defaults.append(enhanced_product)
            
            return final_defaults
            
        except Exception as e:
            self.logger.error(f"生成默認推薦失敗: {e}")
            # 最後後備：返回未評分的示例產品
            return self._get_sample_products()

    def _fallback_search(self, slots: Dict[str, Any]) -> List[Dict[str, Any]]:
        """傳統後備搜尋：嘗試基礎過濾，否則返回前幾個產品"""
        try:
            results = self.filter_products(slots)
            if results:
                return results[:10]
        except Exception:
            pass
        return self.products[:5] if self.products else []
