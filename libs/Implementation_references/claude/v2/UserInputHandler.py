# libs/Implementation_references/claude/v2/UserInputHandler.py
"""
用戶輸入處理器 - 智能解析自然語言為結構化數據
基於 default_slots.json 的11個核心槽位和 default_keywords.json 的同義詞進行智能匹配
"""

import logging
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

###setup debug
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class UserInputHandler:
    """
    用戶輸入處理器
    職責：解析自然語言輸入為意圖與槽位，基於 keywords.json 進行智能匹配
    """
    
    def __init__(self) -> None:
        """初始化用戶輸入處理器"""
        self.slot_schema = self._load_slot_schema()
        self.keywords_data = self._load_keywords()
        self.intent_classifier = self._load_intent_classifier()
        self.slot_extractor = self._build_slot_extractor()
        
        logger.info("UserInputHandler 初始化完成")
    
    def _load_slot_schema(self) -> Dict[str, str]:
        """載入槽位架構定義"""
        try:
            # 從 default_keywords.json 載入 mapping 欄位
            keywords_path = Path(__file__).parent.parent.parent.parent.parent / "HumanData" / "SlotHub" / "default_keywords.json"
            if keywords_path.exists():
                with open(keywords_path, 'r', encoding='utf-8') as f:
                    keywords_data = json.load(f)
                slot_mapping = keywords_data.get("mapping", {})
                logger.info(f"成功載入槽位映射，包含 {len(slot_mapping)} 個槽位")
                return slot_mapping
            else:
                logger.warning(f"關鍵詞文件不存在: {keywords_path}")
                # 使用預設映射
                return {
                    "用途": "usage_purpose",
                    "價格區間": "price_range",
                    "推出時間": "release_time",
                    "CPU效能": "cpu_performance",
                    "GPU效能": "gpu_performance",
                    "重量": "weight",
                    "攜帶性": "portability",
                    "開關機速度": "boot_speed",
                    "螢幕尺寸": "screen_size",
                    "品牌": "brand",
                    "觸控螢幕": "touch_screen"
                }
        except Exception as e:
            logger.error(f"載入槽位架構失敗: {e}")
            return {}

    def _load_mgfd_sys_configure(self) -> Dict[str, str]:
        """載入槽位架構定義"""
        try:
            # 從 default_keywords.json 載入 mapping 欄位
            keywords_path = Path(__file__).parent.parent.parent.parent.parent / "HumanData" / "mgfd_exec_config.json"
            logger.info("*************載入mgfd_exec_config.json*************")
            if keywords_path.exists():
                with open(keywords_path, 'r', encoding='utf-8') as f:
                    keywords_data = json.load(f)
                slot_mapping = keywords_data.get("mapping", {})
                logger.info(f"成功載入槽位映射，包含 {len(slot_mapping)} 個槽位")
                return slot_mapping
            else:
                logger.warning(f"關鍵詞文件不存在: {keywords_path}")
                # 使用預設映射
                return {
                    "用途": "usage_purpose",
                    "價格區間": "price_range",
                    "推出時間": "release_time",
                    "CPU效能": "cpu_performance",
                    "GPU效能": "gpu_performance",
                    "重量": "weight",
                    "攜帶性": "portability",
                    "開關機速度": "boot_speed",
                    "螢幕尺寸": "screen_size",
                    "品牌": "brand",
                    "觸控螢幕": "touch_screen"
                }
        except Exception as e:
            logger.error(f"載入槽位架構失敗: {e}")
            return {}
    
    def _load_keywords(self) -> Dict[str, Dict[str, Any]]:
        """載入 default_keywords.json 中的關鍵詞數據"""
        try:
            # 嘗試從 HumanData/SlotHub/default_keywords.json 載入
            keywords_path = Path(__file__).parent.parent.parent.parent.parent / "HumanData" / "SlotHub" / "default_keywords.json"
            if keywords_path.exists():
                with open(keywords_path, 'r', encoding='utf-8') as f:
                    keywords_data = json.load(f)
                logger.info(f"成功載入關鍵詞數據，包含 {len(keywords_data)} 個槽位")
                return keywords_data
            else:
                logger.warning(f"關鍵詞文件不存在: {keywords_path}")
                return {}
        except Exception as e:
            logger.error(f"載入關鍵詞數據失敗: {e}")
            return {}
    
    def _load_intent_classifier(self) -> Dict[str, List[str]]:
        """載入意圖分類器"""
        # 基於 recept_guest_prompt1.txt 的對話模式定義意圖
        intents = {
            "greet": ["你好", "您好", "hi", "hello", "哈囉", "嗨"],
            "ask_recommendation": ["推薦", "建議", "找", "買", "要", "想", "需要", "尋找"],
            "ask_comparison": ["比較", "對比", "差異", "哪個好", "哪個比較", "有什麼不同"],
            "provide_info": ["用來", "做", "玩", "工作", "學習", "上課", "遊戲", "辦公"],
            "clarify": ["什麼意思", "不懂", "解釋", "說明", "詳細"],
            "restart": ["重新開始", "重來", "reset", "重新", "從頭"],
            "goodbye": ["再見", "謝謝", "bye", "拜拜", "結束"],
            "confirm": ["對", "是的", "沒錯", "正確", "ok", "好"],
            "deny": ["不是", "不對", "錯誤", "不要", "no"]
        }
        return intents
    
    def _build_slot_extractor(self) -> Dict[str, Dict[str, Any]]:
        """構建槽位抽取器"""
        extractor = {}
        
        for slot_name, slot_data in self.keywords_data.items():
            if slot_name in self.slot_schema:
                english_slot_name = self.slot_schema[slot_name]
                extractor[english_slot_name] = {
                    "chinese_name": slot_name,
                    "synonyms": slot_data.get("synonyms", []),
                    "regex": slot_data.get("metadata", {}).get("regex", ""),
                    "metadata": slot_data.get("metadata", {})
                }
        
        logger.info(f"構建槽位抽取器完成，包含 {len(extractor)} 個槽位")
        return extractor
    
    async def parse(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析用戶輸入
        
        Args:
            message: 用戶輸入消息
            context: 當前上下文
            
        Returns:
            解析結果字典，包含：
            - intent: 識別出的意圖
            - slots_update: 槽位更新
            - control: 控制指令
            - errors: 錯誤信息
            - confidence: 置信度
        """
        try:
            logger.info(f"開始解析用戶輸入: {message[:50]}...")
            
            # Step 1: 意圖分類
            intent = await self._classify_intent(message, context)
            
            # Step 2: 槽位抽取
            slots_update = await self._extract_slots(message, context)
            
            # Step 3: 控制邏輯判斷
            control = await self._determine_control(intent, slots_update, context)
            
            # Step 4: 錯誤處理
            errors = await self._validate_input(message, intent, slots_update)
            
            # Step 5: 計算置信度
            confidence = self._calculate_confidence(intent, slots_update)
            
            result = {
                "intent": intent,
                "slots_update": slots_update,
                "control": control,
                "errors": errors,
                "confidence": confidence
            }
            
            logger.info(f"解析完成 - 意圖: {intent}, 槽位: {len(slots_update)}, 置信度: {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"解析用戶輸入時發生錯誤: {e}", exc_info=True)
            return {
                "intent": "unknown",
                "slots_update": {},
                "control": {},
                "errors": [f"解析錯誤: {str(e)}"],
                "confidence": 0.0
            }
    
    async def _classify_intent(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> str:
        """
        意圖分類
        
        Args:
            message: 用戶輸入消息
            context: 當前上下文
            
        Returns:
            識別出的意圖字符串
        """
        message_lower = message.lower()
        
        # 計算每個意圖的匹配分數
        intent_scores = {}
        for intent, keywords in self.intent_classifier.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    score += 1
            if score > 0:
                intent_scores[intent] = score
        
        # 選擇分數最高的意圖
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
            logger.debug(f"意圖分類結果: {best_intent} (分數: {intent_scores[best_intent]})")
            return best_intent
        else:
            logger.debug("未識別出明確意圖，返回 unknown")
            return "unknown"
    
    async def _extract_slots(
        self, 
        message: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        槽位抽取 - 基於 default_keywords.json 進行智能匹配
        
        Args:
            message: 用戶輸入消息
            context: 當前上下文
            
        Returns:
            抽取的槽位字典
        """
        slots_update = {}
        
        for slot_name, slot_info in self.slot_extractor.items():
            extracted_value = self._extract_slot_value(message, slot_name, slot_info)
            if extracted_value:
                slots_update[slot_name] = extracted_value
                logger.debug(f"抽取槽位 {slot_name}: {extracted_value}")
        
        return slots_update
    
    def _extract_slot_value(
        self, 
        message: str, 
        slot_name: str, 
        slot_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        抽取特定槽位值 - 基於 default_keywords.json 的同義詞和正則表達式
        
        Args:
            message: 用戶輸入消息
            slot_name: 槽位名稱（英文）
            slot_info: 槽位信息（包含同義詞、正則表達式等）
            
        Returns:
            抽取的槽位值
        """
        message_lower = message.lower()
        synonyms = slot_info.get("synonyms", [])
        regex_pattern = slot_info.get("regex", "")
        chinese_name = slot_info.get("chinese_name", "")
        
        # 方法1: 直接匹配中文名稱
        if chinese_name and chinese_name.lower() in message_lower:
            return self._extract_value_after_keyword(message, chinese_name)
        
        # 方法2: 匹配同義詞
        for synonym in synonyms:
            if synonym.lower() in message_lower:
                return self._extract_value_after_keyword(message, synonym)
        
        # 方法3: 使用正則表達式匹配
        if regex_pattern:
            try:
                matches = re.findall(regex_pattern, message, re.IGNORECASE)
                if matches:
                    return matches[0] if isinstance(matches[0], str) else matches[0][0]
            except re.error as e:
                logger.warning(f"正則表達式錯誤 {regex_pattern}: {e}")
        
        # 方法4: 特殊槽位的智能抽取
        return self._extract_special_slot_value(message, slot_name, slot_info)
    
    def _extract_value_after_keyword(
        self, 
        message: str, 
        keyword: str
    ) -> Optional[str]:
        """
        從關鍵詞後提取值
        
        Args:
            message: 用戶輸入消息
            keyword: 關鍵詞
            
        Returns:
            提取的值
        """
        try:
            # 找到關鍵詞的位置
            keyword_pos = message.lower().find(keyword.lower())
            if keyword_pos == -1:
                return None
            
            # 提取關鍵詞後的內容
            after_keyword = message[keyword_pos + len(keyword):].strip()
            
            # 如果後面有內容，返回第一個詞或短語
            if after_keyword:
                # 移除常見的標點符號
                after_keyword = re.sub(r'^[，。、：；！？\s]+', '', after_keyword)
                if after_keyword:
                    # 取第一個詞或短語（到標點符號為止）
                    match = re.match(r'^([^，。、：；！？\s]+)', after_keyword)
                    if match:
                        return match.group(1)
            
            # 如果沒有明確的值，返回關鍵詞本身作為標記
            return keyword
            
        except Exception as e:
            logger.warning(f"提取關鍵詞後的值時發生錯誤: {e}")
            return None
    
    def _extract_special_slot_value(
        self, 
        message: str, 
        slot_name: str, 
        slot_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        特殊槽位的智能抽取
        
        Args:
            message: 用戶輸入消息
            slot_name: 槽位名稱
            slot_info: 槽位信息
            
        Returns:
            抽取的值
        """
        message_lower = message.lower()
        
        # 根據槽位類型進行特殊處理
        if slot_name == "usage_purpose":
            return self._extract_usage_purpose(message_lower)
        elif slot_name == "price_range":
            return self._extract_price_range(message_lower)
        elif slot_name == "weight":
            return self._extract_weight(message_lower)
        elif slot_name == "screen_size":
            return self._extract_screen_size(message_lower)
        elif slot_name == "brand":
            return self._extract_brand(message_lower)
        
        return None
    
    def _extract_usage_purpose(self, message: str) -> Optional[str]:
        """抽取用途目的"""
        usage_keywords = {
            "工作": ["工作", "辦公", "文書", "簡報", "會議"],
            "學習": ["學習", "上課", "作業", "報告", "研究"],
            "遊戲": ["遊戲", "電競", "玩", "娛樂", "gaming"],
            "創意": ["設計", "剪輯", "繪圖", "創作", "編輯"]
        }
        
        for purpose, keywords in usage_keywords.items():
            if any(keyword in message for keyword in keywords):
                return purpose
        
        return None
    
    def _extract_price_range(self, message: str) -> Optional[str]:
        """抽取價格範圍"""
        # 匹配價格範圍模式
        price_patterns = [
            (r'(\d+)[萬千]?以下', 'budget_low'),
            (r'(\d+)[萬千]?到(\d+)[萬千]?', 'budget_mid'),
            (r'(\d+)[萬千]?以上', 'budget_high'),
            (r'便宜', 'budget_low'),
            (r'中等', 'budget_mid'),
            (r'高級', 'budget_high')
        ]
        
        for pattern, range_type in price_patterns:
            if re.search(pattern, message):
                return range_type
        
        return None
    
    def _extract_weight(self, message: str) -> Optional[str]:
        """抽取重量信息"""
        weight_patterns = [
            (r'(\d+\.?\d*)公斤', 'heavy'),
            (r'(\d+\.?\d*)kg', 'heavy'),
            (r'輕', 'light'),
            (r'重', 'heavy')
        ]
        
        for pattern, weight_type in weight_patterns:
            if re.search(pattern, message):
                return weight_type
        
        return None
    
    def _extract_screen_size(self, message: str) -> Optional[str]:
        """抽取螢幕尺寸"""
        size_patterns = [
            (r'(\d+\.?\d*)寸', 'large'),
            (r'(\d+\.?\d*)吋', 'large'),
            (r'大螢幕', 'large'),
            (r'小螢幕', 'small')
        ]
        
        for pattern, size_type in size_patterns:
            if re.search(pattern, message):
                return size_type
        
        return None
    
    def _extract_brand(self, message: str) -> Optional[str]:
        """抽取品牌信息"""
        brand_keywords = ["華碩", "ASUS", "宏碁", "ACER", "聯想", "Lenovo", "戴爾", "Dell", "惠普", "HP"]
        
        for brand in brand_keywords:
            if brand.lower() in message:
                return brand
        
        return None
    
    async def _determine_control(
        self, 
        intent: str, 
        slots_update: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        確定控制指令
        
        Args:
            intent: 識別出的意圖
            slots_update: 槽位更新
            context: 當前上下文
            
        Returns:
            控制指令字典
        """
        control = {}
        
        # 檢查是否需要啟動漏斗對話
        current_slots = context.get('slots', {})
        all_slots = {**current_slots, **slots_update}
        
        # 如果關鍵槽位不足，啟動漏斗
        key_slots = ['usage_purpose', 'price_range']
        filled_key_slots = sum(1 for slot in key_slots if slot in all_slots and all_slots[slot])
        
        if filled_key_slots < 2 and intent in ['ask_recommendation', 'provide_info']:
            control['start_funnel'] = True
            logger.info("檢測到關鍵槽位不足，啟動漏斗對話")
        
        # 檢查是否需要重新開始
        if intent == 'restart':
            control['reset_session'] = True
            logger.info("檢測到重新開始意圖")
        
        # 檢查是否需要澄清
        if intent == 'clarify':
            control['need_clarification'] = True
            logger.info("檢測到澄清需求")
        
        return control
    
    async def _validate_input(
        self, 
        message: str, 
        intent: str, 
        slots_update: Dict[str, Any]
    ) -> List[str]:
        """
        輸入驗證
        
        Args:
            message: 用戶輸入消息
            intent: 識別出的意圖
            slots_update: 槽位更新
            
        Returns:
            錯誤信息列表
        """
        errors = []
        
        # 檢查消息長度
        if len(message.strip()) == 0:
            errors.append("輸入消息不能為空")
        
        # 檢查消息長度限制
        if len(message) > 1000:
            errors.append("輸入消息過長，請簡化描述")
        
        # 檢查意圖識別
        if intent == "unknown":
            errors.append("無法識別您的意圖，請重新描述")
        
        # 檢查槽位抽取結果
        if not slots_update and intent in ['ask_recommendation', 'provide_info']:
            errors.append("無法提取到相關信息，請提供更多細節")
        
        return errors
    
    def _calculate_confidence(
        self, 
        intent: str, 
        slots_update: Dict[str, Any]
    ) -> float:
        """
        計算置信度
        
        Args:
            intent: 識別出的意圖
            slots_update: 槽位更新
            
        Returns:
            置信度分數 (0.0-1.0)
        """
        confidence = 0.0
        
        # 意圖置信度
        if intent != "unknown":
            confidence += 0.4
        
        # 槽位抽取置信度
        if slots_update:
            confidence += min(len(slots_update) * 0.2, 0.4)
        
        # 特殊情況調整
        if intent in ['greet', 'goodbye']:
            confidence = 0.9  # 問候和告別通常很明確
        
        return min(confidence, 1.0)
    
    def get_slot_info(self, slot_name: str) -> Optional[Dict[str, Any]]:
        """
        獲取槽位信息
        
        Args:
            slot_name: 槽位名稱
            
        Returns:
            槽位信息字典
        """
        return self.slot_extractor.get(slot_name)
    
    def get_all_slots(self) -> List[str]:
        """
        獲取所有槽位名稱
        
        Returns:
            槽位名稱列表
        """
        return list(self.slot_extractor.keys())
    
    def get_slot_synonyms(self, slot_name: str) -> List[str]:
        """
        獲取槽位的同義詞列表
        
        Args:
            slot_name: 槽位名稱
            
        Returns:
            同義詞列表
        """
        slot_info = self.get_slot_info(slot_name)
        if slot_info:
            return slot_info.get("synonyms", [])
        return []
