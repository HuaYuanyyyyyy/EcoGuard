from rank_bm25 import BM25Okapi
import jieba

# ─────────────────────────────────────────
# 1. 准备语料库（模拟企业文档片段）
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
# 2. 中文分词（BM25 需要 token 列表）
# ─────────────────────────────────────────
def tokenize(text: str) -> list:
    return list(jieba.cut(text))


tokenized_docs = [tokenize(doc) for doc in documents]

print("分词示例：")
print(f"原文：{documents[0]}")
print(f"分词：{tokenized_docs[0]}\n")


# ─────────────────────────────────────────
# 3. 构建 BM25 索引
# ─────────────────────────────────────────
bm25 = BM25Okapi(tokenized_docs)


# ─────────────────────────────────────────
# 4. 检索函数
# ─────────────────────────────────────────
def bm25_search(query: str, top_k: int = 3):
    tokenized_query = tokenize(query)
    print(f"Query 分词：{tokenized_query}")

    scores = bm25.get_scores(tokenized_query)
    
    # 排序取 top_k
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
    
    print(f"\n检索结果（Top {top_k}）：")
    for rank, (idx, score) in enumerate(ranked, 1):
        print(f"  [{rank}] 得分={score:.4f} | {documents[idx]}")
    return ranked


# ─────────────────────────────────────────
# 5. 测试不同类型的 Query
# ─────────────────────────────────────────
print("=" * 60)
print("【Query 1】精确关键词查询")
print("=" * 60)
bm25_search("二氧化硫排放标准")

print("\n" + "=" * 60)
print("【Query 2】专业术语查询")
print("=" * 60)
bm25_search("COD超标废水")

print("\n" + "=" * 60)
print("【Query 3】语义模糊查询（BM25 的弱项）")
print("=" * 60)
bm25_search("工厂排烟污染空气怎么处理")  # 词不在文档里


# ─────────────────────────────────────────
# 6. 查看 IDF 权重（理解哪些词更重要）
# ─────────────────────────────────────────
print("\n" + "=" * 60)
print("【IDF 权重对比】")
print("=" * 60)
test_words = ["的", "二氧化硫", "排放", "标准", "锅炉"]
for word in test_words:
    tokenized = tokenize(word)
    if tokenized:
        scores = bm25.get_scores(tokenized)
        max_score = max(scores)
        print(f"  词：'{word}' → 最高得分={max_score:.4f}（越高说明该词越稀有）")