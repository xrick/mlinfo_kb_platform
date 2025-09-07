#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Console runner to invoke KnowledgeManager.search_product_data and print JSON.

Usage:
  python test/run_search_product_data.py "請介紹輕便的筆電"

It will:
  - Initialize KnowledgeManager
  - Call search_product_data(message)
  - Print the returned JSON
"""

import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from libs.KnowledgeManageHandler.knowledge_manager import KnowledgeManager  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("[USAGE] python test/run_search_product_data.py <query>")
        return 1

    query = sys.argv[1]
    km = KnowledgeManager()
    result = km.search_product_data(query)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())


