[MODE: PLAN]

基於您提供的 AI 提示要求和系統思維原則，我將制定一個全面且實用的實作計畫來加強和改善 KnowledgeManageHandler 的 Polars DB 支援。讓我應用系統思維、批判性思考來確保解決方案架構的全面性，並嚴格避免過度設計。

## �� 系統架構分析與批判性評估

### 現有架構問題識別
通過批判性分析，我發現當前 `impl_list.md` 存在以下問題：
1. **過度複雜化**: 新增了 7 個組件，違反"功能單純"原則
2. **架構膨脹**: 引入了不必要的抽象層，增加維護複雜度
3. **功能重疊**: PolarsQueryOptimizer 與現有查詢功能重複
4. **實現難度**: 多個組件同時實作，違反"容易實作"原則

### 批判性優化策略
基於"不要過度設計"原則，我將：
- 合併重複功能到現有組件
- 簡化組件數量，專注核心價值
- 利用現有架構，最小化新增代碼
- 確保每個功能都有明確的實用價值

## �� 重新設計：簡化實用的 Polars 整合方案

### 核心設計原則
1. **最小化變更**: 只在現有架構上添加必要功能
2. **功能單純**: 每個組件只負責一個明確的職責
3. **高容錯性**: 完善的錯誤處理和降級機制
4. **易於維護**: 清晰的代碼結構和詳細註釋

### 精簡後的組件設計

#### 1. 擴展現有 KnowledgeManager (最小化變更)
**策略**: 不創建新類別，直接在現有 `KnowledgeManager` 中添加 Polars 支援

**新增方法**:
```python
# 在現有 KnowledgeManager 中添加
async def query_polars_data(self, data_source: str, query_expr: str, 
                           lazy: bool = True) -> Optional[Any]:
    """查詢 Polars 數據源，保持與現有查詢接口一致"""
    pass

async def get_polars_stats(self, data_source: str) -> Optional[Dict[str, Any]]:
    """獲取 Polars 數據源統計信息"""
    pass
```

#### 2. 創建 PolarsHelper 工具類別 (功能單純)
**策略**: 單一職責的工具類別，只負責 Polars 相關操作

**功能範圍**:
- 數據源連接管理
- 查詢優化建議
- 內存使用監控
- 錯誤處理和降級

#### 3. 擴展配置系統 (最小化新增)
**策略**: 在現有配置中添加 Polars 相關設定，不創建新的配置文件

### 與現有系統的整合策略

#### 1. 接口一致性
- 使用現有的 `async def action(context)` 標準合約
- 保持與 SQLite 查詢相同的結果格式
- 統一的錯誤處理和日誌記錄模式

#### 2. 數據流整合
- 支援現有的知識庫查詢流程
- 與 SQLite 查詢結果格式兼容
- 共享的緩存和監控機制

#### 3. 配置管理
- 在現有配置文件中添加 Polars 設定
- 支援環境變數覆蓋
- 保持配置結構的一致性

## 📋 詳細技術規範

### 1. 擴展 KnowledgeManager 接口

**文件**: `libs/KnowledgeManageHandler/knowledge_manager.py`

**新增方法規範**:
```python
async def query_polars_data(self, 
                           data_source: str,           # 數據源標識符
                           query_expr: str,            # Polars 查詢表達式
                           lazy: bool = True,          # 是否使用 LazyFrame
                           parallel: bool = True,      # 是否啟用並行處理
                           memory_limit: Optional[int] = None  # 內存限制 (MB)
                           ) -> Optional[Dict[str, Any]]:
    """
    查詢 Polars 數據源
    
    Args:
        data_source: 數據源標識符 (如 'sales_data', 'product_catalog')
        query_expr: Polars 查詢表達式 (如 'df.filter(pl.col("price") > 1000)')
        lazy: 是否使用 LazyFrame 優化
        parallel: 是否啟用並行處理
        memory_limit: 內存使用限制 (MB)
    
    Returns:
        查詢結果字典，包含數據、統計信息和元數據
        格式與現有 SQLite 查詢結果保持一致
    
    Raises:
        PolarsConnectionError: 連接失敗
        PolarsQueryError: 查詢執行失敗
        PolarsMemoryError: 內存不足
    """
    pass
```

### 2. PolarsHelper 工具類別設計

**文件**: `libs/KnowledgeManageHandler/polars_helper.py`

**核心功能規範**:
```python
class PolarsHelper:
    """Polars 數據操作輔助工具類別"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Polars 輔助工具
        
        Args:
            config: 配置字典，包含連接參數、內存限制等
        """
        pass
    
    async def connect_data_source(self, source_config: Dict[str, Any]) -> bool:
        """連接數據源，支援 CSV、Parquet、Arrow、SQL 等格式"""
        pass
    
    async def execute_query(self, query_expr: str, lazy: bool = True, 
                           parallel: bool = True) -> Optional[Any]:
        """執行 Polars 查詢，包含錯誤處理和性能優化"""
        pass
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """獲取當前內存使用情況"""
        pass
    
    def optimize_query_plan(self, query_expr: str) -> str:
        """提供查詢優化建議"""
        pass
```

### 3. 配置擴展規範

**在現有配置中添加 Polars 設定**:
```json
{
  "polars_settings": {
    "enable_lazy_evaluation": true,
    "default_parallel_processing": true,
    "memory_limit_mb": 1024,
    "connection_timeout_seconds": 30,
    "retry_attempts": 3,
    "fallback_to_sqlite": true,
    "supported_formats": ["csv", "parquet", "arrow", "sql"],
    "performance_monitoring": {
      "enable_query_stats": true,
      "enable_memory_monitoring": true,
      "enable_performance_warnings": true
    }
  }
}
```

### 4. 錯誤處理和容錯機制

**分層錯誤處理策略**:
1. **連接層**: 自動重試、連接池管理
2. **查詢層**: 查詢超時處理、語法錯誤處理
3. **結果層**: 內存不足降級、結果格式轉換
4. **降級策略**: 自動回退到 SQLite 查詢（如果可用）

**錯誤類型定義**:
```python
class PolarsConnectionError(Exception):
    """Polars 連接錯誤"""
    pass

class PolarsQueryError(Exception):
    """Polars 查詢錯誤"""
    pass

class PolarsMemoryError(Exception):
    """Polars 內存錯誤"""
    pass
```

## �� 實作階段規劃

### 階段 1: 基礎整合 (1 天)
- [ ] 在現有 KnowledgeManager 中添加 Polars 查詢方法
- [ ] 創建 PolarsHelper 工具類別
- [ ] 擴展現有配置文件
- [ ] 建立基礎錯誤處理機制

### 階段 2: 功能完善 (1 天)
- [ ] 實現完整的查詢接口
- [ ] 添加內存監控和優化
- [ ] 實現降級和容錯機制
- [ ] 建立性能監控基礎

### 階段 3: 測試和優化 (0.5 天)
- [ ] 單元測試和集成測試
- [ ] 性能測試和內存使用測試
- [ ] 錯誤場景測試
- [ ] 文檔更新

## ✅ 實作檢查清單

### IMPLEMENTATION CHECKLIST:

1. **擴展現有 KnowledgeManager**
   - 在 `knowledge_manager.py` 中添加 `query_polars_data` 方法
   - 在 `knowledge_manager.py` 中添加 `get_polars_stats` 方法
   - 確保新方法遵循現有的接口規範和錯誤處理模式

2. **創建 PolarsHelper 工具類別**
   - 建立 `polars_helper.py` 文件
   - 實現數據源連接管理
   - 實現查詢執行和優化
   - 實現內存監控和錯誤處理

3. **擴展配置系統**
   - 在現有配置文件中添加 `polars_settings` 部分
   - 實現配置驗證邏輯
   - 支援環境變數覆蓋
   - 保持與現有配置結構的一致性

4. **實現錯誤處理和容錯機制**
   - 定義 Polars 相關的錯誤類型
   - 實現分層錯誤處理策略
   - 實現自動降級機制
   - 添加詳細的錯誤日誌和診斷信息

5. **整合到現有系統**
   - 更新 `__init__.py` 導出新的功能
   - 確保與現有查詢接口的兼容性
   - 實現統一的性能監控
   - 建立一致的日誌記錄格式

6. **建立測試框架**
   - 編寫單元測試用例
   - 編寫集成測試
   - 編寫性能測試
   - 編寫錯誤場景測試

7. **更新文檔和示例**
   - 更新 `impl_list.md` 中的 Polars 支援狀態
   - 編寫使用示例和最佳實踐
   - 更新配置說明
   - 編寫故障排除指南

這個重新設計的方案嚴格遵循您的要求：
- **避免過度設計**: 只添加必要的功能，不創建多餘的抽象層
- **功能單純**: 每個組件都有明確的單一職責
- **容易實作**: 基於現有架構，最小化新增代碼
- **高容錯性**: 完善的錯誤處理和降級機制
- **易於維護**: 清晰的代碼結構和詳細註釋
- **系統思維**: 確保與現有架構的完美整合
- **目標聚焦**: 專注於 Polars DB 支援的核心需求