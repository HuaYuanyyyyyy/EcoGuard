import cohere
from app.config import settings
import os

# pip install cohere
co = cohere.Client(settings.COHERE_KEY)  # cohere.com 注册免费拿

# ─────────────────────────────────────────
# 1. 模拟粗排召回的文档（假设已经通过向量检索拿到了这些）
# ─────────────────────────────────────────
documents = [
    "二氧化硫排放标准要求，燃煤锅炉每小时排放不得超过200mg/m³",
    "二氧化硫是一种有刺激性气味的气体，对人体呼吸系统有害",
    "氮氧化物排放标准中，火力发电厂限值为100mg/m³",
    "大气污染物排放标准分为一级、二级、三级",
    "锅炉烟气脱硫装置可以减少二氧化硫排放",
    "二氧化硫与水结合会形成亚硫酸，进一步氧化为硫酸",
    "燃煤电厂必须安装脱硫设施，否则将面临处罚",
    "二氧化硫的工业排放限值根据锅炉类型和燃料种类有所不同",
]

query = "燃煤锅炉二氧化硫排放限值是多少"

# ─────────────────────────────────────────
# 2. 粗排结果（向量检索顺序，假设就是上面的顺序）
# ─────────────────────────────────────────
print("【粗排结果（向量检索）】")
for i, doc in enumerate(documents[:5], 1):
    print(f"  [{i}] {doc}")

# ─────────────────────────────────────────
# 3. Rerank 精排
# ─────────────────────────────────────────
response = co.rerank(
    model="rerank-multilingual-v3.0",  # 支持中文
    query=query,
    documents=documents,
    top_n=3  # 只取精排后前3个
)

print(f"\n【精排结果（Rerank后）】")
print(f"Query：{query}\n")
for item in response.results:
    print(f"  [{item.index + 1}] 相关性分数={item.relevance_score:.4f}")
    print(f"       {documents[item.index]}\n")