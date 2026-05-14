from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.api.file import router as file_router
from app.api.chat import router as chat_router

app = FastAPI(title="EcoGuard", description="环保合规智能审查系统")


# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(file_router)


app.include_router(chat_router)

@app.get("/")
def root():
    return {"message": "EcoGuard启动成功"}