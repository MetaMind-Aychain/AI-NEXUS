
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime

app = FastAPI(title="简单社交平台")

class User(BaseModel):
    username: str
    email: str

class Post(BaseModel):
    content: str
    user_id: int

@app.get("/")
def read_root():
    return {"message": "欢迎使用简单社交平台"}

@app.post("/users/")
def create_user(user: User):
    # 创建用户逻辑
    return {"id": 1, "username": user.username, "created_at": datetime.now()}

@app.post("/posts/")
def create_post(post: Post):
    # 创建动态逻辑
    return {"id": 1, "content": post.content, "created_at": datetime.now()}

@app.get("/posts/")
def get_posts():
    # 获取动态列表
    return [
        {"id": 1, "content": "Hello World!", "user": "张三", "created_at": "2024-01-01"},
        {"id": 2, "content": "今天天气真好", "user": "李四", "created_at": "2024-01-02"}
    ]
