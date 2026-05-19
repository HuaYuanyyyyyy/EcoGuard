#构建索引
import jieba
from app.core.rerank import rerank
from app.core.chroma import get_chroma
from rank_bm25 import BM25Okapi


_bm25 = None
_docs = None

# 索引构建
def _build_bm25():
    global _bm25, _docs
    chroma = get_chroma()
    raw = chroma.get()
    _docs = raw.get("documents")
    if not _docs:
        return
    tokenized = [list(jieba.cut(doc)) for doc in _docs]
    _bm25 = BM25Okapi(tokenized)

def get_bm25():
    global _bm25, _docs
    if _bm25 is None:
        _build_bm25()
    return _bm25, _docs

# BM25检索
def bm25_search(query: str, top_k: int = 10) -> list:
    bm25, docs = get_bm25()
    if bm25 is None or not docs:
        return []
    scores = bm25.get_scores(list(jieba.cut(query)))
    ranked = sorted(enumerate(scores),key = lambda x:x[1],reverse = True)[:top_k]
    return [(docs[i], score) for i, score in ranked if score > 0]

# RRF 融合
def rrf_fusion(bm25_results: list, vector_results: list, k: int = 60) -> list:
    scores = {}

    for rank, (doc, _) in enumerate(bm25_results):
        scores[doc] = scores.get(doc, 0) + 1 / (k + rank + 1)

    for rank, (doc, _) in enumerate(vector_results):
        scores[doc] = scores.get(doc, 0) + 1 / (k + rank + 1)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

# 混合检索入口
def hybrid_search(query: str, top_k: int = 5) -> list:
    # 向量检索
    chroma = get_chroma()
    vector_docs = chroma.similarity_search_with_score(query, k=10)
    vector_results = [(doc.page_content, score) for doc, score in vector_docs]

    # BM25 检索
    bm25_results = bm25_search(query, top_k=10)

    # RRF 融合
    fused = rrf_fusion(bm25_results, vector_results)

    # 粗排取前10
    candidates = [doc for doc, _ in fused[:10]]
    
    # Rerank 精排取前 top_k
    return rerank(query, candidates, top_n=top_k)

    # # 返回前 top_k 个文档内容
    # return [doc for doc, _ in fused[:top_k]]    

