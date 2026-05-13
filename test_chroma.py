from app.core.chroma import get_chroma


chroma = get_chroma()
results = chroma.get()
print(f"共存入 {len(results['ids'])} 个chunk")
print(results['documents'][0])  # 看第一个chunk内容
print(results['metadatas'][0])  # 看metadata