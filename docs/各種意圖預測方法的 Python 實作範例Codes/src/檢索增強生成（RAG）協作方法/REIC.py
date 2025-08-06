'''
REIC：RAG 增強意圖分類（向量檢索 + LLM 分類）
'''
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# 1. 建立 (query, intent) 向量索引
kb = [("查天氣","查天氣"),("設鬧鐘","設定鬧鐘")]
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
kb_emb = model.encode([q for q,_ in kb], convert_to_numpy=True)

# 2. Faiss 建索引
import faiss
index = faiss.IndexFlatL2(kb_emb.shape[1])
index.add(kb_emb)

# 3. 檢索 + LLM 驗證
openai = OpenAI()
def classify_rag(query):
    qe = model.encode([query])
    D,I = index.search(qe, k=3)
    candidates = [kb[i][1] for i in I[0]]
    prompt = f"以下三個意圖：{candidates}。請判斷最適合查詢 “{query}” 的意圖。"
    resp = openai.chat.completions.create(model="gpt-4o", messages=[{"role":"user","content":prompt}])
    return resp.choices[0].message.content

print(classify_rag("今天上海氣溫"))  # -> 查天氣
