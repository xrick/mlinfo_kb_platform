# Knowledge Manager (`libs/KnowledgeManageHandler/knowledge_manager.py`)

## Purpose & Structure
- `KnowledgeManager` centralizes data and AI connectors for the notebook knowledge base, mixing SQLite/DuckDB tables, vector storage, and LLM glue code `libs/KnowledgeManageHandler/knowledge_manager.py:60-197`.
- The module is written in Traditional Chinese, but the API surface remains Pythonic and is used by server layers for search and recommendation flows.

## Dependency Detection
- Optional imports flag whether Polars, sentence-transformers, and Milvus integrations are available before the class attempts to use them `libs/KnowledgeManageHandler/knowledge_manager.py:27-57`.
- Flags (`POLARS_AVAILABLE`, `LLM_AVAILABLE`, `MILVUS_AVAILABLE`) guard later calls so features degrade gracefully instead of raising import errors; missing pieces funnel to warnings and `None` state.

## Initialization Workflow
- Constructor accepts an optional `base_path`, defaults to the project root, and creates shared configuration such as the in-memory registry `self.knowledge_bases` and Polars defaults `libs/KnowledgeManageHandler/knowledge_manager.py:66-111`.
- `_initialize_default_knowledge_bases` registers the consolidated sales spec database (`semantic_sales_spec`) and the history database when the underlying files are present `libs/KnowledgeManageHandler/knowledge_manager.py:113-138`.
- `_initialize_polars_helper` attempts to instantiate `PolarsHelper` with the stored config; failures keep `polars_helper` as `None` `libs/KnowledgeManageHandler/knowledge_manager.py:140-151`.
- `_initialize_ai_components` wires sentence embeddings, an LLM client, and the Milvus query wrapper using parameters from `config.py`; any failure leaves those handles unset but logged `libs/KnowledgeManageHandler/knowledge_manager.py:153-196`.

## Knowledge Base Registry & SQLite Utilities
- Registry helpers (`add_knowledge_base`, `remove_knowledge_base`, `list_knowledge_bases`, `get_knowledge_base_info`) expose a minimal CRUD API over the in-memory metadata table `libs/KnowledgeManageHandler/knowledge_manager.py:198-254`.
- `query_sqlite_knowledge_base` provides a generic SQLite executor with row-to-dict conversion and guardrails for type mismatches or missing files `libs/KnowledgeManageHandler/knowledge_manager.py:255-296`.
- `query_sales_specs` is a higher-level helper that assembles filter clauses, although it currently points at a `sales_specs` registry entry that is never defined and uses the SQL `IN` operator with a single placeholder—both issues need correction before production use `libs/KnowledgeManageHandler/knowledge_manager.py:298-359`.
- `search_semantic_knowledge_base` offers a legacy keyword search against the `nbtypes` table for when vector search is unavailable `libs/KnowledgeManageHandler/knowledge_manager.py:369-417`.
- Structural inspection helpers expose schema metadata (`get_knowledge_base_schema`), aggregated stats (`get_knowledge_base_stats`), data exports, and backup routines for SQLite-backed stores `libs/KnowledgeManageHandler/knowledge_manager.py:419-557`.

## Polars & DuckDB Integration
- `query_polars_data` delegates to `PolarsHelper` to execute lazy or eager queries, wraps the results in a consistent response schema, and can fall back to SQLite if the helper raises `libs/KnowledgeManageHandler/knowledge_manager.py:598-655`.
- `get_polars_stats`, `_fallback_to_sqlite_query`, and `_convert_polars_to_sql` provide diagnostics plus a simplistic path for translating Polars expressions into SQL when a fallback is needed `libs/KnowledgeManageHandler/knowledge_manager.py:682-787`.
- Several downstream routines that expect SQLite still reference the `semantic_sales_spec` knowledge base, so in practice the DuckDB file must be queryable through both Polars and SQLite interfaces.

## Vector Search & Retrieval
- `milvus_semantic_search` turns an input query into an embedding and runs a Milvus vector search, returning normalized scores and key chunk metadata `libs/KnowledgeManageHandler/knowledge_manager.py:791-865`.
- `parent_child_retrieval` combines child chunk retrieval with follow-up parent lookups to produce richer context bundles, which feed higher-level workflows `libs/KnowledgeManageHandler/knowledge_manager.py:867-909`.
- `hybrid_search` packages either the parent-child strategy or a plain vector search into a summary object that higher layers can surface directly `libs/KnowledgeManageHandler/knowledge_manager.py:927-1007`.
- `get_milvus_status` captures collection health information when the Milvus connector is live `libs/KnowledgeManageHandler/knowledge_manager.py:1002-1045`.

## LLM Utilities
- `encode_text` and `encode_texts` expose thin wrappers around the sentence-transformers encoder, while `llm_query` delegates prompts to the initialized LLM client with optional context injection `libs/KnowledgeManageHandler/knowledge_manager.py:1039-1084`.
- `get_llm_status` reports which pieces of the LLM stack initialized successfully for diagnostics `libs/KnowledgeManageHandler/knowledge_manager.py:1085-1102`.

## Gaming Laptop Workflows
- `query_specs_by_product_ids` queries the consolidated spec table via Polars (preferred) or SQLite fallback, returning detailed rows keyed by model type `libs/KnowledgeManageHandler/knowledge_manager.py:1106-1169`.
- `evaluate_gaming_performance` scores laptops across CPU, GPU, memory, storage, and thermals with weighted heuristics to derive an overall recommendation grade `libs/KnowledgeManageHandler/knowledge_manager.py:1171-1289`.
- `gaming_laptop_search` orchestrates semantic retrieval, spec enrichment, scoring, and optional LLM summarization; note that it mistakenly calls `self.query_llm` instead of the defined `llm_query` helper, which will raise an `AttributeError` if hit `libs/KnowledgeManageHandler/knowledge_manager.py:1291-1418`.

## Product Code Extraction & General Search
- `_validate_modeltype_exists` checks candidate model codes against the DuckDB file to vet matches during query parsing `libs/KnowledgeManageHandler/knowledge_manager.py:1431-1469`.
- `_extract_product_codes_original` and `_extract_product_codes` implement layered pattern matching (alphanumeric, numeric with context, database validation) to pull product identifiers out of free-form text `libs/KnowledgeManageHandler/knowledge_manager.py:1471-1540`.
- `search_product_data` is the primary entry point for generic spec lookups: it runs Milvus retrieval, merges in detected product codes, pulls detailed specs from DuckDB, and returns a structured response with status flags for each stage `libs/KnowledgeManageHandler/knowledge_manager.py:1541-1696`.
- A legacy implementation of `search_product_data` remains commented at the end of the file for reference `libs/KnowledgeManageHandler/knowledge_manager.py:1699-1781`.

## Notable Considerations & Follow-ups
- Ensure a `sales_specs` knowledge base entry exists or adjust `query_sales_specs` to use the registered `semantic_sales_spec` key and a proper `LIKE` expression `libs/KnowledgeManageHandler/knowledge_manager.py:298-359`.
- Align the storage type metadata for `semantic_sales_spec` with how downstream SQLite-based helpers consume it to avoid type-guard failures `libs/KnowledgeManageHandler/knowledge_manager.py:113-138` and `libs/KnowledgeManageHandler/knowledge_manager.py:255-296`.
- Rename `llm_query` or update callers like `gaming_laptop_search` to prevent runtime errors when requesting LLM-generated analysis `libs/KnowledgeManageHandler/knowledge_manager.py:1085-1102` and `libs/KnowledgeManageHandler/knowledge_manager.py:1394`.
- The `_convert_polars_to_sql` logic is intentionally naive; complex Polars expressions will need a richer translation layer before fallback queries produce accurate results `libs/KnowledgeManageHandler/knowledge_manager.py:758-787`.
