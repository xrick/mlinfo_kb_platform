import json
import os
from typing import TypedDict, List, Dict, Any, Literal

# --- 1. 系統設定與資料結構定義 ---

# 模擬前端傳來的原始使用者輸入
USER_QUERY = "請幫我介紹適合業務工作，快速開關機，且攜帶方便的筆電"
SESSION_ID = "user_abc_123"  # 每個使用者一個獨立的 Session ID
DB_FILE = "session_db.json" # 用於模擬 Redis 的 JSON 資料庫檔案

# 定義「對話狀態」的資料結構，與報告中一致
class DialogueState(TypedDict):
    """
    代表一個獨立 session 的完整對話狀態。
    """
    session_id: str
    chat_history: List]
    filled_slots: Dict[str, Any]

# 定義筆電銷售所需的「槽位綱要 (Slot Schema)」
# 'required' 標記了是否為完成推薦的必要資訊
SLOT_SCHEMA = {
    "use_case": {"type": "String", "required": True},
    "portability": {"type": "String", "required": True},
    "performance_features": {"type": "List", "required": False},
    "budget": {"type": "String", "required": True},
    "screen_size": {"type": "String", "required": True},
}

# --- 2. 模擬資料庫 (JSON as Redis) ---

def load_session_state(session_id: str) -> DialogueState:
    """
    從 JSON 檔案中讀取指定 session_id 的對話狀態。
    如果檔案或 session 不存在，則回傳一個全新的初始狀態。
    """
    if not os.path.exists(DB_FILE):
        return DialogueState(session_id=session_id, chat_history=, filled_slots={})

    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            state_data = data.get(session_id)
            if state_data:
                return DialogueState(**state_data)
        except json.JSONDecodeError:
            pass # 檔案為空或格式錯誤，將回傳新狀態
    
    # 如果找不到對應的 session，回傳一個新的狀態
    return DialogueState(session_id=session_id, chat_history=, filled_slots={})

def save_session_state(state: DialogueState):
    """
    將更新後的對話狀態寫回 JSON 檔案。
    """
    all_data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try:
                all_data = json.load(f)
            except json.JSONDecodeError:
                all_data = {} # 檔案損毀或為空
    
    all_data[state['session_id']] = state
    
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

# --- 3. 模擬大型語言模型 (LLM) 的函式 ---
# 在真實世界中，這些函式會是 API 呼叫

def mock_llm_extract_slots(text: str) -> Dict[str, Any]:
    """
    模擬 LLM 接收原始文本，並根據 Slot Schema 萃取出資訊。
    """
    print("\n 正在萃取使用者輸入中的槽位...")
    # 根據使用者輸入，LLM 辨識出以下資訊
    extracted = {
      "use_case": "業務工作",
      "portability": "高", # "攜帶方便" 被 LLM 解讀為 "高"
      "performance_features": ["快速開關機"]
    }
    print(f" 萃取結果: {extracted}")
    return extracted

def mock_llm_generate_elicitation_response(slot_to_elicit: str, chat_history: List) -> Dict[str, Any]:
    """
    模擬 LLM 根據「需要詢問的槽位」和「對話歷史」，生成一個自然的回應。
    """
    print(f"\n 正在生成關於 '{slot_to_elicit}' 的提問...")
    # 這裡可以加入更複雜的邏輯，根據不同 slot 生成不同問題
    if slot_to_elicit == "budget":
        response = {
          "response_type": "text_with_suggestions",
          "content": "好的，了解您需要一台適合業務工作、輕便且反應快速的筆電。為了給您更精準的推薦，請問您的預算大概是多少呢？",
          "suggestions": ["約 3-4 萬", "約 4-5 萬", "5 萬以上"]
        }
        print(f" 生成的回應物件: {response}")
        return response
    # 可以為其他 slot 增加更多情境
    return {"content": f"請問您的 {slot_to_elicit} 是？", "suggestions":}


# --- 4. 核心模組實作 ---

def user_input_handler(raw_text: str, current_state: DialogueState) -> DialogueState:
    """
    模組一：使用者輸入處理模組
    接收原始文字，調用 LLM 萃取槽位，並更新對話狀態。
    """
    print("\n--- 模組 1: UserInputHandler 啟動 ---")
    
    # 1. 接收資料：raw_text
    print(f"接收到原始輸入: '{raw_text}'")

    # 2. 內部運算：調用 LLM 進行資訊萃取
    extracted_slots = mock_llm_extract_slots(raw_text)
    
    # 3. 轉換與傳遞：更新 DialogueState
    updated_state = current_state.copy()
    updated_state["chat_history"].append({"role": "user", "content": raw_text})
    updated_state["filled_slots"].update(extracted_slots)
    
    print(f"狀態更新完成，準備傳遞給下一模組。")
    return updated_state


def dialogue_manager_router(current_state: DialogueState) -> Dict[str, str]:
    """
    模組二：對話管理器 (路由節點)
    系統的「大腦」，分析當前狀態，決定下一步行動。
    """
    print("\n--- 模組 2: DialogueManager (Router) 啟動 ---")
    print("正在分析 DialogueState 以決定下一步行動...")

    # 1. 接收資料：current_state
    filled_slots = current_state["filled_slots"]
    
    # 2. 內部運算：檢查是否有「必要」槽位尚未被填寫
    for slot_name, schema in SLOT_SCHEMA.items():
        if schema["required"] and slot_name not in filled_slots:
            print(f"決策：發現必要槽位 '{slot_name}' 缺失。")
            # 3. 轉換與傳遞：回傳指令
            decision = {"action": "ELICIT_SLOT", "parameter": slot_name}
            print(f"生成指令: {decision}")
            return decision
            
    # 如果所有必要槽位都已填寫
    print("決策：所有必要槽位皆已滿足。")
    decision = {"action": "RECOMMEND_PRODUCT", "parameter": None}
    print(f"生成指令: {decision}")
    return decision


def action_executor(command: Dict[str, str], current_state: DialogueState) -> (Dict, DialogueState):
    """
    模組三：動作執行器
    根據大腦的指令，執行具體動作。
    """
    print("\n--- 模組 3: ActionExecutor 啟動 ---")
    print(f"接收到指令: {command}")

    action = command.get("action")
    parameter = command.get("parameter")
    
    if action == "ELICIT_SLOT":
        # 1. 接收資料：command, current_state
        # 2. 內部運算：調用 LLM 生成提問
        response_object = mock_llm_generate_elicitation_response(parameter, current_state["chat_history"])
        
        # 3. 轉換與傳遞：更新對話歷史並準備最終輸出
        updated_state = current_state.copy()
        updated_state["chat_history"].append({"role": "assistant", "content": response_object["content"]})
        
        return response_object, updated_state
    
    elif action == "RECOMMEND_PRODUCT":
        # 在此處實作推薦邏輯
        response_object = {"content": "根據您的需求，我推薦以下產品...", "suggestions":}
        updated_state = current_state.copy()
        updated_state["chat_history"].append({"role": "assistant", "content": response_object["content"]})
        return response_object, updated_state
        
    # 處理未知指令
    return {"content": "抱歉，我現在有點問題，請稍後再試。"}, current_state


def response_generator(response_object: Dict) -> str:
    """
    模組四：回應生成模組
    將內部回應物件序列化為 JSON，準備傳給前端。
    """
    print("\n--- 模組 4: ResponseGenerator 啟動 ---")
    print("正在將最終回應物件序列化為 JSON...")
    
    # 序列化為格式化的 JSON 字串
    json_output = json.dumps(response_object, ensure_ascii=False, indent=4)
    
    print("序列化完成。")
    return json_output

# --- 5. 主執行流程 ---

def main():
    """
    主函式，模擬一個完整的使用者互動回合。
    """
    print("="*50)
    print("AI-Sale System 啟動一個新的對話回合")
    print(f"Session ID: {SESSION_ID}")
    print("="*50)

    # 1. 從資料庫載入此 session 的狀態
    state = load_session_state(SESSION_ID)
    
    # 2. 模組一：處理使用者輸入
    state = user_input_handler(USER_QUERY, state)
    
    # 3. 模組二：決定下一步行動
    command = dialogue_manager_router(state)
    
    # 4. 模組三：執行指令
    final_response_object, state = action_executor(command, state)
    
    # 5. 模組四：生成給前端的最終 JSON
    json_to_frontend = response_generator(final_response_object)
    
    # 6. 將更新後的狀態存回資料庫
    save_session_state(state)
    print(f"\n 已將 Session '{SESSION_ID}' 的最新狀態存回 '{DB_FILE}'")

    print("\n" + "="*50)
    print("流程結束。以下是最終產出：")
    print("="*50)
    
    print("\n【產出 1: 準備傳送給前端的 JSON】")
    print(json_to_frontend)
    
    print("\n【產出 2: 儲存在資料庫中的最新對話狀態】")
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        print(f.read())

if __name__ == "__main__":
    main()