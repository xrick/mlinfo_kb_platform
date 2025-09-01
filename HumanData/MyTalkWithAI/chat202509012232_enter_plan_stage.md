[MODE: PLAN]

基於系統性思維，我將全面檢視 ResponseGenHandler 的實作計畫，並從多個角度進行改進，確保與原始架構和目標完全對齊。

## 系統性架構檢視

### 1. **與 MGFD 系統架構對齊分析**

**原始架構要求：**
- 五大核心子模組之一
- 遵循標準動作合約 `action(context) -> dict`
- 與 MGFDKernel 協調工作
- 支援前端 `mgfd_ai.js` 格式

**當前設計對齊度：**
✅ **完全對齊** - Strategy Pattern 實作符合模組化要求
✅ **完全對齊** - 標準動作合約支援
✅ **完全對齊** - 與 MGFDKernel 介面整合
✅ **完全對齊** - 前端格式對齊

### 2. **與現有系統整合性分析**

**與 UserInputHandler 整合：**
- 接收解析後的意圖和槽位信息
- 根據意圖選擇適當的回應策略
- 利用槽位信息生成個性化回應

**與 StateManagementHandler 整合：**
- 支援不同對話階段的回應需求
- 提供狀態轉換所需的回應格式
- 維護回應歷史記錄

**與 PromptManagementHandler 整合：**
- 利用企業級提示模板
- 支援動態提示渲染
- 確保回應風格一致性

## 多角度改進計畫

### **角度一：技術架構改進**

#### 1.1 策略模式優化
```python
# 抽象策略基類
class ResponseStrategy(ABC):
    """回應生成策略抽象基類"""
    
    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name
        self.logger = logging.getLogger(f"{__name__}.{strategy_name}")
    
    @abstractmethod
    def generate_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成回應"""
        pass
    
    @abstractmethod
    def get_response_type(self) -> str:
        """獲取回應類型"""
        pass
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """驗證上下文是否適合此策略"""
        pass
```

#### 1.2 策略工廠模式
```python
class ResponseStrategyFactory:
    """回應策略工廠"""
    
    def __init__(self):
        self.strategies = {
            "funnel_question": FunnelQuestionStrategy(),
            "recommendation": RecommendationStrategy(),
            "elicitation": ElicitationStrategy(),
            "general": GeneralResponseStrategy()
        }
    
    def get_strategy(self, response_type: str) -> ResponseStrategy:
        """根據回應類型獲取策略"""
        return self.strategies.get(response_type, self.strategies["general"])
    
    def select_strategy_by_context(self, context: Dict[str, Any]) -> ResponseStrategy:
        """根據上下文智能選擇策略"""
        # 智能策略選擇邏輯
        pass
```

### **角度二：pytablewriter 整合改進**

#### 2.1 智能 JSON 轉換引擎
```python
class TableDataConverter:
    """表格數據轉換器"""
    
    def convert_json_to_value_matrix(
        self, 
        json_data: Dict[str, Any], 
        table_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[List[Any]]]:
        """
        智能將 JSON 數據轉換為 pytablewriter 格式
        
        Args:
            json_data: 輸入的 JSON 數據
            table_config: 表格配置（可選）
                - headers: 自定義表頭
                - column_mapping: 列映射
                - data_transforms: 數據轉換規則
        
        Returns:
            (headers, value_matrix) 元組
        """
        pass
    
    def _detect_data_structure(self, data: Any) -> str:
        """檢測數據結構類型"""
        pass
    
    def _flatten_nested_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """扁平化嵌套字典"""
        pass
    
    def _extract_list_data(self, data: List[Dict[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
        """提取列表數據"""
        pass
```

#### 2.2 表格樣式配置
```python
class MarkdownTableGenerator:
    """Markdown 表格生成器"""
    
    def __init__(self):
        self.converter = TableDataConverter()
    
    def generate_table(
        self, 
        data: Dict[str, Any], 
        table_name: str = "",
        style_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成 Markdown 表格
        
        Args:
            data: 表格數據
            table_name: 表格名稱
            style_config: 樣式配置
                - alignment: 對齊方式
                - max_width: 最大寬度
                - format_rules: 格式化規則
        
        Returns:
            Markdown 表格字符串
        """
        pass
```

### **角度三：回應品質控制改進**

#### 3.1 回應品質評估系統
```python
class ResponseQualityEvaluator:
    """回應品質評估器"""
    
    def evaluate_response(self, response: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        評估回應品質
        
        Returns:
            包含評估結果的字典
        """
        evaluation = {
            "completeness": self._evaluate_completeness(response, context),
            "clarity": self._evaluate_clarity(response),
            "relevance": self._evaluate_relevance(response, context),
            "consistency": self._evaluate_consistency(response, context),
            "overall_score": 0.0,
            "improvement_suggestions": []
        }
        
        # 計算總分
        evaluation["overall_score"] = self._calculate_overall_score(evaluation)
        
        # 生成改進建議
        evaluation["improvement_suggestions"] = self._generate_suggestions(evaluation)
        
        return evaluation
    
    def _evaluate_completeness(self, response: Dict[str, Any], context: Dict[str, Any]) -> float:
        """評估完整性"""
        pass
    
    def _evaluate_clarity(self, response: Dict[str, Any]) -> float:
        """評估清晰度"""
        pass
    
    def _evaluate_relevance(self, response: Dict[str, Any], context: Dict[str, Any]) -> float:
        """評估相關性"""
        pass
    
    def _evaluate_consistency(self, response: Dict[str, Any], context: Dict[str, Any]) -> float:
        """評估一致性"""
        pass
```

### **角度四：企業級標準化改進**

#### 4.1 回應模板管理
```python
class ResponseTemplateManager:
    """回應模板管理器"""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.template_engine = self._initialize_template_engine()
    
    def get_template(self, template_type: str, context: Dict[str, Any]) -> str:
        """獲取適合的模板"""
        pass
    
    def render_template(self, template: str, context: Dict[str, Any]) -> str:
        """渲染模板"""
        pass
    
    def _load_templates(self) -> Dict[str, str]:
        """載入模板文件"""
        pass
```

#### 4.2 前端格式對齊
```python
class FrontendFormatAdapter:
    """前端格式適配器"""
    
    def adapt_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        適配前端期望的格式
        
        確保與 mgfd_ai.js 完全對齊
        """
        adapted_response = {
            "type": response.get("type", "general"),
            "message": response.get("message", ""),
            "session_id": response.get("session_id"),
            "timestamp": response.get("timestamp", datetime.now().isoformat())
        }
        
        # 根據回應類型添加特定字段
        if response.get("type") == "funnel_question":
            adapted_response.update({
                "question": response.get("question"),
                "options": response.get("options", []),
                "question_message": response.get("question_message", "")
            })
        elif response.get("type") == "recommendation":
            adapted_response.update({
                "recommendations": response.get("recommendations", []),
                "comparison_table": response.get("comparison_table"),
                "summary": response.get("recommendation_summary")
            })
        
        return adapted_response
```

## 完整實作計畫

### **IMPLEMENTATION CHECKLIST:**

#### **Phase 1: 核心架構建立**
1. 建立 `ResponseStrategy` 抽象基類
2. 實作 `ResponseStrategyFactory` 策略工廠
3. 建立 `ResponseGenHandler` 主類別
4. 實作標準動作合約 `generate(context) -> dict`

#### **Phase 2: 具體策略實作**
5. 實作 `FunnelQuestionStrategy` 漏斗問題策略
6. 實作 `RecommendationStrategy` 推薦回應策略
7. 實作 `ElicitationStrategy` 信息收集策略
8. 實作 `GeneralResponseStrategy` 通用回應策略

#### **Phase 3: pytablewriter 整合**
9. 建立 `TableDataConverter` 數據轉換器
10. 實作 `MarkdownTableGenerator` 表格生成器
11. 建立智能 JSON 到 value_matrix 轉換函式
12. 實作表格樣式配置系統

#### **Phase 4: 品質控制系統**
13. 建立 `ResponseQualityEvaluator` 品質評估器
14. 實作回應完整性評估邏輯
15. 實作回應清晰度評估邏輯
16. 實作回應相關性評估邏輯
17. 實作回應一致性評估邏輯

#### **Phase 5: 企業級標準化**
18. 建立 `ResponseTemplateManager` 模板管理器
19. 實作模板載入和渲染系統
20. 建立 `FrontendFormatAdapter` 前端適配器
21. 實作與 `mgfd_ai.js` 的格式對齊

#### **Phase 6: 整合與測試**
22. 整合所有組件到 `ResponseGenHandler`
23. 實作錯誤處理和日誌記錄
24. 建立單元測試套件
25. 建立整合測試
26. 實作效能優化

#### **Phase 7: 文檔與部署**
27. 建立 API 文檔
28. 建立使用範例
29. 更新系統文檔
30. 準備部署配置

## 架構驗證

### **與原始目標對齊度檢查：**

✅ **模組化設計**: Strategy Pattern 確保高度模組化
✅ **可擴展性**: 新策略可輕鬆添加
✅ **品質控制**: 完整的評估和改進機制
✅ **前端對齊**: 完全符合 `mgfd_ai.js` 期望
✅ **企業級標準**: 模板管理和格式標準化
✅ **技術整合**: pytablewriter 專業表格生成
✅ **系統整合**: 與 MGFD 架構完美整合

這個改進後的計畫確保了 ResponseGenHandler 不僅滿足基本需求，更達到了企業級品質標準，同時保持了與整個 MGFD 系統架構的完美一致性。