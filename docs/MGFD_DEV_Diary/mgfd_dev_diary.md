# MGFD 開發日誌

## 開發規則遵守記錄

### 2025-08-11 16:21
**開發規則確認與遵守**
- 確認完全遵守開發規則：
  1. 做任何程式碼修改前，必須先在 mgfd_dev_diary.md 文件中記錄計畫的描述，並記錄準確的時間：年-月-日-時
  2. 在進行程式碼變更、新增、刪除的同時，必須先在 mgfd_dev_diary.md 文件中描述所有的變動，並註明為何要做這樣的變動

**當前狀態**
- 用戶要求確認開發規則遵守
- 已檢查並確認 mgfd_dev_diary.md 文件存在
- 準備開始記錄所有後續的開發活動

**下一步行動**
- 等待用戶的具體開發任務指示
- 所有程式碼修改都將在此日誌中預先記錄

### 2025-08-11 17:30
**變動類別: debug**

**問題分析與記錄**

**問題1：LLM必須回覆「工作」二字才能繼續對話**
- **問題描述**：用戶輸入「工作」後，系統只能識別「工作」二字，多一個字都不行
- **問題根源分析**：
  1. 在 `dialogue_manager.py` 的 `extract_slots_from_input` 方法中，槽位提取邏輯過於嚴格
  2. 第175行：`if any(word in user_input_lower for word in ["工作", "business", "辦公", "商務"]):`
  3. 問題在於 `word in user_input_lower` 的邏輯：當用戶輸入「工作用」時，「工作」確實包含在輸入中，但系統可能因為其他邏輯而無法正確處理
  4. 狀態機在 `_handle_elicitation` 方法中可能沒有正確更新槽位狀態

**問題2：LLM第二次回覆太過制式**
- **問題描述**：LLM的第二個回覆只有固定的問題「您主要會用這台筆電做什麼？遊戲、工作、學習還是其他用途？」
- **問題根源分析**：
  1. 在 `models.py` 第67行：`example_question="您主要會用這台筆電做什麼？遊戲、工作、學習還是其他用途？"`
  2. 在 `dialogue_manager.py` 的 `_generate_elicitation_question` 方法中，系統直接返回 `slot_config.example_question`
  3. 缺乏動態問題生成邏輯，沒有根據對話上下文和已填寫槽位來調整問題內容
  4. 沒有實現「Think, Then Act」的兩層提示系統

**技術架構問題**：
1. **槽位提取邏輯過於簡單**：只使用簡單的關鍵字匹配，缺乏語義理解
2. **問題生成缺乏個性化**：所有問題都是預設的固定模板
3. **狀態管理不完整**：槽位填充後的狀態更新可能不正確
4. **缺乏 LLM 驅動的智能決策**：系統主要依賴規則邏輯，沒有充分利用 LLM 的語言理解能力

**下一步行動計畫**：
1. 修復槽位提取邏輯，支援更靈活的輸入識別
2. 實現動態問題生成，根據對話上下文調整問題內容
3. 完善狀態管理，確保槽位正確更新
4. 整合真正的「Think, Then Act」兩層提示系統

### 2025-08-11 17:45
**變動類別: innovate**

**具體修改計畫制定**

**創新解決方案概述**：
基於對現有系統的深入分析，我將實現一個真正的「Think, Then Act」兩層提示系統，結合 Redis 緩存和智能槽位管理，徹底解決當前的問題。

**需要安裝的軟體套件**：
```bash
pip install redis openai anthropic langchain-openai langchain-anthropic
```

**檔案變動詳細計畫**：

#### 1. 新增檔案
- `libs/mgfd_cursor/llm_manager.py` - LLM 管理器，支援多種 LLM 提供商
- `libs/mgfd_cursor/prompt_templates.py` - 動態提示詞模板系統
- `libs/mgfd_cursor/slot_extractor.py` - 智能槽位提取器
- `libs/mgfd_cursor/redis_cache.py` - Redis 緩存管理器
- `config/mgfd_config.py` - MGFD 專用配置檔案
- `prompts/mgfd/think_prompts.json` - Think 階段的提示詞模板
- `prompts/mgfd/act_prompts.json` - Act 階段的提示詞模板

#### 2. 修改檔案
- `libs/mgfd_cursor/dialogue_manager.py` - 重構為真正的兩層提示系統
- `libs/mgfd_cursor/state_machine.py` - 整合新的 LLM 驅動邏輯
- `libs/mgfd_cursor/models.py` - 擴展槽位架構和狀態模型
- `api/mgfd_routes.py` - 更新 API 以支援新的架構
- `config.py` - 添加 MGFD 和 Redis 配置
- `requirements.txt` - 添加新的依賴套件

#### 3. 刪除檔案
- 無（保留現有架構，進行增量改進）

**核心架構變更**：

1. **兩層提示系統實作**：
   - Think 階段：使用 LLM 分析對話狀態，決定下一步行動
   - Act 階段：根據 Think 階段的決策，生成個性化回應

2. **智能槽位提取**：
   - 使用 LLM 進行語義理解，而非簡單關鍵字匹配
   - 支援模糊匹配和上下文理解

3. **Redis 緩存整合**：
   - 緩存 LLM 回應，提升性能
   - 儲存對話狀態，支援跨會話記憶

4. **動態問題生成**：
   - 根據已填寫槽位和對話歷史，生成個性化問題
   - 避免重複詢問相同資訊

**預期效果**：
- 解決「只能回覆工作二字」的限制
- 實現真正的個性化對話體驗
- 提升系統的智能性和用戶體驗
- 建立可擴展的 MGFD 架構基礎

---
*此文件用於記錄所有 MGFD 相關的開發活動，確保開發過程的透明性和可追溯性*
