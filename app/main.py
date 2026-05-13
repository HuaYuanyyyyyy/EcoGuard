from fastapi import FastAPI
from app.database import init_db
from app.api.file import router as file_router

app = FastAPI(title="EcoGuard", description="环保合规智能审查系统")

@app.on_event("startup")
def startup():
    init_db()

app.include_router(file_router)

@app.get("/")
def root():
    return {"message": "EcoGuard启动成功"}