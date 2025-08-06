#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
對話鍊生成器
負責根據不同策略生成隨機排列的NB特點對話鍊
"""

import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .models import ChatChain, generate_id

class ChatGenerator:
    """對話鍊生成器"""
    
    def __init__(self, features_config_path: str = None, chats_storage_path: str = None):
        """
        初始化對話鍊生成器
        
        Args:
            features_config_path: NB特點配置檔案路徑  
            chats_storage_path: 對話鍊儲存檔案路徑
        """
        self.features_config_path = features_config_path or self._get_default_features_path()
        self.chats_storage_path = chats_storage_path or self._get_default_chats_path()
        
        self.features_config = self._load_features_config()
        self.feature_ids = list(self.features_config.get("nb_features", {}).keys())
        self.feature_priorities = self.features_config.get("feature_priorities", {})
        
        logging.info(f"對話鍊生成器初始化完成，支援特點: {self.feature_ids}")
    
    def _get_default_features_path(self) -> str:
        """獲取預設特點配置路徑"""
        return str(Path(__file__).parent / "nb_features.json")
    
    def _get_default_chats_path(self) -> str:
        """獲取預設對話鍊儲存路徑"""
        return str(Path(__file__).parent / "chats.json")
    
    def _load_features_config(self) -> Dict:
        """載入NB特點配置"""
        try:
            with open(self.features_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logging.info(f"成功載入特點配置: {list(config.get('nb_features', {}).keys())}")
                return config
        except FileNotFoundError:
            logging.error(f"特點配置檔案不存在: {self.features_config_path}")
            return {"nb_features": {}, "feature_priorities": {}}
        except Exception as e:
            logging.error(f"載入特點配置失敗: {e}")
            return {"nb_features": {}, "feature_priorities": {}}
    
    def generate_random_chain(self, strategy: str = "random") -> ChatChain:
        """
        生成隨機對話鍊
        
        Args:
            strategy: 生成策略 ("random", "priority_based", "user_history")
            
        Returns:
            ChatChain: 生成的對話鍊
        """
        try:
            if strategy == "random":
                features_order = self._generate_random_order()
            elif strategy == "priority_based":
                features_order = self._generate_priority_based_order()
            elif strategy == "user_history":
                features_order = self._generate_user_history_based_order()
            else:
                logging.warning(f"未知策略 {strategy}，使用隨機策略")
                features_order = self._generate_random_order()
            
            chain = ChatChain(
                chain_id=generate_id(),
                features_order=features_order,
                strategy=strategy,
                created_at=datetime.now().isoformat(),
                status="active"
            )
            
            logging.info(f"生成對話鍊: {chain.chain_id}, 策略: {strategy}, 順序: {features_order}")
            return chain
            
        except Exception as e:
            logging.error(f"生成對話鍊失敗: {e}")
            raise
    
    def _generate_random_order(self) -> List[str]:
        """生成完全隨機的特點順序"""
        order = self.feature_ids.copy()
        random.shuffle(order)
        return order
    
    def _generate_priority_based_order(self, scenario: str = "general") -> List[str]:
        """
        基於優先級生成順序
        
        Args:
            scenario: 使用場景 ("gaming", "business", "creation", "study", "general")
            
        Returns:
            排序後的特點列表
        """
        priority_order = self.feature_priorities.get(scenario, self.feature_ids)
        
        # 確保所有特點都包含
        missing_features = set(self.feature_ids) - set(priority_order)
        if missing_features:
            priority_order.extend(list(missing_features))
        
        # 在優先級基礎上增加一些隨機性
        return self._add_randomness_to_priority(priority_order)
    
    def _add_randomness_to_priority(self, priority_order: List[str]) -> List[str]:
        """在優先級順序基礎上增加隨機性"""
        result = []
        
        # 前3個保持較高優先級，但可能有輕微調整
        high_priority = priority_order[:3]
        random.shuffle(high_priority)
        result.extend(high_priority)
        
        # 中間的特點完全隨機
        mid_priority = priority_order[3:6]
        random.shuffle(mid_priority)
        result.extend(mid_priority)
        
        # 最後的特點
        low_priority = priority_order[6:]
        random.shuffle(low_priority)
        result.extend(low_priority)
        
        return result
    
    def _generate_user_history_based_order(self) -> List[str]:
        """基於使用者歷史偏好生成順序（未來擴展功能）"""
        # 目前暫時使用隨機策略，未來可結合使用者歷史資料
        logging.info("使用者歷史策略尚未實作，使用隨機策略")
        return self._generate_random_order()
    
    def generate_multiple_chains(self, count: int = 5, strategies: List[str] = None) -> List[ChatChain]:
        """
        生成多條對話鍊
        
        Args:
            count: 生成數量
            strategies: 使用的策略列表
            
        Returns:
            對話鍊列表
        """
        if strategies is None:
            strategies = ["random", "priority_based"]
        
        chains = []
        for i in range(count):
            strategy = strategies[i % len(strategies)]
            chain = self.generate_random_chain(strategy)
            chains.append(chain)
        
        logging.info(f"生成 {len(chains)} 條對話鍊")
        return chains
    
    def save_chains_to_file(self, chains: List[ChatChain]) -> bool:
        """
        將對話鍊儲存到檔案
        
        Args:
            chains: 對話鍊列表
            
        Returns:
            是否儲存成功
        """
        try:
            # 載入現有對話鍊
            existing_chains = self._load_existing_chains()
            
            # 轉換為字典格式
            chains_data = []
            for chain in chains:
                chains_data.append({
                    "chain_id": chain.chain_id,
                    "features_order": chain.features_order,
                    "strategy": chain.strategy,
                    "created_at": chain.created_at,
                    "status": chain.status
                })
            
            # 合併現有和新的對話鍊
            all_chains = existing_chains + chains_data
            
            # 保持最近的100條記錄
            if len(all_chains) > 100:
                all_chains = all_chains[-100:]
            
            # 儲存到檔案
            output_data = {
                "chat_chains": all_chains,
                "metadata": {
                    "total_chains": len(all_chains),
                    "last_updated": datetime.now().isoformat(),
                    "generator_version": "1.0.0"
                }
            }
            
            with open(self.chats_storage_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"成功儲存 {len(chains)} 條對話鍊到 {self.chats_storage_path}")
            return True
            
        except Exception as e:
            logging.error(f"儲存對話鍊失敗: {e}")
            return False
    
    def _load_existing_chains(self) -> List[Dict]:
        """載入現有對話鍊"""
        try:
            with open(self.chats_storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("chat_chains", [])
        except FileNotFoundError:
            logging.info("對話鍊檔案不存在，將建立新檔案")
            return []
        except Exception as e:
            logging.error(f"載入現有對話鍊失敗: {e}")
            return []
    
    def get_random_chain(self, strategy: str = "random") -> ChatChain:
        """
        獲取一條隨機對話鍊（不儲存到檔案）
        
        Args:
            strategy: 生成策略
            
        Returns:
            對話鍊
        """
        return self.generate_random_chain(strategy)
    
    def get_chain_by_scenario(self, scenario: str) -> ChatChain:
        """
        根據使用場景獲取適合的對話鍊
        
        Args:
            scenario: 使用場景 ("gaming", "business", "creation", "study")
            
        Returns:
            對話鍊
        """
        return self.generate_random_chain("priority_based")
    
    def validate_chain(self, chain: ChatChain) -> bool:
        """
        驗證對話鍊的有效性
        
        Args:
            chain: 要驗證的對話鍊
            
        Returns:
            是否有效
        """
        # 檢查是否包含所有必要特點
        required_features = set(self.feature_ids)
        chain_features = set(chain.features_order)
        
        if not required_features.issubset(chain_features):
            missing = required_features - chain_features
            logging.error(f"對話鍊缺少必要特點: {missing}")
            return False
        
        # 檢查是否有重複特點
        if len(chain.features_order) != len(set(chain.features_order)):
            logging.error("對話鍊包含重複特點")
            return False
        
        return True

def main():
    """測試功能"""
    generator = ChatGenerator()
    
    # 生成幾條測試對話鍊
    chains = generator.generate_multiple_chains(count=10)
    
    # 儲存到檔案
    success = generator.save_chains_to_file(chains)
    
    if success:
        print("✅ 對話鍊生成並儲存成功")
        for i, chain in enumerate(chains[:3], 1):
            print(f"對話鍊 {i}: {' -> '.join(chain.features_order)}")
    else:
        print("❌ 對話鍊儲存失敗")

if __name__ == "__main__":
    main()