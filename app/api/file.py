from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.service.file_service import upload_pdf, delete_pdf
from app.model.file import File as FileModel

router = APIRouter(prefix="/files", tags=["文件管理"])

@router.post("/upload")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    file_data = await file.read()
    record = upload_pdf(file.filename, file_data, db)
    
    return {
        "id": record.id,
        "file_name": record.file_name,
        "file_size": record.file_size,
        "upload_time": record.upload_time
    }

@router.get("/list")
def list_files(db: Session = Depends(get_db)):
    files = db.query(FileModel).filter(FileModel.status == "active").all()
    return [
        {
            "id": f.id,
            "file_name": f.file_name,
            "file_size": f.file_size,
            "upload_time": f.upload_time
        }
        for f in files
    ]

@router.delete("/{file_id}")
def delete(file_id: str, db: Session = Depends(get_db)):
    success = delete_pdf(file_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="文件不存在")
    return {"message": "删除成功"}