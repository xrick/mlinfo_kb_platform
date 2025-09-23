llm_init = LLMInitializer(model_name="gpt-oss:20b", temperature=0.1, request_timeout=60)

# 自動安全輸出（會自動計算 num_predict，必要時截斷）
reply = llm_init.safe_completion(
    prompt="請用 5 點條列解釋 Transformer 的注意力機制。",
    reserve_output=2048,  # 希望的輸出上限
)
print(reply)

# 傳統補全（不做安全調整）
reply2 = llm_init.complete(
    prompt="同題，但用更技術的說法。",
    max_tokens=512
)
print(reply2)
