'''
語義路由（Semantic Routing with Sentence-Transformers + Faiss）
'''
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# 1. 定義各意圖的示例句
intents = {
    "查天氣": ["今天的天氣如何？","明天會下雨嗎？"],
    "設定鬧鐘": ["幫我設個鬧鐘","早上七點叫我起床"]
}
texts = sum(intents.values(), [])
labels = sum([[k]*len(v) for k,v in intents.items()], [])

# 2. 建嵌入與索引
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
embeddings = model.encode(texts, convert_to_numpy=True)
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# 3. 查詢路由
def route(query):
    q_emb = model.encode([query])
    D,I = index.search(q_emb, k=2)
    # 基於最近鄰投票
    neigh_labels = [labels[i] for i in I[0]]
    return max(set(neigh_labels), key=neigh_labels.count)

print(route("幫我明天早上叫醒我"))  # -> 設定鬧鐘
