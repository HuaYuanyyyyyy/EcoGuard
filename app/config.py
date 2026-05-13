from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_KEY: str
    BASE_URL: str
    LLM_MODEL: str
    EMBEDDING_MODEL: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str
    CHROMA_DIR: str

    class Config:
        env_file = ".env"

settings = Settings()