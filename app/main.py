from fastapi import FastAPI
from app.database import init_db

app = FastAPI(title="EcoGuard", description="环保合规智能审查系统")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"message": "EcoGuard启动成功"}