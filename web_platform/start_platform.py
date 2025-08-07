#!/usr/bin/env python3
"""
多AI协作开发平台启动脚本

深度集成现有的多AI协作系统，提供Web化的开发体验
"""

import asyncio
import subprocess
import sys
import os
import time
from pathlib import Path
from threading import Thread
import uvicorn

# 确保路径正确
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入平台组件
from backend.main import app
from backend.database import DatabaseManager
from backend.ai_coordinator import AICoordinator

def check_dependencies():
    """检查依赖项"""
    print("🔍 检查系统依赖...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'websockets', 'pydantic',
        'openai', 'langchain', 'typer'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ 系统依赖检查通过")
    return True

def setup_environment():
    """设置环境"""
    print("🛠️ 设置运行环境...")
    
    # 创建必要的目录
    directories = [
        "backend/logs",
        "backend/uploads",
        "backend/temp",
        "ai_workspace",
        "ai_workspace/projects",
        "ai_workspace/shared_memory"
    ]
    
    for directory in directories:
        dir_path = current_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # 检查环境变量
    required_env_vars = ['OPENAI_API_KEY']
    missing_env_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_env_vars.append(var)
    
    if missing_env_vars:
        print(f"⚠️ 缺少环境变量: {', '.join(missing_env_vars)}")
        print("请在 .env 文件中设置这些变量")
        
        # 创建示例 .env 文件
        env_example = current_dir / ".env.example"
        if not env_example.exists():
            with open(env_example, 'w', encoding='utf-8') as f:
                f.write("""# 多AI协作开发平台环境配置
OPENAI_API_KEY=your_openai_api_key_here
NEWSAPI_KEY=your_news_api_key_here

# 数据库配置
DATABASE_URL=sqlite:///./web_platform.db

# Redis配置（可选）
REDIS_URL=redis://localhost:6379

# API配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# WebSocket配置
WS_HEARTBEAT_INTERVAL=30
WS_RECONNECT_INTERVAL=5

# AI配置
AI_MODEL=gpt-4o
AI_TEMPERATURE=0.1
AI_MAX_TOKENS=4000

# 前端配置
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
""")
        print(f"📝 已创建 .env.example 文件，请参考配置")
    
    print("✅ 环境设置完成")

async def initialize_platform():
    """初始化平台"""
    print("🚀 初始化多AI协作开发平台...")
    
    try:
        # 初始化数据库
        db_manager = DatabaseManager("web_platform.db")
        await db_manager.initialize()
        
        # 初始化AI协调器
        ai_coordinator = AICoordinator(work_dir="./ai_workspace")
        await ai_coordinator.initialize()
        
        # 将组件注入到应用中
        app.state.db_manager = db_manager
        app.state.ai_coordinator = ai_coordinator
        
        print("✅ 平台初始化完成")
        return True
        
    except Exception as e:
        print(f"❌ 平台初始化失败: {e}")
        return False

def start_frontend():
    """启动前端开发服务器"""
    print("🌐 启动前端服务...")
    
    frontend_dir = current_dir / "frontend"
    if not frontend_dir.exists():
        print("❌ 前端目录不存在")
        return None
    
    # 检查是否安装了 npm 依赖
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("📦 安装前端依赖...")
        try:
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        except subprocess.CalledProcessError:
            print("❌ npm 依赖安装失败")
            return None
        except FileNotFoundError:
            print("❌ 未找到 npm，请安装 Node.js")
            return None
    
    # 启动前端开发服务器
    try:
        frontend_process = subprocess.Popen(
            ["npm", "start"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待前端服务启动
        time.sleep(5)
        
        if frontend_process.poll() is None:
            print("✅ 前端服务已启动 (http://localhost:3000)")
            return frontend_process
        else:
            print("❌ 前端服务启动失败")
            return None
            
    except Exception as e:
        print(f"❌ 启动前端服务失败: {e}")
        return None

def start_backend():
    """启动后端服务器"""
    print("⚡ 启动后端API服务...")
    
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        ws_ping_interval=20,
        ws_ping_timeout=10
    )
    
    server = uvicorn.Server(config)
    return server

async def run_platform():
    """运行完整平台"""
    print("=" * 60)
    print("🚀 多AI协作开发平台启动中...")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        return False
    
    # 设置环境
    setup_environment()
    
    # 初始化平台
    if not await initialize_platform():
        return False
    
    print("\n🎉 平台启动成功！")
    print("📱 前端界面: http://localhost:3000")
    print("🔧 API文档: http://localhost:8000/docs")
    print("🔌 WebSocket: ws://localhost:8000/ws/{user_id}")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 60)
    
    # 启动前端（在单独线程中）
    frontend_process = None
    frontend_thread = Thread(target=lambda: start_frontend(), daemon=True)
    frontend_thread.start()
    
    # 启动后端服务器
    server = start_backend()
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务...")
        
        # 停止前端服务
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()
        
        print("✅ 服务已停止")
    
    return True

def create_systemd_service():
    """创建systemd服务文件（Linux系统）"""
    service_content = f"""[Unit]
Description=多AI协作开发平台
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory={current_dir.absolute()}
Environment=PATH={sys.executable}
ExecStart={sys.executable} start_platform.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path("/etc/systemd/system/multi-ai-platform.service")
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"✅ 系统服务文件已创建: {service_file}")
        print("启用服务: sudo systemctl enable multi-ai-platform")
        print("启动服务: sudo systemctl start multi-ai-platform")
        
    except PermissionError:
        print("❌ 需要sudo权限创建系统服务")

def show_help():
    """显示帮助信息"""
    print("""
多AI协作开发平台 - 启动脚本

用法:
    python start_platform.py [选项]

选项:
    --help, -h          显示此帮助信息
    --check-deps        仅检查依赖项
    --setup-env         仅设置环境
    --create-service    创建systemd服务文件
    --backend-only      仅启动后端服务
    --frontend-only     仅启动前端服务

示例:
    python start_platform.py                # 启动完整平台
    python start_platform.py --check-deps   # 检查依赖
    python start_platform.py --backend-only # 仅后端
    
环境变量:
    OPENAI_API_KEY     OpenAI API密钥（必需）
    API_PORT           API服务端口（默认8000）
    DEBUG              调试模式（默认True）
    
文档:
    - API文档: http://localhost:8000/docs
    - 前端界面: http://localhost:3000
    - WebSocket: ws://localhost:8000/ws/{user_id}
""")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="多AI协作开发平台")
    parser.add_argument("--check-deps", action="store_true", help="检查依赖项")
    parser.add_argument("--setup-env", action="store_true", help="设置环境")
    parser.add_argument("--create-service", action="store_true", help="创建systemd服务")
    parser.add_argument("--backend-only", action="store_true", help="仅启动后端")
    parser.add_argument("--frontend-only", action="store_true", help="仅启动前端")
    
    args = parser.parse_args()
    
    if args.check_deps:
        check_dependencies()
        return
    
    if args.setup_env:
        setup_environment()
        return
    
    if args.create_service:
        create_systemd_service()
        return
    
    if args.backend_only:
        async def run_backend_only():
            await initialize_platform()
            server = start_backend()
            await server.serve()
        
        try:
            asyncio.run(run_backend_only())
        except KeyboardInterrupt:
            print("\n✅ 后端服务已停止")
        return
    
    if args.frontend_only:
        frontend_process = start_frontend()
        if frontend_process:
            try:
                frontend_process.wait()
            except KeyboardInterrupt:
                frontend_process.terminate()
                print("\n✅ 前端服务已停止")
        return
    
    # 默认启动完整平台
    try:
        asyncio.run(run_platform())
    except KeyboardInterrupt:
        print("\n👋 再见！")
    except Exception as e:
        print(f"❌ 平台启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()