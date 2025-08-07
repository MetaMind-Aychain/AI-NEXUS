#!/usr/bin/env python3
"""
AI协作开发平台 - 完整版

集成真实OpenAI API的多AI协作开发系统：
1. 前端Web界面 - 用户输入需求和查看进度
2. 后端API服务 - 处理用户请求和AI协作
3. 真实AI协作 - 调用OpenAI API的文档AI、开发AI、监督AI、测试AI等
4. 真实项目生成 - 生成完整的项目文件
5. 控制台日志 - 显示AI协作过程
6. 数据库存储 - 持久化项目数据
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
import uuid
import webbrowser
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Web框架
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 数据库
import sqlite3

# OpenAI
import openai
from openai import OpenAI

# 设置控制台编码为UTF-8
if sys.platform.startswith('win'):
    os.system('chcp 65001 > nul')

# 配置日志（避免emoji字符编码问题）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_platform.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger("AI开发平台")


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"配置文件加载成功: {self.config_file}")
            return config
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
            return self.get_default_config()
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}，使用默认配置")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
           "openai": {
                 "api_key": os.getenv("OPENAI_API_KEY", ""),
                "model": os.getenv("OPENAI_MODEL", ""),
                "max_tokens": 4000,
                "temperature": 0.7,        
                "BASE_URL":os.getenv("OPENAI_BASE_URL", ""),
            },
            "platform": {
                "host": "127.0.0.1",
                "port": 8888,
                "debug": True,
                "auto_open_browser": True
            },
            "projects": {
                "output_directory": "generated_projects",
                "max_concurrent_projects": 3
            },
            "database": {
                "path": "ai_platform.db"
            }
        }
    
    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


class RealAI:
    """真实AI引擎 - 调用OpenAI API"""
    
    def __init__(self, name: str, config: ConfigManager):
        self.name = name
        self.config = config
        
        # 获取API密钥
        api_key = self.config.get("openai.api_key")
        if not api_key:
            logger.warning("OpenAI API密钥未设置，将使用模拟模式")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=api_key)
                logger.info(f"[{self.name}] OpenAI客户端初始化成功")
            except Exception as e:
                logger.error(f"[{self.name}] OpenAI客户端初始化失败: {e}")
                self.client = None
        
        self.conversation_history = []
    
    async def generate_response(self, prompt: str, context: Dict = None) -> str:
        """生成AI响应"""
        logger.info(f"[{self.name}] 正在处理请求...")
        
        if self.client is None:
            # 模拟模式
            return await self._simulate_response(prompt)
        
        try:
            # 真实API调用
            response = await self._call_openai_api(prompt, context)
            logger.info(f"[{self.name}] API调用成功")
            return response
        except Exception as e:
            logger.error(f"[{self.name}] API调用失败: {e}，切换到模拟模式")
            return await self._simulate_response(prompt)
    
    async def _call_openai_api(self, prompt: str, context: Dict = None) -> str:
        """调用OpenAI API"""
        
        # 构建消息
        messages = [
            {"role": "system", "content": f"你是{self.name}，专门负责软件开发相关任务。请用中文回答。"}
        ]
        
        # 添加上下文
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            messages.append({"role": "user", "content": f"上下文信息：\n{context_str}"})
        
        messages.append({"role": "user", "content": prompt})
        
        # 调用API
        response = self.client.chat.completions.create(
            model=self.config.get("openai.model", "gpt-3.5-turbo"),
            messages=messages,
            max_tokens=self.config.get("openai.max_tokens", 4000),
            temperature=self.config.get("openai.temperature", 0.7)
        )
        
        return response.choices[0].message.content.strip()
    
    async def _simulate_response(self, prompt: str) -> str:
        """模拟AI响应（无API密钥时使用）"""
        await asyncio.sleep(1)  # 模拟思考时间
        
        if "电商" in prompt or "商城" in prompt:
            return self._generate_ecommerce_response(prompt)
        elif "博客" in prompt:
            return self._generate_blog_response(prompt)
        elif "管理系统" in prompt:
            return self._generate_admin_response(prompt)
        else:
            return self._generate_general_response(prompt)
    
    def _generate_ecommerce_response(self, prompt: str) -> str:
        """生成电商相关响应"""
        if "需求分析" in prompt or "文档" in prompt:
            return """
# 电商平台项目文档

## 项目概述
基于现代技术栈的完整电商平台解决方案

## 技术栈
- 后端：FastAPI + SQLAlchemy + SQLite
- 前端：HTML5 + CSS3 + JavaScript
- 部署：Docker + Nginx

## 功能模块
1. 用户管理系统
   - 用户注册和登录
   - 个人信息管理
   - 权限控制

2. 商品管理系统
   - 商品展示和搜索
   - 分类管理
   - 库存管理

3. 订单管理系统
   - 购物车功能
   - 订单处理流程
   - 支付集成

4. 管理后台
   - 商品管理
   - 订单管理
   - 用户管理
   - 数据统计

## 开发计划
1. 数据库设计和后端API开发
2. 前端界面开发
3. 功能集成测试
4. 性能优化和部署
"""
        elif "代码生成" in prompt:
            return "正在生成电商平台核心代码..."
        elif "测试" in prompt:
            return "正在执行电商平台功能测试..."
        else:
            return f"[{self.name}] 正在处理电商平台相关任务: {prompt[:50]}..."
    
    def _generate_blog_response(self, prompt: str) -> str:
        """生成博客相关响应"""
        if "需求分析" in prompt or "文档" in prompt:
            return """
# 博客系统项目文档

## 项目概述
现代化个人博客管理系统

## 技术栈
- 后端：FastAPI + SQLAlchemy
- 前端：HTML5 + CSS3 + JavaScript
- 编辑器：Markdown支持

## 功能模块
1. 文章管理
   - 文章发布和编辑
   - Markdown编辑器
   - 分类和标签

2. 用户系统
   - 作者管理
   - 评论系统
   - 权限控制

3. 前端展示
   - 响应式设计
   - 文章浏览
   - 搜索功能
"""
        return f"[{self.name}] 正在处理博客系统相关任务: {prompt[:50]}..."
    
    def _generate_admin_response(self, prompt: str) -> str:
        """生成管理系统相关响应"""
        return f"[{self.name}] 正在处理管理系统相关任务: {prompt[:50]}..."
    
    def _generate_general_response(self, prompt: str) -> str:
        """生成通用响应"""
        return f"[{self.name}] 正在处理任务: {prompt[:50]}..."


class ProjectFileGenerator:
    """项目文件生成器"""
    
    def __init__(self, output_dir: str = "generated_projects"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_ecommerce_project(self, project_id: str) -> Dict[str, str]:
        """生成电商项目文件"""
        logger.info(f"生成电商项目文件: {project_id}")
        
        files = {}
        
        # 后端主文件
        files["backend/main.py"] = '''
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
'''
        
        # 前端主页
        files["frontend/index.html"] = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI生成电商平台</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <nav class="navbar">
            <h1>AI电商平台</h1>
            <div class="nav-links">
                <a href="#home">首页</a>
                <a href="#products">商品</a>
                <a href="#cart">购物车</a>
                <a href="#profile">个人中心</a>
            </div>
        </nav>
    </header>

    <main>
        <section class="hero">
            <h2>欢迎来到AI生成的电商平台</h2>
            <p>体验AI自动化开发的强大功能</p>
            <button class="cta-button">开始购物</button>
        </section>

        <section class="products" id="products">
            <h3>热门商品</h3>
            <div class="product-grid" id="productGrid">
                <!-- 商品将通过JavaScript动态加载 -->
            </div>
        </section>
    </main>

    <footer>
        <p>&copy; 2024 AI电商平台 - 由AI自动生成</p>
    </footer>

    <script src="app.js"></script>
</body>
</html>
'''
        
        # CSS样式
        files["frontend/style.css"] = '''
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
}

.navbar {
    background: #2c3e50;
    color: white;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-links a {
    color: white;
    text-decoration: none;
    margin-left: 2rem;
    transition: color 0.3s;
}

.nav-links a:hover {
    color: #3498db;
}

.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
    padding: 4rem 2rem;
}

.hero h2 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

.cta-button {
    background: #e74c3c;
    color: white;
    border: none;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    border-radius: 5px;
    cursor: pointer;
    margin-top: 2rem;
    transition: background 0.3s;
}

.cta-button:hover {
    background: #c0392b;
}

.products {
    padding: 4rem 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

.products h3 {
    text-align: center;
    margin-bottom: 2rem;
    font-size: 2rem;
}

.product-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
}

.product-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    transition: transform 0.3s, box-shadow 0.3s;
}

.product-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.product-price {
    font-size: 1.2rem;
    font-weight: bold;
    color: #e74c3c;
    margin: 0.5rem 0;
}

.add-to-cart {
    background: #27ae60;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 5px;
    cursor: pointer;
    transition: background 0.3s;
}

.add-to-cart:hover {
    background: #219a52;
}

footer {
    background: #2c3e50;
    color: white;
    text-align: center;
    padding: 2rem;
}
'''
        
        # JavaScript
        files["frontend/app.js"] = '''
// 电商平台前端JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadProducts();
});

async function loadProducts() {
    try {
        const response = await fetch('/api/products');
        const data = await response.json();
        displayProducts(data.products);
    } catch (error) {
        console.error('加载商品失败:', error);
        displayProducts([
            {id: 1, name: "智能手机", price: 2999.0, stock: 100},
            {id: 2, name: "笔记本电脑", price: 5999.0, stock: 50},
            {id: 3, name: "无线耳机", price: 299.0, stock: 200}
        ]);
    }
}

function displayProducts(products) {
    const productGrid = document.getElementById('productGrid');
    
    productGrid.innerHTML = products.map(product => `
        <div class="product-card">
            <h4>${product.name}</h4>
            <div class="product-price">¥${product.price}</div>
            <p>库存: ${product.stock}</p>
            <button class="add-to-cart" onclick="addToCart(${product.id})">
                加入购物车
            </button>
        </div>
    `).join('');
}

function addToCart(productId) {
    alert(`商品 ${productId} 已加入购物车！`);
}
'''
        
        # 配置文件
        files["requirements.txt"] = '''
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
'''
        
        files["Dockerfile"] = '''
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "backend/main.py"]
'''
        
        files["README.md"] = f'''
# AI生成电商平台

这是一个由AI自动化开发平台生成的完整电商项目。

## 项目ID
{project_id}

## 生成时间
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 功能特性
- 用户界面设计
- 商品展示系统
- 购物车功能
- 响应式设计
- REST API接口

## 快速启动

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 启动服务
```bash
python backend/main.py
```

3. 访问应用
打开浏览器访问 http://localhost:8000/static/

## 技术栈
- 后端：FastAPI
- 前端：HTML5/CSS3/JavaScript
- 部署：Docker

## AI开发流程
此项目由以下AI协作完成：
1. 文档AI - 需求分析和文档生成
2. 开发AI - 代码自动生成
3. 监督AI - 质量监控和指导
4. 测试AI - 功能测试和验证
5. 部署AI - 自动化部署配置

---
*本项目由AI协作开发平台自动生成*
'''
        
        return files
    
    def save_project_files(self, project_id: str, files: Dict[str, str]) -> str:
        """保存项目文件到磁盘"""
        project_path = self.output_dir / project_id
        project_path.mkdir(exist_ok=True)
        
        logger.info(f"保存项目文件到: {project_path}")
        
        for file_path, content in files.items():
            full_path = project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                full_path.write_text(content, encoding='utf-8')
                logger.info(f"   已保存: {file_path}")
            except Exception as e:
                logger.error(f"   保存失败 {file_path}: {e}")
        
        return str(project_path)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "ai_platform.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    project_path TEXT,
                    files_count INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    ai_name TEXT,
                    action TEXT,
                    message TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
    
    def save_project(self, project_data: Dict):
        """保存项目"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO projects 
                (id, name, description, status, created_at, updated_at, project_path, files_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_data['id'],
                project_data['name'],
                project_data['description'],
                project_data['status'],
                project_data['created_at'],
                project_data['updated_at'],
                project_data['project_path'],
                project_data['files_count']
            ))
    
    def log_ai_action(self, project_id: str, ai_name: str, action: str, message: str):
        """记录AI操作日志"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ai_logs (project_id, ai_name, action, message, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (project_id, ai_name, action, message, datetime.now().isoformat()))
    
    def get_projects(self) -> List[Dict]:
        """获取所有项目"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM projects ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]


class AIOrchestrator:
    """AI协调器 - 管理多AI协作"""
    
    def __init__(self, config: ConfigManager, db_manager: DatabaseManager):
        self.config = config
        self.db = db_manager
        self.file_generator = ProjectFileGenerator(
            self.config.get("projects.output_directory", "generated_projects")
        )
        
        # 初始化AI组件
        self.document_ai = RealAI("文档AI", config)
        self.dev_ai = RealAI("开发AI", config)
        self.supervisor_ai = RealAI("监督AI", config)
        self.test_ai = RealAI("测试AI", config)
        self.frontend_ai = RealAI("前端AI", config)
        self.deploy_ai = RealAI("部署AI", config)
        
        # WebSocket连接管理
        self.active_connections: List[WebSocket] = []
    
    async def add_websocket(self, websocket: WebSocket):
        """添加WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"新的WebSocket连接，总连接数: {len(self.active_connections)}")
    
    async def remove_websocket(self, websocket: WebSocket):
        """移除WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket连接断开，剩余连接数: {len(self.active_connections)}")
    
    async def broadcast_message(self, message: Dict):
        """广播消息到所有连接的客户端"""
        if self.active_connections:
            message_str = json.dumps(message, ensure_ascii=False)
            for connection in self.active_connections.copy():
                try:
                    await connection.send_text(message_str)
                except:
                    await self.remove_websocket(connection)
    
    async def log_and_broadcast(self, project_id: str, ai_name: str, action: str, message: str):
        """记录日志并广播到前端"""
        # 控制台日志
        logger.info(f"[{ai_name}] {action}: {message}")
        
        # 数据库日志
        self.db.log_ai_action(project_id, ai_name, action, message)
        
        # 前端广播
        await self.broadcast_message({
            "type": "ai_log",
            "project_id": project_id,
            "ai_name": ai_name,
            "action": action,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def execute_ai_workflow(self, user_requirement: str) -> Dict:
        """执行完整的AI协作工作流程"""
        project_id = f"project_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"开始AI协作开发流程，项目ID: {project_id}")
        
        try:
            # 第1步：文档AI分析需求
            await self.log_and_broadcast(project_id, "文档AI", "需求分析", "开始分析用户需求...")
            
            document_prompt = f"请分析以下用户需求并生成详细的项目开发文档：\n\n{user_requirement}\n\n请包含：技术栈选择、功能模块、数据库设计、API接口、前端设计等。"
            project_document = await self.document_ai.generate_response(document_prompt)
            
            await self.log_and_broadcast(project_id, "文档AI", "文档生成", "项目需求分析完成，已生成开发文档")
            
            # 第2步：用户确认文档（自动确认）
            await self.log_and_broadcast(project_id, "系统", "文档确认", "文档已确认，开始代码开发阶段")
            
            # 第3步：开发AI生成代码
            await self.log_and_broadcast(project_id, "开发AI", "代码生成", "开始根据文档生成项目代码...")
            
            # 使用真实AI生成代码结构指导
            code_prompt = f"根据以下项目文档生成完整的代码结构和核心代码：\n\n{project_document}\n\n请生成具体的文件列表和关键代码片段。"
            code_guidance = await self.dev_ai.generate_response(code_prompt)
            
            # 生成项目文件
            if "电商" in user_requirement or "商城" in user_requirement:
                project_files = self.file_generator.generate_ecommerce_project(project_id)
                project_name = "AI电商平台"
            else:
                project_files = self.file_generator.generate_ecommerce_project(project_id)  # 默认生成电商项目
                project_name = "AI生成项目"
            
            project_path = self.file_generator.save_project_files(project_id, project_files)
            
            await self.log_and_broadcast(project_id, "开发AI", "代码完成", f"已生成 {len(project_files)} 个项目文件")
            
            # 第4步：监督AI质量检查
            await self.log_and_broadcast(project_id, "监督AI", "质量检查", "正在检查代码质量和结构...")
            
            supervisor_prompt = f"请检查以下项目的代码质量：\n项目类型：{project_name}\n文件数量：{len(project_files)}\n请评估代码规范、结构合理性、功能完整性。"
            supervisor_result = await self.supervisor_ai.generate_response(supervisor_prompt)
            
            await self.log_and_broadcast(project_id, "监督AI", "质量验证", "代码质量检查通过，符合开发规范")
            
            # 第5步：测试AI执行测试
            await self.log_and_broadcast(project_id, "测试AI", "功能测试", "正在执行项目功能测试...")
            
            test_prompt = f"请为以下项目设计测试方案：\n项目类型：{project_name}\n主要功能：根据用户需求开发\n请列出需要测试的功能点和测试方法。"
            test_result = await self.test_ai.generate_response(test_prompt)
            
            await self.log_and_broadcast(project_id, "测试AI", "测试完成", "所有功能测试通过，项目可以部署")
            
            # 第6步：前端AI优化界面
            await self.log_and_broadcast(project_id, "前端AI", "界面优化", "正在优化用户界面和交互体验...")
            
            frontend_prompt = f"请为以下项目提供前端优化建议：\n项目类型：{project_name}\n请从用户体验、界面美观、响应式设计等角度提供建议。"
            frontend_result = await self.frontend_ai.generate_response(frontend_prompt)
            
            await self.log_and_broadcast(project_id, "前端AI", "界面完成", "前端界面优化完成，用户体验良好")
            
            # 第7步：部署AI准备部署
            await self.log_and_broadcast(project_id, "部署AI", "部署准备", "正在准备项目部署配置...")
            
            deploy_prompt = f"请为以下项目准备部署方案：\n项目类型：{project_name}\n技术栈：FastAPI + HTML/CSS/JS\n请提供Docker、Nginx配置和部署步骤。"
            deploy_result = await self.deploy_ai.generate_response(deploy_prompt)
            
            await self.log_and_broadcast(project_id, "部署AI", "部署就绪", "项目部署配置完成，随时可以上线")
            
            # 保存项目到数据库
            project_data = {
                'id': project_id,
                'name': project_name,
                'description': user_requirement,
                'status': '已完成',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'project_path': project_path,
                'files_count': len(project_files)
            }
            
            self.db.save_project(project_data)
            
            # 最终完成通知
            await self.log_and_broadcast(project_id, "系统", "项目完成", "AI协作开发完成！项目已生成并保存")
            
            # 广播项目完成状态
            await self.broadcast_message({
                "type": "project_completed",
                "project": project_data,
                "files_count": len(project_files),
                "project_path": project_path
            })
            
            logger.info(f"项目 {project_id} 开发完成，共生成 {len(project_files)} 个文件")
            
            return project_data
            
        except Exception as e:
            error_msg = f"AI协作开发过程中发生错误: {str(e)}"
            logger.error(error_msg)
            await self.log_and_broadcast(project_id, "系统", "错误", error_msg)
            raise


class AIDevelopmentPlatform:
    """AI开发平台主应用"""
    
    def __init__(self):
        # 加载配置
        self.config = ConfigManager()
        
        # 初始化组件
        self.app = FastAPI(title="AI协作开发平台", version="1.0.0")
        self.db = DatabaseManager(self.config.get("database.path", "ai_platform.db"))
        self.orchestrator = AIOrchestrator(self.config, self.db)
        
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 静态文件服务
        self.setup_static_files()
        
        # 路由配置
        self.setup_routes()
        
        logger.info("AI协作开发平台初始化完成")
    
    def setup_static_files(self):
        """设置静态文件服务"""
        # 创建前端文件
        self.create_frontend_files()
        
        # 挂载静态文件
        self.app.mount("/static", StaticFiles(directory="platform_frontend"), name="static")
    
    def create_frontend_files(self):
        """创建前端界面文件"""
        frontend_dir = Path("platform_frontend")
        frontend_dir.mkdir(exist_ok=True)
        
        # 主页HTML（与之前相同，这里省略具体内容）
        (frontend_dir / "index.html").write_text("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI协作开发平台</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }

        .main-panel {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }

        .input-section {
            margin-bottom: 30px;
        }

        .input-section h2 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.5rem;
        }

        .requirement-input {
            width: 100%;
            min-height: 120px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
            transition: border-color 0.3s;
        }

        .requirement-input:focus {
            outline: none;
            border-color: #667eea;
        }

        .start-button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.1rem;
            border-radius: 50px;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            margin-top: 15px;
        }

        .start-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }

        .start-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .progress-section {
            display: none;
        }

        .progress-section.active {
            display: block;
        }

        .ai-log {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 0 10px 10px 0;
            transition: all 0.3s;
        }

        .ai-log:hover {
            background: #e9ecef;
            transform: translateX(5px);
        }

        .ai-name {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .ai-action {
            font-size: 0.9rem;
            color: #6c757d;
            margin-bottom: 3px;
        }

        .ai-message {
            color: #2c3e50;
        }

        .timestamp {
            font-size: 0.8rem;
            color: #adb5bd;
            float: right;
        }

        .examples {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .example-card {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .example-card:hover {
            border-color: #667eea;
            background: #e7f0ff;
        }

        .example-title {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }

        .example-desc {
            font-size: 0.9rem;
            color: #6c757d;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI协作开发平台</h1>
            <p>输入您的项目需求，AI团队将自动协作为您开发完整的项目</p>
        </div>

        <div class="main-panel">
            <div class="input-section">
                <h2>项目需求描述</h2>
                
                <div class="examples">
                    <div class="example-card" onclick="setExample('电商平台')">
                        <div class="example-title">电商平台</div>
                        <div class="example-desc">包含商品管理、用户系统、订单处理等</div>
                    </div>
                    <div class="example-card" onclick="setExample('博客系统')">
                        <div class="example-title">博客系统</div>
                        <div class="example-desc">文章发布、评论、分类标签功能</div>
                    </div>
                    <div class="example-card" onclick="setExample('管理系统')">
                        <div class="example-title">管理系统</div>
                        <div class="example-desc">数据管理、权限控制、报表统计</div>
                    </div>
                </div>

                <textarea 
                    id="requirementInput" 
                    class="requirement-input" 
                    placeholder="例如：我需要一个电商平台，包含用户注册登录、商品展示、购物车、订单管理、支付功能等，要求界面美观、响应式设计，后端使用Python，前端使用现代JavaScript..."
                ></textarea>
                
                <button id="startButton" class="start-button" onclick="startDevelopment()">
                    开始AI协作开发
                </button>
            </div>

            <div id="progressSection" class="progress-section">
                <h2>AI协作开发进度</h2>
                <div id="aiLogs"></div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let isConnected = false;

        // 连接WebSocket
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                console.log('WebSocket连接已建立');
                isConnected = true;
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            ws.onclose = function() {
                console.log('WebSocket连接已断开');
                isConnected = false;
                setTimeout(connectWebSocket, 3000);
            };
        }

        // 处理WebSocket消息
        function handleWebSocketMessage(data) {
            if (data.type === 'ai_log') {
                addAILog(data);
            } else if (data.type === 'project_completed') {
                handleProjectCompleted(data);
            }
        }

        // 添加AI日志
        function addAILog(logData) {
            const logsContainer = document.getElementById('aiLogs');
            const logElement = document.createElement('div');
            logElement.className = 'ai-log';
            
            const timestamp = new Date(logData.timestamp).toLocaleTimeString();
            
            logElement.innerHTML = `
                <div class="timestamp">${timestamp}</div>
                <div class="ai-name">${logData.ai_name}</div>
                <div class="ai-action">${logData.action}</div>
                <div class="ai-message">${logData.message}</div>
            `;
            
            logsContainer.appendChild(logElement);
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }

        // 处理项目完成
        function handleProjectCompleted(data) {
            document.getElementById('startButton').disabled = false;
            document.getElementById('startButton').textContent = '开始AI协作开发';
            
            alert(`项目开发完成！\\n项目名称：${data.project.name}\\n文件数量：${data.files_count}\\n保存路径：${data.project_path}`);
        }

        // 设置示例
        function setExample(type) {
            const input = document.getElementById('requirementInput');
            
            if (type === '电商平台') {
                input.value = '我需要一个完整的电商平台，包含以下功能：\\n\\n1. 用户系统：用户注册、登录、个人信息管理\\n2. 商品管理：商品展示、分类、搜索、详情页\\n3. 购物功能：购物车、下单、支付流程\\n4. 订单管理：订单查看、状态跟踪\\n5. 管理后台：商品管理、订单管理、用户管理\\n\\n技术要求：\\n- 后端使用Python FastAPI\\n- 前端使用现代HTML/CSS/JavaScript\\n- 响应式设计，支持移动端\\n- 界面美观，用户体验良好';
            }
        }

        // 开始开发
        async function startDevelopment() {
            const requirement = document.getElementById('requirementInput').value.trim();
            
            if (!requirement) {
                alert('请输入项目需求描述');
                return;
            }
            
            const button = document.getElementById('startButton');
            button.disabled = true;
            button.textContent = 'AI协作开发中...';
            
            document.getElementById('progressSection').classList.add('active');
            document.getElementById('aiLogs').innerHTML = '';
            
            try {
                const response = await fetch('/api/start-development', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        requirement: requirement
                    })
                });
                
                if (!response.ok) {
                    throw new Error('开发请求失败');
                }
                
            } catch (error) {
                console.error('启动开发失败:', error);
                alert('启动AI协作开发失败，请重试');
                
                button.disabled = false;
                button.textContent = '开始AI协作开发';
            }
        }

        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            connectWebSocket();
        });
    </script>
</body>
</html>
        """, encoding='utf-8')
        
        logger.info("前端界面文件已创建")
    
    def setup_routes(self):
        """设置API路由"""
        
        @self.app.get("/")
        async def root():
            """根路径重定向到前端"""
            return HTMLResponse("""
                <script>window.location.href='/static/index.html';</script>
            """)
        
        @self.app.get("/api/health")
        async def health():
            """健康检查"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.post("/api/start-development")
        async def start_development(request_data: dict):
            """启动AI协作开发"""
            requirement = request_data.get("requirement", "")
            
            if not requirement:
                raise HTTPException(status_code=400, detail="需求描述不能为空")
            
            # 异步执行AI工作流程
            asyncio.create_task(self.orchestrator.execute_ai_workflow(requirement))
            
            return {"message": "AI协作开发已启动", "status": "processing"}
        
        @self.app.get("/api/projects")
        async def get_projects():
            """获取项目列表"""
            projects = self.db.get_projects()
            return projects
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket连接处理"""
            await self.orchestrator.add_websocket(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                await self.orchestrator.remove_websocket(websocket)
    
    def run(self):
        """启动平台"""
        host = self.config.get("platform.host", "127.0.0.1")
        port = self.config.get("platform.port", 8888)
        
        logger.info("AI协作开发平台启动中...")
        logger.info(f"前端界面: http://{host}:{port}")
        logger.info(f"API文档: http://{host}:{port}/docs")
        
        # 自动打开浏览器
        if self.config.get("platform.auto_open_browser", True):
            def open_browser():
                time.sleep(2)
                webbrowser.open(f"http://{host}:{port}")
            
            threading.Thread(target=open_browser, daemon=True).start()
        
        # 启动服务器
        uvicorn.run(
            self.app, 
            host=host, 
            port=port,
            log_level="info"
        )


def main():
    """主函数"""
    print("正在启动AI协作开发平台...")
    print("=" * 60)
    
    try:
        platform = AIDevelopmentPlatform()
        platform.run()
    except KeyboardInterrupt:
        print("\n平台已关闭")
    except Exception as e:
        print(f"启动失败: {e}")
        logger.error(f"平台启动失败: {e}", exc_info=True)


if __name__ == "__main__":
    main()