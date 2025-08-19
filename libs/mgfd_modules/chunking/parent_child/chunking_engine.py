#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MGFD Parent-Child Chunking Engine
實現產品數據的分層分塊處理策略
"""

import logging
import hashlib
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available. Using mock embeddings.")

import numpy as np

from ..chunking_strategy import ChunkingStrategy, ChunkingStrategyType


class ProductChunkingEngine(ChunkingStrategy):
    """產品分塊引擎 - Parent-Child架構"""
    
    def __init__(self, embedding_model: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
        """
        初始化分塊引擎
        
        Args:
            embedding_model: 句子嵌入模型名稱
        """
        super().__init__("ProductChunkingEngine")
        self.logger = logging.getLogger(__name__)
        self.embedding_model_name = embedding_model
        
        # 初始化嵌入模型
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.sentence_transformer = SentenceTransformer(embedding_model)
                self.logger.info(f"成功載入嵌入模型: {embedding_model}")
            except Exception as e:
                self.logger.error(f"載入嵌入模型失敗: {e}")
                self.sentence_transformer = None
        else:
            self.sentence_transformer = None
            
        # 分塊配置
        self.chunk_config = {
            'max_parent_length': 2000,
            'max_child_length': 800,
            'overlap_size': 100,
            'min_chunk_length': 50
        }
        
        # 統計訊息
        self.stats = {
            'total_products_processed': 0,
            'total_chunks_created': 0,
            'processing_errors': 0,
            'last_processed': None
        }
    
    def create_chunks(self, product: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        為單個產品創建Parent-Child chunks
        
        Args:
            product: 產品數據字典
            
        Returns:
            (parent_chunk, child_chunks): Parent chunk和Child chunks列表
        """
        try:
            # 創建Parent Chunk
            parent_chunk = self._create_parent_chunk(product)
            
            # 創建四種Child Chunks
            child_chunks = [
                self._create_performance_chunk(product),
                self._create_design_chunk(product),
                self._create_connectivity_chunk(product),
                self._create_business_chunk(product)
            ]
            
            # 生成嵌入向量
            parent_chunk['embedding'] = self.generate_embedding(parent_chunk['content'])
            
            for child in child_chunks:
                child['embedding'] = self.generate_embedding(child['content'])
                child['parent_id'] = parent_chunk['chunk_id']
            
            # 更新統計
            self.stats['total_products_processed'] += 1
            self.stats['total_chunks_created'] += 1 + len(child_chunks)
            self.stats['last_processed'] = datetime.now().isoformat()
            
            self.logger.debug(f"成功為產品 {product.get('modelname', 'Unknown')} 創建分塊")
            
            return parent_chunk, child_chunks
            
        except Exception as e:
            self.logger.error(f"為產品創建分塊失敗: {e}")
            self.stats['processing_errors'] += 1
            raise
    
    def batch_create_chunks(self, products: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批量創建產品分塊
        
        Args:
            products: 產品列表
            
        Returns:
            (all_parent_chunks, all_child_chunks): 所有父分塊和子分塊
        """
        all_parent_chunks = []
        all_child_chunks = []
        
        self.logger.info(f"開始批量處理 {len(products)} 個產品")
        
        for i, product in enumerate(products):
            try:
                parent, children = self.create_chunks(product)
                all_parent_chunks.append(parent)
                all_child_chunks.extend(children)
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"已處理 {i + 1}/{len(products)} 個產品")
                    
            except Exception as e:
                self.logger.error(f"處理產品 {i} 失敗: {e}")
                continue
        
        self.logger.info(f"批量處理完成: {len(all_parent_chunks)} 個父分塊, {len(all_child_chunks)} 個子分塊")
        
        return all_parent_chunks, all_child_chunks
    
    def _create_parent_chunk(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """創建產品概覽Parent Chunk"""
        chunk_id = f"parent_{product.get('modeltype', 'unknown')}_{self._generate_hash(product.get('modelname', ''))}"
        
        # 構建產品概覽內容
        content = self._create_parent_summary(product)
        
        # 提取元數據
        metadata = {
            "modeltype": product.get("modeltype", ""),
            "modelname": product.get("modelname", ""),
            "price_tier": product.get("price_tier", self._categorize_price(product)),
            "primary_usage": product.get("primary_usage", self._infer_usage(product)),
            "popularity_score": product.get("popularity_score", 5.0),
            "key_features": product.get("key_features", self._extract_features(product)),
            "target_users": product.get("target_users", []),
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "chunk_id": chunk_id,
            "chunk_type": "parent",
            "product_id": product.get("modeltype", "unknown"),
            "content": content,
            "metadata": metadata,
            "raw_product": product
        }
    
    def _create_parent_summary(self, product: Dict[str, Any]) -> str:
        """創建產品概覽摘要"""
        modelname = product.get('modelname', 'Unknown Model')
        modeltype = product.get('modeltype', 'Unknown')
        
        # 提取關鍵規格
        cpu = self._extract_cpu_info(product)
        gpu = self._extract_gpu_info(product)
        memory = self._extract_memory_info(product)
        storage = self._extract_storage_info(product)
        display = self._extract_display_info(product)
        
        # 推斷使用場景
        usage_scenarios = self._infer_usage_scenarios(product)
        target_users = self._identify_target_users(product)
        price_positioning = self._get_price_positioning(product)
        
        summary = f"""{modelname} - {modeltype}系列筆電

主要規格：
- 處理器：{cpu}
- 顯示晶片：{gpu}
- 記憶體：{memory}
- 儲存空間：{storage}
- 顯示器：{display}

適用場景：{usage_scenarios}
目標用戶：{target_users}
價格定位：{price_positioning}

這是一款{self._get_product_positioning(product)}，適合{self._get_recommendation_context(product)}的專業需求。
"""
        return summary.strip()
    
    def _create_performance_chunk(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """創建效能專門Child Chunk"""
        chunk_id = f"perf_{product.get('modeltype', 'unknown')}_{self._generate_hash(product.get('modelname', ''))}"
        
        content = self._create_performance_content(product)
        
        metadata = {
            "focus": "performance",
            "cpu_tier": self._categorize_cpu_tier(product.get('cpu', '')),
            "gpu_tier": self._categorize_gpu_tier(product.get('gpu', '')),
            "performance_score": self._calculate_performance_score(product),
            "target_workloads": self._identify_performance_workloads(product)
        }
        
        return {
            "chunk_id": chunk_id,
            "chunk_type": "child_performance",
            "product_id": product.get("modeltype", "unknown"),
            "content": content,
            "metadata": metadata
        }
    
    def _create_performance_content(self, product: Dict[str, Any]) -> str:
        """創建效能內容"""
        modelname = product.get('modelname', 'Unknown')
        
        cpu_info = self._extract_cpu_info(product)
        cpu_tier = self._categorize_cpu_tier(product.get('cpu', ''))
        cpu_use_cases = self._get_cpu_use_cases(cpu_tier)
        
        gpu_info = self._extract_gpu_info(product)
        gpu_capability = self._assess_gpu_capability(product.get('gpu', ''))
        gaming_support = self._evaluate_gaming_support(product.get('gpu', ''))
        
        memory_info = self._extract_memory_info(product)
        multitasking_capability = self._assess_multitasking(product.get('memory', ''))
        
        storage_info = self._extract_storage_info(product)
        storage_speed = self._evaluate_storage_speed(product.get('storage', ''))
        
        performance_score = self._calculate_performance_score(product)
        
        content = f"""{modelname} 效能規格分析

處理器效能：{cpu_info}
- 效能等級：{cpu_tier}
- 適用工作：{cpu_use_cases}

顯示晶片：{gpu_info}
- 圖形處理能力：{gpu_capability}
- 遊戲支援度：{gaming_support}

記憶體配置：{memory_info}
- 多工處理能力：{multitasking_capability}

儲存效能：{storage_info}
- 存取速度：{storage_speed}

綜合效能評分：{performance_score}/10

這款筆電在效能方面{self._get_performance_summary(product)}，特別適合{self._get_performance_target_usage(product)}。
"""
        return content.strip()
    
    def _create_design_chunk(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """創建設計便攜性Child Chunk"""
        chunk_id = f"design_{product.get('modeltype', 'unknown')}_{self._generate_hash(product.get('modelname', ''))}"
        
        content = self._create_design_content(product)
        
        metadata = {
            "focus": "design_portability",
            "screen_size_category": self._categorize_screen_size(product.get('lcd', '')),
            "weight_category": self._categorize_weight(product),
            "portability_score": self._calculate_portability_score(product),
            "target_scenarios": self._identify_design_scenarios(product)
        }
        
        return {
            "chunk_id": chunk_id,
            "chunk_type": "child_design",
            "product_id": product.get("modeltype", "unknown"),
            "content": content,
            "metadata": metadata
        }
    
    def _create_design_content(self, product: Dict[str, Any]) -> str:
        """創建設計內容"""
        modelname = product.get('modelname', 'Unknown')
        
        display_info = self._extract_display_info(product)
        screen_size = self._extract_screen_size(product.get('lcd', ''))
        display_quality = self._assess_display_quality(product.get('lcd', ''))
        
        portability_info = self._extract_portability_info(product)
        weight_category = self._categorize_weight(product)
        design_style = self._identify_design_style(product)
        
        battery_info = self._extract_battery_info(product)
        battery_life = self._estimate_battery_life(product.get('battery', ''))
        
        io_info = self._extract_io_info(product)
        connectivity_rating = self._assess_connectivity(product.get('iointerface', ''))
        
        portability_score = self._calculate_portability_score(product)
        
        content = f"""{modelname} 設計與便攜性

顯示器設計：{display_info}
- 螢幕尺寸：{screen_size}
- 顯示品質：{display_quality}

外觀設計：
- 重量等級：{weight_category}
- 便攜性：{portability_info}
- 設計風格：{design_style}

電池續航：{battery_info}
- 使用時間：{battery_life}

連接介面：{io_info}
- 擴充能力：{connectivity_rating}

便攜性評分：{portability_score}/10

這款筆電在設計上{self._get_design_summary(product)}，非常適合{self._get_design_target_scenarios(product)}。
"""
        return content.strip()
    
    def _create_connectivity_chunk(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """創建連接性Child Chunk"""
        chunk_id = f"conn_{product.get('modeltype', 'unknown')}_{self._generate_hash(product.get('modelname', ''))}"
        
        content = self._create_connectivity_content(product)
        
        metadata = {
            "focus": "connectivity_expansion",
            "wifi_generation": self._extract_wifi_generation(product.get('wireless', '')),
            "usb_types": self._analyze_usb_types(product.get('iointerface', '')),
            "connectivity_score": self._calculate_connectivity_score(product),
            "target_needs": self._identify_connectivity_needs(product)
        }
        
        return {
            "chunk_id": chunk_id,
            "chunk_type": "child_connectivity",
            "product_id": product.get("modeltype", "unknown"),
            "content": content,
            "metadata": metadata
        }
    
    def _create_connectivity_content(self, product: Dict[str, Any]) -> str:
        """創建連接性內容"""
        modelname = product.get('modelname', 'Unknown')
        
        wireless_info = self._extract_wireless_info(product)
        wifi_standard = self._extract_wifi_standard(product.get('wireless', ''))
        wifi_performance = self._assess_wifi_performance(product.get('wireless', ''))
        
        bluetooth_info = self._extract_bluetooth_info(product)
        bluetooth_version = self._extract_bluetooth_version(product.get('bluetooth', ''))
        
        lan_info = self._extract_lan_info(product)
        lan_speed = self._assess_lan_speed(product.get('lan', ''))
        
        io_ports = self._analyze_io_ports(product)
        usb_analysis = self._analyze_usb_ports(product.get('iointerface', ''))
        display_outputs = self._identify_display_outputs(product.get('iointerface', ''))
        
        connectivity_score = self._calculate_connectivity_score(product)
        
        content = f"""{modelname} 連接與擴充性

無線連接：{wireless_info}
- Wi-Fi標準：{wifi_standard}
- 網路效能：{wifi_performance}

藍牙連接：{bluetooth_info}
- 藍牙版本：{bluetooth_version}

有線網路：{lan_info}
- 網路速度：{lan_speed}

連接埠配置：{io_ports}
- USB分析：{usb_analysis}
- 顯示輸出：{display_outputs}

連接性評分：{connectivity_score}/10

這款筆電在連接性方面{self._get_connectivity_summary(product)}，滿足{self._get_connectivity_target_needs(product)}的需求。
"""
        return content.strip()
    
    def _create_business_chunk(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """創建商務專業Child Chunk"""
        chunk_id = f"biz_{product.get('modeltype', 'unknown')}_{self._generate_hash(product.get('modelname', ''))}"
        
        content = self._create_business_content(product)
        
        metadata = {
            "focus": "business_professional",
            "security_level": self._assess_security_level(product),
            "meeting_capability": self._assess_meeting_capability(product),
            "business_score": self._calculate_business_score(product),
            "target_users": self._identify_business_users(product)
        }
        
        return {
            "chunk_id": chunk_id,
            "chunk_type": "child_business",
            "product_id": product.get("modeltype", "unknown"),
            "content": content,
            "metadata": metadata
        }
    
    def _create_business_content(self, product: Dict[str, Any]) -> str:
        """創建商務內容"""
        modelname = product.get('modelname', 'Unknown')
        
        certifications = self._extract_certifications(product)
        security_features = self._assess_security_features(product)
        
        meeting_features = self._assess_meeting_features(product)
        productivity_rating = self._assess_productivity(product)
        
        support_features = self._identify_support_features(product)
        enterprise_readiness = self._assess_enterprise_readiness(product)
        
        business_score = self._calculate_business_score(product)
        
        content = f"""{modelname} 商務專業功能

認證與安全：{certifications}
- 安全功能：{security_features}

商務功能：
- 會議能力：{meeting_features}
- 生產力表現：{productivity_rating}

支援服務：{support_features}
- 企業就緒度：{enterprise_readiness}

商務適用性：{business_score}/10

這款筆電在商務應用上{self._get_business_summary(product)}，特別適合{self._get_business_target_users(product)}。
"""
        return content.strip()
    
    # === 輔助方法 ===
    
    def generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        if self.sentence_transformer:
            try:
                embedding = self.sentence_transformer.encode(text)
                return embedding.tolist()
            except Exception as e:
                self.logger.error(f"生成嵌入向量失敗: {e}")
                
        # 使用模擬嵌入向量作為後備
        return self._create_mock_embedding(text).tolist()
    
    def _create_mock_embedding(self, text: str, dimension: int = 384) -> np.ndarray:
        """創建模擬嵌入向量"""
        # 基於文本哈希創建可重現的向量
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)
        np.random.seed(seed % (2**31))
        return np.random.normal(0, 1, dimension).astype(np.float32)
    
    def _generate_hash(self, text: str) -> str:
        """生成文本哈希"""
        return hashlib.md5(text.encode()).hexdigest()[:8]
    
    # === 產品信息提取方法 ===
    
    def _extract_cpu_info(self, product: Dict[str, Any]) -> str:
        """提取CPU信息"""
        cpu = str(product.get('cpu', '')).strip()
        if cpu and cpu != 'nan':
            # 取第一行或第一個逗號前的內容
            cpu_main = cpu.split('\n')[0].split(',')[0]
            return cpu_main
        return "標準處理器"
    
    def _extract_gpu_info(self, product: Dict[str, Any]) -> str:
        """提取GPU信息"""
        gpu = str(product.get('gpu', '')).strip()
        if gpu and gpu != 'nan':
            gpu_main = gpu.split('\n')[0]
            return gpu_main
        return "內建顯示晶片"
    
    def _extract_memory_info(self, product: Dict[str, Any]) -> str:
        """提取記憶體信息"""
        memory = str(product.get('memory', '')).strip()
        if memory and memory != 'nan':
            # 尋找記憶體容量關鍵字
            if 'DDR4' in memory or 'DDR5' in memory:
                return memory.split('\n')[0]
        return "標準記憶體配置"
    
    def _extract_storage_info(self, product: Dict[str, Any]) -> str:
        """提取儲存信息"""
        storage = str(product.get('storage', '')).strip()
        if storage and storage != 'nan':
            # 提取儲存相關信息
            if 'SSD' in storage or 'NVME' in storage:
                return storage.split('\n')[0]
        return "標準儲存配置"
    
    def _extract_display_info(self, product: Dict[str, Any]) -> str:
        """提取顯示器信息"""
        lcd = str(product.get('lcd', '')).strip()
        if lcd and lcd != 'nan':
            # 提取螢幕尺寸和解析度
            return lcd.split('\n')[0]
        return "標準顯示器"
    
    # === 評估和分類方法 ===
    
    def _categorize_price(self, product: Dict[str, Any]) -> str:
        """分類價格等級"""
        modeltype = product.get('modeltype', '')
        if modeltype in ['958']:
            return 'premium'
        elif modeltype in ['819']:
            return 'mid_range'
        elif modeltype in ['839']:
            return 'budget'
        return 'standard'
    
    def _infer_usage(self, product: Dict[str, Any]) -> str:
        """推斷主要用途"""
        cpu = str(product.get('cpu', '')).lower()
        gpu = str(product.get('gpu', '')).lower()
        
        if any(term in gpu for term in ['rtx', 'gtx']) and any(term in cpu for term in ['i7', 'i9']):
            return 'gaming'
        elif 'business' in str(product.get('certifications', '')).lower():
            return 'business'
        elif any(term in cpu for term in ['i7', 'i9']) and 'radeon' in gpu:
            return 'creative'
        return 'general'
    
    def _extract_features(self, product: Dict[str, Any]) -> List[str]:
        """提取關鍵特色"""
        # 使用現有的特色提取邏輯
        if 'key_features' in product:
            return product['key_features']
        return ["高品質", "可靠穩定"]
    
    def _categorize_cpu_tier(self, cpu: str) -> str:
        """分類CPU等級"""
        cpu_lower = str(cpu).lower()
        if any(term in cpu_lower for term in ['i9', 'ryzen 9']):
            return 'high'
        elif any(term in cpu_lower for term in ['i7', 'ryzen 7']):
            return 'medium_high'
        elif any(term in cpu_lower for term in ['i5', 'ryzen 5']):
            return 'medium'
        return 'basic'
    
    def _categorize_gpu_tier(self, gpu: str) -> str:
        """分類GPU等級"""
        gpu_lower = str(gpu).lower()
        if 'rtx' in gpu_lower:
            return 'gaming'
        elif 'gtx' in gpu_lower:
            return 'performance'
        elif 'radeon' in gpu_lower:
            return 'professional'
        return 'integrated'
    
    def _calculate_performance_score(self, product: Dict[str, Any]) -> float:
        """計算效能評分"""
        if 'popularity_score' in product:
            return min(product['popularity_score'], 10.0)
        return 7.0
    
    def _calculate_portability_score(self, product: Dict[str, Any]) -> float:
        """計算便攜性評分"""
        score = 6.0
        
        # 基於重量信息評分
        struct_config = str(product.get('structconfig', '')).lower()
        if any(term in struct_config for term in ['1.3', '1.4', '1.5']):
            score += 2.0
        elif any(term in struct_config for term in ['1.6', '1.7', '1.8']):
            score += 1.0
        
        return min(score, 10.0)
    
    def _calculate_connectivity_score(self, product: Dict[str, Any]) -> float:
        """計算連接性評分"""
        score = 6.0
        
        # 基於連接埠數量和類型
        io_interface = str(product.get('iointerface', '')).lower()
        if 'usb3' in io_interface and 'type-c' in io_interface:
            score += 1.5
        if 'hdmi' in io_interface:
            score += 0.5
        if 'wifi' in str(product.get('wireless', '')).lower():
            score += 1.0
        
        return min(score, 10.0)
    
    def _calculate_business_score(self, product: Dict[str, Any]) -> float:
        """計算商務適用性評分"""
        score = 6.0
        
        # 基於安全和商務功能
        if product.get('fingerprint'):
            score += 1.0
        if product.get('tpm'):
            score += 1.0
        if 'webcamera' in product and product['webcamera']:
            score += 0.5
        
        return min(score, 10.0)
    
    # === 更多輔助方法（簡化版本） ===
    
    def _infer_usage_scenarios(self, product: Dict[str, Any]) -> str:
        """推斷使用場景"""
        usage = self._infer_usage(product)
        if usage == 'gaming':
            return "遊戲娛樂、高效能運算"
        elif usage == 'business':
            return "商務辦公、會議簡報"
        elif usage == 'creative':
            return "創作設計、影音處理"
        return "日常辦公、學習娛樂"
    
    def _identify_target_users(self, product: Dict[str, Any]) -> str:
        """識別目標用戶"""
        if 'target_users' in product and product['target_users']:
            return ", ".join(product['target_users'])
        return "一般用戶、專業人士"
    
    def _get_price_positioning(self, product: Dict[str, Any]) -> str:
        """獲取價格定位"""
        tier = self._categorize_price(product)
        if tier == 'premium':
            return "高階定位"
        elif tier == 'mid_range':
            return "中階主流"
        elif tier == 'budget':
            return "經濟實惠"
        return "標準配置"
    
    def _get_product_positioning(self, product: Dict[str, Any]) -> str:
        """獲取產品定位"""
        return f"{self._get_price_positioning(product)}的{self._infer_usage_scenarios(product)}筆電"
    
    def _get_recommendation_context(self, product: Dict[str, Any]) -> str:
        """獲取推薦語境"""
        usage = self._infer_usage(product)
        if usage == 'gaming':
            return "遊戲和高效能"
        elif usage == 'business':
            return "商務和辦公"
        return "日常和專業"
    
    # === 快速實現的評估方法 ===
    
    def _get_cpu_use_cases(self, cpu_tier: str) -> str:
        """獲取CPU適用工作"""
        if cpu_tier == 'high':
            return "重度多工、專業軟體、遊戲"
        elif cpu_tier == 'medium_high':
            return "一般多工、辦公軟體、中度遊戲"
        return "日常辦公、網頁瀏覽、輕度應用"
    
    def _assess_gpu_capability(self, gpu: str) -> str:
        """評估GPU能力"""
        if 'rtx' in gpu.lower():
            return "優秀"
        elif 'gtx' in gpu.lower():
            return "良好"
        return "基本"
    
    def _evaluate_gaming_support(self, gpu: str) -> str:
        """評估遊戲支援"""
        if 'rtx' in gpu.lower():
            return "支援高畫質遊戲"
        elif 'gtx' in gpu.lower():
            return "支援中等畫質遊戲"
        return "支援基本遊戲"
    
    def _assess_multitasking(self, memory: str) -> str:
        """評估多工能力"""
        if '32gb' in memory.lower():
            return "優秀多工處理"
        elif '16gb' in memory.lower():
            return "良好多工處理"
        return "基本多工處理"
    
    def _evaluate_storage_speed(self, storage: str) -> str:
        """評估儲存速度"""
        if 'nvme' in storage.lower():
            return "超高速存取"
        elif 'ssd' in storage.lower():
            return "高速存取"
        return "標準存取"
    
    def _get_performance_summary(self, product: Dict[str, Any]) -> str:
        """獲取效能總結"""
        score = self._calculate_performance_score(product)
        if score >= 8:
            return "表現優異"
        elif score >= 7:
            return "表現良好"
        return "滿足基本需求"
    
    def _get_performance_target_usage(self, product: Dict[str, Any]) -> str:
        """獲取效能目標用途"""
        return self._infer_usage_scenarios(product)
    
    # === 設計相關方法 ===
    
    def _extract_screen_size(self, lcd: str) -> str:
        """提取螢幕尺寸"""
        if '15.6' in lcd:
            return "15.6吋"
        elif '14' in lcd:
            return "14吋"
        elif '13' in lcd:
            return "13.3吋"
        return "標準尺寸"
    
    def _assess_display_quality(self, lcd: str) -> str:
        """評估顯示品質"""
        if 'fhd' in lcd.lower() and '144hz' in lcd.lower():
            return "高刷新率全高清"
        elif 'fhd' in lcd.lower():
            return "全高清顯示"
        return "標準顯示"
    
    def _extract_portability_info(self, product: Dict[str, Any]) -> str:
        """提取便攜性信息"""
        struct = product.get('structconfig', '')
        if '1860' in struct:
            return "適中重量設計"
        return "標準設計"
    
    def _categorize_weight(self, product: Dict[str, Any]) -> str:
        """分類重量等級"""
        struct = product.get('structconfig', '').lower()
        if any(term in struct for term in ['1.3', '1.4', '1.5']):
            return "輕薄"
        elif any(term in struct for term in ['1.6', '1.7', '1.8']):
            return "標準"
        return "厚重"
    
    def _identify_design_style(self, product: Dict[str, Any]) -> str:
        """識別設計風格"""
        modeltype = product.get('modeltype', '')
        if modeltype in ['958']:
            return "商務專業"
        elif modeltype in ['819']:
            return "現代簡約"
        return "實用耐用"
    
    def _extract_battery_info(self, product: Dict[str, Any]) -> str:
        """提取電池信息"""
        battery = product.get('battery', '')
        if '55wh' in battery.lower():
            return "55Wh鋰電池"
        elif '65wh' in battery.lower():
            return "65Wh鋰電池"
        return "標準鋰電池"
    
    def _estimate_battery_life(self, battery: str) -> str:
        """估算電池續航"""
        if '10 hours' in battery.lower():
            return "約10小時"
        elif '8 hours' in battery.lower():
            return "約8小時"
        return "標準續航"
    
    def _extract_io_info(self, product: Dict[str, Any]) -> str:
        """提取I/O信息"""
        io = product.get('iointerface', '')
        if 'usb3' in io.lower() and 'type-c' in io.lower():
            return "豐富連接埠配置"
        return "標準連接埠配置"
    
    def _assess_connectivity(self, io_interface: str) -> str:
        """評估連接能力"""
        if 'hdmi' in io_interface.lower() and 'usb3' in io_interface.lower():
            return "優秀"
        return "良好"
    
    def _get_design_summary(self, product: Dict[str, Any]) -> str:
        """獲取設計總結"""
        return "兼顧美觀與實用性"
    
    def _get_design_target_scenarios(self, product: Dict[str, Any]) -> str:
        """獲取設計目標場景"""
        return "商務出差、日常攜帶"
    
    # === 連接性相關方法 ===
    
    def _extract_wireless_info(self, product: Dict[str, Any]) -> str:
        """提取無線信息"""
        wireless = product.get('wireless', '')
        if 'wifi 5' in wireless.lower():
            return "Wi-Fi 5雙頻無線"
        return "標準無線連接"
    
    def _extract_wifi_standard(self, wireless: str) -> str:
        """提取Wi-Fi標準"""
        if 'wifi 6' in wireless.lower():
            return "Wi-Fi 6"
        elif 'wifi 5' in wireless.lower():
            return "Wi-Fi 5"
        return "標準Wi-Fi"
    
    def _assess_wifi_performance(self, wireless: str) -> str:
        """評估Wi-Fi效能"""
        if 'dual-band' in wireless.lower():
            return "雙頻高速"
        return "標準效能"
    
    def _extract_bluetooth_info(self, product: Dict[str, Any]) -> str:
        """提取藍牙信息"""
        bluetooth = product.get('bluetooth', '')
        if 'bluetooth 5' in bluetooth.lower():
            return "Bluetooth 5.0"
        return "標準藍牙"
    
    def _extract_bluetooth_version(self, bluetooth: str) -> str:
        """提取藍牙版本"""
        if '5.0' in bluetooth:
            return "5.0"
        return "標準版本"
    
    def _extract_lan_info(self, product: Dict[str, Any]) -> str:
        """提取有線網路信息"""
        lan = product.get('lan', '')
        if 'giga' in lan.lower():
            return "Gigabit乙太網路"
        return "標準乙太網路"
    
    def _assess_lan_speed(self, lan: str) -> str:
        """評估有線網路速度"""
        if '1000mbps' in lan.lower():
            return "1000Mbps高速"
        return "標準速度"
    
    def _analyze_io_ports(self, product: Dict[str, Any]) -> str:
        """分析I/O連接埠"""
        return "多樣化連接埠"
    
    def _analyze_usb_ports(self, io_interface: str) -> str:
        """分析USB連接埠"""
        if 'usb3.2' in io_interface.lower():
            return "USB 3.2高速傳輸"
        return "標準USB連接"
    
    def _identify_display_outputs(self, io_interface: str) -> str:
        """識別顯示輸出"""
        if 'hdmi' in io_interface.lower():
            return "HDMI輸出"
        return "標準輸出"
    
    def _extract_wifi_generation(self, wireless: str) -> str:
        """提取Wi-Fi世代"""
        if 'wifi6' in wireless.lower():
            return "wifi6"
        elif 'wifi5' in wireless.lower():
            return "wifi5"
        return "wifi4"
    
    def _analyze_usb_types(self, io_interface: str) -> List[str]:
        """分析USB類型"""
        types = []
        if 'type-a' in io_interface.lower():
            types.append('usb_a')
        if 'type-c' in io_interface.lower():
            types.append('usb_c')
        return types
    
    def _identify_connectivity_needs(self, product: Dict[str, Any]) -> List[str]:
        """識別連接需求"""
        return ["standard_connectivity", "external_display"]
    
    def _get_connectivity_summary(self, product: Dict[str, Any]) -> str:
        """獲取連接性總結"""
        return "提供全面的連接選項"
    
    def _get_connectivity_target_needs(self, product: Dict[str, Any]) -> str:
        """獲取連接目標需求"""
        return "多設備連接和擴充"
    
    # === 商務相關方法 ===
    
    def _extract_certifications(self, product: Dict[str, Any]) -> str:
        """提取認證信息"""
        cert = product.get('certifications', '')
        if cert and cert.strip():
            return cert.split('\n')[0]
        return "標準認證"
    
    def _assess_security_features(self, product: Dict[str, Any]) -> str:
        """評估安全功能"""
        features = []
        if product.get('fingerprint'):
            features.append("指紋識別")
        if product.get('tpm'):
            features.append("TPM安全晶片")
        return ", ".join(features) if features else "基本安全功能"
    
    def _assess_meeting_features(self, product: Dict[str, Any]) -> str:
        """評估會議功能"""
        webcam = product.get('webcamera', '')
        if 'webcamera' in webcam.lower():
            return "支援視訊會議"
        return "基本通訊功能"
    
    def _assess_productivity(self, product: Dict[str, Any]) -> str:
        """評估生產力"""
        return "適合辦公軟體運行"
    
    def _identify_support_features(self, product: Dict[str, Any]) -> str:
        """識別支援功能"""
        return "標準技術支援"
    
    def _assess_enterprise_readiness(self, product: Dict[str, Any]) -> str:
        """評估企業就緒度"""
        return "適合企業部署"
    
    def _assess_security_level(self, product: Dict[str, Any]) -> str:
        """評估安全等級"""
        if product.get('fingerprint') and product.get('tpm'):
            return "enterprise"
        elif product.get('fingerprint') or product.get('tpm'):
            return "standard"
        return "basic"
    
    def _assess_meeting_capability(self, product: Dict[str, Any]) -> str:
        """評估會議能力"""
        if 'webcamera' in str(product.get('webcamera', '')).lower():
            return "good"
        return "basic"
    
    def _identify_business_users(self, product: Dict[str, Any]) -> List[str]:
        """識別商務用戶"""
        return ["business_professional", "office_worker"]
    
    def _get_business_summary(self, product: Dict[str, Any]) -> str:
        """獲取商務總結"""
        return "滿足商務辦公需求"
    
    def _get_business_target_users(self, product: Dict[str, Any]) -> str:
        """獲取商務目標用戶"""
        return "商務人士和辦公用戶"
    
    # === 其他分類方法 ===
    
    def _categorize_screen_size(self, lcd: str) -> str:
        """分類螢幕尺寸"""
        if '15.6' in lcd:
            return "15"
        elif '14' in lcd:
            return "14"
        return "15"
    
    def _identify_design_scenarios(self, product: Dict[str, Any]) -> List[str]:
        """識別設計場景"""
        return ["office_use", "mobile_work"]
    
    def _identify_performance_workloads(self, product: Dict[str, Any]) -> List[str]:
        """識別效能工作負載"""
        usage = self._infer_usage(product)
        if usage == 'gaming':
            return ["gaming", "multimedia"]
        elif usage == 'business':
            return ["office", "productivity"]
        return ["general", "web_browsing"]
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """獲取處理統計"""
        return self.stats.copy()
    
    def get_strategy_type(self) -> ChunkingStrategyType:
        """獲取策略類型"""
        return ChunkingStrategyType.PARENT_CHILD
    
    def get_description(self) -> str:
        """獲取策略描述"""
        return "Parent-Child分層分塊策略，創建產品概覽和四個專業子分塊"