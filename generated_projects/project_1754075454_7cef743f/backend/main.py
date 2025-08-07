
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="电商平台API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root():
    return {"message": "电商平台API正在运行", "version": "1.0.0"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/products")
async def get_products():
    return {
        "products": [
            {"id": 1, "name": "智能手机", "price": 2999.0, "stock": 100},
            {"id": 2, "name": "笔记本电脑", "price": 5999.0, "stock": 50},
            {"id": 3, "name": "无线耳机", "price": 299.0, "stock": 200}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
