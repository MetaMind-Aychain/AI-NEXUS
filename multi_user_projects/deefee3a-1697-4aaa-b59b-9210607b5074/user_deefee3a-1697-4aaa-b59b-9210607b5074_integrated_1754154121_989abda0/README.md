
# 简单社交平台

这是一个基于AI生成的简单社交平台项目。

## 功能特性

- 用户注册和登录
- 发布动态
- 查看动态流
- 现代化界面设计

## 技术栈

- 后端：Python + FastAPI
- 前端：HTML + CSS + JavaScript
- 数据库：SQLite
- 部署：Docker

## 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 启动服务：`uvicorn backend.main:app --reload`
3. 访问：http://localhost:8000

## 部署

使用Docker：
```bash
docker build -t simple-social-platform .
docker run -p 8000:8000 simple-social-platform
```

---
*此项目由AI协作开发平台自动生成*
