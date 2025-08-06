from pydantic import BaseModel
from typing import List, Dict, Optional, Any

# 資料處理相關模型
class ProcessRequest(BaseModel):
    text_content: str
    custom_rules: Optional[Dict[str, List[str]]] = None
    temp_regex: Optional[List[str]] = None
    file_name: Optional[str] = None
    user_modeltype: Optional[str] = None

class ProcessResponse(BaseModel):
    data: List[Dict[str, str]]
    error: Optional[str] = None

class IngestRequest(BaseModel):
    data: List[Dict[str, str]]

class IngestResponse(BaseModel):
    success: bool
    message: str
    duckdb_rows_added: int
    milvus_entities_added: int

# RAG 查詢相關模型
class ChatQueryRequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str, str]]] = None
    max_results: Optional[int] = 5

class ChatQueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    query_time: float
    success: bool

class CompareRequest(BaseModel):
    models: List[str]
    compare_fields: Optional[List[str]] = None

class CompareResponse(BaseModel):
    comparison_table: List[Dict[str, str]]
    summary: str
    success: bool

# 系統狀態相關模型
class SystemHealthResponse(BaseModel):
    status: str
    duckdb_status: str
    milvus_status: str
    total_records: int
    last_update: Optional[str] = None

class SystemStatsResponse(BaseModel):
    total_queries: int
    total_records: int
    database_size: str
    popular_queries: List[Dict[str, Any]]
    success: bool
