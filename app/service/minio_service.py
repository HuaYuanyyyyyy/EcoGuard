from minio import Minio
from app.config import settings

client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False
)

def ensure_bucket():
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)

def upload_file(file_id: str, file_name: str, file_data, file_size: int) -> str:
    ensure_bucket()
    minio_path = f"{file_id}/{file_name}"
    client.put_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=minio_path,
        data=file_data,
        length=file_size,
        content_type="application/pdf"
    )
    return minio_path

def delete_file(minio_path: str):
    client.remove_object(settings.MINIO_BUCKET, minio_path)