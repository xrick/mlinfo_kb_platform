太棒了 ✨ 這樣我們就能把剛才的 **三層式範例（System + Context + User）**，直接寫成一個完整的 Python 範例程式。
我會假設你要用 OpenAI 官方的 `chat.completions` API（`openai` 套件）。

---

# 🔹 Python 完整範例程式

````python
from openai import OpenAI

# 初始化客戶端（確保你已經設好 OPENAI_API_KEY 環境變數）
client = OpenAI()

# ------------------------------
# System Message（極簡版 10 行守則）
# ------------------------------
system_message = """# Enterprise Business Assistant AI – Minimal Version

1. Role: You are a professional, cautious enterprise business assistant AI.  
2. Knowledge Source: Only use the official internal knowledge base and user-provided text.  
3. Prohibited: No fabrication, guessing, or using external knowledge.  
4. Thinking Rule: Plan internally first (not shown), then generate the reply.  
5. Response Format:  
   - Executive Summary (1–3 sentences)  
   - Detailed Breakdown: Features → Usage → Recommendations  
   - Closing Guidance: Customer service note or next-step prompt  
6. Knowledge Gaps: If info is missing, reply with: “Thank you for your question… please contact our customer service experts.”  
7. Non-product topics: Add disclaimer: “For reference only, consult professionals.”  
8. Tone: Professional, polite, neutral; respect privacy and confidentiality.  
9. Context: Combine {product_data}, {prompt_using}, {answer}, {query} as input.  
10. If {product_data} is empty, display “Product Data: None”.  
"""

# ------------------------------
# Context Message（系統組合上下文）
# ------------------------------
product_data = None   # 假設目前沒有產品資料
previous_answer = "Currently none"
prompt_using = ""     # 假設沒有前一輪上下文

if product_data:
    product_data_text = f"```text\n{product_data}\n```"
else:
    product_data_text = "Product Data: None"

context_message = f"""product data:
{product_data_text}

Prompt Using:
{prompt_using}
Previous Answer: {previous_answer}
"""

# ------------------------------
# User Message（使用者最新 query）
# ------------------------------
user_query = "What are the available renewal plans for this product?"

# ------------------------------
# 呼叫 LLM
# ------------------------------
messages = [
    {"role": "system", "content": system_message},
    {"role": "assistant", "content": context_message},
    {"role": "user", "content": user_query}
]

response = client.chat.completions.create(
    model="gpt-4o",   # 你也可以換成 "gpt-4.1" 或其他模型
    messages=messages
)

# ------------------------------
# 顯示結果
# ------------------------------
print("=== LLM 回覆 ===")
print(response.choices[0].message.content)
````

---

# 🔹 程式重點說明

1. **system\_message**
   → 放入「極簡版 10 行守則」，確保 LLM 知道規範。

2. **context\_message**
   → 動態組合 `{product_data}`、`{prompt_using}`、`{previous_answer}`。

   * 如果沒有產品資料 → 自動顯示 `Product Data: None`。
   * 確保上下文每次都傳給模型。

3. **user\_query**
   → 使用者的最新問題，直接放在 `"role": "user"`。

4. **messages 結構**

   * **system** → 規則守則
   * **assistant** → 系統上下文（上一輪回答 + 產品資料）
   * **user** → 使用者 query

---

✅ 這樣，每次呼叫 LLM 的時候，你就能保證：

* 有「守則」護欄（system）
* 有「上下文」連貫性（assistant）
* 有「當前問題」（user）

---

要不要我幫你加一個 **多輪對話範例**（模擬使用者問兩次問題，如何把前一輪的回答存起來再傳給 LLM）？
