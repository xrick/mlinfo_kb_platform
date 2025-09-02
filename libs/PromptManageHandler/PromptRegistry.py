"""
PromptRegistry - 提示註冊中心
統一管理所有提示模板的載入、緩存和版本控制

主要功能：
1. 自動掃描和載入提示目錄
2. 提示模板緩存和熱重載
3. 提示元數據管理
4. 統一的提示ID命名規範
5. 版本控制和回滾支援
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import hashlib
import asyncio
import aiofiles
import re

logger = logging.getLogger(__name__)


@dataclass
class PromptMetadata:
    """提示模板元數據"""
    prompt_id: str              # 提示唯一ID
    title: str                  # 提示標題
    description: str            # 提示描述
    version: str                # 版本號
    author: str                 # 作者
    created_at: str             # 創建時間
    updated_at: str             # 更新時間
    category: str               # 分類（如：funnel, comparison, technical）
    state_mapping: List[str]    # 適用的對話狀態
    intent_mapping: List[str]   # 適用的用戶意圖
    language: str               # 語言（zh-TW, zh-CN, en）
    priority: int               # 優先級（1-10，10最高）
    content_hash: str           # 內容雜湊值，用於變更檢測
    file_path: str              # 文件路徑
    is_active: bool = True      # 是否啟用
    usage_count: int = 0        # 使用次數統計


class PromptRegistryError(Exception):
    """提示註冊中心相關錯誤"""
    pass


class PromptRegistry:
    """
    提示註冊中心
    
    負責統一管理所有提示模板，提供高效的載入、緩存和查找功能
    """
    
    def __init__(self, 
                 prompts_base_dir: str = None,
                 cache_expiry_hours: int = 24,
                 auto_reload: bool = True):
        """
        初始化提示註冊中心
        
        Args:
            prompts_base_dir: 提示基礎目錄，默認為 HumanData/PromptsHub
            cache_expiry_hours: 緩存過期時間（小時）
            auto_reload: 是否自動重載提示
        """
        # 設定基礎路徑
        if prompts_base_dir is None:
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent
            self.prompts_base_dir = project_root / "HumanData" / "PromptsHub"
        else:
            self.prompts_base_dir = Path(prompts_base_dir)
        
        self.cache_expiry_hours = cache_expiry_hours
        self.auto_reload = auto_reload
        
        # 提示緩存和索引
        self.prompts_cache: Dict[str, str] = {}                    # prompt_id -> content
        self.metadata_cache: Dict[str, PromptMetadata] = {}        # prompt_id -> metadata
        self.category_index: Dict[str, List[str]] = {}             # category -> [prompt_ids]
        self.state_index: Dict[str, List[str]] = {}                # state -> [prompt_ids]
        self.intent_index: Dict[str, List[str]] = {}               # intent -> [prompt_ids]
        self.file_timestamps: Dict[str, float] = {}                # file_path -> timestamp
        
        # 統計信息
        self.stats = {
            "total_prompts": 0,
            "active_prompts": 0,
            "total_usage": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "last_reload": None,
            "load_errors": 0
        }
        
        logger.info(f"PromptRegistry 初始化完成，基礎目錄: {self.prompts_base_dir}")
    
    async def initialize(self) -> Dict[str, Any]:
        """
        初始化註冊中心，掃描並載入所有提示
        
        Returns:
            初始化結果摘要
        """
        try:
            logger.info("開始初始化提示註冊中心...")
            
            # 確保基礎目錄存在
            if not self.prompts_base_dir.exists():
                logger.warning(f"提示目錄不存在，創建: {self.prompts_base_dir}")
                self.prompts_base_dir.mkdir(parents=True, exist_ok=True)
            
            # 掃描並載入所有提示
            scan_result = await self.scan_and_load_prompts()
            
            # 構建索引
            await self._build_indexes()
            
            # 更新統計
            self.stats["last_reload"] = datetime.now().isoformat()
            
            logger.info(f"提示註冊中心初始化完成，載入 {self.stats['total_prompts']} 個提示")
            
            return {
                "success": True,
                "prompts_loaded": self.stats["total_prompts"],
                "active_prompts": self.stats["active_prompts"],
                "categories": list(self.category_index.keys()),
                "scan_result": scan_result,
                "base_directory": str(self.prompts_base_dir)
            }
            
        except Exception as e:
            logger.error(f"初始化提示註冊中心失敗: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "prompts_loaded": 0
            }
    
    async def scan_and_load_prompts(self) -> Dict[str, Any]:
        """
        掃描並載入提示目錄中的所有提示文件
        
        Returns:
            掃描結果摘要
        """
        loaded_count = 0
        error_count = 0
        skipped_count = 0
        
        try:
            # 支援的文件擴展名
            supported_extensions = {'.txt', '.md', '.json'}
            
            # 遞迴掃描所有提示文件
            for file_path in self.prompts_base_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix in supported_extensions:
                    try:
                        # 檢查文件是否需要重載
                        if await self._should_reload_file(file_path):
                            result = await self._load_single_prompt(file_path)
                            if result["success"]:
                                loaded_count += 1
                            else:
                                error_count += 1
                                logger.warning(f"載入提示失敗: {file_path} - {result['error']}")
                        else:
                            skipped_count += 1
                            
                    except Exception as e:
                        error_count += 1
                        logger.error(f"處理提示文件失敗: {file_path} - {e}")
            
            # 更新統計
            self.stats["total_prompts"] = len(self.prompts_cache)
            self.stats["active_prompts"] = len([
                p for p in self.metadata_cache.values() if p.is_active
            ])
            self.stats["load_errors"] += error_count
            
            return {
                "loaded": loaded_count,
                "errors": error_count,
                "skipped": skipped_count,
                "total_in_cache": len(self.prompts_cache)
            }
            
        except Exception as e:
            logger.error(f"掃描提示目錄失敗: {e}")
            return {
                "loaded": 0,
                "errors": 1,
                "skipped": 0,
                "error": str(e)
            }
    
    async def _load_single_prompt(self, file_path: Path) -> Dict[str, Any]:
        """
        載入單個提示文件
        
        Args:
            file_path: 提示文件路徑
            
        Returns:
            載入結果
        """
        try:
            # 生成提示ID
            prompt_id = self._generate_prompt_id(file_path)
            
            # 讀取文件內容
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # 解析元數據（從文件頭註釋或同名 .json 文件）
            metadata = await self._parse_metadata(file_path, content)
            metadata.prompt_id = prompt_id
            metadata.file_path = str(file_path)
            metadata.content_hash = hashlib.md5(content.encode()).hexdigest()
            metadata.updated_at = datetime.now().isoformat()
            
            # 存儲到緩存
            self.prompts_cache[prompt_id] = content
            self.metadata_cache[prompt_id] = metadata
            self.file_timestamps[str(file_path)] = file_path.stat().st_mtime
            
            logger.debug(f"載入提示: {prompt_id} ({metadata.title})")
            
            return {
                "success": True,
                "prompt_id": prompt_id,
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": str(file_path)
            }
    
    def _generate_prompt_id(self, file_path: Path) -> str:
        """
        生成提示唯一ID
        
        基於文件路徑和名稱生成清晰的ID
        例如: PromptsHub/MGFD_Principal_Prompts/MGFD_Principal_Prompt.txt
        -> mgfd_principal_prompt
        """
        # 獲取相對於基礎目錄的路徑
        try:
            relative_path = file_path.relative_to(self.prompts_base_dir)
        except ValueError:
            # 如果文件不在基礎目錄下，使用絕對路徑
            relative_path = file_path
        
        # 組合路徑和文件名（不含擴展名）
        path_parts = list(relative_path.parts[:-1])  # 目錄部分
        file_name = file_path.stem  # 文件名（不含擴展名）
        
        # 清理和標準化
        all_parts = path_parts + [file_name]
        cleaned_parts = []
        
        for part in all_parts:
            # 轉換為小寫，替換非字母數字字符為下劃線
            cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', part.lower())
            # 移除連續的下劃線
            cleaned = re.sub(r'_+', '_', cleaned)
            # 移除開頭和結尾的下劃線
            cleaned = cleaned.strip('_')
            
            if cleaned and cleaned not in ['promptshub', 'prompts']:
                cleaned_parts.append(cleaned)
        
        # 生成最終ID
        prompt_id = '_'.join(cleaned_parts)
        
        # 確保ID不為空
        if not prompt_id:
            prompt_id = f"prompt_{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}"
        
        return prompt_id
    
    async def _parse_metadata(self, file_path: Path, content: str) -> PromptMetadata:
        """
        解析提示元數據
        
        支援多種元數據來源：
        1. 同名 .json 文件
        2. 文件頭部的 YAML 格式註釋
        3. 基於文件路徑的推斷
        """
        # 默認元數據
        metadata = PromptMetadata(
            prompt_id="",  # 會在後面設定
            title=file_path.stem.replace('_', ' ').title(),
            description=f"從 {file_path.name} 載入的提示",
            version="1.0.0",
            author="System",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            category=self._infer_category(file_path),
            state_mapping=self._infer_states(file_path),
            intent_mapping=self._infer_intents(file_path),
            language="zh-TW",
            priority=5,
            content_hash="",
            file_path=str(file_path),
            is_active=True,
            usage_count=0
        )
        
        # 嘗試載入同名 .json 元數據文件
        metadata_file = file_path.with_suffix('.metadata.json')
        if metadata_file.exists():
            try:
                async with aiofiles.open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata_json = json.loads(await f.read())
                    
                # 更新元數據
                for key, value in metadata_json.items():
                    if hasattr(metadata, key):
                        setattr(metadata, key, value)
                        
                logger.debug(f"載入元數據文件: {metadata_file}")
                
            except Exception as e:
                logger.warning(f"解析元數據文件失敗: {metadata_file} - {e}")
        
        # 嘗試從文件內容解析元數據（YAML 前置區塊）
        try:
            if content.startswith('---\n'):
                yaml_end = content.find('\n---\n', 4)
                if yaml_end > 0:
                    yaml_content = content[4:yaml_end]
                    # 簡單的 YAML 解析（只支援基本鍵值對）
                    for line in yaml_content.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            
                            if hasattr(metadata, key):
                                # 嘗試轉換數據類型
                                if key in ['state_mapping', 'intent_mapping']:
                                    value = [v.strip() for v in value.split(',')]
                                elif key == 'priority':
                                    value = int(value)
                                elif key == 'is_active':
                                    value = value.lower() in ['true', 'yes', '1']
                                
                                setattr(metadata, key, value)
        
        except Exception as e:
            logger.debug(f"解析文件頭元數據失敗: {e}")
        
        return metadata
    
    def _infer_category(self, file_path: Path) -> str:
        """根據文件路徑推斷提示分類"""
        path_str = str(file_path).lower()
        
        if 'principal' in path_str or 'main' in path_str:
            return 'principal'
        elif 'funnel' in path_str or 'collect' in path_str:
            return 'funnel'
        elif 'comparison' in path_str or 'compare' in path_str:
            return 'comparison'
        elif 'technical' in path_str or 'spec' in path_str:
            return 'technical'
        elif 'greeting' in path_str or 'welcome' in path_str or 'recept' in path_str:
            return 'greeting'
        elif 'sales' in path_str:
            return 'sales'
        else:
            return 'general'
    
    def _infer_states(self, file_path: Path) -> List[str]:
        """根據文件路徑推斷適用的對話狀態"""
        path_str = str(file_path).lower()
        states = []
        
        if 'principal' in path_str:
            states.extend(['INIT', 'FUNNEL_START', 'RECOMMENDATION_PRESENTATION'])
        elif 'funnel' in path_str or 'collect' in path_str:
            states.extend(['FUNNEL_QUESTION', 'ELICITATION'])
        elif 'comparison' in path_str:
            states.extend(['RECOMMENDATION_PRESENTATION', 'PRODUCT_QA'])
        elif 'greeting' in path_str or 'recept' in path_str:
            states.extend(['INIT', 'FUNNEL_START'])
        elif 'sales' in path_str:
            states.extend(['RECOMMENDATION_PRESENTATION', 'PRODUCT_QA', 'PURCHASE_GUIDANCE'])
        
        return states
    
    def _infer_intents(self, file_path: Path) -> List[str]:
        """根據文件路徑推斷適用的用戶意圖"""
        path_str = str(file_path).lower()
        intents = []
        
        if 'comparison' in path_str:
            intents.extend(['ask_comparison', 'ask_specs'])
        elif 'price' in path_str:
            intents.extend(['ask_price'])
        elif 'recommendation' in path_str:
            intents.extend(['ask_recommendation'])
        elif 'greeting' in path_str:
            intents.extend(['greet'])
        elif 'technical' in path_str:
            intents.extend(['ask_specs', 'technical_question'])
        
        return intents
    
    async def _should_reload_file(self, file_path: Path) -> bool:
        """
        檢查文件是否需要重載
        
        基於文件修改時間和緩存狀態判斷
        """
        file_path_str = str(file_path)
        
        # 如果文件未在緩存中，需要載入
        if file_path_str not in self.file_timestamps:
            return True
        
        # 如果不啟用自動重載，跳過
        if not self.auto_reload:
            return False
        
        try:
            current_mtime = file_path.stat().st_mtime
            cached_mtime = self.file_timestamps[file_path_str]
            
            # 文件已修改
            if current_mtime > cached_mtime:
                logger.debug(f"檢測到文件更新: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"檢查文件修改時間失敗: {file_path} - {e}")
            return False
    
    async def _build_indexes(self):
        """構建各種索引以提升查詢性能"""
        self.category_index.clear()
        self.state_index.clear()
        self.intent_index.clear()
        
        for prompt_id, metadata in self.metadata_cache.items():
            if not metadata.is_active:
                continue
            
            # 分類索引
            category = metadata.category
            if category not in self.category_index:
                self.category_index[category] = []
            self.category_index[category].append(prompt_id)
            
            # 狀態索引
            for state in metadata.state_mapping:
                if state not in self.state_index:
                    self.state_index[state] = []
                self.state_index[state].append(prompt_id)
            
            # 意圖索引
            for intent in metadata.intent_mapping:
                if intent not in self.intent_index:
                    self.intent_index[intent] = []
                self.intent_index[intent].append(prompt_id)
        
        logger.debug(f"索引構建完成: {len(self.category_index)} 分類, "
                    f"{len(self.state_index)} 狀態, {len(self.intent_index)} 意圖")
    
    async def get_prompt(self, prompt_id: str) -> Optional[str]:
        """
        獲取提示內容
        
        Args:
            prompt_id: 提示ID
            
        Returns:
            提示內容，如果不存在則返回 None
        """
        if prompt_id in self.prompts_cache:
            # 更新使用統計
            if prompt_id in self.metadata_cache:
                self.metadata_cache[prompt_id].usage_count += 1
            self.stats["cache_hits"] += 1
            self.stats["total_usage"] += 1
            
            return self.prompts_cache[prompt_id]
        
        self.stats["cache_misses"] += 1
        logger.warning(f"提示不存在: {prompt_id}")
        return None
    
    async def get_metadata(self, prompt_id: str) -> Optional[PromptMetadata]:
        """
        獲取提示元數據
        
        Args:
            prompt_id: 提示ID
            
        Returns:
            提示元數據，如果不存在則返回 None
        """
        return self.metadata_cache.get(prompt_id)
    
    async def list_prompts_by_category(self, category: str) -> List[str]:
        """
        根據分類列出提示ID
        
        Args:
            category: 分類名稱
            
        Returns:
            提示ID列表
        """
        return self.category_index.get(category, [])
    
    async def list_prompts_by_state(self, state: str) -> List[str]:
        """
        根據對話狀態列出適用的提示ID
        
        Args:
            state: 對話狀態
            
        Returns:
            提示ID列表
        """
        return self.state_index.get(state, [])
    
    async def list_prompts_by_intent(self, intent: str) -> List[str]:
        """
        根據用戶意圖列出適用的提示ID
        
        Args:
            intent: 用戶意圖
            
        Returns:
            提示ID列表
        """
        return self.intent_index.get(intent, [])
    
    async def register_prompt(
        self, 
        prompt_id: str, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        動態註冊新提示
        
        Args:
            prompt_id: 提示ID
            content: 提示內容
            metadata: 元數據字典
            
        Returns:
            註冊結果
        """
        try:
            # 創建元數據對象
            prompt_metadata = PromptMetadata(
                prompt_id=prompt_id,
                title=metadata.get('title', prompt_id),
                description=metadata.get('description', '動態註冊的提示'),
                version=metadata.get('version', '1.0.0'),
                author=metadata.get('author', 'System'),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                category=metadata.get('category', 'general'),
                state_mapping=metadata.get('state_mapping', []),
                intent_mapping=metadata.get('intent_mapping', []),
                language=metadata.get('language', 'zh-TW'),
                priority=metadata.get('priority', 5),
                content_hash=hashlib.md5(content.encode()).hexdigest(),
                file_path='dynamic',
                is_active=metadata.get('is_active', True),
                usage_count=0
            )
            
            # 存儲到緩存
            self.prompts_cache[prompt_id] = content
            self.metadata_cache[prompt_id] = prompt_metadata
            
            # 重建索引
            await self._build_indexes()
            
            # 更新統計
            self.stats["total_prompts"] = len(self.prompts_cache)
            
            logger.info(f"動態註冊提示: {prompt_id}")
            
            return {
                "success": True,
                "prompt_id": prompt_id,
                "message": "提示註冊成功"
            }
            
        except Exception as e:
            logger.error(f"註冊提示失敗: {prompt_id} - {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def reload_prompts(self) -> Dict[str, Any]:
        """
        手動重載所有提示
        
        Returns:
            重載結果摘要
        """
        logger.info("開始手動重載提示...")
        
        # 清空緩存
        old_count = len(self.prompts_cache)
        self.prompts_cache.clear()
        self.metadata_cache.clear()
        self.file_timestamps.clear()
        
        # 重新掃描載入
        scan_result = await self.scan_and_load_prompts()
        await self._build_indexes()
        
        # 更新統計
        self.stats["last_reload"] = datetime.now().isoformat()
        
        new_count = len(self.prompts_cache)
        logger.info(f"提示重載完成: {old_count} -> {new_count}")
        
        return {
            "success": True,
            "old_count": old_count,
            "new_count": new_count,
            "scan_result": scan_result,
            "reload_time": self.stats["last_reload"]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        獲取註冊中心統計信息
        
        Returns:
            統計信息字典
        """
        return {
            **self.stats,
            "categories": list(self.category_index.keys()),
            "states_covered": list(self.state_index.keys()),
            "intents_covered": list(self.intent_index.keys()),
            "cache_hit_rate": (
                self.stats["cache_hits"] / 
                max(self.stats["cache_hits"] + self.stats["cache_misses"], 1)
            ),
            "timestamp": datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康檢查
        
        Returns:
            健康狀態信息
        """
        try:
            # 檢查基礎目錄
            base_dir_exists = self.prompts_base_dir.exists()
            
            # 檢查緩存狀態
            cache_healthy = len(self.prompts_cache) > 0
            
            # 檢查索引狀態
            indexes_healthy = (
                len(self.category_index) > 0 or
                len(self.state_index) > 0 or
                len(self.intent_index) > 0
            )
            
            # 總體健康狀態
            is_healthy = base_dir_exists and cache_healthy
            
            return {
                "healthy": is_healthy,
                "base_directory_exists": base_dir_exists,
                "cache_healthy": cache_healthy,
                "indexes_healthy": indexes_healthy,
                "total_prompts": len(self.prompts_cache),
                "active_prompts": self.stats["active_prompts"],
                "last_reload": self.stats["last_reload"],
                "load_errors": self.stats["load_errors"]
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }