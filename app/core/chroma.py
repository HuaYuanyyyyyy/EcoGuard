from langchain_chroma import Chroma
from app.core.embedding import MyEmbeddings
from app.config import settings

#全局初始化一次
embeddings = MyEmbeddings()

def get_chroma(collection_name: str = "ecoguard") -> Chroma:
    return Chroma(
        persist_directory=settings.CHROMA_DIR,
        embedding_function=embeddings,
        collection_name=collection_name
    )