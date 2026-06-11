#构建索引
import threading
import jieba
from app.core.rerank import rerank
from app.core.chroma import get_chroma
from rank_bm25 import BM25Okapi


_bm25 = None
_docs = None
_built = False  # 区分「未构建」和「构建过但库是空的」，空库时不能每次检索都重建
_lock = threading.Lock()

# 索引构建
def _build_bm25():
    global _bm25, _docs, _built
    chroma = get_chroma()
    raw = chroma.get()
    docs = raw.get("documents")
    if docs:
        tokenized = [list(jieba.cut(doc)) for doc in docs]
        _bm25 = BM25Okapi(tokenized)
        _docs = docs
    else:
        _bm25 = None
        _docs = []
    _built = True

def invalidate_bm25():
    """上传/删除文件后调用，标记索引失效，下次检索时惰性重建。"""
    global _bm25, _docs, _built
    with _lock:
        _bm25 = None
        _docs = None
        _built = False

def get_bm25():
    if not _built:
        with _lock:
            # double-check：等锁期间可能已被其他请求构建完
            if not _built:
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

# 按文件名定向检索（用于 MHTML 已知参照标准文件的场景）
def hybrid_search_by_filename(query: str, file_name: str, top_k: int = 5) -> list:
    """Vector-only search restricted to a specific PDF by file_name metadata."""
    chroma = get_chroma()
    try:
        vector_docs = chroma.similarity_search_with_score(
            query,
            k=top_k,
            filter={"file_name": file_name},
        )
        results = [doc.page_content for doc, _ in vector_docs]
        if results:
            return results
    except Exception:
        pass
    # Fall back to global hybrid search when filter returns nothing
    return hybrid_search(query, top_k=top_k)


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

