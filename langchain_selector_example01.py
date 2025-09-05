# pip install langchain langchain-openai pydantic

from langchain.prompts import FewShotPromptTemplate, PromptTemplate
from langchain.prompts.example_selector import LengthBasedExampleSelector

# 你的「範例池」：可換成客訴/客服/產品QA等
examples = [
    {"question": "How to track my order?", "answer": "Use the tracking link in your email."},
    {"question": "How to request a return?", "answer": "Start a return in your account within 30 days."},
    {"question": "My card was declined", "answer": "Check card details or contact bank; try another method."},
    {"question": "Warranty coverage?", "answer": "Most items have a 1-year limited warranty."},
]

# 每個範例在 Prompt 中的呈現格式
example_prompt = PromptTemplate.from_template(
    "Q: {question}\nA: {answer}"
)

# 重點：用長度限制，塞入「最多但合適」的範例
selector = LengthBasedExampleSelector(
    examples=examples,
    example_prompt=example_prompt,
    max_length=180   # 視你的 context 窗口與成本調整
)

# few-shot Prompt：會「動態」用 selector 挑例子
prompt = FewShotPromptTemplate(
    example_selector=selector,
    example_prompt=example_prompt,
    prefix="You are a helpful customer support assistant. Use prior examples as style/format guides.",
    suffix="Q: {input}\nA:",
    input_variables=["input"]
)

# 實際來一個用戶問題
user_input = "Where is my package now? I need the current delivery status."
final_prompt_text = prompt.format(input=user_input)
print(final_prompt_text)

# 接下來你可把 final_prompt_text 丟給任何 LLM（OpenAI、Anthropic、Llama 等）
# 例如（僅示意）：
# from langchain_openai import OpenAI
# llm = OpenAI(temperature=0.2)
# print(llm.invoke(final_prompt_text))