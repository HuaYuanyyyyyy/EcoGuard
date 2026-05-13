import uuid
import io
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.model.file import File
from app.service.minio_service import upload_file, delete_file
from app.core.chroma import get_chroma
import tempfile
import os

def upload_pdf(file_name: str, file_data: bytes, db: Session): 

    # 检查是否已存在同名文件，存在则先删除
    existing = db.query(File).filter(
        File.file_name == file_name,
        File.status == "active"
    ).first()
    
    if existing:
        delete_pdf(existing.id, db)

    file_id = str(uuid.uuid4())
    file_size = len(file_data)
    minio_path = None
    chroma_ids = None

    try:
        # 1. 存MinIO
        minio_path = upload_file(
            file_id=file_id,
            file_name=file_name,
            file_data=io.BytesIO(file_data),
            file_size=file_size
        )

        # 2. 解析PDF切块存Chroma
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name

        try:
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            chunks = splitter.split_documents(docs)
            for chunk in chunks:
                chunk.metadata["file_id"] = file_id
                chunk.metadata["file_name"] = file_name

            chroma = get_chroma()
            chroma_ids = chroma.add_documents(chunks)
        finally:
            os.unlink(tmp_path)

        # 3. 存MySQL
        file_record = File(
            id=file_id,
            file_name=file_name,
            minio_path=minio_path,
            file_size=file_size
        )
        db.add(file_record)
        db.commit()

        return file_record

    except Exception as e:
        # 回滚：哪步成功了就回滚哪步
        if minio_path:
            try:
                delete_file(minio_path)
            except:
                pass
        if chroma_ids:
            try:
                chroma = get_chroma()
                chroma.delete(ids=chroma_ids)
            except:
                pass
        db.rollback()
        raise e


def delete_pdf(file_id: str, db: Session):
    # 1. 查MySQL
    file_record = db.query(File).filter(File.id == file_id).first()
    if not file_record:
        return False

    # 2. 删MinIO
    delete_file(file_record.minio_path)

    # 3. 删Chroma
    chroma = get_chroma()
    results = chroma.get(where={"file_id": file_id})
    if results["ids"]:
        chroma.delete(ids=results["ids"])

    # 4. 删MySQL
    db.delete(file_record)
    db.commit()

    return True