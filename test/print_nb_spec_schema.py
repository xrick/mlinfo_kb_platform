#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Console tool: Print schema of the SQLite database db/nb_spec_0250821v1.db

Usage:
  python test/print_nb_spec_schema.py

Behavior:
  - Connects to ./db/nb_spec_0250821v1.db via sqlite3
  - Lists tables and prints each table's schema (columns, types, constraints)
  - Prints clear diagnostics if the file is missing or not a valid SQLite DB
"""

import sys
import sqlite3
from pathlib import Path


def print_table_schema(conn: sqlite3.Connection, table: str) -> None:
    print(f"\n-- Schema for table: {table}")
    try:
        cur = conn.cursor()
        # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
        cur.execute(f"PRAGMA table_info('{table}')")
        rows = cur.fetchall()
        if not rows:
            print("  (no columns reported)")
        else:
            print("cid\tname\ttype\tnotnull\tdefault\tprimary_key")
            for cid, name, coltype, notnull, dflt, pk in rows:
                print(f"{cid}\t{name}\t{coltype}\t{notnull}\t{dflt}\t{pk}")

        # Show indexes
        cur.execute(f"PRAGMA index_list('{table}')")
        idx_list = cur.fetchall()
        if idx_list:
            print("  Indexes:")
            for idx in idx_list:
                # idx tuple: (seq, name, unique, origin, partial)
                print(f"    - name={idx[1]}, unique={idx[2]}")
        else:
            print("  (no indexes)")

    except Exception as e:
        print(f"  [ERROR] Failed to read schema for {table}: {e}")


def main() -> int:
    db_path = Path(__file__).resolve().parents[1] / "db" / "nb_spec_0250821v1.db"
    print(f"[INFO] Target DB path: {db_path}")

    if not db_path.exists():
        print("[ERROR] nb_spec_0250821v1.db not found under ./db/")
        return 1

    try:
        conn = sqlite3.connect(str(db_path))
    except Exception as e:
        print("[ERROR] Failed to open database as SQLite.")
        print(f"[DETAIL] {e}")
        return 1

    try:
        cur = conn.cursor()
        # List tables from sqlite_master
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]

        if not tables:
            print("[WARN] No tables found in database.")
            return 0

        print("[INFO] Tables found:")
        for tbl in tables:
            print(f"  - {tbl}")

        print("\n[INFO] Schemas:")
        for tbl in tables:
            print_table_schema(conn, tbl)

        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())


