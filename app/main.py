from fastapi import FastAPI

app = FastAPI(title="EcoGuard", description="环保合规智能审查系统")

@app.get("/")
def root():
    return {"message": "EcoGuard启动成功"}