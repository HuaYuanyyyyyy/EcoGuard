
from minio import Minio
from dotenv import load_dotenv
import os

load_dotenv()

client = Minio(
    endpoint=os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False
)

# 测试连接，列出所有bucket
buckets = client.list_buckets()
for bucket in buckets:
    print(f"bucket: {bucket.name}")

print("MinIO连接成功")