import cohere
from app.config import settings

_client = None

def get_cohere():
    global _client
    if _client is None:
        _client = cohere.Client(settings.COHERE_KEY)
    return _client

def rerank(query: str, documents: list, top_n: int = 3) -> list:
    if not documents:
        return []
    
    client = get_cohere()
    response = client.rerank(
        model="rerank-multilingual-v3.0",  # 支持中文
        query=query,
        documents=documents,
        top_n=top_n
    )
    
    # 按相关性分数返回重排后的文档
    return [documents[item.index] for item in response.results]