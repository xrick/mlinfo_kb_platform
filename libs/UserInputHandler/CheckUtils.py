import json

def ChkKeyword(input_sentence: str, keyword_db: dict) -> dict:
    """
    檢查輸入語句是否包含資料庫中定義的關鍵字或其同義詞。

    這個函式會遍歷關鍵字資料庫，對於每個主關鍵字，它會檢查
    主關鍵字本身或其任何一個同義詞是否存在於輸入語句中。
    一旦找到第一個匹配項，函式就會立即回傳結果。

    Args:
        input_sentence: 使用者輸入的語句字串。
        keyword_db: 一個字典，其結構定義了關鍵字、同義詞及元資料。

    Returns:
        如果找到匹配項，則回傳一個包含匹配資訊的字典：
        {"ret": "yes", "kw": "主關鍵字", "區間": "對應的重量區間值"}
        如果未找到任何匹配項，則回傳：
        {"ret": "no"}
    """
    # 遍歷資料庫中的每一個主關鍵字及其對應的資料
    for main_keyword, data in keyword_db.items():
        # 建立一個包含主關鍵字及其所有同義詞的搜尋列表
        # 使用 .get("同意詞", []) 來安全地處理可能不存在 "同意詞" 的情況
        search_terms = [main_keyword] + data.get("同意詞", [])

        # 檢查搜尋列表中的每一個詞是否出現在輸入語句中
        for term in search_terms:
            if term in input_sentence:
                # 一旦找到匹配，立即提取元資料並準備回傳
                # 同樣使用 .get() 來安全地存取可能不存在的巢狀鍵
                metadata = data.get("metadata", {})
                interval = metadata.get("重量區間", "nodata")
                
                return {
                    "ret": "yes",
                    "kw": main_keyword,  # 關鍵是回傳「主關鍵字」，而非匹配到的同義詞
                    "區間": interval
                }
    
    # 如果遍歷完所有關鍵字都沒有找到匹配項，則回傳 "no"
    return {"ret": "no"}