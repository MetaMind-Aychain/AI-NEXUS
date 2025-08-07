"""
AI协调器

深度集成现有的多AI协作系统，负责协调各个AI服务的工作
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# 深度集成现有的多AI系统
import sys
sys.path.append('../..')
from multi_ai_system.orchestrator import MultiAIOrchestrator
from multi_ai_system.core.enhanced_dev_ai import EnhancedDevAI
from multi_ai_system.ai.supervisor_ai import SupervisorAI
from multi_ai_system.ai.test_ai import TestAI
from multi_ai_system.ai.deploy_ai import DeployAI
from multi_ai_system.memory.shared_memory import SharedMemoryManager
from multi_ai_system.core.base_interfaces import (
    ProjectResult, DevPlan, DevelopmentEvent, TaskStatus
)
from gpt_engineer.core.ai import AI
from gpt_engineer.core.prompt import Prompt

# Web平台组件
from .models import (
    Project, ProjectDocument, DevelopmentTask, FrontendPreview,
    DeploymentStatus, AIType, ProjectStatus
)
from .ai_services import (
    DocumentAI, FrontendAI, TransferAI, 
    ServerSupervisorAI, WebTestAI
)
from .database import DatabaseManager


class AICoordinator:
    """
    AI协调器 - 深度集成多AI协作系统的核心组件
    
    负责：
    1. 管理和协调所有AI服务
    2. 集成现有的多AI协作系统
    3. 处理用户请求的路由和分发
    4. 监控AI服务状态和性能
    5. 管理项目的完整生命周期
    """
    
    def __init__(self, work_dir: str = "./ai_workspace"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        
        # 核心AI实例
        self.main_ai = None
        
        # 现有多AI系统组件
        self.orchestrator: Optional[MultiAIOrchestrator] = None
        self.shared_memory: Optional[SharedMemoryManager] = None
        
        # Web平台专用AI服务
        self.document_ai: Optional[DocumentAI] = None
        self.frontend_ai: Optional[FrontendAI] = None
        self.transfer_ai: Optional[TransferAI] = None
        self.server_supervisor_ai: Optional[ServerSupervisorAI] = None
        self.web_test_ai: Optional[WebTestAI] = None
        
        # 项目管理
        self.active_projects: Dict[str, Dict[str, Any]] = {}
        self.project_orchestrators: Dict[str, MultiAIOrchestrator] = {}
        
        # 数据库管理器
        self.db_manager: Optional[DatabaseManager] = None
        
        # WebSocket管理器（稍后注入）
        self.websocket_manager = None
        
        # 性能监控
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "active_ai_sessions": 0
        }
    
    async def initialize(self):
        """初始化AI协调器"""
        print("🚀 AI协调器初始化中...")
        
        # 初始化主AI实例
        self.main_ai = AI(
            model_name="gpt-4o",
            temperature=0.1
        )
        
        # 初始化共享记忆系统
        memory_path = self.work_dir / "shared_memory"
        self.shared_memory = SharedMemoryManager(str(memory_path))
        
        # 初始化Web平台专用AI服务
        self.document_ai = DocumentAI(self.main_ai)
        self.frontend_ai = FrontendAI(self.main_ai)
        self.transfer_ai = TransferAI(self.main_ai)
        self.server_supervisor_ai = ServerSupervisorAI(self.main_ai)
        self.web_test_ai = WebTestAI(self.main_ai)
        
        print("✅ AI协调器初始化完成")
    
    def set_database_manager(self, db_manager: DatabaseManager):
        """设置数据库管理器"""
        self.db_manager = db_manager
    
    def set_websocket_manager(self, websocket_manager):
        """设置WebSocket管理器"""
        self.websocket_manager = websocket_manager
    
    # === 项目生命周期管理 ===
    
    async def start_development_process(self, project_id: str, document: ProjectDocument, 
                                      user_id: str) -> DevelopmentTask:
        """
        启动开发流程
        
        深度集成现有的多AI协作系统，创建项目专用的Orchestrator
        """
        try:
            # 为项目创建专用的工作目录
            project_work_dir = self.work_dir / f"project_{project_id}"
            project_work_dir.mkdir(exist_ok=True)
            
            # 创建项目专用的MultiAIOrchestrator
            orchestrator = MultiAIOrchestrator(
                work_dir=str(project_work_dir),
                ai_config={'model_name': 'gpt-4o', 'temperature': 0.1},
                workflow_config={
                    'max_dev_iterations': 5,
                    'package_type': 'docker',
                    'include_frontend': True,
                    'auto_deploy': False  # 由Web平台控制部署
                }
            )
            
            # 深度集成：注入共享记忆
            orchestrator.shared_memory = self.shared_memory
            
            # 存储项目编排器
            self.project_orchestrators[project_id] = orchestrator
            
            # 创建开发任务
            dev_task = DevelopmentTask(
                project_id=project_id,
                task_name="完整项目开发",
                description="基于项目文档进行完整的自动化开发",
                task_type="full_development",
                assigned_ai=AIType.DEVELOPMENT_AI,
                estimated_hours=8.0
            )
            
            # 保存任务到数据库
            if self.db_manager:
                await self.db_manager.save_task(dev_task)
            
            # 记录项目为活跃状态
            self.active_projects[project_id] = {
                "user_id": user_id,
                "orchestrator": orchestrator,
                "start_time": datetime.now(),
                "current_stage": "backend_development",
                "status": "in_progress"
            }
            
            # 启动异步开发流程
            asyncio.create_task(self._run_development_workflow(project_id, document, dev_task))
            
            # 通知用户开发已开始
            if self.websocket_manager:
                await self.websocket_manager.send_ai_status_update(
                    project_id, "development_ai", "started", 
                    {"task_id": dev_task.id}
                )
            
            return dev_task
            
        except Exception as e:
            print(f"启动开发流程失败: {e}")
            raise
    
    async def _run_development_workflow(self, project_id: str, document: ProjectDocument, 
                                      dev_task: DevelopmentTask):
        """
        运行完整的开发工作流程
        
        这是核心的开发流程，深度集成现有的多AI系统
        """
        try:
            orchestrator = self.project_orchestrators[project_id]
            
            # 转换文档为orchestrator需要的格式
            user_requirement = self._convert_document_to_requirement(document)
            
            # 设置工作流选项
            workflow_options = {
                'include_frontend': False,  # 先完成后端，前端由Web平台专门处理
                'auto_deploy': False,       # 部署由Web平台控制
                'max_dev_iterations': 5
            }
            
            # 更新任务状态
            dev_task.status = "in_progress"
            dev_task.started_at = datetime.now()
            if self.db_manager:
                await self.db_manager.save_task(dev_task)
            
            # 通知进度更新
            await self._notify_progress_update(project_id, "backend_development", 20)
            
            # 执行核心开发工作流
            result = await orchestrator.execute_workflow(
                user_requirement=user_requirement,
                workflow_options=workflow_options
            )
            
            # 处理开发结果
            if result.success:
                await self._handle_development_success(project_id, result, dev_task)
            else:
                await self._handle_development_failure(project_id, result, dev_task)
                
        except Exception as e:
            await self._handle_development_error(project_id, dev_task, str(e))
    
    async def _handle_development_success(self, project_id: str, result: ProjectResult, 
                                        dev_task: DevelopmentTask):
        """处理开发成功"""
        try:
            # 更新任务状态
            dev_task.status = "completed"
            dev_task.completed_at = datetime.now()
            dev_task.quality_score = result.final_score
            dev_task.output_files = list(result.files.keys())
            
            if self.db_manager:
                await self.db_manager.save_task(dev_task)
                await self.db_manager.update_project_status(project_id, ProjectStatus.BACKEND_DEVELOPMENT)
            
            # 更新项目状态
            if project_id in self.active_projects:
                self.active_projects[project_id]["current_stage"] = "backend_completed"
                self.active_projects[project_id]["backend_result"] = result
            
            # 通知进度更新
            await self._notify_progress_update(project_id, "backend_completed", 60)
            
            # 启动前端开发流程
            await self._start_frontend_development(project_id, result)
            
        except Exception as e:
            print(f"处理开发成功结果失败: {e}")
    
    async def _start_frontend_development(self, project_id: str, backend_result: ProjectResult):
        """启动前端开发流程"""
        try:
            # 获取项目文档
            document = await self.db_manager.get_document(project_id)
            
            # 分析后端API规范
            api_specs = self._extract_api_specifications(backend_result.files)
            
            # 生成前端预览
            preview = await self.frontend_ai.generate_frontend_preview(
                project_id, document, api_specs
            )
            
            # 保存前端预览
            if self.db_manager:
                await self.db_manager.save_frontend_preview(preview)
            
            # 通知用户前端预览已生成
            if self.websocket_manager:
                await self.websocket_manager.send_to_user(
                    self.active_projects[project_id]["user_id"],
                    {
                        "type": "frontend_preview_ready",
                        "project_id": project_id,
                        "preview_id": preview.id
                    }
                )
            
            # 更新项目状态
            if self.db_manager:
                await self.db_manager.update_project_status(project_id, ProjectStatus.FRONTEND_DEVELOPMENT)
            
            await self._notify_progress_update(project_id, "frontend_development", 75)
            
        except Exception as e:
            print(f"启动前端开发失败: {e}")
    
    async def _handle_development_failure(self, project_id: str, result: ProjectResult, 
                                        dev_task: DevelopmentTask):
        """处理开发失败"""
        dev_task.status = "failed"
        dev_task.completed_at = datetime.now()
        
        if self.db_manager:
            await self.db_manager.save_task(dev_task)
            await self.db_manager.update_project_status(project_id, ProjectStatus.FAILED)
        
        # 通知用户开发失败
        if self.websocket_manager:
            user_id = self.active_projects[project_id]["user_id"]
            await self.websocket_manager.send_error_notification(
                user_id, "development_failed", 
                result.error_message or "开发过程中发生未知错误",
                project_id
            )
    
    async def _handle_development_error(self, project_id: str, dev_task: DevelopmentTask, error_message: str):
        """处理开发错误"""
        dev_task.status = "failed"
        dev_task.completed_at = datetime.now()
        
        if self.db_manager:
            await self.db_manager.save_task(dev_task)
        
        # 通知用户开发错误
        if self.websocket_manager:
            user_id = self.active_projects[project_id]["user_id"]
            await self.websocket_manager.send_error_notification(
                user_id, "development_error", error_message, project_id
            )
    
    # === AI服务接口 ===
    
    def get_document_ai(self) -> DocumentAI:
        """获取文档AI服务"""
        return self.document_ai
    
    def get_frontend_ai(self) -> FrontendAI:
        """获取前端AI服务"""
        return self.frontend_ai
    
    def get_transfer_ai(self) -> TransferAI:
        """获取中转AI服务"""
        return self.transfer_ai
    
    def get_web_test_ai(self) -> WebTestAI:
        """获取Web测试AI服务"""
        return self.web_test_ai
    
    # === 用户交互接口 ===
    
    async def handle_user_chat(self, user_id: str, project_id: str, ai_type: str, message: str) -> str:
        """处理用户与AI的对话"""
        try:
            if ai_type == "document":
                return await self.document_ai.chat_with_user(project_id, message)
            elif ai_type == "frontend":
                # 实现前端AI对话逻辑
                return await self._chat_with_frontend_ai(project_id, message)
            elif ai_type == "general":
                return await self._chat_with_general_ai(project_id, message)
            else:
                return "不支持的AI类型"
                
        except Exception as e:
            return f"AI对话失败: {str(e)}"
    
    async def process_user_feedback(self, user_id: str, project_id: str, 
                                  feedback_type: str, feedback_content: str):
        """处理用户反馈"""
        try:
            if feedback_type == "frontend_feedback":
                await self._process_frontend_feedback(project_id, feedback_content)
            elif feedback_type == "document_feedback":
                await self._process_document_feedback(project_id, feedback_content)
            else:
                print(f"未知的反馈类型: {feedback_type}")
                
        except Exception as e:
            print(f"处理用户反馈失败: {e}")
    
    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """获取项目状态"""
        if project_id not in self.active_projects:
            # 从数据库获取项目信息
            if self.db_manager:
                project = await self.db_manager.get_project(project_id)
                if project:
                    return {
                        "project_id": project_id,
                        "status": project.status.value,
                        "progress": 0,
                        "current_stage": "unknown"
                    }
            
            return {"project_id": project_id, "status": "not_found"}
        
        project_info = self.active_projects[project_id]
        return {
            "project_id": project_id,
            "status": project_info["status"],
            "current_stage": project_info["current_stage"],
            "start_time": project_info["start_time"].isoformat(),
            "progress": self._calculate_project_progress(project_id)
        }
    
    async def get_development_status(self, project_id: str) -> Dict[str, Any]:
        """获取详细的开发状态"""
        status = await self.get_project_status(project_id)
        
        # 添加详细信息
        if self.db_manager:
            tasks = await self.db_manager.get_project_tasks(project_id)
            status["tasks"] = [task.dict() for task in tasks]
        
        return status
    
    # === 部署管理 ===
    
    async def deploy_project(self, project_id: str, deployment_config: Dict[str, Any]) -> DeploymentStatus:
        """部署项目"""
        try:
            # 获取项目的最终代码
            orchestrator = self.project_orchestrators.get(project_id)
            if not orchestrator:
                raise Exception("项目编排器不存在")
            
            # 集成前后端代码
            integrated_files = await self._integrate_frontend_backend(project_id)
            
            # 使用现有的部署AI进行部署
            deploy_ai = orchestrator.deploy_ai
            
            # 打包项目
            package_result = deploy_ai.package_project(integrated_files, {
                'package_type': deployment_config.get('package_type', 'docker'),
                'version': '1.0.0'
            })
            
            # 部署到服务器
            server_config = {
                'platform': deployment_config.get('platform', 'docker'),
                'port': deployment_config.get('port', 8000)
            }
            
            deploy_result = deploy_ai.upload_to_server(package_result, server_config)
            
            # 创建部署状态记录
            deployment_status = DeploymentStatus(
                project_id=project_id,
                deployment_type=deployment_config.get('deployment_type', 'cloud'),
                status="deploying" if deploy_result.success else "failed",
                deployment_url=deploy_result.url,
                server_config=deployment_config
            )
            
            return deployment_status
            
        except Exception as e:
            print(f"部署项目失败: {e}")
            return DeploymentStatus(
                project_id=project_id,
                status="failed",
                error_logs=[str(e)]
            )
    
    # === 辅助方法 ===
    
    def _convert_document_to_requirement(self, document: ProjectDocument) -> str:
        """将项目文档转换为orchestrator需要的需求格式"""
        return f"""
项目需求：
{document.content}

技术要求：
{json.dumps(document.technical_specs, ensure_ascii=False, indent=2)}

功能需求：
{json.dumps(document.requirements, ensure_ascii=False, indent=2)}
"""
    
    def _extract_api_specifications(self, files_dict) -> List[Dict[str, Any]]:
        """从后端代码中提取API规范"""
        api_specs = []
        
        # 简化实现：分析文件名和内容提取API信息
        for filename, content in files_dict.items():
            if 'api' in filename.lower() or 'route' in filename.lower():
                # 这里应该实现更复杂的API分析逻辑
                api_specs.append({
                    "file": filename,
                    "endpoints": [],  # 应该从代码中提取
                    "models": []      # 应该从代码中提取
                })
        
        return api_specs
    
    async def _integrate_frontend_backend(self, project_id: str):
        """集成前后端代码"""
        # 获取后端代码
        backend_result = self.active_projects[project_id].get("backend_result")
        if not backend_result:
            raise Exception("后端代码不存在")
        
        # 获取前端代码
        frontend_preview = await self.db_manager.get_frontend_preview(project_id)
        if not frontend_preview:
            raise Exception("前端代码不存在")
        
        # 集成代码
        from gpt_engineer.core.files_dict import FilesDict
        integrated_files = FilesDict(backend_result.files)
        
        # 添加前端文件
        integrated_files["frontend/index.html"] = frontend_preview.html_content
        integrated_files["frontend/styles.css"] = frontend_preview.css_content
        integrated_files["frontend/script.js"] = frontend_preview.js_content
        
        return integrated_files
    
    def _calculate_project_progress(self, project_id: str) -> float:
        """计算项目进度"""
        if project_id not in self.active_projects:
            return 0.0
        
        project_info = self.active_projects[project_id]
        stage = project_info["current_stage"]
        
        stage_progress = {
            "backend_development": 30,
            "backend_completed": 60,
            "frontend_development": 75,
            "frontend_completed": 85,
            "integration": 90,
            "testing": 95,
            "deployment": 98,
            "completed": 100
        }
        
        return stage_progress.get(stage, 0)
    
    async def _notify_progress_update(self, project_id: str, stage: str, progress: float):
        """通知进度更新"""
        if self.websocket_manager:
            await self.websocket_manager.send_progress_update(project_id, {
                "stage": stage,
                "progress": progress,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _chat_with_frontend_ai(self, project_id: str, message: str) -> str:
        """与前端AI对话"""
        # 实现前端AI对话逻辑
        return "前端AI对话功能开发中..."
    
    async def _chat_with_general_ai(self, project_id: str, message: str) -> str:
        """与通用AI对话"""
        # 实现通用AI对话逻辑
        return "通用AI对话功能开发中..."
    
    async def _process_frontend_feedback(self, project_id: str, feedback: str):
        """处理前端反馈"""
        # 实现前端反馈处理逻辑
        pass
    
    async def _process_document_feedback(self, project_id: str, feedback: str):
        """处理文档反馈"""
        # 实现文档反馈处理逻辑
        pass
    
    async def cleanup(self):
        """清理资源"""
        # 清理活跃项目
        self.active_projects.clear()
        self.project_orchestrators.clear()
        
        print("✅ AI协调器资源已清理")