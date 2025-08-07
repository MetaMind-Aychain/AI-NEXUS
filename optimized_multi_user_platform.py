#!/usr/bin/env python3
"""
优化的多用户AI协作开发平台
集成API优化、用户隔离、智能调度等功能
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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn

# 导入我们的组件
from multi_user_database import MultiUserDatabaseManager
from multi_user_ai_orchestrator import MultiUserAIOrchestrator

# 设置控制台编码
if sys.platform.startswith('win'):
    os.system('chcp 65001 > nul')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimized_multi_user_platform.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger("优化多用户平台")

# 安全认证
security = HTTPBearer()

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
                "port": 8890,
                "debug": True,
                "auto_open_browser": True
            },
            "optimization": {
                "cache_ttl": 3600,
                "max_cache_size": 1000,
                "rate_limit_per_minute": 60,
                "batch_processing": True
            },
            "users": {
                "max_concurrent_users": 100,
                "session_timeout": 1800,
                "default_subscription_tier": "basic"
            },
            "projects": {
                "output_directory": "multi_user_projects",
                "max_projects_per_user": 50
            },
            "database": {
                "path": "optimized_multi_user_platform.db"
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

class OptimizedMultiUserPlatform:
    """优化的多用户AI开发平台"""
    
    def __init__(self):
        # 加载配置
        self.config = ConfigManager()
        
        # 初始化组件
        self.app = FastAPI(
            title="优化多用户AI协作开发平台", 
            version="3.0.0",
            description="支持多用户、API优化、智能调度的AI协作开发平台"
        )
        
        # 数据库管理器
        self.db = MultiUserDatabaseManager(
            self.config.get("database.path", "optimized_multi_user_platform.db")
        )
        
        # AI协调器
        self.orchestrator = MultiUserAIOrchestrator(self.config.config, self.db)
        
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
        
        logger.info("优化的多用户AI协作开发平台初始化完成")
    
    def setup_static_files(self):
        """设置静态文件服务"""
        # 创建前端文件
        self.create_frontend_files()
        
        # 挂载静态文件
        self.app.mount("/static", StaticFiles(directory="optimized_frontend"), name="static")
    
    def create_frontend_files(self):
        """创建优化的前端界面文件"""
        frontend_dir = Path("optimized_frontend")
        frontend_dir.mkdir(exist_ok=True)
        
        # 创建现代化的前端界面
        (frontend_dir / "index.html").write_text("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>优化多用户AI协作开发平台</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .glass-effect {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .card-hover {
            transition: all 0.3s ease;
        }
        .card-hover:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .ai-log {
            animation: slideIn 0.5s ease-out;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .progress-bar {
            transition: width 0.3s ease;
        }
    </style>
</head>
<body class="gradient-bg min-h-screen">
    <!-- 登录界面 -->
    <div id="loginSection" class="min-h-screen flex items-center justify-center">
        <div class="glass-effect rounded-2xl p-8 w-full max-w-md">
            <div class="text-center mb-8">
                <i class="fas fa-robot text-4xl text-white mb-4"></i>
                <h1 class="text-3xl font-bold text-white mb-2">AI协作开发平台</h1>
                <p class="text-white opacity-80">多用户 · 优化 · 智能</p>
            </div>
            
            <form id="loginForm" class="space-y-6">
                <div>
                    <label class="block text-white text-sm font-medium mb-2">用户名</label>
                    <input type="text" id="usernameInput" 
                           class="w-full px-4 py-3 rounded-lg bg-white bg-opacity-20 border border-white border-opacity-30 text-white placeholder-white placeholder-opacity-60 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
                           placeholder="请输入用户名">
                </div>
                
                <div>
                    <label class="block text-white text-sm font-medium mb-2">邮箱 (可选)</label>
                    <input type="email" id="emailInput" 
                           class="w-full px-4 py-3 rounded-lg bg-white bg-opacity-20 border border-white border-opacity-30 text-white placeholder-white placeholder-opacity-60 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50"
                           placeholder="请输入邮箱">
                </div>
                
                <button type="submit" 
                        class="w-full bg-white bg-opacity-20 hover:bg-opacity-30 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-300 transform hover:scale-105">
                    <i class="fas fa-sign-in-alt mr-2"></i>登录 / 注册
                </button>
            </form>
            
            <div class="mt-6 text-center">
                <p class="text-white text-sm opacity-80">
                    <i class="fas fa-shield-alt mr-1"></i>
                    安全认证 · 数据隔离 · 性能优化
                </p>
            </div>
        </div>
    </div>

    <!-- 主界面 -->
    <div id="mainSection" class="min-h-screen hidden">
        <!-- 顶部导航栏 -->
        <nav class="glass-effect border-b border-white border-opacity-20">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <div class="flex items-center">
                        <i class="fas fa-robot text-2xl text-white mr-3"></i>
                        <h1 class="text-xl font-bold text-white">AI协作开发平台</h1>
                    </div>
                    
                    <div class="flex items-center space-x-4">
                        <div class="text-white text-sm">
                            <i class="fas fa-user mr-1"></i>
                            <span id="currentUserDisplay"></span>
                        </div>
                        
                        <div class="text-white text-sm">
                            <i class="fas fa-chart-line mr-1"></i>
                            API使用: <span id="apiUsageDisplay">0/1000</span>
                        </div>
                        
                        <button onclick="logout()" 
                                class="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition-all duration-300">
                            <i class="fas fa-sign-out-alt mr-1"></i>退出
                        </button>
                    </div>
                </div>
            </div>
        </nav>

        <!-- 主要内容区域 -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- 功能特性展示 -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="glass-effect rounded-xl p-6 card-hover">
                    <div class="text-center">
                        <i class="fas fa-users text-3xl text-white mb-4"></i>
                        <h3 class="text-lg font-semibold text-white mb-2">多用户支持</h3>
                        <p class="text-white opacity-80 text-sm">完全隔离的用户环境，安全可靠</p>
                    </div>
                </div>
                
                <div class="glass-effect rounded-xl p-6 card-hover">
                    <div class="text-center">
                        <i class="fas fa-rocket text-3xl text-white mb-4"></i>
                        <h3 class="text-lg font-semibold text-white mb-2">API优化</h3>
                        <p class="text-white opacity-80 text-sm">智能缓存、批量处理、减少调用</p>
                    </div>
                </div>
                
                <div class="glass-effect rounded-xl p-6 card-hover">
                    <div class="text-center">
                        <i class="fas fa-brain text-3xl text-white mb-4"></i>
                        <h3 class="text-lg font-semibold text-white mb-2">智能调度</h3>
                        <p class="text-white opacity-80 text-sm">AI协作、质量保证、自动优化</p>
                    </div>
                </div>
            </div>

            <!-- 项目输入区域 -->
            <div class="glass-effect rounded-xl p-8 mb-8">
                <h2 class="text-2xl font-bold text-white mb-6">
                    <i class="fas fa-code mr-2"></i>项目需求描述
                </h2>
                
                <div class="mb-6">
                    <label class="block text-white text-sm font-medium mb-2">项目需求</label>
                    <textarea id="requirementInput" 
                              class="w-full h-32 px-4 py-3 rounded-lg bg-white bg-opacity-20 border border-white border-opacity-30 text-white placeholder-white placeholder-opacity-60 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50 resize-none"
                              placeholder="请详细描述您的项目需求，例如：我需要一个电商平台，包含用户注册登录、商品展示、购物车、订单管理等功能。要求使用Python后端，现代化前端界面，支持移动端..."></textarea>
                </div>
                
                <button id="startButton" onclick="startOptimizedAIDevelopment()" 
                        class="bg-gradient-to-r from-green-400 to-blue-500 hover:from-green-500 hover:to-blue-600 text-white font-semibold py-3 px-8 rounded-lg transition-all duration-300 transform hover:scale-105">
                    <i class="fas fa-play mr-2"></i>启动优化AI协作开发
                </button>
            </div>

            <!-- 进度监控区域 -->
            <div id="progressSection" class="glass-effect rounded-xl p-8 hidden">
                <h2 class="text-2xl font-bold text-white mb-6">
                    <i class="fas fa-chart-bar mr-2"></i>AI协作进度
                </h2>
                
                <!-- 进度条 -->
                <div class="mb-6">
                    <div class="flex justify-between text-white text-sm mb-2">
                        <span>项目进度</span>
                        <span id="progressPercentage">0%</span>
                    </div>
                    <div class="w-full bg-white bg-opacity-20 rounded-full h-2">
                        <div id="progressBar" class="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full progress-bar" style="width: 0%"></div>
                    </div>
                </div>
                
                <!-- AI日志 -->
                <div id="aiLogs" class="space-y-4 max-h-96 overflow-y-auto"></div>
            </div>

            <!-- 项目列表 -->
            <div class="glass-effect rounded-xl p-8">
                <h2 class="text-2xl font-bold text-white mb-6">
                    <i class="fas fa-folder mr-2"></i>我的项目
                </h2>
                
                <div id="projectsList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- 项目卡片将通过JavaScript动态生成 -->
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentUserId = null;
        let currentUsername = null;
        let ws = null;
        let isConnected = false;

        // 登录处理
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('usernameInput').value.trim();
            const email = document.getElementById('emailInput').value.trim();
            
            if (!username) {
                alert('请输入用户名');
                return;
            }
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: username, email: email })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    currentUserId = data.user_id;
                    currentUsername = username;
                    
                    // 切换到主界面
                    document.getElementById('loginSection').classList.add('hidden');
                    document.getElementById('mainSection').classList.remove('hidden');
                    document.getElementById('currentUserDisplay').textContent = username;
                    
                    // 连接WebSocket
                    connectWebSocket();
                    
                    // 加载用户数据
                    loadUserData();
                    loadProjects();
                } else {
                    const error = await response.json();
                    alert(error.detail || '登录失败');
                }
            } catch (error) {
                console.error('登录失败:', error);
                alert('登录失败，请重试');
            }
        });

        // 连接WebSocket
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws?user_id=${currentUserId}`;
            
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
                updateProgress();
            } else if (data.type === 'project_completed') {
                handleProjectCompleted(data);
            } else if (data.type === 'user_stats_update') {
                updateUserStats(data);
            }
        }

        // 添加AI日志
        function addAILog(logData) {
            const logsContainer = document.getElementById('aiLogs');
            const logElement = document.createElement('div');
            logElement.className = 'ai-log glass-effect rounded-lg p-4';
            
            const timestamp = new Date(logData.timestamp).toLocaleTimeString();
            
            logElement.innerHTML = `
                <div class="flex justify-between items-start mb-2">
                    <div class="flex items-center">
                        <i class="fas fa-robot text-green-400 mr-2"></i>
                        <span class="font-semibold text-white">${logData.ai_name}</span>
                        <span class="ml-2 px-2 py-1 bg-green-400 bg-opacity-20 text-green-400 text-xs rounded">优化AI</span>
                    </div>
                    <span class="text-white opacity-60 text-sm">${timestamp}</span>
                </div>
                <div class="text-white opacity-80 text-sm mb-1">${logData.action}</div>
                <div class="text-white">${logData.message}</div>
                ${logData.tokens_used ? `<div class="text-white opacity-60 text-xs mt-2">Token使用: ${logData.tokens_used} | 成本: $${logData.cost.toFixed(4)}</div>` : ''}
            `;
            
            logsContainer.appendChild(logElement);
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }

        // 更新进度
        function updateProgress() {
            const logs = document.querySelectorAll('.ai-log');
            const totalSteps = 7; // 总步骤数
            const currentStep = Math.min(logs.length, totalSteps);
            const percentage = Math.round((currentStep / totalSteps) * 100);
            
            document.getElementById('progressPercentage').textContent = percentage + '%';
            document.getElementById('progressBar').style.width = percentage + '%';
        }

        // 处理项目完成
        function handleProjectCompleted(data) {
            document.getElementById('startButton').disabled = false;
            document.getElementById('startButton').innerHTML = '<i class="fas fa-play mr-2"></i>启动优化AI协作开发';
            
            const message = `优化AI协作开发完成！\\n项目名称：${data.project.name}\\n文件数量：${data.files_count}\\n保存路径：${data.project_path}\\n\\n✅ 所有AI都参与了优化工作`;
            
            alert(message);
            
            // 重新加载项目列表
            loadProjects();
        }

        // 开始优化AI开发
        async function startOptimizedAIDevelopment() {
            const requirement = document.getElementById('requirementInput').value.trim();
            
            if (!requirement) {
                alert('请输入项目需求描述');
                return;
            }
            
            const button = document.getElementById('startButton');
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>优化AI协作中...';
            
            document.getElementById('progressSection').classList.remove('hidden');
            document.getElementById('aiLogs').innerHTML = '';
            
            try {
                const response = await fetch('/api/start-optimized-ai-development', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: currentUserId,
                        requirement: requirement
                    })
                });
                
                if (!response.ok) {
                    throw new Error('优化AI开发请求失败');
                }
                
            } catch (error) {
                console.error('启动优化AI开发失败:', error);
                alert('启动优化AI协作开发失败，请重试');
                
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-play mr-2"></i>启动优化AI协作开发';
            }
        }

        // 加载用户数据
        async function loadUserData() {
            try {
                const response = await fetch(`/api/user-stats/${currentUserId}`);
                if (response.ok) {
                    const data = await response.json();
                    updateUserStats(data);
                }
            } catch (error) {
                console.error('加载用户数据失败:', error);
            }
        }

        // 更新用户统计
        function updateUserStats(data) {
            const user = data.user;
            document.getElementById('apiUsageDisplay').textContent = 
                `${user.api_usage_count}/${user.api_usage_limit}`;
        }

        // 加载项目列表
        async function loadProjects() {
            try {
                const response = await fetch(`/api/user-projects/${currentUserId}`);
                if (response.ok) {
                    const projects = await response.json();
                    displayProjects(projects);
                }
            } catch (error) {
                console.error('加载项目列表失败:', error);
            }
        }

        // 显示项目列表
        function displayProjects(projects) {
            const container = document.getElementById('projectsList');
            
            if (projects.length === 0) {
                container.innerHTML = '<div class="col-span-full text-center text-white opacity-60">暂无项目</div>';
                return;
            }
            
            container.innerHTML = projects.map(project => `
                <div class="glass-effect rounded-xl p-6 card-hover">
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-lg font-semibold text-white">${project.name}</h3>
                        <span class="px-2 py-1 text-xs rounded ${
                            project.status === '已完成' ? 'bg-green-400 bg-opacity-20 text-green-400' : 
                            'bg-yellow-400 bg-opacity-20 text-yellow-400'
                        }">${project.status}</span>
                    </div>
                    <p class="text-white opacity-80 text-sm mb-4">${project.description}</p>
                    <div class="flex justify-between text-white text-xs opacity-60">
                        <span>文件: ${project.files_count}</span>
                        <span>${new Date(project.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
            `).join('');
        }

        // 退出登录
        function logout() {
            currentUserId = null;
            currentUsername = null;
            
            if (ws) {
                ws.close();
            }
            
            document.getElementById('mainSection').classList.add('hidden');
            document.getElementById('loginSection').classList.remove('hidden');
            document.getElementById('usernameInput').value = '';
            document.getElementById('emailInput').value = '';
        }
    </script>
</body>
</html>
        """, encoding='utf-8')
        
        logger.info("优化的多用户前端界面文件已创建")
    
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
            return {
                "status": "healthy", 
                "platform": "优化多用户AI协作开发平台",
                "version": "3.0.0",
                "multi_user": True,
                "optimization_enabled": True,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/api/login")
        async def login(request_data: dict):
            """用户登录/注册"""
            username = request_data.get("username", "")
            email = request_data.get("email", "")
            
            if not username:
                raise HTTPException(status_code=400, detail="用户名不能为空")
            
            try:
                # 检查用户是否存在
                existing_user = self.db.get_user_by_username(username)
                
                if existing_user:
                    # 用户存在，更新登录时间
                    user_id = existing_user.id
                    self.db.update_user_login(user_id)
                    logger.info(f"用户登录: {username}")
                else:
                    # 创建新用户
                    user_id = self.db.create_user(
                        username, 
                        email, 
                        self.config.get("users.default_subscription_tier", "basic")
                    )
                    logger.info(f"新用户注册: {username}")
                
                return {
                    "user_id": user_id,
                    "username": username,
                    "status": "success"
                }
                
            except Exception as e:
                logger.error(f"登录失败: {e}")
                raise HTTPException(status_code=500, detail="登录失败")
        
        @self.app.post("/api/start-optimized-ai-development")
        async def start_optimized_ai_development(request_data: dict):
            """启动优化的AI协作开发"""
            user_id = request_data.get("user_id", "")
            requirement = request_data.get("requirement", "")
            
            if not user_id:
                raise HTTPException(status_code=400, detail="用户ID不能为空")
            if not requirement:
                raise HTTPException(status_code=400, detail="需求描述不能为空")
            
            # 检查用户是否存在
            user = self.db.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            # 检查API使用限制
            if not self.db.check_user_api_limit(user_id):
                raise HTTPException(status_code=429, detail="API使用次数已达上限")
            
            # 异步执行优化的AI工作流程
            asyncio.create_task(
                self.orchestrator.execute_optimized_ai_workflow(user_id, requirement)
            )
            
            return {
                "message": "优化的AI协作开发已启动", 
                "status": "processing",
                "user_id": user_id,
                "optimization_enabled": True
            }
        
        @self.app.get("/api/user-stats/{user_id}")
        async def get_user_stats(user_id: str):
            """获取用户统计信息"""
            user = self.db.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            return self.orchestrator.get_user_stats(user_id)
        
        @self.app.get("/api/user-projects/{user_id}")
        async def get_user_projects(user_id: str):
            """获取用户项目列表"""
            user = self.db.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            projects = self.db.get_user_projects(user_id)
            return [asdict(project) for project in projects]
        
        @self.app.get("/api/optimization-stats")
        async def get_optimization_stats():
            """获取优化统计信息"""
            return {
                "cache_stats": self.orchestrator.api_optimizer.get_cache_stats(),
                "batch_stats": self.orchestrator.api_optimizer.get_batch_stats(),
                "rate_limit_stats": self.orchestrator.api_optimizer.get_rate_limit_stats()
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket连接处理"""
            user_id = websocket.query_params.get("user_id")
            if not user_id:
                await websocket.close(code=4000, reason="Missing user_id")
                return
            
            await self.orchestrator.add_websocket(websocket, user_id)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                await self.orchestrator.remove_websocket(websocket, user_id)
    
    def run(self):
        """启动平台"""
        host = self.config.get("platform.host", "127.0.0.1")
        port = self.config.get("platform.port", 8890)
        
        logger.info("优化的多用户AI协作开发平台启动中...")
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
    print("正在启动优化的多用户AI协作开发平台...")
    print("=" * 60)
    
    try:
        platform = OptimizedMultiUserPlatform()
        platform.run()
    except KeyboardInterrupt:
        print("\n平台已关闭")
    except Exception as e:
        print(f"启动失败: {e}")
        logger.error(f"平台启动失败: {e}", exc_info=True)

if __name__ == "__main__":
    main() 