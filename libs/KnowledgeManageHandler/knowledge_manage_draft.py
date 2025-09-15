# libs/KnowledgeManageHandler/knowledge_manage_draft.py

##############################General Product Data Search##############################
query_parsing_prompt = """你是一個產品查詢剖析器，專門從中文/英文自然語句中抽取「筆電單一型號」或「整個系列/機系」的名稱，
並以嚴格 JSON 輸出。不要多話，不要加註解。

【任務】
- 從「使用者查詢」中找出：
  1) models: 精確的單一型號（如：ATX834、AYU996、A515-56-73AP、15-eg0021nr、GA401QM、X1C Gen 11、Surface Laptop 5 13.5"）
  2) families: 系列/機系（如：ThinkPad X1 Carbon、MacBook Air、ROG Zephyrus G14、TUF Gaming、Legion 5、IdeaPad 5、Yoga Slim 7）
- 正規化：去除多餘空白、全形轉半形、大小寫不敏感但保留常見習慣（如 ROG Zephyrus）。
- 僅輸出你極有把握的結果；模糊詞（如「輕薄」、「遊戲筆電」）不要放進 models/families。
- 若沒有命中，輸出空陣列。

【輸出 JSON 結構】
{
  "models": [ "<精確單一型號1>", "<精確單一型號2>", ... ],
  "families": [ "<系列/機系名稱1>", "<系列/機系名稱2>", ... ],
  "confidence": 0.0~1.0 之間的數字（整體抽取信心）
}

【範例】
使用者查詢: "請比對 ATX834 與 AYU996 的螢幕"
輸出:
{"models": ["ATX834","AYU996"], "families": [], "confidence": 0.96}
"""
# ------------------------------------------------------------
# 簡單的規則擷取（與 LLM 搭配）：先快抓明顯型號，抓不到再問 LLM
# ------------------------------------------------------------

_MODEL_TOKEN_REGEX = re.compile(
    r"""
    (?<![A-Z0-9-])
    (                           # 常見型號片段（大小寫不敏感）
        [A-Z]{2,}\d{2,}[A-Z0-9-]*   # 例：ATX834、A515-56-73AP、GA401QM
    )
    (?![A-Z0-9-])
    """,
    re.IGNORECASE | re.VERBOSE,
) 

    def _extract_by_rules(self, message: str) -> Tuple[List[str], List[str]]:
        """快速規則抽取：回傳 (models, families)"""
        # models
        models = set(m.strip().replace("  ", " ") for m in _MODEL_TOKEN_REGEX.findall(message))
        # families（以關鍵片段搜索，避免誤抓一般詞）
        fams = set()
        low = message.lower()
        for fam in _FAMILY_CANDIDATES:
            if fam.lower() in low:
                fams.add(fam)
        return (sorted(models), sorted(fams))

    def _safe_dedup_keep_order(items: List[str]) -> List[str]:
        seen = set()
        out = []
        for x in items:
            k = x.strip()
            if not k: 
                continue
            if k.lower() in seen:
                continue
            seen.add(k.lower())
            out.append(k)
        return out

    def _normalize_names(models: List[str], families: List[str]) -> Tuple[List[str], List[str]]:
        # 基本正規化：全形轉半形、Trim、大小寫保留常用樣式
        def to_halfwidth(s: str) -> str:
            res = []
            for ch in s:
                code = ord(ch)
                if 0xFF01 <= code <= 0xFF5E:
                    code -= 0xFEE0
                elif code == 0x3000:
                    code = 0x20
                res.append(chr(code))
            return "".join(res)
        models = [to_halfwidth(m).strip() for m in models]
        families = [to_halfwidth(f).strip() for f in families]
        return (_safe_dedup_keep_order(models), _safe_dedup_keep_order(families))
            
    def general_product_data_search(self, message: str) -> Dict[str, Any]:
        """
        通用產品規格搜尋函式
        使用語義搜尋和 DuckDB 規格查詢
        """
        try:
            self.logger.info(f"[general_product_data_search] 開始：{message!r}")

            # 0) 先用規則抽取；若不夠，再用 LLM 解析補齊
            rule_models, rule_families = _extract_by_rules(message)
            rule_models, rule_families = _normalize_names(rule_models, rule_families)

            llm_models: List[str] = []
            llm_families: List[str] = []
            llm_conf: float = 0.0

            if not rule_models and not rule_families:
                # 呼叫你現有的 LLM 介面；以下假設有 self.llm_completion(prompt: str) -> str
                prompt = query_parsing_prompt.format(message=message.replace("\n", " ").strip())
                self.logger.info("[general_product_data_search] 使用 LLM 解析查詢")
                llm_raw = self.llm_completion(prompt)  # 你可改為 self.ollama_call(...) 或其他
                try:
                    parsed = json.loads(llm_raw.strip())
                    llm_models = parsed.get("models", []) or []
                    llm_families = parsed.get("families", []) or []
                    llm_conf = float(parsed.get("confidence", 0.0))
                except Exception as parse_err:
                    self.logger.warning(f"[general_product_data_search] LLM JSON 解析失敗：{parse_err}; 原始輸出：{llm_raw!r}")

                # 合併規則與 LLM 的抽取
                models = _safe_dedup_keep_order((rule_models or []) + (llm_models or []))
                families = _safe_dedup_keep_order((rule_families or []) + (llm_families or []))
                self.logger.info(f"[general_product_data_search] 擷取結果 models={models}, families={families}, llm_conf={llm_conf:.2f}")

                if not models and not families:
                    return {
                        "query": message,
                        "status": "no_target_found",
                        "note": "未偵測到明確的單一型號或系列名稱",
                        "products": []
                    }

                # 1) 用擷取的 models/families 組合查詢詞，進 Milvus 語義搜尋
                #    需求是「以此進行 milvus 語意搜尋 product_id」
                #    做法：把 models + families 當成多個 query_text，彙整回傳的 product_id
                candidate_queries = models + families
                milvus_topk = 12 if families else 10  # 系列可能較廣，抓多一點
                found_product_ids: List[str] = []

                for q in candidate_queries:
                    res = self.milvus_semantic_search(query_text=q, top_k=milvus_topk)
                    for item in (res or []):
                        pid = str(item.get("product_id", "")).strip()
                        if pid:
                            found_product_ids.append(pid)

                found_product_ids = _safe_dedup_keep_order(found_product_ids)
                self.logger.info(f"[general_product_data_search] Milvus 回收 product_id 數量：{len(found_product_ids)}")

                if not found_product_ids:
                    return {
                        "query": message,
                        "status": "no_results_milvus",
                        "models": models,
                        "families": families,
                        "products": []
                    }

                # 2) 以 product_id 當作 nbtypes.modeltype 的比對鍵，在 DuckDB 查規格
                kb_info = self.knowledge_bases.get("semantic_sales_spec")
                if not kb_info:
                    self.logger.error("語義銷售規格知識庫不存在 (semantic_sales_spec)")
                    return {
                        "query": message,
                        "status": "no_database",
                        "models": models,
                        "families": families,
                        "matched_keys": found_product_ids,
                        "products": []
                    }

                import duckdb  # lazy import

                essential_fields = [
                    "modeltype", "modelname", "brand", "series", "cpu", "gpu",
                    "memory", "storage", "lcd", "battery", "weight",
                    "audio", "wireless", "bluetooth"
                ]

                placeholders = ",".join(["?"] * len(found_product_ids))
                sql = f"""
                    SELECT {', '.join(essential_fields)}
                    FROM nbtypes
                    WHERE modeltype IN ({placeholders})
                """

                self.logger.info("[general_product_data_search] 執行 DuckDB IN 查詢（使用參數化避免注入）")
                specs: List[Dict[str, Any]] = []
                con = duckdb.connect(kb_info["path"])
                try:
                    cur = con.execute(sql, found_product_ids)
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description] if cur.description else []
                    for r in rows:
                        specs.append({cols[i]: r[i] for i in range(len(cols))})
                finally:
                    try:
                        con.close()
                    except Exception:
                        pass

                if not specs:
                    return {
                        "query": message,
                        "status": "no_spec_data",
                        "models": models,
                        "families": families,
                        "matched_keys": found_product_ids,
                        "products": []
                    }

                return {
                "query": message,
                "status": "success",
                "models": models,
                "families": families,
                "matched_keys": found_product_ids,
                "count": len(specs),
                "products": specs
            }

        except Exception as e:
            self.logger.exception(f"[general_product_data_search] 失敗：{e}")
            return {
                "query": message,
                "status": "error",
                "error": str(e),
                "products": []
            }
    