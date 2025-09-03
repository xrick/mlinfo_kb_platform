# KnowledgeManageHandler - Polars 支援

## 概述

KnowledgeManageHandler 現在支援 Polars 數據庫，提供高性能的 DataFrame 操作和查詢功能。Polars 是一個用 Rust 編寫的快速 DataFrame 庫，專為大數據處理和並行計算而設計。

## 主要特性

### 🚀 高性能
- **Rust 核心**: 底層使用 Rust 實現，性能優越
- **並行處理**: 原生支援多線程和並行計算
- **內存優化**: 高效的內存管理和零拷貝操作

### 🔧 靈活配置
- **LazyFrame 支援**: 延遲執行查詢，優化查詢計劃
- **內存限制**: 可配置的內存使用限制
- **降級策略**: 自動降級到 SQLite 查詢（如果可用）

### 📊 多格式支援
- **CSV**: 支援多種分隔符和編碼
- **Parquet**: 列式存儲，壓縮效率高
- **Arrow**: 高效的二進制格式
- **SQL**: 支援 SQL 查詢（通過轉換）

## 安裝要求

### 必需依賴
```bash
pip install polars
```

### 可選依賴
```bash
pip install psutil  # 用於內存監控
pip install pandas  # 用於示例數據創建
```

## 快速開始

### 1. 基本使用

```python
from KnowledgeManageHandler import KnowledgeManager

# 初始化知識管理器
km = KnowledgeManager()

# 執行 Polars 查詢
result = await km.query_polars_data(
    data_source="sales_data",
    query_expr="df.filter(pl.col('price') > 1000)",
    lazy=True,
    parallel=True
)

print(f"查詢結果: {len(result['data'])} 條記錄")
```

### 2. 連接數據源

```python
# 連接 CSV 數據源
csv_config = {
    "name": "sales_data",
    "type": "csv",
    "path": "data/sales.csv"
}

# 注意：實際連接需要通過 PolarsHelper 實現
# 這裡只是配置示例
```

### 3. 查詢優化

```python
# 使用 LazyFrame 優化查詢
result = await km.query_polars_data(
    data_source="sales_data",
    query_expr="df.filter(pl.col('price') > 1000).select(['modelname', 'price'])",
    lazy=True,  # 啟用 LazyFrame
    parallel=True  # 啟用並行處理
)
```

## 配置說明

### 主要配置選項

```json
{
  "polars_settings": {
    "enable_lazy_evaluation": true,        // 啟用 LazyFrame
    "default_parallel_processing": true,   // 默認並行處理
    "memory_limit_mb": 1024,              // 內存限制 (MB)
    "fallback_to_sqlite": true,           // 啟用 SQLite 降級
    "supported_formats": ["csv", "parquet", "arrow", "sql"]
  }
}
```

### 性能監控配置

```json
{
  "performance_monitoring": {
    "enable_query_stats": true,           // 查詢統計
    "enable_memory_monitoring": true,     // 內存監控
    "enable_performance_warnings": true   // 性能警告
  }
}
```

## API 參考

### KnowledgeManager 新增方法

#### `query_polars_data()`
執行 Polars 查詢

```python
async def query_polars_data(
    self, 
    data_source: str,           # 數據源標識符
    query_expr: str,            # Polars 查詢表達式
    lazy: bool = True,          # 是否使用 LazyFrame
    parallel: bool = True,      # 是否啟用並行處理
    memory_limit: Optional[int] = None  # 內存限制 (MB)
) -> Optional[Dict[str, Any]]
```

**參數說明**:
- `data_source`: 數據源名稱，用於識別要查詢的數據
- `query_expr`: Polars 查詢表達式，支援過濾、選擇、分組等操作
- `lazy`: 是否使用 LazyFrame 優化查詢性能
- `parallel`: 是否啟用並行處理
- `memory_limit`: 內存使用限制，超過限制會觸發警告

**返回值**:
```python
{
    "data": [...],              # 查詢結果數據
    "metadata": {               # 查詢元數據
        "source": "sales_data",
        "query": "df.filter(pl.col('price') > 1000)",
        "lazy": True,
        "parallel": True,
        "result_count": 150,
        "timestamp": "2025-01-01T12:00:00"
    },
    "performance": {            # 性能信息
        "memory_usage_mb": 45.2,
        "query_optimized": True
    }
}
```

#### `get_polars_stats()`
獲取 Polars 統計信息

```python
async def get_polars_stats(
    self, 
    data_source: str
) -> Optional[Dict[str, Any]]
```

**返回值**:
```python
{
    "data_source": "sales_data",
    "polars_version": "0.20.0",
    "memory_usage": {
        "system_total_gb": 16.0,
        "system_available_gb": 8.5,
        "process_memory_mb": 256.8,
        "polars_memory_mb": 45.2
    },
    "config": {...},
    "timestamp": "2025-01-01T12:00:00"
}
```

### PolarsHelper 類別

#### `connect_data_source()`
連接數據源

```python
async def connect_data_source(
    self, 
    source_config: Dict[str, Any]
) -> bool
```

#### `execute_query()`
執行查詢

```python
async def execute_query(
    self, 
    query_expr: str, 
    lazy: bool = True, 
    parallel: bool = True
) -> Optional[Any]
```

#### `get_memory_usage()`
獲取內存使用情況

```python
def get_memory_usage(self) -> Dict[str, Any]
```

## 查詢表達式示例

### 基本過濾
```python
# 價格大於 1000 的產品
"df.filter(pl.col('price') > 1000)"

# 特定型號類型的產品
"df.filter(pl.col('modeltype') == 'Business')"

# 多條件過濾
"df.filter((pl.col('price') > 1000) & (pl.col('ram') >= 16))"
```

### 列選擇
```python
# 選擇特定列
"df.select(['modelname', 'price', 'modeltype'])"

# 重命名列
"df.select([pl.col('modelname').alias('name'), pl.col('price').alias('cost')])"
```

### 分組聚合
```python
# 按型號類型分組，計算平均價格
"df.groupby('modeltype').agg([pl.col('price').mean().alias('avg_price')])"

# 多個聚合操作
"df.groupby('modeltype').agg([
    pl.col('price').mean().alias('avg_price'),
    pl.col('price').count().alias('count'),
    pl.col('ram').max().alias('max_ram')
])"
```

### 排序
```python
# 按價格排序
"df.sort('price', descending=True)"

# 多列排序
"df.sort(['modeltype', 'price'], descending=[False, True])"
```

## 性能優化建議

### 1. 使用 LazyFrame
```python
# 推薦：使用 LazyFrame 優化查詢
result = await km.query_polars_data(
    data_source="sales_data",
    query_expr="df.filter(pl.col('price') > 1000).select(['modelname', 'price'])",
    lazy=True  # 啟用 LazyFrame
)
```

### 2. 啟用並行處理
```python
# 推薦：啟用並行處理提升性能
result = await km.query_polars_data(
    data_source="sales_data",
    query_expr="df.filter(pl.col('price') > 1000)",
    parallel=True  # 啟用並行處理
)
```

### 3. 內存管理
```python
# 設置適當的內存限制
km.polars_config["memory_limit_mb"] = 2048  # 2GB 限制

# 監控內存使用
stats = await km.get_polars_stats("sales_data")
print(f"當前內存使用: {stats['memory_usage']['polars_memory_mb']}MB")
```

## 錯誤處理

### 常見錯誤類型

1. **PolarsConnectionError**: 數據源連接失敗
2. **PolarsQueryError**: 查詢執行失敗
3. **PolarsMemoryError**: 內存使用超出限制

### 錯誤處理示例

```python
try:
    result = await km.query_polars_data(
        data_source="sales_data",
        query_expr="df.filter(pl.col('price') > 1000)"
    )
    
    if result:
        print(f"查詢成功: {len(result['data'])} 條記錄")
    else:
        print("查詢失敗，可能已降級到 SQLite")
        
except Exception as e:
    print(f"查詢出現錯誤: {e}")
    
    # 檢查是否啟用了降級
    if km.polars_config.get("fallback_to_sqlite", True):
        print("系統將嘗試使用 SQLite 查詢")
```

## 最佳實踐

### 1. 查詢優化
- 優先使用 LazyFrame 進行查詢優化
- 合理使用過濾條件，減少數據傳輸
- 選擇必要的列，避免全表掃描

### 2. 內存管理
- 設置適當的內存限制
- 監控內存使用情況
- 及時清理不需要的數據

### 3. 錯誤處理
- 實現適當的錯誤處理邏輯
- 使用降級策略提高系統穩定性
- 記錄詳細的錯誤日誌

### 4. 性能監控
- 定期檢查查詢性能統計
- 監控內存使用趨勢
- 根據性能數據調整配置

## 故障排除

### 常見問題

1. **Polars 未安裝**
   ```
   解決方案: pip install polars
   ```

2. **內存不足**
   ```
   解決方案: 調整 memory_limit_mb 配置
   ```

3. **查詢執行失敗**
   ```
   解決方案: 檢查查詢表達式語法，啟用 SQLite 降級
   ```

4. **性能不佳**
   ```
   解決方案: 啟用 LazyFrame 和並行處理
   ```

### 調試技巧

1. **啟用詳細日誌**
   ```python
   logging.getLogger('KnowledgeManageHandler').setLevel(logging.DEBUG)
   ```

2. **檢查配置**
   ```python
   print(km.polars_config)
   ```

3. **監控性能**
   ```python
   stats = await km.get_polars_stats("data_source")
   print(stats)
   ```

## 更新日誌

### v1.0.0 (2025-01-01)
- 初始版本發布
- 支援基本的 Polars 查詢功能
- 實現 LazyFrame 優化
- 支援並行處理
- 內存使用監控
- SQLite 降級策略

## 貢獻指南

歡迎提交 Issue 和 Pull Request 來改進 Polars 支援功能。

## 授權

本項目採用 MIT 授權條款。
