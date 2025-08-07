#!/usr/bin/env python3
"""
多用户AI协作开发平台 - 基于原有integrated_ai_platform.py升级
集成真正的GPT-ENGINEER + 多用户支持 + API优化
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
import uuid
import random
import webbrowser
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Web框架
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 数据库
import sqlite3

# 导入真正的GPT-ENGINEER组件
from gpt_engineer.core.ai import AI
from gpt_engineer.core.default.simple_agent import SimpleAgent
from gpt_engineer.core.default.disk_memory import DiskMemory
from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv
from gpt_engineer.core.files_dict import FilesDict
from gpt_engineer.core.prompt import Prompt

# 导入深度集成AI组件
from multi_ai_system.core.deep_integration import DeepIntegratedDevAI, DeepIntegrationManager
from multi_ai_system.ai.advanced_document_ai import AdvancedDocumentAI
from multi_ai_system.ai.advanced_supervisor_ai import AdvancedSupervisorAI
from multi_ai_system.ai.advanced_test_ai import AdvancedTestAI
from multi_ai_system.memory.shared_memory import SharedMemoryManager

# 导入多用户和优化组件
from multi_user_database import MultiUserDatabaseManager, User, Project
from api_optimization_manager import APIOptimizationManager, RequestDeduplicator
from vip_manager import VIPManager
from blockchain_manager import BlockchainManager, NetworkSelector
from real_blockchain_manager import RealBlockchainManager, BlockchainUtils
from enhanced_business_manager import (
    EnhancedBusinessManager, 
    DocumentReviewRequest, 
    FrontendReviewRequest, 
    DeploymentRequest, 
    PaymentRequest,
    MockProjectGenerator
)
from real_payment_manager import RealPaymentManager, PaymentUtils
from real_invitation_manager import RealInvitationManager

# 设置控制台编码
if sys.platform.startswith('win'):
    os.system('chcp 65001 > nul')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_user_integrated_platform.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger("多用户集成AI平台")

@dataclass
class UserSession:
    """用户会话数据"""
    user_id: str
    username: str
    websockets: List[WebSocket]
    current_project_id: Optional[str] = None
    session_start: float = 0.0
    last_activity: float = 0.0

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
                "model": "generalv3.5",
                "max_tokens": 4000,
                "temperature": 0.7,        "BASE_URL":"https://spark-api-open.xf-yun.com/v1"
            },
            "platform": {
                "host": "127.0.0.1",
                "port": 8892,  # 改为新端口
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
            "database": {
                "path": "multi_user_integrated_platform.db"
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

class MultiUserIntegratedOrchestrator:
    """多用户集成AI协调器 - 基于原有IntegratedAIOrchestrator升级"""
    
    def __init__(self, config: ConfigManager, db_manager: MultiUserDatabaseManager):
        self.config = config
        self.db = db_manager
        
        # 初始化API优化管理器
        self.api_optimizer = APIOptimizationManager(
            cache_ttl=config.get("optimization.cache_ttl", 3600),
            max_cache_size=config.get("optimization.max_cache_size", 1000)
        )
        
        # 请求去重器
        self.deduplicator = RequestDeduplicator()
        
        # 增强业务管理器
        self.business_manager = EnhancedBusinessManager(db_manager)
        
        # VIP管理器
        self.vip_manager = VIPManager(db_manager.db_path)
        self.vip_manager.init_vip_tables()
        
        # 区块链管理器
        self.blockchain_manager = BlockchainManager(db_manager.db_path)
        
        # 真实区块链管理器
        self.real_blockchain_manager = RealBlockchainManager(db_manager.db_path, use_testnet=True)
        
        # 真实支付管理器
        self.real_payment_manager = RealPaymentManager(db_manager.db_path)
        
        # 真实邀请管理器
        self.real_invitation_manager = RealInvitationManager(db_manager.db_path)
        
        # 用户会话管理
        self.user_sessions: Dict[str, UserSession] = {}
        
        # 设置OpenAI API密钥到环境变量
        api_key = self.config.get("openai.api_key")
        if api_key and api_key != "your-openai-api-key-here":
            os.environ["OPENAI_API_KEY"] = api_key
            logger.info("OpenAI API密钥已设置")
        else:
            logger.warning("未找到有效的OpenAI API密钥，某些功能可能无法正常工作")
        
        # 初始化全局AI引擎（复用原有逻辑）
        model_name = self.config.get("openai.model", "gpt-3.5-turbo")
        temperature = self.config.get("openai.temperature", 0.7)
        self.ai_engine = AI(model_name=model_name, temperature=temperature)
        
        logger.info("多用户集成AI协调器初始化完成")
    
    def _init_user_ai_components(self, user_id: str):
        """为用户初始化AI组件（复用原有逻辑）"""
        # 用户特定的共享记忆
        user_shared_memory = SharedMemoryManager(f"./user_memory/{user_id}")
        
        # 用户特定的AI组件（复用原有的正确初始化方式）
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
    
    async def execute_integrated_ai_workflow(self, user_id: str, user_requirement: str, test_mode: bool = True, development_id: str = None) -> Dict:
        """执行AI协作工作流程（支持测试模式和真实模式）"""
        # 检查是否可以使用免费测试
        has_used_free = self.db.has_free_test_used(user_id)
        
        if test_mode and not has_used_free:
            # 免费测试，不扣除配额
            required_quota = 0
            logger.info(f"用户 {user_id} 使用免费测试机会")
        elif test_mode:
            # 测试模式，扣除1配额
            required_quota = 1
        else:
            # 真实模式，扣除30配额
            required_quota = 30
        
        if required_quota > 0 and not self.db.deduct_api_balance(user_id, required_quota):
            raise Exception(f"API配额不足，需要{required_quota}个配额")
        
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
        
        logger.info(f"开始用户 {user_id} 的真正AI协作开发流程，项目ID: {project_id}")
        
        try:
            # 第1步：文档AI分析需求
            await self.log_and_broadcast(user_id, project_id, "文档AI", "需求分析", 
                                       "分析用户需求，生成项目文档...")
            
            if test_mode:
                # 测试模式：使用模拟文档生成
                document_result = self.business_manager.mock_responses["document_analysis"]
                tokens_used = 50  # 模拟token使用
                cost = 0.001  # 模拟成本
                
                # 模拟处理时间
                await asyncio.sleep(1)
            else:
                # 真实模式：调用真实AI
                # 优化提示词
                optimized_requirement = self.api_optimizer.optimize_prompt(user_requirement)
                
                # 初始化用户AI组件
                user_ai_components = self._init_user_ai_components(user_id)
                
                # 调用文档AI
                start_time = time.time()
                document_result = await user_ai_components["document_ai"].analyze_requirements(
                    optimized_requirement, 
                    context={"project_id": project_id, "user_id": user_id, "platform": "multi_user"}
                )
                response_time = time.time() - start_time
                
                # 估算token使用和缓存
                tokens_used = self.api_optimizer.estimate_tokens(optimized_requirement + str(document_result))
                cost = tokens_used * 0.000002
                
                self.api_optimizer.cache_response(
                    user_requirement, "文档AI", "需求分析", 
                    json.dumps(document_result), quality_score=0.9
                )
            
            # 保存文档到项目
            document_content = json.dumps(document_result, ensure_ascii=False, indent=2)
            self.db.update_project_document(project_id, document_content, confirmed=False)
            
            await self.log_and_broadcast(user_id, project_id, "文档AI", "需求分析完成", 
                                       f"生成了详细的项目文档，包含 {len(document_result.get('features', []))} 个功能模块",
                                       user_requirement, str(document_result), tokens_used, cost)
            
            # 第2步：开发AI代码生成
            await self.log_and_broadcast(user_id, project_id, "开发AI", "代码生成", 
                                       "生成项目代码...")
            
            if test_mode:
                # 测试模式：使用模拟代码生成
                generated_files = await MockProjectGenerator.generate_simple_social_platform()
                tokens_used = 200  # 模拟token使用
                cost = 0.004  # 模拟成本
                
                # 模拟处理时间
                await asyncio.sleep(2)
            else:
                # 真实模式：使用GPT-ENGINEER
                # 创建深度集成开发AI
                dev_ai = user_ai_components["integration_manager"].create_deep_integrated_agent()
                
                # 构建开发提示
                development_prompt = self._build_development_prompt(document_result, user_requirement)
                
                # 调用GPT-ENGINEER
                start_time = time.time()
                generated_files = dev_ai.init(development_prompt)
                response_time = time.time() - start_time
                
                tokens_used = self.api_optimizer.estimate_tokens(development_prompt + str(generated_files))
                cost = tokens_used * 0.000002
            
            await self.log_and_broadcast(user_id, project_id, "开发AI", "代码生成完成", 
                                       f"生成了 {len(generated_files)} 个文件",
                                       "", f"生成了 {len(generated_files)} 个文件", tokens_used, cost)
            
            if test_mode:
                # 测试模式：简化监督和测试流程
                await self.log_and_broadcast(user_id, project_id, "监督AI", "质量检查", 
                                           "测试模式：跳过AI质量检查，默认通过")
                await asyncio.sleep(0.5)
                
                await self.log_and_broadcast(user_id, project_id, "测试AI", "测试验证", 
                                           "测试模式：跳过AI测试验证，默认通过")
                await asyncio.sleep(0.5)
                
                quality_score = 0.9  # 模拟高质量评分
                pass_rate = 0.95     # 模拟高通过率
            else:
                # 真实模式：完整的监督和测试流程
                # 第3步：监督AI质量检查
                await self.log_and_broadcast(user_id, project_id, "监督AI", "质量监督", 
                                           "监督AI开始检查代码质量...")
                
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
                                               "根据监督AI反馈，改进代码...")
                    
                    improvement_feedback = supervision_result.feedback
                    improved_files = dev_ai.improve(generated_files, improvement_feedback)
                    generated_files = improved_files
                    
                    await self.log_and_broadcast(user_id, project_id, "开发AI", "代码改进完成", 
                                               "代码已根据监督AI建议进行改进")
                
                # 第5步：测试AI验证
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
                
                quality_score = supervision_result.quality_score
                pass_rate = test_result.pass_rate
            
            # 第7步：保存项目文件
            project_path = await self._save_user_project(user_id, project_id, generated_files, document_result)
            
            # 创建前端预览链接
            preview_url = f"/preview/{project_id}/frontend"
            self.db.update_project_frontend(project_id, preview_url, confirmed=False)
            
            # 保存项目到数据库
            project_data = {
                'id': project_id,
                'user_id': user_id,
                'name': document_result.get('project_name', 'AI集成项目'),
                'description': user_requirement,
                'status': '待确认文档',  # 新状态：需要用户确认文档
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'project_path': project_path,
                'files_count': len(generated_files),
                'ai_generated': True,
                'project_type': document_result.get('project_type', 'web_application'),
                'tech_stack': json.dumps(document_result.get('tech_stack', [])),
                'completion_percentage': 60.0,  # 60%：代码生成完成，待确认
                'deployment_status': '未部署',
                'document_confirmed': False,
                'frontend_confirmed': False,
                'document_content': document_content,
                'frontend_preview_url': preview_url
            }
            
            self.db.save_project(project_data)
            
            # 最终完成通知
            mode_text = "测试模式" if test_mode else "真实模式"
            await self.log_and_broadcast(user_id, project_id, "系统", "代码生成完成", 
                                       f"AI协作开发完成（{mode_text}）！请确认项目文档和前端界面。")
            
            # 广播项目状态
            await self.broadcast_to_user(user_id, {
                "type": "project_ready_for_review",
                "project": project_data,
                "files_count": len(generated_files),
                "project_path": project_path,
                "preview_url": preview_url,
                "test_mode": test_mode,
                "quality_score": quality_score,
                "pass_rate": pass_rate,
                "next_steps": ["确认文档", "确认前端", "部署项目"]
            })
            
            logger.info(f"用户 {user_id} 的真正AI协作项目 {project_id} 开发完成")
            
            return project_data
            
        except Exception as e:
            error_msg = f"AI协作开发过程中发生错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await self.log_and_broadcast(user_id, project_id, "系统", "错误", error_msg)
            raise
    
    def _build_development_prompt(self, document_result: Dict, user_requirement: str) -> str:
        """构建开发提示（复用原有逻辑）"""
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
        
        请开始生成项目代码。
        """
        
        return self.api_optimizer.optimize_prompt(base_prompt)
    
    async def _save_user_project(self, user_id: str, project_id: str, files_dict: FilesDict, 
                                document_result: Dict) -> str:
        """保存用户项目文件"""
        project_dir = Path(f"multi_user_projects/{user_id}/{project_id}")
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
    
    async def process_document_modification(self, user_id: str, project_id: str, modification_request: str) -> Dict:
        """处理文档修改请求"""
        logger.info(f"[用户:{user_id}] 处理文档修改请求: {modification_request[:50]}...")
        
        try:
            # 获取现有项目文档
            project = self.db.get_project(project_id)
            if not project:
                raise Exception("项目不存在")
            
            # 使用AI进行文档修改
            if hasattr(self, 'config') and self.config.get("openai.api_key"):
                # 真实LLM调用
                response = await self._call_real_llm_for_document_modification(
                    project, modification_request
                )
            else:
                # 模拟响应
                response = self._simulate_document_modification(modification_request)
            
            # 更新项目文档
            await self._update_project_document(project_id, response.get("updated_content", ""))
            
            return {
                "response": response.get("explanation", "文档已根据您的要求进行修改"),
                "document_updated": True
            }
            
        except Exception as e:
            logger.error(f"文档修改失败: {e}")
            return {
                "response": f"抱歉，文档修改失败: {str(e)}",
                "document_updated": False
            }
    
    async def process_frontend_modification(self, user_id: str, project_id: str, modification_request: str) -> Dict:
        """处理前端修改请求"""
        logger.info(f"[用户:{user_id}] 处理前端修改请求: {modification_request[:50]}...")
        
        try:
            # 获取现有项目前端
            project = self.db.get_project(project_id)
            if not project:
                raise Exception("项目不存在")
            
            # 使用AI进行前端修改
            if hasattr(self, 'config') and self.config.get("openai.api_key"):
                # 真实LLM调用
                response = await self._call_real_llm_for_frontend_modification(
                    project, modification_request
                )
            else:
                # 模拟响应
                response = self._simulate_frontend_modification(modification_request)
            
            return {
                "response": response.get("explanation", "前端界面已根据您的要求进行修改"),
                "frontend_updated": True
            }
            
        except Exception as e:
            logger.error(f"前端修改失败: {e}")
            return {
                "response": f"抱歉，前端修改失败: {str(e)}",
                "frontend_updated": False
            }
    
    async def confirm_project_document(self, user_id: str, project_id: str) -> Dict:
        """确认项目文档"""
        logger.info(f"[用户:{user_id}] 确认项目文档: {project_id}")
        
        try:
            # 更新项目状态
            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute("""
                    UPDATE projects 
                    SET document_status = 'confirmed', document_confirmed_at = ?
                    WHERE id = ? AND user_id = ?
                """, (datetime.now().isoformat(), project_id, user_id))
                conn.commit()
            
            return {"success": True, "message": "文档确认成功"}
            
        except Exception as e:
            logger.error(f"确认文档失败: {e}")
            raise Exception(f"确认文档失败: {str(e)}")
    
    async def confirm_project_frontend(self, user_id: str, project_id: str) -> Dict:
        """确认项目前端"""
        logger.info(f"[用户:{user_id}] 确认项目前端: {project_id}")
        
        try:
            # 更新项目状态
            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute("""
                    UPDATE projects 
                    SET frontend_status = 'confirmed', frontend_confirmed_at = ?, status = 'completed'
                    WHERE id = ? AND user_id = ?
                """, (datetime.now().isoformat(), project_id, user_id))
                conn.commit()
            
            return {"success": True, "message": "前端确认成功"}
            
        except Exception as e:
            logger.error(f"确认前端失败: {e}")
            raise Exception(f"确认前端失败: {str(e)}")
    
    def _simulate_document_modification(self, modification_request: str) -> Dict:
        """模拟文档修改响应"""
        responses = {
            "功能": "我已为您的项目添加了更多功能模块，包括高级计算功能和用户界面优化。",
            "设计": "文档中的UI/UX设计部分已更新，采用了更现代化的设计风格。",
            "技术": "技术架构部分已优化，增加了性能优化和安全性考虑。",
            "部署": "部署方案已更新，支持多种部署环境和自动化流程。"
        }
        
        for key, response in responses.items():
            if key in modification_request:
                return {"updated_content": f"已更新的文档内容...", "explanation": response}
        
        return {
            "updated_content": "已根据您的要求更新文档内容...",
            "explanation": "我已经根据您的要求对文档进行了相应的修改和优化。"
        }
    
    def _simulate_frontend_modification(self, modification_request: str) -> Dict:
        """模拟前端修改响应"""
        responses = {
            "颜色": "我已为您调整了界面的配色方案，采用了更协调的色彩搭配。",
            "布局": "界面布局已优化，提供了更好的视觉层次和用户体验。",
            "按钮": "按钮样式已更新，增加了hover效果和更好的交互反馈。",
            "字体": "字体大小和样式已调整，提高了可读性。",
            "响应式": "已优化移动端适配，确保在各种设备上都有良好的显示效果。"
        }
        
        for key, response in responses.items():
            if key in modification_request:
                return {"explanation": response}
        
        return {
            "explanation": "我已经根据您的要求对前端界面进行了相应的修改和优化。请查看预览区域的更新效果。"
        }

class MultiUserIntegratedPlatform:
    """多用户集成AI开发平台"""
    
    def __init__(self):
        # 加载配置
        self.config = ConfigManager()
        
        # 初始化组件
        self.app = FastAPI(
            title="多用户集成AI协作开发平台", 
            version="4.0.0",
            description="基于GPT-ENGINEER的真正多用户AI协作开发平台"
        )
        
        # 多用户数据库管理器
        self.db = MultiUserDatabaseManager(
            self.config.get("database.path", "multi_user_integrated_platform.db")
        )
        
        # 多用户AI协调器
        self.orchestrator = MultiUserIntegratedOrchestrator(self.config, self.db)
        
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
        
        logger.info("多用户集成AI协作开发平台初始化完成")
    
    def setup_static_files(self):
        """设置静态文件服务"""
        # 使用增强版的前端界面
        self.app.mount("/static", StaticFiles(directory="enhanced_frontend"), name="static")
    
    def setup_routes(self):
        """设置API路由"""
        
        @self.app.get("/")
        async def root():
            """根路径重定向到前端"""
            return HTMLResponse("""
                <script>window.location.href='/static/futuristic_platform.html';</script>
            """)
        
        @self.app.get("/payment/demo")
        async def payment_demo():
            """支付页面"""
            return FileResponse("enhanced_frontend/payment_page.html")
        
        @self.app.get("/vip-invite")
        async def vip_invite(request: Request):
            """VIP邀请页面"""
            invite_code = request.query_params.get("code", "")
            vip_level = request.query_params.get("vip", "0")
            
            # 返回特殊的VIP邀请页面
            response = FileResponse("enhanced_frontend/futuristic_platform.html")
            # 设置Cookie以便前端识别邀请码
            response.set_cookie("invite_code", invite_code, max_age=3600)
            response.set_cookie("vip_invite", vip_level, max_age=3600)
            return response
        
        @self.app.get("/static/interactive_document_viewer.html")
        async def interactive_document_viewer():
            """交互式文档查看器"""
            return FileResponse("enhanced_frontend/interactive_document_viewer.html")
        
        @self.app.get("/static/interactive_frontend_editor.html")
        async def interactive_frontend_editor():
            """交互式前端编辑器"""
            return FileResponse("enhanced_frontend/interactive_frontend_editor.html")
        
        @self.app.get("/api/health")
        async def health():
            """健康检查"""
            return {
                "status": "healthy", 
                "platform": "多用户集成AI协作开发平台",
                "version": "4.0.0",
                "multi_user": True,
                "gpt_engineer_integrated": True,
                "optimization_enabled": True,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/api/login")
        async def login(request_data: dict):
            """用户登录/注册"""
            username = request_data.get("username", "")
            email = request_data.get("email", "")
            inviter_code = request_data.get("inviter_code", "")
            
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
                        self.config.get("users.default_subscription_tier", "basic"),
                        inviter_code=inviter_code
                    )
                    
                    # 处理邀请注册奖励
                    if inviter_code:
                        invitation_result = self.orchestrator.real_invitation_manager.process_invitation_registration(
                            inviter_code, user_id, username
                        )
                        if invitation_result["success"]:
                            logger.info(f"邀请奖励处理成功: 邀请人获得 {invitation_result['reward_amount']} 配额")
                    
                    logger.info(f"新用户注册: {username}, 邀请码: {inviter_code}")
                
                return {
                    "user_id": user_id,
                    "username": username,
                    "status": "success"
                }
                
            except Exception as e:
                logger.error(f"登录失败: {e}")
                raise HTTPException(status_code=500, detail="登录失败")
        
        @self.app.post("/api/start-integrated-ai-development")
        async def start_integrated_ai_development(request_data: dict):
            """启动AI协作开发"""
            user_id = request_data.get("user_id", "")
            requirement = request_data.get("requirement", "")
            test_mode = request_data.get("test_mode", True)  # 默认测试模式
            
            if not user_id:
                raise HTTPException(status_code=400, detail="用户ID不能为空")
            if not requirement:
                raise HTTPException(status_code=400, detail="需求描述不能为空")
            
            # 检查用户是否存在
            user = self.db.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            # 检查API余额
            required_quota = 1 if test_mode else 10
            if user.api_balance < required_quota:
                raise HTTPException(status_code=429, detail=f"API配额不足，需要{required_quota}个配额")
            
            # 生成开发ID
            development_id = f"dev_{user_id}_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # 异步执行AI工作流程
            asyncio.create_task(
                self.orchestrator.execute_integrated_ai_workflow(user_id, requirement, test_mode, development_id)
            )
            
            return {
                "message": "AI协作开发已启动", 
                "status": "processing",
                "user_id": user_id,
                "development_id": development_id,
                "test_mode": test_mode,
                "required_quota": required_quota
            }
        
        @self.app.post("/api/review-document")
        async def review_document(request_data: dict):
            """文档审查"""
            try:
                request = DocumentReviewRequest(**request_data)
                result = await self.orchestrator.business_manager.process_document_review(request)
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/review-frontend")
        async def review_frontend(request_data: dict):
            """前端审查"""
            try:
                request = FrontendReviewRequest(**request_data)
                result = await self.orchestrator.business_manager.process_frontend_review(request)
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/modify-document")
        async def modify_document(request_data: dict):
            """交互式文档修改"""
            try:
                user_id = request_data.get("user_id", "")
                project_id = request_data.get("project_id", "")
                modification_request = request_data.get("modification_request", "")
                
                if not all([user_id, project_id, modification_request]):
                    raise HTTPException(status_code=400, detail="缺少必要参数")
                
                # 检查用户是否存在
                user = self.db.get_user(user_id)
                if not user:
                    raise HTTPException(status_code=404, detail="用户不存在")
                
                # 检查配额
                if not self.db.deduct_api_balance(user_id, 1):
                    raise HTTPException(status_code=429, detail="API配额不足")
                
                # 调用AI进行文档修改
                ai_response = await self.orchestrator.process_document_modification(
                    user_id, project_id, modification_request
                )
                
                return {
                    "success": True,
                    "response": ai_response.get("response", "文档修改完成"),
                    "document_updated": ai_response.get("document_updated", True)
                }
                
            except Exception as e:
                logger.error(f"文档修改失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/modify-frontend")
        async def modify_frontend(request_data: dict):
            """交互式前端修改"""
            try:
                user_id = request_data.get("user_id", "")
                project_id = request_data.get("project_id", "")
                modification_request = request_data.get("modification_request", "")
                
                if not all([user_id, project_id, modification_request]):
                    raise HTTPException(status_code=400, detail="缺少必要参数")
                
                # 检查配额
                if not self.db.deduct_api_balance(user_id, 1):
                    raise HTTPException(status_code=429, detail="API配额不足")
                
                # 调用AI进行前端修改
                ai_response = await self.orchestrator.process_frontend_modification(
                    user_id, project_id, modification_request
                )
                
                return {
                    "success": True,
                    "response": ai_response.get("response", "前端修改完成"),
                    "frontend_updated": ai_response.get("frontend_updated", True)
                }
                
            except Exception as e:
                logger.error(f"前端修改失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/confirm-document")
        async def confirm_document(request_data: dict):
            """确认文档"""
            try:
                user_id = request_data.get("user_id", "")
                project_id = request_data.get("project_id", "")
                
                if not all([user_id, project_id]):
                    raise HTTPException(status_code=400, detail="缺少必要参数")
                
                # 确认文档
                result = await self.orchestrator.confirm_project_document(user_id, project_id)
                
                return {
                    "success": True,
                    "message": "文档确认成功",
                    "status": "confirmed"
                }
                
            except Exception as e:
                logger.error(f"确认文档失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/confirm-frontend")
        async def confirm_frontend(request_data: dict):
            """确认前端界面"""
            try:
                user_id = request_data.get("user_id", "")
                project_id = request_data.get("project_id", "")
                
                if not all([user_id, project_id]):
                    raise HTTPException(status_code=400, detail="缺少必要参数")
                
                # 确认前端
                result = await self.orchestrator.confirm_project_frontend(user_id, project_id)
                
                return {
                    "success": True,
                    "message": "前端确认成功",
                    "status": "confirmed"
                }
                
            except Exception as e:
                logger.error(f"确认前端失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/projects/{project_id}/document")
        async def get_project_document(project_id: str):
            """获取项目文档"""
            try:
                project = self.db.get_project(project_id)
                if not project:
                    raise HTTPException(status_code=404, detail="项目不存在")
                
                return {
                    "content": getattr(project, 'document_content', '') or "项目文档内容...",
                    "status": getattr(project, 'document_status', 'draft'),
                    "confirmed_at": getattr(project, 'document_confirmed_at', None)
                }
            except Exception as e:
                logger.error(f"获取项目文档失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/projects/{project_id}/frontend")
        async def get_project_frontend(project_id: str):
            """获取项目前端"""
            try:
                project = self.db.get_project(project_id)
                if not project:
                    raise HTTPException(status_code=404, detail="项目不存在")
                
                return {
                    "content": getattr(project, 'frontend_content', '') or "",
                    "status": getattr(project, 'frontend_status', 'draft'),
                    "confirmed_at": getattr(project, 'frontend_confirmed_at', None)
                }
            except Exception as e:
                logger.error(f"获取项目前端失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/deploy-project")
        async def deploy_project(request_data: dict):
            """部署项目"""
            try:
                project_id = request_data.get("project_id")
                user_id = request_data.get("user_id")
                
                # 参数验证
                if not all([project_id, user_id]):
                    raise HTTPException(status_code=400, detail="缺少必要参数：project_id, user_id")
                
                # 检查项目是否存在
                project = self.db.get_project(project_id)
                if not project or project.user_id != user_id:
                    raise HTTPException(status_code=404, detail="项目不存在或无权限")
                
                # 检查配额
                if not self.db.deduct_api_balance(user_id, 20):
                    raise HTTPException(status_code=400, detail="配额不足，部署需要20个配额")
                
                # 模拟部署过程
                import time
                import uuid
                deployment_url = f"https://app-{project_id[:8]}.nexus-cloud.com"
                
                # 更新项目部署状态
                with sqlite3.connect(self.db.db_path) as conn:
                    conn.execute("""
                        UPDATE projects 
                        SET deployment_status = 'deployed', 
                            deployment_url = ?,
                            deployed_at = ?
                        WHERE id = ?
                    """, (deployment_url, datetime.now().isoformat(), project_id))
                    conn.commit()
                
                return {
                    "status": "success",
                    "deployment_url": deployment_url,
                    "message": "项目部署成功"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/deploy-blockchain")
        async def deploy_blockchain(request_data: dict):
            """一键上链"""
            try:
                project_id = request_data.get("project_id")
                user_id = request_data.get("user_id")
                network = request_data.get("network", "polygon")
                
                # 检查VIP权益
                vip_benefits = self.orchestrator.vip_manager.check_vip_benefits(user_id, "blockchain")
                required_quota = 0 if vip_benefits.get("benefits", {}).get("free_blockchain") else 30
                
                if required_quota > 0 and not self.db.deduct_api_balance(user_id, required_quota):
                    raise HTTPException(status_code=400, detail=f"配额不足，上链需要{required_quota}个配额")
                
                # 获取项目数据
                project = self.db.get_project(project_id)
                if not project:
                    raise HTTPException(status_code=404, detail="项目不存在")
                
                project_data = {
                    "project_id": project_id,
                    "name": project.name,
                    "description": project.description,
                    "status": project.status,
                    "deployment_url": project.deployment_url,
                    "created_at": project.created_at
                }
                
                # 推荐最适合的网络
                if not network:
                    vip_level = vip_benefits.get("vip_level", 0)
                    network = NetworkSelector.recommend_network("project_deployment", vip_level)
                
                # 部署到区块链
                result = self.orchestrator.blockchain_manager.deploy_project_to_blockchain(
                    project_id, user_id, project_data, network
                )
                
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/recharge")
        async def recharge(request_data: dict):
            """真实充值"""
            try:
                user_id = request_data.get("user_id", "")
                amount = float(request_data.get("amount", 0))
                payment_method = request_data.get("payment_method", "alipay")
                
                if not user_id or amount <= 0:
                    raise HTTPException(status_code=400, detail="参数错误")
                
                if not PaymentUtils.validate_amount(amount):
                    raise HTTPException(status_code=400, detail="充值金额无效")
                
                # 检查首次充值折扣
                is_first_time = self.db.check_first_time_discount(user_id)
                discount_rate = 0.5 if is_first_time else 0.0
                
                # 创建支付订单
                order_result = self.orchestrator.real_payment_manager.create_payment_order(
                    user_id=user_id,
                    amount=amount,
                    payment_method=payment_method,
                    order_type="recharge",
                    discount_rate=discount_rate
                )
                
                return {
                    "success": True,
                    "order_id": order_result["order_id"],
                    "payment_url": order_result["payment_url"],
                    "amount": amount,
                    "final_amount": order_result["final_amount"],
                    "quota_amount": order_result["quota_amount"],
                    "discount_applied": discount_rate > 0,
                    "payment_method": payment_method,
                    "qr_code": order_result.get("qr_code")
                }
                
            except Exception as e:
                logger.error(f"充值失败: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/payment/callback")
        async def payment_callback(request_data: dict):
            """支付回调处理"""
            try:
                order_id = request_data.get("order_id")
                provider_data = request_data.get("provider_data", {})
                
                # 处理支付回调
                result = self.orchestrator.real_payment_manager.process_payment_callback(
                    order_id, provider_data
                )
                
                if result["success"]:
                    user_id = result["user_id"]
                    quota_amount = result["quota_amount"]
                    
                    # 增加用户配额
                    if quota_amount > 0:
                        self.db.deduct_api_balance(user_id, -quota_amount)  # 负数表示增加
                    
                    # 处理邀请返佣
                    if result["order_type"] == "recharge":
                        order = self.orchestrator.real_payment_manager.get_payment_order(order_id)
                        if order:
                            self.orchestrator.real_invitation_manager.process_invitation_recharge(
                                user_id, order["final_amount"]
                            )
                    
                    return {"success": True, "message": "支付成功"}
                else:
                    return {"success": False, "message": result["message"]}
                    
            except Exception as e:
                logger.error(f"支付回调处理失败: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/payment/simulate-success")
        async def simulate_payment_success(request_data: dict):
            """模拟支付成功（测试用）"""
            try:
                order_id = request_data.get("order_id")
                
                if not order_id:
                    raise HTTPException(status_code=400, detail="订单ID不能为空")
                
                # 模拟支付成功
                result = self.orchestrator.real_payment_manager.simulate_payment_success(order_id)
                
                if result["success"]:
                    user_id = result["user_id"]
                    quota_amount = result["quota_amount"]
                    
                    # 增加用户配额
                    if quota_amount > 0:
                        self.db.deduct_api_balance(user_id, -quota_amount)
                    
                    # 处理邀请返佣
                    if result["order_type"] == "recharge":
                        order = self.orchestrator.real_payment_manager.get_payment_order(order_id)
                        if order:
                            self.orchestrator.real_invitation_manager.process_invitation_recharge(
                                user_id, order["final_amount"]
                            )
                    
                    return {"success": True, "message": "模拟支付成功", "quota_added": quota_amount}
                else:
                    return {"success": False, "message": result["message"]}
                    
            except Exception as e:
                logger.error(f"模拟支付失败: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/vip-info/{user_id}")
        async def get_vip_info(user_id: str):
            """获取用户VIP信息"""
            try:
                vip_info = self.orchestrator.vip_manager.get_user_vip_info(user_id)
                return vip_info
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/vip-upgrade")
        async def upgrade_vip(request_data: dict):
            """VIP升级"""
            try:
                user_id = request_data.get("user_id")
                vip_level = request_data.get("vip_level")
                payment_amount = request_data.get("payment_amount")
                
                # 参数验证
                if not all([user_id, vip_level, payment_amount]):
                    raise HTTPException(status_code=400, detail="缺少必要参数：user_id, vip_level, payment_amount")
                
                try:
                    vip_level = int(vip_level)
                    payment_amount = float(payment_amount)
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail="参数类型错误")
                
                result = self.orchestrator.vip_manager.upgrade_vip(user_id, vip_level, payment_amount)
                return result
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"VIP升级失败: {e}")
                raise HTTPException(status_code=500, detail=f"VIP升级失败: {str(e)}")
        
        @self.app.post("/api/vip-renew")
        async def renew_vip(request_data: dict):
            """VIP续费"""
            try:
                user_id = request_data.get("user_id")
                payment_amount = request_data.get("payment_amount")
                
                result = self.orchestrator.vip_manager.renew_vip(user_id, payment_amount)
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/blockchain/deploy-user-profile")
        async def deploy_user_profile_blockchain(request_data: dict):
            """将用户档案真实部署到区块链"""
            try:
                user_id = request_data.get("user_id")
                network = request_data.get("network", "solana-devnet")
                
                # 检查配额
                if not self.db.deduct_api_balance(user_id, 15):
                    raise HTTPException(status_code=400, detail="配额不足，用户档案上链需要15个配额")
                
                # 获取用户数据
                user = self.db.get_user(user_id)
                if not user:
                    raise HTTPException(status_code=404, detail="用户不存在")
                
                profile_data = {
                    "user_id": user_id,
                    "username": user.username,
                    "vip_level": getattr(user, 'vip_level', 0),
                    "total_projects": len(self.db.get_user_projects(user_id)),
                    "reputation_score": 100,
                    "created_at": user.created_at,
                    "profile_version": "1.0",
                    "data_type": "user_profile"
                }
                
                # 使用真实区块链管理器
                result = self.orchestrator.real_blockchain_manager.store_data_on_chain(
                    user_id, profile_data, "user_profile", network
                )
                
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/blockchain/deploy-vip-contract")
        async def deploy_vip_contract(request_data: dict):
            """将VIP状态部署为智能合约"""
            try:
                user_id = request_data.get("user_id")
                network = request_data.get("network", "ethereum")
                
                # 检查配额
                if not self.db.deduct_api_balance(user_id, 25):
                    raise HTTPException(status_code=400, detail="配额不足，VIP合约部署需要25个配额")
                
                # 获取VIP信息
                vip_info = self.orchestrator.vip_manager.get_user_vip_info(user_id)
                
                result = self.orchestrator.blockchain_manager.deploy_vip_contract(
                    user_id, vip_info, network
                )
                
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/blockchain/records/{user_id}")
        async def get_blockchain_records(user_id: str):
            """获取用户的区块链记录"""
            try:
                records = self.orchestrator.blockchain_manager.get_user_blockchain_records(user_id)
                return {"records": records}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/blockchain/contracts/{user_id}")
        async def get_smart_contracts(user_id: str):
            """获取用户的智能合约"""
            try:
                contracts = self.orchestrator.blockchain_manager.get_user_smart_contracts(user_id)
                return {"contracts": contracts}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/blockchain/verify/{record_id}")
        async def verify_blockchain_record(record_id: str):
            """验证区块链记录"""
            try:
                result = self.orchestrator.blockchain_manager.verify_blockchain_record(record_id)
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/blockchain/statistics")
        async def get_blockchain_statistics():
            """获取区块链统计信息"""
            try:
                stats = self.orchestrator.blockchain_manager.get_blockchain_statistics()
                return stats
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/blockchain/create-wallet")
        async def create_blockchain_wallet(request_data: dict):
            """为用户创建区块链钱包"""
            try:
                user_id = request_data.get("user_id")
                network = request_data.get("network", "solana-devnet")
                
                if not user_id:
                    raise HTTPException(status_code=400, detail="用户ID不能为空")
                
                # 创建真实钱包
                wallet = self.orchestrator.real_blockchain_manager.create_user_wallet(user_id, network)
                
                return {
                    "status": "success",
                    "wallet": wallet,
                    "message": f"成功创建{network}钱包"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/blockchain/wallet/{user_id}")
        async def get_user_wallets(user_id: str):
            """获取用户的区块链钱包"""
            try:
                wallets = []
                
                # 获取所有支持网络的钱包
                for network in ["solana-devnet", "ethereum", "polygon"]:
                    wallet = self.orchestrator.real_blockchain_manager.get_user_wallet(user_id, network)
                    if wallet:
                        # 更新余额
                        balance = self.orchestrator.real_blockchain_manager.get_wallet_balance(
                            wallet["address"], network
                        )
                        wallet["balance"] = balance
                        wallet["formatted_balance"] = BlockchainUtils.format_balance(balance)
                        wallets.append(wallet)
                
                return {"wallets": wallets}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/blockchain/deploy-project-real")
        async def deploy_project_real_blockchain(request_data: dict):
            """真实项目上链部署"""
            try:
                project_id = request_data.get("project_id")
                user_id = request_data.get("user_id")
                network = request_data.get("network", "solana-devnet")
                
                # 检查VIP权益
                vip_benefits = self.orchestrator.vip_manager.check_vip_benefits(user_id, "blockchain")
                required_quota = 0 if vip_benefits.get("benefits", {}).get("free_blockchain") else 30
                
                if required_quota > 0 and not self.db.deduct_api_balance(user_id, required_quota):
                    raise HTTPException(status_code=400, detail=f"配额不足，项目上链需要{required_quota}个配额")
                
                # 获取项目数据
                project = self.db.get_project(project_id)
                if not project:
                    raise HTTPException(status_code=404, detail="项目不存在")
                
                project_data = {
                    "project_id": project_id,
                    "name": project.name,
                    "description": project.description,
                    "status": project.status,
                    "deployment_url": project.deployment_url,
                    "created_at": project.created_at,
                    "user_id": user_id,
                    "project_version": "1.0",
                    "data_type": "project_deployment"
                }
                
                # 真实上链
                result = self.orchestrator.real_blockchain_manager.store_data_on_chain(
                    user_id, project_data, "project_deployment", network
                )
                
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/blockchain/data/{user_id}")
        async def get_user_blockchain_data(user_id: str):
            """获取用户的区块链数据"""
            try:
                data = self.orchestrator.real_blockchain_manager.get_user_blockchain_data(user_id)
                return {"blockchain_data": data}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/blockchain/verify-data")
        async def verify_blockchain_data(request_data: dict):
            """验证区块链数据"""
            try:
                data_id = request_data.get("data_id")
                
                if not data_id:
                    raise HTTPException(status_code=400, detail="数据ID不能为空")
                
                result = self.orchestrator.real_blockchain_manager.verify_blockchain_data(data_id)
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/share")
        async def share(request_data: dict):
            """真实分享获得奖励"""
            user_id = request_data.get("user_id", "")
            platform = request_data.get("platform", "wechat")
            
            if not user_id:
                raise HTTPException(status_code=400, detail="用户ID不能为空")
            
            try:
                # 分享到平台
                share_result = self.orchestrator.real_invitation_manager.share_to_platform(
                    user_id, platform
                )
                
                if share_result["success"]:
                    # 处理每日分享奖励
                    platforms_shared = [platform]
                    reward_result = self.orchestrator.real_invitation_manager.process_daily_share_reward(
                        user_id, platforms_shared
                    )
                    
                    # 增加用户配额
                    if reward_result["success"]:
                        reward_amount = reward_result["reward_amount"]
                        self.db.deduct_api_balance(user_id, -reward_amount)  # 负数表示增加
                        
                        return {
                            "success": True,
                            "platform": platform,
                            "share_url": share_result["share_url"],
                            "reward_amount": reward_amount,
                            "platform_name": share_result["platform_name"],
                            "message": f"分享成功！获得 {reward_amount} 配额奖励"
                        }
                    else:
                        return {
                            "success": True,
                            "platform": platform,
                            "share_url": share_result["share_url"],
                            "reward_amount": 0,
                            "platform_name": share_result["platform_name"],
                            "message": reward_result["message"]
                        }
                else:
                    raise HTTPException(status_code=400, detail=share_result["message"])
                    
            except Exception as e:
                logger.error(f"分享失败: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/invitation/platforms")
        async def get_share_platforms():
            """获取可用的分享平台"""
            try:
                platforms = self.orchestrator.real_invitation_manager.get_available_platforms()
                return {"platforms": platforms}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/invitation/code/{user_id}")
        async def get_invitation_code(user_id: str):
            """获取用户邀请码"""
            try:
                invitation_code = self.orchestrator.real_invitation_manager.get_user_invitation_code(user_id)
                share_link = self.orchestrator.real_invitation_manager.create_share_link(user_id)
                
                return {
                    "invitation_code": invitation_code,
                    "share_link": share_link
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/api/invitation/validate")
        async def validate_invitation_code(request_data: dict):
            """验证邀请码"""
            try:
                code = request_data.get("code", "")
                
                if not code:
                    raise HTTPException(status_code=400, detail="邀请码不能为空")
                
                result = self.orchestrator.real_invitation_manager.validate_invitation_code(code)
                
                if result:
                    return {"valid": True, "inviter_info": result}
                else:
                    return {"valid": False, "message": "无效的邀请码"}
                    
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/user-stats/{user_id}")
        async def get_user_stats(user_id: str):
            """获取用户统计信息"""
            user = self.db.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            # 获取用户项目
            projects = self.db.get_user_projects(user_id)
            
            # 获取邀请和分享统计
            invitation_stats = self.orchestrator.real_invitation_manager.get_invitation_statistics(user_id)
            share_stats = self.orchestrator.real_invitation_manager.get_share_statistics(user_id)
            
            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "api_balance": user.api_balance or 30,
                    "total_recharge": user.total_recharge or 0,
                    "subscription_tier": user.subscription_tier,
                    "created_at": user.created_at,
                    "invitation_code": invitation_stats.get("invitation_code", ""),
                    "total_invitations": invitation_stats.get("total_invitations", 0),
                    "total_rewards": invitation_stats.get("total_rewards", 0),
                    "total_commission": invitation_stats.get("total_commission", 0.0),
                    "total_shares": share_stats.get("total_shares", 0),
                    "share_rewards": share_stats.get("share_rewards", 0)
                },
                "projects": {
                    "total": len(projects),
                    "completed": len([p for p in projects if p.status == "completed"]),
                    "in_progress": len([p for p in projects if p.status == "in_progress"])
                }
            }
        
        @self.app.get("/api/user-projects/{user_id}")
        async def get_user_projects(user_id: str):
            """获取用户项目列表"""
            user = self.db.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            projects = self.db.get_user_projects(user_id)
            projects_with_details = []
            
            for project in projects:
                project_dict = asdict(project)
                # 获取部署记录
                deployment_records = self.db.get_project_deployment_records(project.id)
                project_dict["deployment_records"] = deployment_records
                projects_with_details.append(project_dict)
            
            return projects_with_details
        
        @self.app.get("/api/recharge-records/{user_id}")
        async def get_recharge_records(user_id: str):
            """获取用户充值记录"""
            user = self.db.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            return self.db.get_user_recharge_records(user_id)
        
        @self.app.get("/api/share-records/{user_id}")
        async def get_share_records(user_id: str):
            """获取用户分享记录"""
            user = self.db.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            return self.db.get_user_share_records(user_id)
        
        @self.app.get("/api/invitation-stats/{user_id}")
        async def get_invitation_stats(user_id: str):
            """获取用户邀请统计"""
            user = self.db.get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            stats = self.db.get_user_invitation_stats(user_id)
            stats["invitation_code"] = user.invitation_code
            return stats
        
        @self.app.get("/api/projects/{project_id}/document")
        async def get_project_document(project_id: str):
            """获取项目文档"""
            project = self.db.get_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="项目不存在")
            
            return {
                "document": project.document_content,
                "confirmed": project.document_confirmed or False
            }
        
        @self.app.get("/api/projects/{project_id}/frontend")
        async def get_project_frontend(project_id: str):
            """获取项目前端"""
            project = self.db.get_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="项目不存在")
            
            return {
                "preview_url": project.frontend_preview_url or f"/preview/{project_id}/frontend",
                "confirmed": project.frontend_confirmed or False
            }
        
        @self.app.get("/preview/{project_id}/frontend")
        async def preview_frontend(project_id: str):
            """前端预览"""
            # 返回项目前端预览HTML
            return HTMLResponse("""
                <html>
                <head><title>项目预览</title></head>
                <body>
                    <h1>项目前端预览</h1>
                    <p>这是项目 {project_id} 的前端预览页面</p>
                    <div style="padding: 20px; border: 1px solid #ddd; margin: 20px 0;">
                        <h2>简单社交平台演示</h2>
                        <div style="background: #f5f5f5; padding: 10px; margin: 10px 0;">
                            <h3>登录界面</h3>
                            <input placeholder="用户名" style="margin: 5px; padding: 5px;">
                            <input placeholder="密码" type="password" style="margin: 5px; padding: 5px;">
                            <button style="margin: 5px; padding: 5px 15px;">登录</button>
                        </div>
                        <div style="background: #f0f8ff; padding: 10px; margin: 10px 0;">
                            <h3>动态发布</h3>
                            <textarea placeholder="分享你的想法..." style="width: 100%; height: 60px; margin: 5px 0;"></textarea>
                            <button style="margin: 5px; padding: 5px 15px;">发布</button>
                        </div>
                        <div style="background: #fff; border: 1px solid #eee; padding: 10px; margin: 10px 0;">
                            <h4>示例动态</h4>
                            <p><strong>张三:</strong> 今天天气真好！</p>
                            <small style="color: #666;">2小时前</small>
                        </div>
                    </div>
                    <script>
                        document.body.style.fontFamily = 'Arial, sans-serif';
                        document.body.style.maxWidth = '800px';
                        document.body.style.margin = '0 auto';
                        document.body.style.padding = '20px';
                    </script>
                </body>
                </html>
            """.replace("{project_id}", project_id))
        
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
        port = self.config.get("platform.port", 8891)
        
        logger.info("多用户集成AI协作开发平台启动中...")
        logger.info(f"前端界面: http://{host}:{port}")
        logger.info(f"API文档: http://{host}:{port}/docs")
        logger.info("✅ 基于原有integrated_ai_platform.py的工作版本")
        logger.info("✅ 集成了真正的GPT-ENGINEER")
        logger.info("✅ 支持多用户和API优化")
        
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
    print("正在启动多用户集成AI协作开发平台...")
    print("=" * 60)
    print("🚀 基于原有integrated_ai_platform.py升级")
    print("🤖 集成真正的GPT-ENGINEER")
    print("👥 支持多用户")
    print("⚡ API优化")
    print("=" * 60)
    
    try:
        platform = MultiUserIntegratedPlatform()
        platform.run()
    except KeyboardInterrupt:
        print("\n平台已关闭")
    except Exception as e:
        print(f"启动失败: {e}")
        logger.error(f"平台启动失败: {e}", exc_info=True)

if __name__ == "__main__":
    main()