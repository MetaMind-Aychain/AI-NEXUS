"""
多AI协作开发平台 - Web后端主应用

基于FastAPI构建的Web后端，提供完整的API服务和实时通信
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn

# 导入我们的多AI系统
import sys
sys.path.append('..')
from multi_ai_system.orchestrator import MultiAIOrchestrator
from multi_ai_system.core.base_interfaces import ProjectResult, DevPlan
from multi_ai_system.ai.supervisor_ai import SupervisorAI
from multi_ai_system.memory.shared_memory import SharedMemoryManager

# 导入Web平台组件
from .models import (
    UserRequest, ProjectDocument, DevelopmentTask, 
    FrontendPreview, DeploymentStatus, User, Project
)
from .ai_services import (
    DocumentAI, FrontendAI, TransferAI, 
    ServerSupervisorAI, WebTestAI
)
from .database import DatabaseManager
from .websocket_manager import WebSocketManager
from .ai_coordinator import AICoordinator

# 创建FastAPI应用
app = FastAPI(
    title="多AI协作开发平台",
    description="基于AI的全自动化Web开发平台",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 安全认证
security = HTTPBearer()

# 全局组件
db_manager = DatabaseManager()
websocket_manager = WebSocketManager()
ai_coordinator = AICoordinator()

# 数据模型
class UserRequestModel(BaseModel):
    """用户需求请求模型"""
    description: str
    requirements: Dict[str, Any]
    domain_preference: Optional[str] = None
    technology_preference: Optional[str] = None
    
class DocumentUpdateModel(BaseModel):
    """文档更新模型"""
    project_id: str
    document_content: str
    update_type: str  # "manual" or "ai_generated"
    user_feedback: Optional[str] = None

class FrontendFeedbackModel(BaseModel):
    """前端反馈模型"""
    project_id: str
    feedback_type: str  # "approve", "modify", "regenerate"
    modifications: Optional[Dict[str, Any]] = None
    user_comments: Optional[str] = None


# API路由
@app.get("/")
async def root():
    """首页"""
    return {"message": "多AI协作开发平台", "status": "running"}

@app.post("/api/v1/projects/create")
async def create_project(request: UserRequestModel, user_token: HTTPAuthorizationCredentials = Depends(security)):
    """
    创建新项目
    
    1. 接收用户需求
    2. 调用文档AI生成项目文档
    3. 返回项目ID和初始文档
    """
    try:
        # 验证用户身份
        user = await verify_user_token(user_token.credentials)
        
        # 创建新项目
        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            user_id=user.id,
            name=request.description[:50],  # 取前50字符作为项目名
            status="document_generation",
            created_at=datetime.now()
        )
        
        # 保存项目到数据库
        await db_manager.save_project(project)
        
        # 调用文档AI生成项目文档
        document_ai = ai_coordinator.get_document_ai()
        document = await document_ai.generate_project_document(request.dict())
        
        # 保存文档
        await db_manager.save_document(project_id, document)
        
        # 通知WebSocket客户端
        await websocket_manager.broadcast_to_user(
            user.id, 
            {
                "type": "project_created",
                "project_id": project_id,
                "document": document.dict()
            }
        )
        
        return {
            "success": True,
            "project_id": project_id,
            "document": document.dict(),
            "status": "document_ready"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"项目创建失败: {str(e)}")

@app.post("/api/v1/projects/{project_id}/document/update")
async def update_document(project_id: str, update: DocumentUpdateModel, 
                         user_token: HTTPAuthorizationCredentials = Depends(security)):
    """
    更新项目文档
    
    1. 接收用户的文档修改
    2. 如果是AI协助修改，调用文档AI
    3. 更新文档并保存历史版本
    """
    try:
        user = await verify_user_token(user_token.credentials)
        
        # 验证项目权限
        project = await db_manager.get_project(project_id)
        if not project or project.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权限访问此项目")
        
        if update.update_type == "ai_generated" and update.user_feedback:
            # 使用AI协助修改文档
            document_ai = ai_coordinator.get_document_ai()
            current_doc = await db_manager.get_document(project_id)
            
            updated_document = await document_ai.refine_document(
                current_doc, update.user_feedback
            )
        else:
            # 手动修改文档
            updated_document = ProjectDocument(
                content=update.document_content,
                version=await db_manager.get_next_document_version(project_id),
                updated_at=datetime.now()
            )
        
        # 保存更新的文档
        await db_manager.save_document(project_id, updated_document)
        
        # 实时通知用户
        await websocket_manager.broadcast_to_user(
            user.id,
            {
                "type": "document_updated",
                "project_id": project_id,
                "document": updated_document.dict()
            }
        )
        
        return {
            "success": True,
            "document": updated_document.dict(),
            "version": updated_document.version
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档更新失败: {str(e)}")

@app.post("/api/v1/projects/{project_id}/development/start")
async def start_development(project_id: str, user_token: HTTPAuthorizationCredentials = Depends(security)):
    """
    开始项目开发
    
    1. 确认文档最终版本
    2. 启动开发AI和监管AI
    3. 开始持续性开发流程
    """
    try:
        user = await verify_user_token(user_token.credentials)
        
        # 验证项目状态
        project = await db_manager.get_project(project_id)
        if project.status != "document_confirmed":
            raise HTTPException(status_code=400, detail="项目文档尚未确认")
        
        # 获取最终确认的文档
        document = await db_manager.get_document(project_id)
        
        # 更新项目状态
        await db_manager.update_project_status(project_id, "development_started")
        
        # 启动AI协作开发流程
        development_task = await ai_coordinator.start_development_process(
            project_id, document, user.id
        )
        
        # 实时通知开发开始
        await websocket_manager.broadcast_to_user(
            user.id,
            {
                "type": "development_started", 
                "project_id": project_id,
                "task_id": development_task.id
            }
        )
        
        return {
            "success": True,
            "message": "开发流程已启动",
            "task_id": development_task.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"开发启动失败: {str(e)}")

@app.get("/api/v1/projects/{project_id}/development/status")
async def get_development_status(project_id: str, user_token: HTTPAuthorizationCredentials = Depends(security)):
    """获取开发状态"""
    try:
        user = await verify_user_token(user_token.credentials)
        
        # 获取开发状态
        status = await ai_coordinator.get_development_status(project_id)
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@app.get("/api/v1/projects/{project_id}/frontend/preview")
async def get_frontend_preview(project_id: str, user_token: HTTPAuthorizationCredentials = Depends(security)):
    """
    获取前端预览
    
    当后端开发完成后，生成前端预览供用户查看
    """
    try:
        user = await verify_user_token(user_token.credentials)
        
        # 获取前端预览
        frontend_ai = ai_coordinator.get_frontend_ai()
        preview = await frontend_ai.generate_preview(project_id)
        
        return {
            "success": True,
            "preview": preview.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"前端预览生成失败: {str(e)}")

@app.post("/api/v1/projects/{project_id}/frontend/feedback")
async def submit_frontend_feedback(project_id: str, feedback: FrontendFeedbackModel,
                                 user_token: HTTPAuthorizationCredentials = Depends(security)):
    """
    提交前端反馈
    
    用户对前端界面提供反馈，AI根据反馈调整
    """
    try:
        user = await verify_user_token(user_token.credentials)
        
        # 处理前端反馈
        frontend_ai = ai_coordinator.get_frontend_ai()
        updated_preview = await frontend_ai.process_user_feedback(
            project_id, feedback.dict()
        )
        
        # 实时推送更新的预览
        await websocket_manager.broadcast_to_user(
            user.id,
            {
                "type": "frontend_updated",
                "project_id": project_id,
                "preview": updated_preview.dict()
            }
        )
        
        return {
            "success": True,
            "preview": updated_preview.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"前端反馈处理失败: {str(e)}")

@app.post("/api/v1/projects/{project_id}/deploy")
async def deploy_project(project_id: str, deployment_config: Dict[str, Any],
                        user_token: HTTPAuthorizationCredentials = Depends(security)):
    """
    部署项目
    
    1. 项目测试完成后进行部署
    2. 配置服务器环境
    3. 设置域名和SSL
    """
    try:
        user = await verify_user_token(user_token.credentials)
        
        # 启动部署流程
        deployment_result = await ai_coordinator.deploy_project(
            project_id, deployment_config
        )
        
        # 更新项目状态
        await db_manager.update_project_status(project_id, "deploying")
        
        return {
            "success": True,
            "deployment_id": deployment_result.deployment_id,
            "status": deployment_result.status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"部署失败: {str(e)}")

@app.get("/api/v1/projects/{project_id}/final-test")
async def run_final_test(project_id: str, user_token: HTTPAuthorizationCredentials = Depends(security)):
    """
    执行最终测试和验收
    
    1. 网站测试AI对比开发文档
    2. 功能完整性检查
    3. 生成验收报告
    """
    try:
        user = await verify_user_token(user_token.credentials)
        
        # 执行最终测试
        web_test_ai = ai_coordinator.get_web_test_ai()
        test_result = await web_test_ai.run_final_acceptance_test(project_id)
        
        # 更新项目状态
        if test_result.passed:
            await db_manager.update_project_status(project_id, "completed")
        
        # 通知用户测试结果
        await websocket_manager.broadcast_to_user(
            user.id,
            {
                "type": "final_test_completed",
                "project_id": project_id,
                "result": test_result.dict()
            }
        )
        
        return {
            "success": True,
            "test_result": test_result.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"最终测试失败: {str(e)}")

# WebSocket端点
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket连接端点，用于实时通信"""
    await websocket_manager.connect(websocket, user_id)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理不同类型的消息
            await handle_websocket_message(user_id, message)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id)

async def handle_websocket_message(user_id: str, message: Dict[str, Any]):
    """处理WebSocket消息"""
    message_type = message.get("type")
    
    if message_type == "ping":
        await websocket_manager.send_to_user(user_id, {"type": "pong"})
        
    elif message_type == "subscribe_project":
        project_id = message.get("project_id")
        await websocket_manager.subscribe_to_project(user_id, project_id)
        
    elif message_type == "chat_message":
        # 处理与AI的对话消息
        await handle_ai_chat(user_id, message)

async def handle_ai_chat(user_id: str, message: Dict[str, Any]):
    """处理与AI的对话"""
    project_id = message.get("project_id")
    chat_content = message.get("content")
    ai_type = message.get("ai_type", "document")  # document, frontend, general
    
    # 根据AI类型调用相应的AI服务
    if ai_type == "document":
        response = await ai_coordinator.chat_with_document_ai(project_id, chat_content)
    elif ai_type == "frontend":
        response = await ai_coordinator.chat_with_frontend_ai(project_id, chat_content)
    else:
        response = await ai_coordinator.chat_with_general_ai(project_id, chat_content)
    
    # 发送AI回复
    await websocket_manager.send_to_user(
        user_id,
        {
            "type": "ai_response",
            "ai_type": ai_type,
            "content": response,
            "project_id": project_id
        }
    )

async def verify_user_token(token: str) -> User:
    """验证用户token"""
    # 这里应该实现真实的token验证逻辑
    # 为了演示，我们返回一个模拟用户
    return User(
        id="user_123",
        username="demo_user",
        email="demo@example.com"
    )

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    print("🚀 多AI协作开发平台启动中...")
    
    # 初始化数据库
    await db_manager.initialize()
    
    # 初始化AI协调器
    await ai_coordinator.initialize()
    
    print("✅ 平台启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    print("🔄 平台关闭中...")
    
    # 清理资源
    await db_manager.cleanup()
    await ai_coordinator.cleanup()
    
    print("✅ 平台已关闭")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )