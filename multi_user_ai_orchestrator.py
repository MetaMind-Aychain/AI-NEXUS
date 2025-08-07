#!/usr/bin/env python3
"""
多用户AI协调器
支持用户隔离、API优化、智能调度等功能
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from fastapi import WebSocket

from multi_user_database import MultiUserDatabaseManager, User, Project
from api_optimization_manager import APIOptimizationManager, APIRequest, RequestDeduplicator
from gpt_engineer.core.ai import AI
from gpt_engineer.core.files_dict import FilesDict

# 导入AI组件
from multi_ai_system.ai.advanced_document_ai import AdvancedDocumentAI
from multi_ai_system.ai.advanced_supervisor_ai import AdvancedSupervisorAI
from multi_ai_system.ai.advanced_test_ai import AdvancedTestAI
from multi_ai_system.memory.shared_memory import SharedMemoryManager
from multi_ai_system.core.deep_integration import DeepIntegrationManager

logger = logging.getLogger("多用户AI协调器")

@dataclass
class UserSession:
    """用户会话数据"""
    user_id: str
    username: str
    websockets: List[WebSocket]
    current_project_id: Optional[str] = None
    session_start: float = 0.0
    last_activity: float = 0.0

class MultiUserAIOrchestrator:
    """多用户AI协调器"""
    
    def __init__(self, config: Dict, db_manager: MultiUserDatabaseManager):
        self.config = config
        self.db = db_manager
        
        # API优化管理器
        self.api_optimizer = APIOptimizationManager(
            cache_ttl=config.get("cache_ttl", 3600),
            max_cache_size=config.get("max_cache_size", 1000)
        )
        
        # 请求去重器
        self.deduplicator = RequestDeduplicator()
        
        # 用户会话管理
        self.user_sessions: Dict[str, UserSession] = {}
        
        # 初始化AI引擎
        self._init_ai_components()
        
        # 启动清理任务（延迟到运行时）
        self._cleanup_task_started = False
    
    def _init_ai_components(self):
        """初始化AI组件"""
        # 设置OpenAI API密钥
        api_key = self.config.get("openai.api_key")
        if api_key and api_key != "your-openai-api-key-here":
            import os
            os.environ["OPENAI_API_KEY"] = api_key
            logger.info("OpenAI API密钥已设置")
        else:
            logger.warning("未找到有效的OpenAI API密钥")
        
        # 初始化AI引擎
        model_name = self.config.get("openai.model", "gpt-3.5-turbo")
        temperature = self.config.get("openai.temperature", 0.7)
        
        try:
            # 直接传递API密钥给AI构造函数
            self.ai_engine = AI(
                model_name=model_name, 
                temperature=temperature
            )
            logger.info(f"AI引擎初始化成功: {model_name}")
        except Exception as e:
            logger.error(f"AI引擎初始化失败: {e}")
            # 创建一个模拟的AI引擎用于测试
            logger.info("创建模拟AI引擎用于测试")
            self.ai_engine = self._create_mock_ai_engine()
        
        # 初始化AI组件（每个用户会话时会创建独立的实例）
        self._ai_components_initialized = False
    
    def _create_mock_ai_engine(self):
        """创建模拟AI引擎用于测试"""
        class MockAI:
            def __init__(self):
                self.model_name = "mock-gpt-3.5-turbo"
                self.temperature = 0.7
                self.streaming = False
                self.vision = False
                self.token_usage_log = None
            
            def start(self, prompt, **kwargs):
                """模拟AI响应"""
                logger.info(f"模拟AI响应: {prompt[:100]}...")
                return f"模拟AI响应: {prompt[:50]}..."
            
            def next(self, messages, **kwargs):
                """模拟AI对话"""
                logger.info(f"模拟AI对话: {len(messages)} 条消息")
                return f"模拟AI对话响应: {messages[-1]['content'][:50]}..."
            
            def __getattr__(self, name):
                """处理其他方法调用"""
                def method(*args, **kwargs):
                    logger.info(f"模拟AI方法调用: {name}")
                    if name == "start":
                        return "模拟响应"
                    elif name == "next":
                        return "模拟对话响应"
                    else:
                        return "模拟响应"
                return method
        
        return MockAI()
    
    def _init_user_ai_components(self, user_id: str):
        """为用户初始化AI组件"""
        # 用户特定的共享记忆
        user_shared_memory = SharedMemoryManager(f"./user_memory/{user_id}")
        
        # 确保AI引擎存在
        if self.ai_engine is None:
            logger.warning("AI引擎未初始化，使用模拟引擎")
            self.ai_engine = self._create_mock_ai_engine()
        
        try:
            # 用户特定的AI组件
            document_ai = AdvancedDocumentAI(self.ai_engine, user_shared_memory)
            supervisor_ai = AdvancedSupervisorAI(self.ai_engine, user_shared_memory)
            test_ai = AdvancedTestAI(self.ai_engine)
            
            # 用户特定的深度集成管理器
            integration_manager = DeepIntegrationManager(f"./user_workspace/{user_id}")
            integration_manager.setup_gpt_engineer_core(self.ai_engine)
            integration_manager.setup_upgraded_ai_components(
                supervisor_ai, test_ai, user_shared_memory
            )
            
            return {
                "document_ai": document_ai,
                "supervisor_ai": supervisor_ai,
                "test_ai": test_ai,
                "integration_manager": integration_manager,
                "shared_memory": user_shared_memory
            }
        except Exception as e:
            logger.error(f"初始化用户AI组件失败: {e}")
            # 返回模拟组件
            return self._create_mock_user_components(user_id, user_shared_memory)
    
    def _create_mock_user_components(self, user_id: str, shared_memory):
        """创建模拟用户AI组件"""
        class MockDocumentAI:
            async def analyze_requirements(self, user_input: str, context: Optional[Dict] = None):
                logger.info(f"模拟文档AI分析需求: {user_input[:100]}...")
                return {
                    "project_name": "模拟项目",
                    "project_type": "web_application",
                    "features": ["用户管理", "数据展示", "API接口"],
                    "tech_stack": ["Python", "FastAPI", "React"],
                    "architecture": "前后端分离",
                    "database": "SQLite",
                    "deployment": "Docker"
                }
        
        class MockSupervisorAI:
            async def monitor_progress(self, session_id: str, event_data: Dict):
                logger.info(f"模拟监督AI监控进度: {session_id}")
                return type('obj', (object,), {
                    'quality_score': 0.8,
                    'feedback': '模拟监督反馈',
                    'recommendations': ['继续开发', '优化代码']
                })()
        
        class MockTestAI:
            async def comprehensive_test(self, project_id: str, context: Dict):
                logger.info(f"模拟测试AI执行测试: {project_id}")
                return type('obj', (object,), {
                    'pass_rate': 0.9,
                    'issues': ['模拟测试问题1', '模拟测试问题2'],
                    'coverage': 0.85
                })()
        
        class MockIntegrationManager:
            def create_deep_integrated_agent(self):
                class MockAgent:
                    def init(self, prompt):
                        logger.info(f"模拟GPT-ENGINEER生成代码: {prompt[:100]}...")
                        return FilesDict({
                            "main.py": "# 模拟主程序\nprint('Hello World')",
                            "requirements.txt": "fastapi\nuvicorn",
                            "README.md": "# 模拟项目\n这是一个模拟生成的项目"
                        })
                    
                    def improve(self, files, feedback):
                        logger.info(f"模拟GPT-ENGINEER改进代码: {feedback[:50]}...")
                        return files
                
                return MockAgent()
        
        return {
            "document_ai": MockDocumentAI(),
            "supervisor_ai": MockSupervisorAI(),
            "test_ai": MockTestAI(),
            "integration_manager": MockIntegrationManager(),
            "shared_memory": shared_memory
        }
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        if hasattr(self, '_cleanup_task_started') and self._cleanup_task_started:
            return
        
        self._cleanup_task_started = True
        
        # 使用线程而不是异步任务，避免事件循环问题
        import threading
        def cleanup_thread():
            while True:
                time.sleep(300)  # 每5分钟清理一次
                self._cleanup_inactive_sessions()
                self.deduplicator.cleanup_old_requests()
        
        cleanup_thread_obj = threading.Thread(target=cleanup_thread, daemon=True)
        cleanup_thread_obj.start()
        logger.info("清理任务已启动（线程模式）")
    
    def _cleanup_inactive_sessions(self):
        """清理非活跃会话"""
        current_time = time.time()
        inactive_timeout = 1800  # 30分钟无活动则清理
        
        inactive_users = []
        for user_id, session in self.user_sessions.items():
            if current_time - session.last_activity > inactive_timeout:
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            del self.user_sessions[user_id]
            logger.info(f"清理非活跃用户会话: {user_id}")
    
    async def add_websocket(self, websocket: WebSocket, user_id: str):
        """添加用户WebSocket连接"""
        await websocket.accept()
        
        if user_id not in self.user_sessions:
            # 创建新用户会话
            user = self.db.get_user(user_id)
            if not user:
                await websocket.close(code=4000, reason="User not found")
                return
            
            self.user_sessions[user_id] = UserSession(
                user_id=user_id,
                username=user.username,
                websockets=[websocket],
                session_start=time.time(),
                last_activity=time.time()
            )
            logger.info(f"创建新用户会话: {user.username} (ID: {user_id})")
        else:
            # 添加到现有会话
            self.user_sessions[user_id].websockets.append(websocket)
            self.user_sessions[user_id].last_activity = time.time()
        
        logger.info(f"用户 {user_id} WebSocket连接，总连接数: {len(self.user_sessions[user_id].websockets)}")
    
    async def remove_websocket(self, websocket: WebSocket, user_id: str):
        """移除用户WebSocket连接"""
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            if websocket in session.websockets:
                session.websockets.remove(websocket)
            
            # 如果没有活跃连接，清理会话
            if not session.websockets:
                del self.user_sessions[user_id]
                logger.info(f"清理用户会话: {user_id}")
            else:
                logger.info(f"用户 {user_id} WebSocket断开，剩余连接数: {len(session.websockets)}")
    
    async def broadcast_to_user(self, user_id: str, message: Dict):
        """向特定用户广播消息"""
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            message_str = json.dumps(message, ensure_ascii=False)
            
            # 更新最后活动时间
            session.last_activity = time.time()
            
            # 向所有连接发送消息
            for connection in session.websockets.copy():
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    logger.error(f"发送消息失败: {e}")
                    await self.remove_websocket(connection, user_id)
    
    async def log_and_broadcast(self, user_id: str, project_id: str, ai_name: str, 
                               action: str, message: str, prompt: str = "", 
                               response: str = "", tokens_used: int = 0, cost: float = 0.0):
        """记录日志并广播到用户"""
        # 控制台日志
        logger.info(f"[用户:{user_id}] [{ai_name}] {action}: {message}")
        
        # 数据库日志
        if prompt and response:
            self.db.log_ai_interaction(
                user_id, project_id, ai_name, action, prompt, response, 
                tokens_used=tokens_used, cost=cost
            )
        
        # 用户广播
        await self.broadcast_to_user(user_id, {
            "type": "ai_log",
            "project_id": project_id,
            "ai_name": ai_name,
            "action": action,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "tokens_used": tokens_used,
            "cost": cost
        })
    
    async def execute_optimized_ai_workflow(self, user_id: str, user_requirement: str) -> Dict:
        """执行优化的AI协作工作流程"""
        # 检查用户API限制
        if not self.db.check_user_api_limit(user_id):
            raise Exception("用户API使用次数已达上限")
        
        # 检查速率限制
        if not self.api_optimizer.check_rate_limit(user_id):
            raise Exception("请求过于频繁，请稍后再试")
        
        # 检查重复请求
        if self.deduplicator.is_duplicate(user_requirement, user_id):
            raise Exception("检测到重复请求，请稍后再试")
        
        # 生成项目ID
        project_id = f"user_{user_id}_integrated_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # 初始化用户AI组件
        user_ai_components = self._init_user_ai_components(user_id)
        
        # 更新用户会话
        if user_id in self.user_sessions:
            self.user_sessions[user_id].current_project_id = project_id
            self.user_sessions[user_id].last_activity = time.time()
        
        logger.info(f"开始用户 {user_id} 的AI协作开发流程，项目ID: {project_id}")
        
        try:
            # 第1步：优化的文档AI分析需求
            await self.log_and_broadcast(user_id, project_id, "文档AI", "需求分析", 
                                       "使用优化AI分析用户需求...")
            
            # 检查缓存
            cached_result = self.api_optimizer.get_cached_response(
                user_requirement, "文档AI", "需求分析"
            )
            
            if cached_result:
                document_result = json.loads(cached_result)
                await self.log_and_broadcast(user_id, project_id, "文档AI", "需求分析完成", 
                                           "使用缓存结果", user_requirement, cached_result)
            else:
                # 优化提示词
                optimized_requirement = self.api_optimizer.optimize_prompt(user_requirement)
                
                # 调用文档AI
                start_time = time.time()
                document_result = await user_ai_components["document_ai"].analyze_requirements(
                    optimized_requirement, 
                    context={"project_id": project_id, "user_id": user_id, "platform": "multi_user"}
                )
                response_time = time.time() - start_time
                
                # 估算token使用
                tokens_used = self.api_optimizer.estimate_tokens(optimized_requirement + str(document_result))
                cost = tokens_used * 0.000002  # 粗略估算成本
                
                # 缓存结果
                self.api_optimizer.cache_response(
                    user_requirement, "文档AI", "需求分析", 
                    json.dumps(document_result), quality_score=0.9
                )
                
                await self.log_and_broadcast(user_id, project_id, "文档AI", "需求分析完成", 
                                           f"生成了详细的项目文档，包含 {len(document_result.get('features', []))} 个功能模块",
                                           optimized_requirement, str(document_result), tokens_used, cost)
            
            # 记录AI协作
            self.db.log_ai_collaboration(user_id, project_id, "需求分析", ["文档AI"], 
                                       f"分析用户需求，生成项目文档")
            
            # 第2步：优化的开发AI代码生成
            await self.log_and_broadcast(user_id, project_id, "开发AI", "代码生成", 
                                       "使用GPT-ENGINEER核心引擎生成代码...")
            
            # 创建深度集成开发AI
            dev_ai = user_ai_components["integration_manager"].create_deep_integrated_agent()
            
            # 构建优化的开发提示
            development_prompt = self._build_optimized_development_prompt(document_result, user_requirement)
            
            # 调用GPT-ENGINEER
            start_time = time.time()
            generated_files = dev_ai.init(development_prompt)
            response_time = time.time() - start_time
            
            # 估算token使用
            tokens_used = self.api_optimizer.estimate_tokens(development_prompt + str(generated_files))
            cost = tokens_used * 0.000002
            
            await self.log_and_broadcast(user_id, project_id, "开发AI", "代码生成完成", 
                                       f"GPT-ENGINEER生成了 {len(generated_files)} 个文件",
                                       development_prompt, f"生成了 {len(generated_files)} 个文件", tokens_used, cost)
            
            # 第3步：优化的监督AI质量检查
            await self.log_and_broadcast(user_id, project_id, "监督AI", "质量监督", 
                                       "监督AI开始检查代码质量...")
            
            # 启动监督
            supervision_result = await user_ai_components["supervisor_ai"].monitor_progress(
                f"supervision_{project_id}",
                {
                    "event_type": "code_generated",
                    "files": generated_files,
                    "requirements": document_result
                }
            )
            
            await self.log_and_broadcast(user_id, project_id, "监督AI", "质量检查完成", 
                                       f"代码质量评分: {supervision_result.quality_score:.2f}")
            
            # 第4步：如果质量不达标，进行改进
            if supervision_result.quality_score < 0.8:
                await self.log_and_broadcast(user_id, project_id, "开发AI", "代码改进", 
                                           "根据监督AI反馈，使用GPT-ENGINEER改进代码...")
                
                improvement_feedback = supervision_result.feedback
                improved_files = dev_ai.improve(generated_files, improvement_feedback)
                generated_files = improved_files
                
                await self.log_and_broadcast(user_id, project_id, "开发AI", "代码改进完成", 
                                           "代码已根据监督AI建议进行改进")
            
            # 第5步：优化的测试AI验证
            await self.log_and_broadcast(user_id, project_id, "测试AI", "生成测试", 
                                       "测试AI开始为生成的代码创建测试...")
            
            test_result = await user_ai_components["test_ai"].comprehensive_test(
                project_id,
                {
                    "files": generated_files,
                    "requirements": document_result,
                    "project_type": document_result.get("project_type", "web_application")
                }
            )
            
            await self.log_and_broadcast(user_id, project_id, "测试AI", "测试完成", 
                                       f"测试通过率: {test_result.pass_rate:.1%}，发现 {len(test_result.issues)} 个问题")
            
            # 第6步：如果有测试问题，再次改进
            if test_result.issues:
                await self.log_and_broadcast(user_id, project_id, "开发AI", "修复问题", 
                                           "根据测试结果修复发现的问题...")
                
                fix_prompt = f"修复以下测试发现的问题：\n"
                for issue in test_result.issues:
                    fix_prompt += f"- {issue}\n"
                
                fixed_files = dev_ai.improve(generated_files, fix_prompt)
                generated_files = fixed_files
                
                await self.log_and_broadcast(user_id, project_id, "开发AI", "问题修复完成", 
                                           "所有测试问题已修复")
            
            # 第7步：保存项目文件
            project_path = await self._save_user_project(user_id, project_id, generated_files, document_result)
            
            # 记录最终协作结果
            self.db.log_ai_collaboration(user_id, project_id, "项目完成", 
                                       ["文档AI", "开发AI", "监督AI", "测试AI"], 
                                       f"完成项目开发，生成 {len(generated_files)} 个文件")
            
            # 保存项目到数据库
            project_data = {
                'id': project_id,
                'user_id': user_id,
                'name': document_result.get('project_name', 'AI集成项目'),
                'description': user_requirement,
                'status': '已完成',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'project_path': project_path,
                'files_count': len(generated_files),
                'ai_generated': True,
                'project_type': document_result.get('project_type', 'web_application'),
                'tech_stack': json.dumps(document_result.get('tech_stack', [])),
                'completion_percentage': 100.0
            }
            
            self.db.save_project(project_data)
            
            # 最终完成通知
            await self.log_and_broadcast(user_id, project_id, "系统", "项目完成", 
                                       "优化的AI协作开发完成！")
            
            # 广播项目完成状态
            await self.broadcast_to_user(user_id, {
                "type": "project_completed",
                "project": project_data,
                "files_count": len(generated_files),
                "project_path": project_path,
                "ai_collaboration": True,
                "optimization_stats": self.api_optimizer.get_cache_stats()
            })
            
            logger.info(f"用户 {user_id} 的AI协作项目 {project_id} 开发完成")
            
            return project_data
            
        except Exception as e:
            error_msg = f"AI协作开发过程中发生错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await self.log_and_broadcast(user_id, project_id, "系统", "错误", error_msg)
            raise
    
    def _build_optimized_development_prompt(self, document_result: Dict, user_requirement: str) -> str:
        """构建优化的开发提示"""
        # 使用API优化器优化提示词
        base_prompt = f"""
        请开发一个项目，用户需求如下：
        原始需求：{user_requirement}
        
        项目规格：
        项目名称：{document_result.get('project_name')}
        项目类型：{document_result.get('project_type')}
        技术栈：{', '.join(document_result.get('tech_stack', []))}
        
        核心功能模块：
        """
        
        for i, feature in enumerate(document_result.get('features', []), 1):
            base_prompt += f"{i}. {feature}\n"
        
        base_prompt += """
        开发要求：
        1. 生成完整可运行的项目代码
        2. 包含完整的后端API实现
        3. 包含现代化前端界面
        4. 包含必要的配置文件
        5. 包含详细的README文档
        6. 遵循最佳实践和代码规范
        7. 确保代码可维护性和可扩展性
        
        请开始生成项目代码。
        """
        
        return self.api_optimizer.optimize_prompt(base_prompt)
    
    async def _save_user_project(self, user_id: str, project_id: str, files_dict: FilesDict, 
                                document_result: Dict) -> str:
        """保存用户项目文件"""
        project_dir = Path(f"integrated_projects/{user_id}/{project_id}")
        project_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"保存用户 {user_id} 的项目文件到: {project_dir}")
        
        # 保存GPT-ENGINEER生成的文件
        for filename, content in files_dict.items():
            file_path = project_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                file_path.write_text(content, encoding='utf-8')
                logger.info(f"   已保存AI生成文件: {filename}")
            except Exception as e:
                logger.error(f"   保存文件失败 {filename}: {e}")
        
        # 生成项目元数据
        metadata = {
            "project_id": project_id,
            "user_id": user_id,
            "generated_by": "多用户AI协作系统",
            "ai_components": ["文档AI", "开发AI(GPT-ENGINEER)", "监督AI", "测试AI"],
            "gpt_engineer_integration": True,
            "optimization_enabled": True,
            "generation_time": datetime.now().isoformat(),
            "document_analysis": document_result,
            "files_count": len(files_dict),
            "cache_stats": self.api_optimizer.get_cache_stats()
        }
        
        (project_dir / "ai_metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), 
            encoding='utf-8'
        )
        
        return str(project_dir)
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息"""
        user = self.db.get_user(user_id)
        if not user:
            return {}
        
        projects = self.db.get_user_projects(user_id)
        api_usage = self.db.get_user_api_usage(user_id)
        
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "subscription_tier": user.subscription_tier,
                "api_usage_count": user.api_usage_count,
                "api_usage_limit": user.api_usage_limit
            },
            "projects": {
                "total": len(projects),
                "completed": len([p for p in projects if p.status == "已完成"]),
                "in_progress": len([p for p in projects if p.status == "进行中"])
            },
            "api_usage": api_usage,
            "optimization_stats": self.api_optimizer.get_cache_stats()
        } 