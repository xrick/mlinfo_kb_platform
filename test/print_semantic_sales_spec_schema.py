#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Console tool: Print schema of the Polars/DuckDB database semantic_sales_spec.db

Usage:
  python test/print_semantic_sales_spec_schema.py

Behavior:
  - Attempts to open ./db/semantic_sales_spec.db as a DuckDB database
  - Lists tables and prints each table's schema
  - Prints clear diagnostics if the file is missing or not a valid DuckDB database
"""

import sys
from pathlib import Path

def main() -> int:
    db_path = Path(__file__).resolve().parents[1] / "db" / "semantic_sales_spec.db"
    print(f"[INFO] Target DB path: {db_path}")

    if not db_path.exists():
        print("[ERROR] semantic_sales_spec.db not found under ./db/")
        return 1

    try:
        import duckdb  # DuckDB is commonly used as the execution engine behind Polars SQL
    except Exception as e:
        print("[ERROR] duckdb module is not available. Please install duckdb: pip install duckdb")
        print(f"[DETAIL] {e}")
        return 1

    try:
        con = duckdb.connect(str(db_path))
    except Exception as e:
        print("[ERROR] Failed to open database as DuckDB. The file may not be a DuckDB database.")
        print(f"[DETAIL] {e}")
        return 1

    try:
        # List tables
        try:
            tables = con.execute("SHOW TABLES").fetchall()
        except Exception:
            # DuckDB >=0.8 uses pragma or information_schema
            tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')").fetchall()

        if not tables:
            print("[WARN] No tables found in database.")
            return 0

        print("[INFO] Tables found:")
        for (tbl,) in tables:
            print(f"  - {tbl}")

        print("\n[INFO] Schemas:")
        for (tbl,) in tables:
            print(f"\n-- Schema for table: {tbl}")
            try:
                # PRAGMA table_info works in DuckDB
                rows = con.execute(f"PRAGMA table_info('{tbl}')").fetchall()
                if rows:
                    # columns: cid, name, type, notnull, dflt_value, pk
                    print("cid\tname\ttype\tnotnull\tdefault\tprimary_key")
                    for r in rows:
                        cid, name, coltype, notnull, dflt, pk = r[:6]
                        print(f"{cid}\t{name}\t{coltype}\t{notnull}\t{dflt}\t{pk}")
                else:
                    print("  (no columns reported)")
            except Exception as e:
                print(f"  [ERROR] Failed to read schema for {tbl}: {e}")

        return 0
    finally:
        try:
            con.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())


