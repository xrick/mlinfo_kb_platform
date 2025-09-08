#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將 db/semantic_sales_spec.db 內所有來源表（spec_data_% 與特例 spec_AC01_result）
合併為單表 nbtypes，輸出至 db/semantic_sales_spec_all.db（覆寫）。

規格摘要：
- 欄位統一：以所有來源表的欄位全集為準，缺欄以 NULL 補齊；所有欄位 CAST 為 TEXT。
- 去重主鍵：modeltype + modelname + product_id；時間戳優先（updated_at > last_updated > modified_at > timestamp > created_at）。
- 來源 DB：db/semantic_sales_spec.db
- 目標 DB：db/semantic_sales_spec_all.db（覆寫）
- 目標表：nbtypes；並嘗試在 modeltype 建索引。

錯誤處理：
- 找不到來源 DB 或來源表為空時，清楚列印錯誤並以非零狀態離開。
- 建索引若不支援，將記錄警告但不中止。
"""

from __future__ import annotations

import os
import sys
import logging
from typing import List, Dict, Set, Tuple

try:
    import duckdb  # type: ignore
except Exception as e:  # pragma: no cover
    print(f"[ERROR] duckdb 未安裝或載入失敗: {e}")
    sys.exit(1)


# 日誌設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


SOURCE_DB = os.path.join('db', 'semantic_sales_spec.db')
TARGET_DB = os.path.join('db', 'semantic_sales_spec_all.db')
TARGET_TABLE = 'nbtypes'

# 時間戳優先序欄位（由高到低）
TS_PRIORITY = [
    'updated_at', 'last_updated', 'modified_at', 'timestamp', 'created_at'
]


def get_all_source_tables(con: "duckdb.DuckDBPyConnection") -> List[str]:
    """取得需要合併的來源表清單。包含 spec_data_% 與特例 spec_AC01_result。"""
    rows = con.execute("SHOW TABLES").fetchall()
    tables = [r[0] for r in rows]
    selected = [t for t in tables if t.startswith('spec_data_')]
    if 'spec_AC01_result' in tables:
        selected.append('spec_AC01_result')
    return sorted(list(dict.fromkeys(selected)))


def get_table_columns(con: "duckdb.DuckDBPyConnection", table_name: str) -> List[Tuple[str, str]]:
    """回傳表的欄位 schema 列表 [(col, type), ...]"""
    try:
        return con.execute(f"DESCRIBE {table_name}").fetchall()
    except Exception as e:
        logger.warning(f"DESCRIBE 失敗: {table_name}: {e}")
        return []


def build_union_all_query(con: "duckdb.DuckDBPyConnection", tables: List[str]) -> Tuple[str, List[str]]:
    """
    根據來源表生成 UNION ALL SQL。所有欄位以全集為準，CAST 為 TEXT，缺欄補 NULL AS col。
    回傳 (union_sql, all_columns)
    """
    # 1) 收集欄位全集（保持穩定順序）
    all_cols_order: List[str] = []
    all_cols_set: Set[str] = set()
    per_table_cols: Dict[str, Set[str]] = {}

    for t in tables:
        schema = get_table_columns(con, t)
        cols = [c[0] for c in schema] if schema else []
        per_table_cols[t] = set(cols)
        for c in cols:
            if c not in all_cols_set:
                all_cols_set.add(c)
                all_cols_order.append(c)

    if not all_cols_order:
        raise RuntimeError("來源表的欄位全集為空，無法合併。")

    # 2) 為每個表生成齊次 SELECT（全欄 CAST TEXT；缺欄補 NULL）
    select_sqls: List[str] = []
    for t in tables:
        cols_exprs = []
        table_cols = per_table_cols.get(t, set())
        for col in all_cols_order:
            if col in table_cols:
                cols_exprs.append(f"CAST({col} AS TEXT) AS {col}")
            else:
                cols_exprs.append(f"CAST(NULL AS TEXT) AS {col}")
        select_sqls.append(f"SELECT {', '.join(cols_exprs)} FROM {t}")

    union_sql = "\nUNION ALL\n".join(select_sqls)
    return union_sql, all_cols_order


def pick_timestamp_expr(all_columns: List[str]) -> str:
    """根據優先序，產生可用作排序用的時間戳表達式 ts_pick。若無任一欄位，回傳 NULL。"""
    for ts_col in TS_PRIORITY:
        if ts_col in all_columns:
            # 將文本轉為 TIMESTAMP，無法解析時為 NULL
            return f"try_cast({ts_col} AS TIMESTAMP)"
    return "NULL"


def build_dedup_query(all_columns: List[str], raw_table: str = "__nbtypes_raw") -> str:
    """
    基於 (modeltype, modelname) + 時間戳優先序，取 row_number=1 作為去重，產出 nbtypes。
    注意：product_id 僅存在於 Milvus，DuckDB 中不包含此欄位。
    """
    # 確保最低欄位存在於輸出（若不在全集，將在上一階段已補為 NULL AS col）
    partition_keys = ["modeltype", "modelname"]

    ts_pick = pick_timestamp_expr(all_columns)
    order_expr = f"{ts_pick} DESC NULLS LAST"

    # 移除 product_id 欄位（僅存在於 Milvus）
    select_cols_list = [col for col in all_columns if col != 'product_id']
    select_cols = ", ".join(select_cols_list)
    dedup_sql = f"""
        CREATE OR REPLACE TABLE {TARGET_TABLE} AS
        WITH ranked AS (
            SELECT
                {select_cols},
                ROW_NUMBER() OVER (
                    PARTITION BY {', '.join(partition_keys)}
                    ORDER BY {order_expr}
                ) AS rn
            FROM {raw_table}
        )
        SELECT {select_cols}
        FROM ranked
        WHERE rn = 1
    """
    return dedup_sql


def create_index_if_supported(con: "duckdb.DuckDBPyConnection") -> None:
    """嘗試在 modeltype 建索引；若版本不支援則記錄告警並略過。"""
    try:
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_{TARGET_TABLE}_modeltype ON {TARGET_TABLE}(modeltype)")
        logger.info("已建立索引：idx_nbtypes_modeltype(modeltype)")
    except Exception as e:
        logger.warning(f"建立索引失敗或不支援，已略過：{e}")


def main() -> int:
    logger.info("=== 開始合併 semantic_sales_spec.db → semantic_sales_spec_all.db ===")

    if not os.path.exists(SOURCE_DB):
        logger.error(f"找不到來源 DB：{SOURCE_DB}")
        return 2

    # 覆寫目標 DB：若存在則刪除
    if os.path.exists(TARGET_DB):
        try:
            os.remove(TARGET_DB)
            logger.info(f"已移除既有目標 DB：{TARGET_DB}")
        except Exception as e:
            logger.error(f"無法刪除既有目標 DB：{TARGET_DB}: {e}")
            return 3

    # 來源連線（唯讀）與目標連線（可寫）
    try:
        src = duckdb.connect(SOURCE_DB, read_only=True)
        dst = duckdb.connect(TARGET_DB)
    except Exception as e:
        logger.error(f"DuckDB 連線失敗：{e}")
        return 4

    try:
        tables = get_all_source_tables(src)
        if not tables:
            logger.error("來源 DB 中找不到任何符合規則的表（spec_data_% 或 spec_AC01_result）")
            return 5
        logger.info(f"來源表共 {len(tables)}：{tables}")

        union_sql, all_columns = build_union_all_query(src, tables)
        logger.info(f"欄位全集共 {len(all_columns)} 個欄位：{all_columns}")

        # 在來源 DB 執行 UNION，取回 DataFrame 後寫入目標 DB
        raw_df = src.execute(union_sql).fetchdf()
        dst.register("__nbtypes_raw_df", raw_df)
        dst.execute("CREATE OR REPLACE TABLE __nbtypes_raw AS SELECT * FROM __nbtypes_raw_df")
        raw_count = len(raw_df)
        logger.info(f"__nbtypes_raw 筆數：{raw_count}")

        # 去重輸出 nbtypes
        dedup_sql = build_dedup_query(all_columns, raw_table="__nbtypes_raw")
        dst.execute(dedup_sql)
        total_count = dst.execute(f"SELECT COUNT(*) FROM {TARGET_TABLE}").fetchone()[0]

        # 基本統計：去重差值
        distinct_count = dst.execute(
            f"SELECT COUNT(*) FROM (SELECT DISTINCT modeltype, modelname FROM {TARGET_TABLE})"
        ).fetchone()[0]
        logger.info(f"nbtypes 筆數：{total_count}，distinct(主鍵) 筆數：{distinct_count}")

        # 建索引（若支援）
        create_index_if_supported(dst)

        # 簡易驗證：檢查必要欄位存在與 NOT NULL 比例
        must_cols = ['modeltype', 'modelname']
        for c in must_cols:
            if c not in all_columns:
                logger.warning(f"必要欄位缺失：{c}（已以 NULL 補齊）")
            else:
                notnull = dst.execute(f"SELECT COUNT(*) FROM {TARGET_TABLE} WHERE {c} IS NOT NULL").fetchone()[0]
                logger.info(f"欄位 {c} 非空筆數：{notnull}/{total_count}")

        logger.info("=== 合併完成 ===")
        return 0

    except Exception as e:
        logger.error(f"合併過程失敗：{e}", exc_info=True)
        return 6
    finally:
        try:
            src.close()
        except Exception:
            pass
        try:
            dst.close()
        except Exception:
            pass


if __name__ == '__main__':
    code = main()
    sys.exit(code)


