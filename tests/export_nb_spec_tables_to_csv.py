#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Console tool: Export all tables from SQLite db/nb_spec_0250821v1.db to CSV files under test/

Usage:
  python test/export_nb_spec_tables_to_csv.py

Behavior:
  - Connects to ./db/nb_spec_0250821v1.db via sqlite3
  - Lists all tables in sqlite_master
  - Exports each table to test/<table>.csv with UTF-8 encoding and headers
  - Skips SQLite internal tables (sqlite_*)
"""

import sys
import csv
import sqlite3
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    db_path = project_root / "db" / "nb_spec_0250821v1.db"
    out_dir = project_root / "test"
    print(f"[INFO] Target DB path: {db_path}")

    if not db_path.exists():
        print("[ERROR] nb_spec_0250821v1.db not found under ./db/")
        return 1

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
    except Exception as e:
        print("[ERROR] Failed to open database as SQLite.")
        print(f"[DETAIL] {e}")
        return 1

    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall() if not r[0].startswith("sqlite_")]

        if not tables:
            print("[WARN] No user tables found in database.")
            return 0

        out_dir.mkdir(parents=True, exist_ok=True)

        exported = 0
        for tbl in tables:
            out_file = out_dir / f"{tbl}.csv"
            print(f"[INFO] Exporting table '{tbl}' -> {out_file}")
            try:
                cur.execute(f"SELECT * FROM '{tbl}'")
                rows = cur.fetchall()
                headers = rows[0].keys() if rows else [d[0] for d in cur.description]

                with out_file.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    for row in rows:
                        writer.writerow([row[h] for h in headers])
                exported += 1
            except Exception as e:
                print(f"[ERROR] Failed to export table {tbl}: {e}")

        print(f"[INFO] Export completed. {exported}/{len(tables)} tables exported.")
        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
