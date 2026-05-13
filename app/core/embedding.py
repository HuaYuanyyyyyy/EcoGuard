from openai import OpenAI
from langchain_core.embeddings import Embeddings
from typing import List
from app.config import settings

#目前国内只有text-embedding-v4可用，使用不能兼容langchain中的写法，重写embeddings
class MyEmbeddings(Embeddings):
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.API_KEY,
            base_url=settings.EMBEDDING_BASE_URL
        )
        self.model = settings.EMBEDDING_MODEL

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        results = []
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            response = self.client.embeddings.create(
                model=self.model,
                input=batch
            )
            results.extend([item.embedding for item in response.data])
        return results

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

# # 测试一下
# vector = embeddings.embed_query("今天天气真好")
# print(f"向量维度：{len(vector)}")       