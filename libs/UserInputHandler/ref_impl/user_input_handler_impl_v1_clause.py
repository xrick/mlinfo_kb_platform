import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# 關鍵字庫配置
KEYWORD_DATABASE = {
    "輕便": {
        "同義詞": ["重量較輕", "容易攜帶", "輕薄", "便攜", "輕巧", "易攜"],
        "metadata": {
            "regex": r"(輕[便薄巧]?|便攜|易攜帶?|好帶|方便攜帶|重量[較很]?輕)",
            "重量區間": "< 1.5kg",
            "category": "portability",
            "priority": 1
        }
    },
    "高效能": {
        "同義詞": ["效能好", "跑得快", "性能強", "強勁", "高規格"],
        "metadata": {
            "regex": r"(高[效性]能?|效能[好強高]|性能[強好]|跑得快|強勁|高規格?)",
            "處理器等級": "i7/Ryzen7 以上",
            "category": "performance",
            "priority": 1
        }
    },
    "電池續航": {
        "同義詞": ["電池持久", "續航力強", "電力持久", "使用時間長"],
        "metadata": {
            "regex": r"(電池[續持]航?[力強久長]?|續航[力強長]?|電力持久|使用時間[長久])",
            "續航時間": "> 8小時",
            "category": "battery",
            "priority": 2
        }
    },
    "螢幕大": {
        "同義詞": ["大螢幕", "顯示器大", "畫面大"],
        "metadata": {
            "regex": r"(螢幕[大較]|大螢幕|顯示器?[大較]|畫面[大較]|1[567][\.\d]*[吋寸])",
            "尺寸區間": ">= 15吋",
            "category": "display",
            "priority": 2
        }
    },
    "預算考量": {
        "同義詞": ["便宜", "價格親民", "CP值高", "性價比高", "經濟實惠"],
        "metadata": {
            "regex": r"(便宜|預算|價[格錢][親低便]?|CP值?[高好]?|性價比[高好]?|經濟實惠|萬[元塊][以內下]?)",
            "價格區間": "依預算而定",
            "category": "budget",
            "priority": 1
        }
    }
}

@dataclass
class KeywordMatch:
    """關鍵字匹配結果"""
    detected: bool
    keyword: Optional[str]
    matched_text: Optional[str]
    metadata: Optional[Dict[str, Any]]
    confidence: float

class KeywordDetector:
    """關鍵字檢測器"""
    
    def __init__(self, keyword_db: Dict[str, Any] = None):
        self.keyword_db = keyword_db or KEYWORD_DATABASE
        self._compile_patterns()
    
    def _compile_patterns(self):
        """預編譯所有正則表達式以提高效能"""
        self.compiled_patterns = {}
        for keyword, data in self.keyword_db.items():
            if "metadata" in data and "regex" in data["metadata"]:
                self.compiled_patterns[keyword] = re.compile(
                    data["metadata"]["regex"], 
                    re.IGNORECASE
                )
    
    def ChkKeyword(self, input_sentence: str) -> Dict[str, Any]:
        """
        檢測輸入句子中的關鍵字
        
        Args:
            input_sentence: 輸入的句子
            
        Returns:
            檢測結果字典，包含是否檢測到、關鍵字、區間等信息
        """
        results = []
        
        # 遍歷所有關鍵字進行檢測
        for keyword, data in self.keyword_db.items():
            # 1. 直接關鍵字匹配
            if keyword in input_sentence:
                results.append(self._create_result(keyword, keyword, data, 1.0))
                continue
            
            # 2. 同義詞匹配
            for synonym in data.get("同義詞", []):
                if synonym in input_sentence:
                    results.append(self._create_result(keyword, synonym, data, 0.9))
                    break
            
            # 3. 正則表達式匹配
            if keyword in self.compiled_patterns:
                match = self.compiled_patterns[keyword].search(input_sentence)
                if match:
                    results.append(self._create_result(
                        keyword, match.group(), data, 0.85
                    ))
        
        # 如果沒有檢測到任何關鍵字
        if not results:
            return {
                "ret": "no",
                "kw": None,
                "區間": "nodata",
                "metadata": {}
            }
        
        # 根據優先級和置信度排序，返回最佳匹配
        best_match = max(results, key=lambda x: (
            x["metadata"].get("priority", 999),
            x["confidence"]
        ))
        
        return best_match
    
    def _create_result(self, keyword: str, matched_text: str, 
                      data: Dict[str, Any], confidence: float) -> Dict[str, Any]:
        """創建檢測結果"""
        metadata = data.get("metadata", {})
        
        # 提取區間信息
        interval = None
        if "重量區間" in metadata:
            interval = metadata["重量區間"]
        elif "續航時間" in metadata:
            interval = metadata["續航時間"]
        elif "尺寸區間" in metadata:
            interval = metadata["尺寸區間"]
        elif "價格區間" in metadata:
            interval = metadata["價格區間"]
        
        return {
            "ret": "yes",
            "kw": keyword,
            "matched_text": matched_text,
            "區間": interval or "nodata",
            "metadata": metadata,
            "confidence": confidence
        }
    
    def detect_multiple_keywords(self, input_sentence: str) -> List[Dict[str, Any]]:
        """檢測多個關鍵字"""
        results = []
        detected_keywords = set()
        
        for keyword, data in self.keyword_db.items():
            if keyword in detected_keywords:
                continue
                
            # 檢測邏輯同上
            match_found = False
            
            # 直接匹配
            if keyword in input_sentence:
                results.append(self._create_result(keyword, keyword, data, 1.0))
                detected_keywords.add(keyword)
                match_found = True
            
            # 同義詞匹配
            if not match_found:
                for synonym in data.get("同義詞", []):
                    if synonym in input_sentence:
                        results.append(self._create_result(keyword, synonym, data, 0.9))
                        detected_keywords.add(keyword)
                        match_found = True
                        break
            
            # 正則匹配
            if not match_found and keyword in self.compiled_patterns:
                match = self.compiled_patterns[keyword].search(input_sentence)
                if match:
                    results.append(self._create_result(
                        keyword, match.group(), data, 0.85
                    ))
                    detected_keywords.add(keyword)
        
        return results

class UserInputHandler:
    """用戶輸入處理器"""
    
    def __init__(self):
        self.keyword_detector = KeywordDetector()
        self.state = "Ready"
    
    def process_input(self, input_data: str) -> Dict[str, Any]:
        """處理用戶輸入"""
        # 驗證輸入
        if not self.validate_input(input_data):
            return {
                "status": "error",
                "message": "Invalid input",
                "data": None
            }
        
        # 解析輸入
        parsed_data = self.parse_input(input_data)
        
        # 路由輸入
        action = self.route_input(parsed_data)
        
        return {
            "status": "success",
            "parsed_data": parsed_data,
            "action": action,
            "state": self.state
        }
    
    def validate_input(self, input_data: str) -> bool:
        """驗證用戶輸入"""
        if not input_data or not isinstance(input_data, str):
            return False
        
        # 檢查輸入長度
        if len(input_data.strip()) < 2 or len(input_data) > 500:
            return False
        
        # 可以添加更多驗證規則
        return True
    
    def parse_input(self, input_data: str) -> Dict[str, Any]:
        """解析用戶輸入"""
        # 清理輸入
        cleaned_input = input_data.strip()
        
        # 檢測關鍵字
        keyword_result = self.keyword_detector.ChkKeyword(cleaned_input)
        
        # 檢測多個關鍵字
        multiple_keywords = self.keyword_detector.detect_multiple_keywords(cleaned_input)
        
        # 分析意圖
        intent = self._analyze_intent(cleaned_input, multiple_keywords)
        
        return {
            "original_input": input_data,
            "cleaned_input": cleaned_input,
            "primary_keyword": keyword_result,
            "all_keywords": multiple_keywords,
            "intent": intent,
            "timestamp": self._get_timestamp()
        }
    
    def route_input(self, parsed_input: Dict[str, Any]) -> str:
        """路由用戶輸入到相應的處理動作"""
        intent = parsed_input.get("intent", "unknown")
        keywords = parsed_input.get("all_keywords", [])
        
        # 根據意圖和關鍵字決定路由
        if intent == "product_recommendation":
            if any(kw["kw"] == "輕便" for kw in keywords):
                return "recommend_portable_laptops"
            elif any(kw["kw"] == "高效能" for kw in keywords):
                return "recommend_performance_laptops"
            elif any(kw["kw"] == "預算考量" for kw in keywords):
                return "recommend_budget_laptops"
            else:
                return "recommend_general_laptops"
        
        elif intent == "product_comparison":
            return "compare_products"
        
        elif intent == "technical_support":
            return "provide_technical_support"
        
        else:
            return "general_inquiry"
    
    def _analyze_intent(self, input_text: str, keywords: List[Dict]) -> str:
        """分析用戶意圖"""
        # 簡單的意圖分析邏輯
        recommendation_words = ["推薦", "介紹", "建議", "哪個好", "哪款"]
        comparison_words = ["比較", "對比", "差異", "區別"]
        support_words = ["問題", "故障", "修理", "維修", "怎麼辦"]
        
        for word in recommendation_words:
            if word in input_text:
                return "product_recommendation"
        
        for word in comparison_words:
            if word in input_text:
                return "product_comparison"
        
        for word in support_words:
            if word in input_text:
                return "technical_support"
        
        # 如果有關鍵字但沒有明確意圖詞，預設為產品推薦
        if keywords:
            return "product_recommendation"
        
        return "general_inquiry"
    
    def _get_timestamp(self) -> str:
        """獲取時間戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# 使用示例
def main():
    # 創建處理器實例
    handler = UserInputHandler()
    detector = KeywordDetector()
    
    # 測試用例
    test_cases = [
        "請幫我介紹較為輕便容易攜帶的筆電",
        "我想要高效能且電池續航力強的筆電",
        "有沒有便宜又大螢幕的筆電推薦",
        "我需要一台重量較輕的筆電用於出差",
        "15吋螢幕且CP值高的筆電有哪些"
    ]
    
    print("=" * 60)
    print("關鍵字檢測系統測試")
    print("=" * 60)
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n測試案例 {i}: {test_input}")
        print("-" * 40)
        
        # 單一關鍵字檢測
        result = detector.ChkKeyword(test_input)
        print(f"主要關鍵字: {result['kw']}")
        print(f"檢測結果: {result['ret']}")
        print(f"區間: {result['區間']}")
        
        # 多關鍵字檢測
        multiple = detector.detect_multiple_keywords(test_input)
        if multiple:
            print(f"所有檢測到的關鍵字: {[m['kw'] for m in multiple]}")
        
        # 完整處理流程
        processed = handler.process_input(test_input)
        print(f"意圖: {processed['parsed_data']['intent']}")
        print(f"建議動作: {processed['action']}")

if __name__ == "__main__":
    main()