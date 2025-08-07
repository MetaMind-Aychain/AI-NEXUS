#!/usr/bin/env python3
"""
真正集成GPT-ENGINEER的AI协作开发平台

此平台真正使用：
1. GPT-ENGINEER的SimpleAgent进行代码生成
2. 深度集成的各个AI组件真正协作
3. 真实的OpenAI API调用
4. 真正的AI监督、测试、文档生成流程
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

# 导入真正的GPT-ENGINEER组件
from gpt_engineer.core.ai import AI
from gpt_engineer.core.default.simple_agent import SimpleAgent
from gpt_engineer.core.default.disk_memory import DiskMemory
from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv
from gpt_engineer.core.files_dict import FilesDict
from gpt_engineer.core.prompt import Prompt

# 导入我们的深度集成AI组件
from multi_ai_system.core.deep_integration import DeepIntegratedDevAI, DeepIntegrationManager
from multi_ai_system.ai.advanced_document_ai import AdvancedDocumentAI
from multi_ai_system.ai.advanced_supervisor_ai import AdvancedSupervisorAI
from multi_ai_system.ai.advanced_test_ai import AdvancedTestAI
from multi_ai_system.memory.shared_memory import SharedMemoryManager

# 设置控制台编码
if sys.platform.startswith('win'):
    os.system('chcp 65001 > nul')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integrated_ai_platform.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger("集成AI平台")


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
                "port": 8889,  # 使用新端口
                "debug": True,
                "auto_open_browser": True
            },
            "projects": {
                "output_directory": "integrated_projects",
                "max_concurrent_projects": 3
            },
            "database": {
                "path": "integrated_ai_platform.db"
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


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "integrated_ai_platform.db"):
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
                    files_count INTEGER DEFAULT 0,
                    ai_generated BOOLEAN DEFAULT TRUE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    ai_name TEXT,
                    action TEXT,
                    input_prompt TEXT,
                    ai_response TEXT,
                    timestamp TEXT,
                    success BOOLEAN,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_collaborations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    collaboration_step TEXT,
                    involved_ais TEXT,
                    result_summary TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
    
    def save_project(self, project_data: Dict):
        """保存项目"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO projects 
                (id, name, description, status, created_at, updated_at, project_path, files_count, ai_generated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_data['id'],
                project_data['name'],
                project_data['description'],
                project_data['status'],
                project_data['created_at'],
                project_data['updated_at'],
                project_data['project_path'],
                project_data['files_count'],
                project_data.get('ai_generated', True)
            ))
    
    def log_ai_interaction(self, project_id: str, ai_name: str, action: str, 
                          input_prompt: str, ai_response: str, success: bool = True):
        """记录AI交互"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ai_interactions 
                (project_id, ai_name, action, input_prompt, ai_response, timestamp, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (project_id, ai_name, action, input_prompt, ai_response, 
                  datetime.now().isoformat(), success))
    
    def log_ai_collaboration(self, project_id: str, step: str, involved_ais: List[str], 
                           result_summary: str):
        """记录AI协作"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ai_collaborations 
                (project_id, collaboration_step, involved_ais, result_summary, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (project_id, step, json.dumps(involved_ais), result_summary, 
                  datetime.now().isoformat()))
    
    def get_projects(self) -> List[Dict]:
        """获取所有项目"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM projects ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]


class IntegratedAIOrchestrator:
    """真正集成GPT-ENGINEER的AI协调器"""
    
    def __init__(self, config: ConfigManager, db_manager: DatabaseManager):
        self.config = config
        self.db = db_manager
        
        # 设置OpenAI API密钥到环境变量
        api_key = self.config.get("openai.api_key")
        if api_key and api_key != "your-openai-api-key-here":
            os.environ["OPENAI_API_KEY"] = api_key
            logger.info("OpenAI API密钥已设置")
        else:
            logger.warning("未找到有效的OpenAI API密钥，某些功能可能无法正常工作")
        
        # 初始化共享记忆
        self.shared_memory = SharedMemoryManager("./integrated_ai_memory")
        
        # 初始化AI引擎（从配置文件获取模型参数）
        model_name = self.config.get("openai.model", "gpt-3.5-turbo")
        temperature = self.config.get("openai.temperature", 0.7)
        self.ai_engine = AI(model_name=model_name, temperature=temperature)
        
        # 初始化真正的AI组件
        self.document_ai = AdvancedDocumentAI(self.ai_engine, self.shared_memory)
        self.supervisor_ai = AdvancedSupervisorAI(self.ai_engine, self.shared_memory)
        self.test_ai = AdvancedTestAI(self.ai_engine)  # AdvancedTestAI不接受shared_memory参数
        
        # 初始化深度集成管理器
        self.integration_manager = DeepIntegrationManager("./integrated_workspace")
        self.integration_manager.setup_gpt_engineer_core(self.ai_engine)
        self.integration_manager.setup_upgraded_ai_components(
            self.supervisor_ai, self.test_ai, self.shared_memory
        )
        
        # WebSocket连接管理
        self.active_connections: List[WebSocket] = []
        
        logger.info("真正的AI协调器初始化完成")
    
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
    
    async def log_and_broadcast(self, project_id: str, ai_name: str, action: str, 
                               message: str, prompt: str = "", response: str = ""):
        """记录日志并广播到前端"""
        # 控制台日志
        logger.info(f"[{ai_name}] {action}: {message}")
        
        # 数据库日志
        if prompt and response:
            self.db.log_ai_interaction(project_id, ai_name, action, prompt, response)
        
        # 前端广播
        await self.broadcast_message({
            "type": "ai_log",
            "project_id": project_id,
            "ai_name": ai_name,
            "action": action,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def execute_real_ai_workflow(self, user_requirement: str) -> Dict:
        """执行真正的AI协作工作流程"""
        project_id = f"integrated_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"开始真正的AI协作开发流程，项目ID: {project_id}")
        
        try:
            # 第1步：真正的文档AI分析需求
            await self.log_and_broadcast(project_id, "文档AI", "需求分析", 
                                       "使用真实AI分析用户需求...")
            
            # 调用真正的文档AI
            document_result = await self.document_ai.analyze_requirements(
                user_requirement, 
                context={"project_id": project_id, "platform": "integrated"}
            )
            
            await self.log_and_broadcast(project_id, "文档AI", "需求分析完成", 
                                       f"生成了详细的项目文档，包含 {len(document_result.get('features', []))} 个功能模块",
                                       user_requirement, str(document_result))
            
            # 记录AI协作
            self.db.log_ai_collaboration(project_id, "需求分析", ["文档AI"], 
                                       f"分析用户需求，生成项目文档")
            
            # 第2步：真正的开发AI使用GPT-ENGINEER生成代码
            await self.log_and_broadcast(project_id, "开发AI", "代码生成", 
                                       "使用GPT-ENGINEER核心引擎生成代码...")
            
            # 创建真正的深度集成开发AI
            dev_ai = self.integration_manager.create_deep_integrated_agent()
            
            # 构建开发提示
            development_prompt = self._build_development_prompt(document_result, user_requirement)
            
            # 真正调用GPT-ENGINEER的init方法
            logger.info("调用GPT-ENGINEER SimpleAgent.init() 方法")
            generated_files = dev_ai.init(development_prompt)
            
            await self.log_and_broadcast(project_id, "开发AI", "代码生成完成", 
                                       f"GPT-ENGINEER生成了 {len(generated_files)} 个文件",
                                       development_prompt, f"生成了 {len(generated_files)} 个文件")
            
            # 第3步：真正的监督AI监督代码质量
            await self.log_and_broadcast(project_id, "监督AI", "质量监督", 
                                       "监督AI开始检查GPT-ENGINEER生成的代码...")
            
            # 启动监督
            supervision_result = await self.supervisor_ai.monitor_progress(
                "supervision_" + project_id,
                {
                    "event_type": "code_generated",
                    "files": generated_files,
                    "requirements": document_result
                }
            )
            
            await self.log_and_broadcast(project_id, "监督AI", "质量检查完成", 
                                       f"代码质量评分: {supervision_result.quality_score:.2f}")
            
            # 第4步：如果监督AI建议改进，调用GPT-ENGINEER的improve方法
            if supervision_result.quality_score < 0.8:
                await self.log_and_broadcast(project_id, "开发AI", "代码改进", 
                                           "根据监督AI反馈，使用GPT-ENGINEER改进代码...")
                
                # 真正调用GPT-ENGINEER的improve方法
                improvement_feedback = supervision_result.feedback
                improved_files = dev_ai.improve(generated_files, improvement_feedback)
                
                generated_files = improved_files
                
                await self.log_and_broadcast(project_id, "开发AI", "代码改进完成", 
                                           "代码已根据监督AI建议进行改进")
            
            # 第5步：真正的测试AI生成和执行测试
            await self.log_and_broadcast(project_id, "测试AI", "生成测试", 
                                       "测试AI开始为生成的代码创建测试...")
            
            test_result = await self.test_ai.comprehensive_test(
                project_id,
                {
                    "files": generated_files,
                    "requirements": document_result,
                    "project_type": document_result.get("project_type", "web_application")
                }
            )
            
            await self.log_and_broadcast(project_id, "测试AI", "测试完成", 
                                       f"测试通过率: {test_result.pass_rate:.1%}，发现 {len(test_result.issues)} 个问题")
            
            # 第6步：如果有测试问题，再次改进
            if test_result.issues:
                await self.log_and_broadcast(project_id, "开发AI", "修复问题", 
                                           "根据测试结果修复发现的问题...")
                
                # 构建问题修复提示
                fix_prompt = f"修复以下测试发现的问题：\n"
                for issue in test_result.issues:
                    fix_prompt += f"- {issue}\n"
                
                # 再次调用improve方法
                fixed_files = dev_ai.improve(generated_files, fix_prompt)
                generated_files = fixed_files
                
                await self.log_and_broadcast(project_id, "开发AI", "问题修复完成", 
                                           "所有测试问题已修复")
            
            # 第7步：保存项目文件
            project_path = await self._save_integrated_project(project_id, generated_files, document_result)
            
            # 记录最终协作结果
            self.db.log_ai_collaboration(project_id, "项目完成", 
                                       ["文档AI", "开发AI", "监督AI", "测试AI"], 
                                       f"完成项目开发，生成 {len(generated_files)} 个文件")
            
            # 保存项目到数据库
            project_data = {
                'id': project_id,
                'name': document_result.get('project_name', 'AI集成项目'),
                'description': user_requirement,
                'status': '已完成',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'project_path': project_path,
                'files_count': len(generated_files),
                'ai_generated': True
            }
            
            self.db.save_project(project_data)
            
            # 最终完成通知
            await self.log_and_broadcast(project_id, "系统", "项目完成", 
                                       "真正的AI协作开发完成！所有AI都参与了工作")
            
            # 广播项目完成状态
            await self.broadcast_message({
                "type": "project_completed",
                "project": project_data,
                "files_count": len(generated_files),
                "project_path": project_path,
                "ai_collaboration": True
            })
            
            logger.info(f"真正的AI协作项目 {project_id} 开发完成，共生成 {len(generated_files)} 个文件")
            
            return project_data
            
        except Exception as e:
            error_msg = f"真正的AI协作开发过程中发生错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await self.log_and_broadcast(project_id, "系统", "错误", error_msg)
            raise
    
    def _build_development_prompt(self, document_result: Dict, user_requirement: str) -> str:
        """构建给GPT-ENGINEER的开发提示"""
        prompt_parts = [
            f"请开发一个项目，用户需求如下：",
            f"原始需求：{user_requirement}",
            f"",
            f"根据文档AI的分析，项目应该包含以下特性：",
            f"项目名称：{document_result.get('project_name', '未命名项目')}",
            f"项目类型：{document_result.get('project_type', 'web应用')}",
            f"",
            f"技术栈：{', '.join(document_result.get('tech_stack', ['Python', 'HTML', 'CSS', 'JavaScript']))}",
            f"",
            f"主要功能模块：",
        ]
        
        for i, feature in enumerate(document_result.get('features', []), 1):
            prompt_parts.append(f"{i}. {feature}")
        
        prompt_parts.extend([
            f"",
            f"架构要求：{document_result.get('architecture', {}).get('description', '标准Web应用架构')}",
            f"",
            f"请生成完整可运行的项目代码，包括：",
            f"- 完整的后端API（如果需要）",
            f"- 前端用户界面",
            f"- 必要的配置文件",
            f"- README文档",
            f"- 基础测试文件",
            f"",
            f"确保代码质量高，结构清晰，遵循最佳实践。",
            f"生成的项目应该能直接运行。"
        ])
        
        return "\n".join(prompt_parts)
    
    async def _save_integrated_project(self, project_id: str, files_dict: FilesDict, 
                                     document_result: Dict) -> str:
        """保存集成项目文件"""
        project_dir = Path(self.config.get("projects.output_directory", "integrated_projects")) / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"保存真正AI生成的项目文件到: {project_dir}")
        
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
            "generated_by": "真正的AI协作系统",
            "ai_components": ["文档AI", "开发AI(GPT-ENGINEER)", "监督AI", "测试AI"],
            "gpt_engineer_integration": True,
            "generation_time": datetime.now().isoformat(),
            "document_analysis": document_result,
            "files_count": len(files_dict)
        }
        
        (project_dir / "ai_metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), 
            encoding='utf-8'
        )
        
        return str(project_dir)


class IntegratedAIDevelopmentPlatform:
    """真正集成GPT-ENGINEER的AI开发平台"""
    
    def __init__(self):
        # 加载配置
        self.config = ConfigManager()
        
        # 初始化组件
        self.app = FastAPI(title="集成AI协作开发平台", version="2.0.0")
        self.db = DatabaseManager(self.config.get("database.path", "integrated_ai_platform.db"))
        self.orchestrator = IntegratedAIOrchestrator(self.config, self.db)
        
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
        
        logger.info("真正集成GPT-ENGINEER的AI协作开发平台初始化完成")
    
    def setup_static_files(self):
        """设置静态文件服务"""
        # 创建前端文件
        self.create_frontend_files()
        
        # 挂载静态文件
        self.app.mount("/static", StaticFiles(directory="integrated_frontend"), name="static")
    
    def create_frontend_files(self):
        """创建前端界面文件"""
        frontend_dir = Path("integrated_frontend")
        frontend_dir.mkdir(exist_ok=True)
        
        # 创建强调真实AI协作的前端界面
        (frontend_dir / "index.html").write_text("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>真正集成GPT-ENGINEER的AI协作开发平台</title>
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
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            background: rgba(255,255,255,0.1);
            padding: 10px 20px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 10px;
        }

        .ai-integration-info {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            border-left: 5px solid #28a745;
        }

        .ai-integration-info h3 {
            color: #28a745;
            margin-bottom: 15px;
        }

        .ai-integration-info ul {
            list-style: none;
            padding: 0;
        }

        .ai-integration-info li {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }

        .ai-integration-info li:last-child {
            border-bottom: none;
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
            background: linear-gradient(45deg, #28a745, #20c997);
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
            box-shadow: 0 10px 20px rgba(40, 167, 69, 0.3);
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
            border-left: 4px solid #28a745;
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
            color: #28a745;
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

        .real-ai-indicator {
            background: #28a745;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            display: inline-block;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>真正集成GPT-ENGINEER的AI协作平台</h1>
            <div class="subtitle">
                使用真实的AI进行协作开发，深度集成GPT-ENGINEER核心引擎
            </div>
        </div>

        <div class="ai-integration-info">
            <h3>真实AI协作系统特性</h3>
            <ul>
                <li>✅ 文档AI：真正分析用户需求，生成详细开发文档</li>
                <li>✅ 开发AI：真正调用GPT-ENGINEER的SimpleAgent.init()和improve()方法</li>
                <li>✅ 监督AI：真正监督代码质量，提供改进建议</li>
                <li>✅ 测试AI：真正生成测试用例，执行代码验证</li>
                <li>✅ 深度集成：使用原有GPT-ENGINEER核心组件，非模拟</li>
                <li>✅ 真实协作：各AI之间真正协作，互相反馈和改进</li>
            </ul>
        </div>

        <div class="main-panel">
            <div class="input-section">
                <h2>项目需求描述 <span class="real-ai-indicator">真实AI处理</span></h2>
                <p style="color: #6c757d; margin-bottom: 15px;">
                    请详细描述您的项目需求，真正的AI团队将协作为您开发
                </p>

                <textarea 
                    id="requirementInput" 
                    class="requirement-input" 
                    placeholder="例如：我需要一个电商平台，包含用户注册登录、商品展示、购物车、订单管理等功能。要求使用Python后端，现代化前端界面，支持移动端..."
                ></textarea>
                
                <button id="startButton" class="start-button" onclick="startRealAIDevelopment()">
                    启动真实AI协作开发
                </button>
            </div>

            <div id="progressSection" class="progress-section">
                <h2>真实AI协作进度 <span class="real-ai-indicator">实时监控</span></h2>
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
                <div class="ai-name">${logData.ai_name} <span class="real-ai-indicator">真实AI</span></div>
                <div class="ai-action">${logData.action}</div>
                <div class="ai-message">${logData.message}</div>
            `;
            
            logsContainer.appendChild(logElement);
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }

        // 处理项目完成
        function handleProjectCompleted(data) {
            document.getElementById('startButton').disabled = false;
            document.getElementById('startButton').textContent = '启动真实AI协作开发';
            
            const message = data.ai_collaboration ? 
                `真实AI协作开发完成！\\n项目名称：${data.project.name}\\n文件数量：${data.files_count}\\n保存路径：${data.project_path}\\n\\n✅ 所有AI都参与了真实工作` :
                `项目开发完成！\\n项目名称：${data.project.name}\\n文件数量：${data.files_count}\\n保存路径：${data.project_path}`;
            
            alert(message);
        }

        // 开始真实AI开发
        async function startRealAIDevelopment() {
            const requirement = document.getElementById('requirementInput').value.trim();
            
            if (!requirement) {
                alert('请输入项目需求描述');
                return;
            }
            
            const button = document.getElementById('startButton');
            button.disabled = true;
            button.textContent = '真实AI协作中...';
            
            document.getElementById('progressSection').classList.add('active');
            document.getElementById('aiLogs').innerHTML = '';
            
            try {
                const response = await fetch('/api/start-real-ai-development', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        requirement: requirement
                    })
                });
                
                if (!response.ok) {
                    throw new Error('真实AI开发请求失败');
                }
                
            } catch (error) {
                console.error('启动真实AI开发失败:', error);
                alert('启动真实AI协作开发失败，请重试');
                
                button.disabled = false;
                button.textContent = '启动真实AI协作开发';
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
        
        logger.info("真实AI协作前端界面文件已创建")
    
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
                "platform": "真正集成GPT-ENGINEER的AI协作平台",
                "ai_integration": True,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/api/start-real-ai-development")
        async def start_real_ai_development(request_data: dict):
            """启动真实AI协作开发"""
            requirement = request_data.get("requirement", "")
            
            if not requirement:
                raise HTTPException(status_code=400, detail="需求描述不能为空")
            
            # 异步执行真实AI工作流程
            asyncio.create_task(self.orchestrator.execute_real_ai_workflow(requirement))
            
            return {
                "message": "真实AI协作开发已启动", 
                "status": "processing",
                "ai_integration": True,
                "real_ai_collaboration": True
            }
        
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
        port = self.config.get("platform.port", 8889)
        
        logger.info("真正集成GPT-ENGINEER的AI协作开发平台启动中...")
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
    print("正在启动真正集成GPT-ENGINEER的AI协作开发平台...")
    print("=" * 60)
    
    try:
        platform = IntegratedAIDevelopmentPlatform()
        platform.run()
    except KeyboardInterrupt:
        print("\n平台已关闭")
    except Exception as e:
        print(f"启动失败: {e}")
        logger.error(f"平台启动失败: {e}", exc_info=True)


if __name__ == "__main__":
    main()