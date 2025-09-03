我先定位 `libs/MGFDKernel.py` 中五個模組的初始化方式，並在各模組目錄中搜尋主要對外統一介面（類或函式），僅閱讀不修改任何程式碼。

[17 tools called]

[MODE: REVIEW]

以下為嚴格只讀檢查結果（未更動任何程式碼）。

### MGFDKernel 五大模組的初始化方式
- 檔案：`libs/MGFDKernel.py`
- 狀態：
  - 五大模組的 import 皆被註解（L13-L18）
  - 在 `__init__` 中僅以 None 佔位（L41-L45）：
    - `self.user_input_handler = None`
    - `self.prompt_manager = None`
    - `self.knowledge_manager = None`
    - `self.response_generator = None`
    - `self.state_manager = None`
  - 提供外部 setter（L384-L407）：
    - `set_user_input_handler(handler)`
    - `set_prompt_manager(manager)`
    - `set_knowledge_manager(manager)`
    - `set_response_generator(generator)`
    - `set_state_manager(manager)`

結論：MGFDKernel 本體不主動 new 實體，目前採外部注入（setter）策略，預設為 None。

### 五大模組的主要對外統一介面

1) UserInputHandler
- 檔案：`libs/UserInputHandler/UserInputHandler.py`
- 主要類別：`UserInputHandler`
- 對外方法（被 MGFDKernel 使用）：
  - `async def parse(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]`（L111-L119）
- MGFDKernel 依賴：
  - `input_result = await self.user_input_handler.parse(message, context)`（`MGFDKernel._process_message_internal` L236-L239）
- 一致性：接口存在且為 async，符合 Kernel 期待。

2) KnowledgeManageHandler
- 檔案：`libs/KnowledgeManageHandler/knowledge_manager.py`
- 主要類別：`KnowledgeManager`
- 對外常見方法（非 async，多以同步方法實作，範例）：
  - `def query_sales_specs(...) -> Optional[List[Dict[str, Any]]]`（L221）
  - `def search_semantic_knowledge_base(query: str, ...) -> Optional[List[Dict[str, Any]]]`（L281）
  - Polars 相關：
    - `def query_polars_data(...) -> Optional[Dict[str, Any]]`（L508）
    - `def get_polars_stats(...) -> Optional[Dict[str, Any]]`（L592）
- MGFDKernel 依賴（重要異常）：
  - 呼叫了 `await self.knowledge_manager.search(context)`（`MGFDKernel._process_message_internal` L262-L265）
  - 然而 `KnowledgeManager` 並無 `async def search(context)` 與該簽名的對外方法
- 結論：Kernel 期望的統一接口 `search(context)` 不存在；現有 API 為多個同步方法且參數/返回值型別不同。

3) PromptManagementHandler
- 檔案：`libs/PromptManagementHandler/prompt_manager.py`
- 主要類別：`PromptManager`
- 對外方法（同步）：
  - `def get_prompt(prompt_name: str, force_reload: bool = False) -> Optional[str]`（L81-L91）
  - `def get_multiple_prompts(prompt_names: List[str], ...) -> Dict[str, str]`（L118-L136）
- MGFDKernel 使用狀態：
  - 目前 Kernel 中未呼叫 `PromptManager` 方法（`prompt_manager` 僅設置為 None 且沒被使用）
- 結論：有明確介面，但未與 Kernel 對接。

4) ResponseGenHandler
- 檔案：`libs/ResponseGenHandler/ResponseGenHandler.py`
- 主要類別：`ResponseGenHandler`
- 對外方法（被 MGFDKernel 使用）：
  - `async def generate(self, context: Dict[str, Any]) -> Dict[str, Any]`（L84-L95）
- MGFDKernel 依賴：
  - `response_result = await self.response_generator.generate(context)`（`MGFDKernel._process_message_internal` L267-L269）
- 一致性：接口存在且為 async，符合 Kernel 期待。

5) StateManageHandler
- 檔案：`libs/StateManageHandler/StateManagementHandler.py`
- 主要類別：`StateManagementHandler`
- 對外方法（與 Kernel 預期相關）：
  - `async def process_state(self, context: Dict[str, Any]) -> Dict[str, Any]`（L148-L157）→ 存在
  - 但 Kernel 還期望：
    - `await self.state_manager.get_session(session_id)`（`MGFDKernel._build_context` L300-L302）→ 未找到 `get_session`
    - `await self.state_manager.update_session(session_id, context)`（`MGFDKernel._process_message_internal` L278-L279）→ 未找到 `update_session`
- 補充：`StateManagementHandler` 內含簡化 DSM 的執行器/引擎初始化，但對外統一介面仍以 `process_state(...)` 為主。
- 結論：`process_state` 符合；但 `get_session`、`update_session` 兩個 Kernel 依賴的對外介面不存在。

### 跨模組一致性與缺口（重點）
- MGFDKernel 當前調用鏈期待的統一介面：
  - UserInputHandler.parse(...) → 存在（async）
  - StateManageHandler.process_state(...) → 存在（async）
  - KnowledgeManager.search(context) → 不存在（Kernel 調用為 async search(context)，而 KM 提供多個同步查詢方法）
  - StateManageHandler.get_session(session_id) → 不存在
  - StateManageHandler.update_session(session_id, context) → 不存在
  - ResponseGenHandler.generate(context) → 存在（async）
- PromptManager 目前未被 Kernel 使用，雖有介面（同步）。

### 總結
- 初始化：五模組在 `MGFDKernel` 內皆為 None 佔位，需透過 setter 外部注入。
- 對外統一介面：
  - 已齊：`UserInputHandler.parse`（async）、`ResponseGenHandler.generate`（async）、`StateManageHandler.process_state`（async）
  - 缺失/不一致：
    - `KnowledgeManager.search(context)`（Kernel 期待）缺失；KM 實作為多個同步具體方法（`query_*`、`search_semantic_*` 等）
    - `StateManageHandler.get_session`、`update_session`（Kernel 期待）缺失
  - `PromptManager` 介面可用，但 Kernel 未使用

如需，我可以再列出行號/方法原文段落以便您對照。