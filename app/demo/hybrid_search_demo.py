from rank_bm25 import BM25Okapi
import jieba
import sys
import os
from app.core.chroma import get_chroma
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



# ─────────────────────────────────────────
# 1. 准备语料库
# ─────────────────────────────────────────
documents = [
    "二氧化硫排放标准要求，燃煤锅炉每小时排放不得超过200mg/m³",
    "氮氧化物是大气污染的主要成分，火力发电厂需严格控制排放量",
    "废水处理流程包括沉淀、过滤、消毒三个阶段，pH值需控制在6到9之间",
    "固体废物处置需遵循减量化、资源化、无害化原则",
    "二氧化氮浓度超标会导致酸雨，影响生态环境",
    "锅炉烟气脱硫装置安装后，二氧化硫排放下降了85%",
    "环保局对该工厂的废水排放进行了专项检查，发现COD超标",
    "大气污染物排放标准分为一级、二级、三级，根据环境功能区确定",
]

# ─────────────────────────────────────────
# 2. 构建 BM25 索引
# ─────────────────────────────────────────
def tokenize(text):
    return list(jieba.cut(text))

tokenized_docs = [tokenize(doc) for doc in documents]
bm25 = BM25Okapi(tokenized_docs)

# ─────────────────────────────────────────
# 3. BM25 单路检索
# ─────────────────────────────────────────
def bm25_search(query, top_k=5):
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
    return [(documents[i], score) for i, score in ranked if score > 0]

# ─────────────────────────────────────────
# 4. 向量单路检索
# ─────────────────────────────────────────
def vector_search(query, top_k=5):
    chroma = get_chroma()
    docs = chroma.similarity_search_with_score(query, k=top_k)
    return [(doc.page_content, score) for doc, score in docs]

# ─────────────────────────────────────────
# 5. RRF 融合
# ─────────────────────────────────────────
def rrf_fusion(bm25_results, vector_results, k=60):
    """
    RRF 公式：score = 1 / (k + rank)
    k=60 是经验值，防止排名靠前的结果权重过大
    """
    scores = {}

    # BM25 结果贡献分数
    for rank, (doc, _) in enumerate(bm25_results):
        scores[doc] = scores.get(doc, 0) + 1 / (k + rank + 1)

    # 向量结果贡献分数
    for rank, (doc, _) in enumerate(vector_results):
        scores[doc] = scores.get(doc, 0) + 1 / (k + rank + 1)

    # 按融合分数排序
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked

# ─────────────────────────────────────────
# 6. 对比测试
# ─────────────────────────────────────────
def compare(query):
    print(f"\n{'='*60}")
    print(f"Query：{query}")
    print('='*60)

    bm25_res = bm25_search(query)
    vector_res = vector_search(query)
    hybrid_res = rrf_fusion(bm25_res, vector_res)

    print("\n【BM25 单路】")
    for i, (doc, score) in enumerate(bm25_res[:3], 1):
        print(f"  [{i}] {doc[:40]}... (score={score:.4f})")

    print("\n【向量 单路】")
    for i, (doc, score) in enumerate(vector_res[:3], 1):
        print(f"  [{i}] {doc[:40]}... (score={score:.4f})")

    print("\n【混合 RRF】")
    for i, (doc, score) in enumerate(hybrid_res[:3], 1):
        print(f"  [{i}] {doc[:40]}... (score={score:.4f})")


# ─────────────────────────────────────────
# 7. 测试不同类型 Query
# ─────────────────────────────────────────
# 精确关键词查询 → BM25 应该更好
compare("二氧化硫200mg排放标准")

# 语义模糊查询 → 向量应该更好
compare("工厂排烟污染怎么处理")

# 专业缩写 → BM25 应该更好
compare("COD超标废水检查")

# 混合型 → 混合应该最好
compare("锅炉脱硫后排放是否达标")