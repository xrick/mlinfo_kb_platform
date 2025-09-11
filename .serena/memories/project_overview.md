# 專案概覽

## 專案目的
SalesRAG Integration System - 智能筆電銷售助理系統，結合Sales-AI功能與筆電規格數據處理能力。

## 技術棧
- **後端**: FastAPI + Uvicorn ASGI server
- **前端**: HTML/CSS/JavaScript
- **資料庫**: 
  - DuckDB (筆電規格儲存)
  - SQLite (歷史記錄追蹤)
  - Milvus (向量搜索/相似度匹配)
- **AI/ML**: LangChain + sentence-transformers for RAG

## 核心架構
- MGFD (Multi-Goal Funnel Dialog) 系統架構
- Parent-Child chunking 策略
- 混合搜索 (向量 + 關鍵字)
- LLM 整合 (Ollama gpt-oss:20b)
- Event sourcing 狀態管理