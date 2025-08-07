"""
多AI协作编排器

这是整个多AI协作系统的核心控制器，负责协调各个AI之间的工作流程
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import logging

from gpt_engineer.core.ai import AI
from gpt_engineer.core.prompt import Prompt
from gpt_engineer.core.files_dict import FilesDict
from gpt_engineer.core.preprompts_holder import PrepromptsHolder

from .core.base_interfaces import (
    ProjectResult, DevPlan, TaskStatus,
    DevelopmentEvent, TestResult, PackageResult, DeployResult
)
from .core.enhanced_dev_ai import EnhancedDevAI
from .ai.supervisor_ai import SupervisorAI
from .ai.test_ai import TestAI
from .ai.deploy_ai import DeployAI
from .memory.shared_memory import SharedMemoryManager


# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiAIOrchestrator:
    """
    多AI协作编排器
    
    负责：
    - 工作流程编排
    - AI之间的协调
    - 状态管理
    - 错误处理和恢复
    - 进度跟踪
    """
    
    def __init__(self, 
                 work_dir: str,
                 ai_config: Dict[str, Any] = None,
                 workflow_config: Dict[str, Any] = None):
        """
        初始化编排器
        
        Args:
            work_dir: 工作目录
            ai_config: AI配置
            workflow_config: 工作流配置
        """
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置
        self.ai_config = ai_config or {}
        self.workflow_config = workflow_config or {}
        
        # 初始化AI组件
        self._init_ai_components()
        
        # 初始化共享记忆
        self.shared_memory = SharedMemoryManager(str(self.work_dir / "memory"))
        
        # 当前会话状态
        self.current_session = {
            'session_id': str(uuid.uuid4()),
            'start_time': datetime.now(),
            'status': 'initialized',
            'current_stage': 'preparation',
            'project_id': None,
            'progress': 0.0
        }
        
        # 工作流阶段定义
        self.workflow_stages = [
            'document_generation',
            'development_planning', 
            'iterative_development',
            'testing_validation',
            'frontend_development',
            'integration',
            'packaging',
            'deployment',
            'final_evaluation'
        ]
        
        # 注册事件处理器
        self.event_handlers = {}
        self._register_default_handlers()
    
    def _init_ai_components(self):
        """初始化AI组件"""
        # 主AI实例
        self.main_ai = AI(
            model_name=self.ai_config.get('model_name', 'gpt-4o'),
            temperature=self.ai_config.get('temperature', 0.1)
        )
        
        # 初始化各个AI角色
        self.document_ai = DocumentAI(self.main_ai)
        self.dev_ai = None  # 将在需要时初始化
        self.supervisor_ai = SupervisorAI(self.main_ai)
        self.test_ai = TestAI(self.main_ai, str(self.work_dir / "test_env"))
        self.frontend_ai = FrontendAI(self.main_ai)
        self.deploy_ai = DeployAI(self.main_ai, str(self.work_dir / "deploy"))
    
    async def execute_workflow(self, user_requirement: str, 
                             workflow_options: Dict[str, Any] = None) -> ProjectResult:
        """
        执行完整的开发工作流
        
        Args:
            user_requirement: 用户需求
            workflow_options: 工作流选项
            
        Returns:
            ProjectResult: 项目结果
        """
        workflow_options = workflow_options or {}
        project_id = str(uuid.uuid4())
        
        # 更新会话状态
        self.current_session.update({
            'project_id': project_id,
            'status': 'running',
            'user_requirement': user_requirement
        })
        
        logger.info(f"开始执行项目 {project_id} 的开发工作流")
        
        try:
            # 阶段1：文档生成
            doc_result = await self._stage_document_generation(user_requirement)
            
            # 阶段2：开发计划制定
            dev_plan = await self._stage_development_planning(doc_result)
            
            # 阶段3：迭代开发
            code_result = await self._stage_iterative_development(dev_plan)
            
            # 阶段4：测试验证
            test_results = await self._stage_testing_validation(code_result)
            
            # 阶段5：前端开发（如果需要）
            if workflow_options.get('include_frontend', True):
                frontend_result = await self._stage_frontend_development(code_result, doc_result)
                code_result = await self._stage_integration(code_result, frontend_result)
            
            # 阶段6：项目打包
            package_result = await self._stage_packaging(code_result)
            
            # 阶段7：部署
            deploy_result = None
            if workflow_options.get('auto_deploy', False):
                deploy_result = await self._stage_deployment(package_result, workflow_options)
            
            # 阶段8：最终评估
            final_score = await self._stage_final_evaluation(
                code_result, test_results, deploy_result
            )
            
            # 构建项目结果
            project_result = ProjectResult(
                project_id=project_id,
                files=code_result,
                deployment=deploy_result,
                test_results=test_results,
                final_score=final_score,
                development_time=(datetime.now() - self.current_session['start_time']).total_seconds(),
                success=True,
                metadata={
                    'session_id': self.current_session['session_id'],
                    'stages_completed': self.workflow_stages,
                    'user_requirement': user_requirement,
                    'workflow_options': workflow_options
                }
            )
            
            # 更新会话状态
            self.current_session['status'] = 'completed'
            self.current_session['progress'] = 100.0
            
            # 存储项目结果到共享记忆
            await self._store_project_result(project_result)
            
            logger.info(f"项目 {project_id} 开发完成，最终评分: {final_score}")
            
            return project_result
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            
            # 错误恢复
            recovery_result = await self._handle_workflow_error(e, project_id)
            if recovery_result:
                return recovery_result
            
            # 返回失败结果
            return ProjectResult(
                project_id=project_id,
                files=FilesDict({}),
                success=False,
                error_message=str(e),
                metadata={'session_id': self.current_session['session_id']}
            )
    
    async def _stage_document_generation(self, user_requirement: str) -> Dict[str, Any]:
        """阶段1：文档生成"""
        logger.info("开始文档生成阶段")
        self._update_progress('document_generation', 10)
        
        doc_result = await self.document_ai.generate_document(user_requirement)
        
        # 记录事件
        await self._record_event(
            'document_generation',
            '生成需求文档',
            {'doc_length': len(doc_result.get('content', '')), 'sections': len(doc_result.get('sections', []))}
        )
        
        return doc_result
    
    async def _stage_development_planning(self, doc_result: Dict[str, Any]) -> DevPlan:
        """阶段2：开发计划制定"""
        logger.info("开始开发计划制定阶段")
        self._update_progress('development_planning', 20)
        
        # 初始化增强开发AI
        self.dev_ai = EnhancedDevAI.with_enhanced_config(
            path=str(self.work_dir / "development"),
            ai=self.main_ai,
            supervisor_ai=self.supervisor_ai,
            test_ai=self.test_ai,
            shared_memory=self.shared_memory
        )
        
        # 创建开发计划
        requirements = {
            'description': doc_result.get('content', ''),
            'features': doc_result.get('features', []),
            'technical_requirements': doc_result.get('technical_requirements', {}),
            'constraints': doc_result.get('constraints', {})
        }
        
        dev_plan = self.dev_ai.create_development_plan(requirements)
        
        # 记录事件
        await self._record_event(
            'development_planning',
            '制定开发计划',
            {'tasks_count': len(dev_plan.tasks), 'estimated_hours': dev_plan.estimated_time}
        )
        
        return dev_plan
    
    async def _stage_iterative_development(self, dev_plan: DevPlan) -> FilesDict:
        """阶段3：迭代开发"""
        logger.info("开始迭代开发阶段")
        self._update_progress('iterative_development', 30)
        
        # 执行迭代开发
        requirements = dev_plan.requirements
        max_iterations = self.workflow_config.get('max_dev_iterations', 5)
        
        code_result = self.dev_ai.iterative_develop(requirements, max_iterations)
        
        # 记录事件
        await self._record_event(
            'iterative_development',
            '完成迭代开发',
            {
                'files_count': len(code_result),
                'completion_percentage': dev_plan.completion_percentage,
                'iterations': max_iterations
            }
        )
        
        return code_result
    
    async def _stage_testing_validation(self, code_result: FilesDict) -> List[TestResult]:
        """阶段4：测试验证"""
        logger.info("开始测试验证阶段")
        self._update_progress('testing_validation', 60)
        
        test_results = []
        
        # 生成测试用例
        requirements = {'description': '全面测试应用功能'}  # 简化需求
        test_files = self.test_ai.generate_tests(code_result, requirements)
        
        # 合并测试文件到代码中
        complete_files = FilesDict({**code_result, **test_files})
        
        # 执行测试
        test_result = self.test_ai.execute_tests(complete_files)
        test_results.append(test_result)
        
        # 记录事件
        await self._record_event(
            'testing_validation',
            '执行测试验证',
            {
                'test_passed': test_result.passed,
                'total_tests': test_result.total_tests,
                'coverage': test_result.coverage_percentage
            }
        )
        
        return test_results
    
    async def _stage_frontend_development(self, code_result: FilesDict, 
                                        doc_result: Dict[str, Any]) -> FilesDict:
        """阶段5：前端开发"""
        logger.info("开始前端开发阶段")
        self._update_progress('frontend_development', 75)
        
        # 分析后端API
        api_spec = self._analyze_backend_api(code_result)
        
        # 生成前端代码
        frontend_result = await self.frontend_ai.develop_ui(
            api_spec, doc_result.get('ui_requirements', {})
        )
        
        # 记录事件
        await self._record_event(
            'frontend_development',
            '完成前端开发',
            {'frontend_files': len(frontend_result)}
        )
        
        return frontend_result
    
    async def _stage_integration(self, backend_files: FilesDict, 
                               frontend_files: FilesDict) -> FilesDict:
        """阶段6：前后端集成"""
        logger.info("开始前后端集成阶段")
        self._update_progress('integration', 80)
        
        # 简单的文件合并集成
        integrated_files = FilesDict({**backend_files, **frontend_files})
        
        # 生成集成配置
        integration_config = self._generate_integration_config(backend_files, frontend_files)
        integrated_files.update(integration_config)
        
        # 记录事件
        await self._record_event(
            'integration',
            '完成前后端集成',
            {'total_files': len(integrated_files)}
        )
        
        return integrated_files
    
    async def _stage_packaging(self, code_result: FilesDict) -> PackageResult:
        """阶段7：项目打包"""
        logger.info("开始项目打包阶段")
        self._update_progress('packaging', 85)
        
        # 配置打包选项
        package_config = {
            'package_type': self.workflow_config.get('package_type', 'docker'),
            'version': '1.0.0',
            'image_name': f'project_{self.current_session["project_id"][:8]}'
        }
        
        # 执行打包
        package_result = self.deploy_ai.package_project(code_result, package_config)
        
        # 记录事件
        await self._record_event(
            'packaging',
            '完成项目打包',
            {
                'package_type': package_result.package_type,
                'success': package_result.success,
                'size_mb': package_result.size_mb
            }
        )
        
        return package_result
    
    async def _stage_deployment(self, package_result: PackageResult, 
                              workflow_options: Dict[str, Any]) -> Optional[DeployResult]:
        """阶段8：部署"""
        logger.info("开始部署阶段")
        self._update_progress('deployment', 90)
        
        if not package_result.success:
            logger.warning("打包失败，跳过部署阶段")
            return None
        
        # 配置部署选项
        server_config = {
            'platform': workflow_options.get('deploy_platform', 'docker'),
            'port': workflow_options.get('deploy_port', 8000),
            'container_name': f'app_{self.current_session["project_id"][:8]}'
        }
        
        # 执行部署
        deploy_result = self.deploy_ai.upload_to_server(package_result, server_config)
        
        # 记录事件
        await self._record_event(
            'deployment',
            '完成项目部署',
            {
                'success': deploy_result.success,
                'url': deploy_result.url,
                'platform': server_config['platform']
            }
        )
        
        return deploy_result
    
    async def _stage_final_evaluation(self, code_result: FilesDict, 
                                    test_results: List[TestResult],
                                    deploy_result: Optional[DeployResult]) -> float:
        """阶段9：最终评估"""
        logger.info("开始最终评估阶段")
        self._update_progress('final_evaluation', 95)
        
        # 代码质量评分
        quality_report = self.supervisor_ai.analyze_quality(code_result)
        quality_score = quality_report.overall_score
        
        # 测试评分
        test_score = 0.0
        if test_results:
            avg_coverage = sum(tr.coverage_percentage for tr in test_results) / len(test_results)
            avg_pass_rate = sum(tr.passed_tests / max(tr.total_tests, 1) for tr in test_results) / len(test_results)
            test_score = (avg_coverage + avg_pass_rate * 100) / 2
        
        # 部署评分
        deploy_score = 0.0
        if deploy_result:
            deploy_score = self.test_ai.final_evaluation(deploy_result)
        
        # 综合评分
        weights = {
            'quality': 0.4,
            'testing': 0.3,
            'deployment': 0.3 if deploy_result else 0.0
        }
        
        if not deploy_result:
            weights['quality'] = 0.6
            weights['testing'] = 0.4
        
        final_score = (
            quality_score * weights['quality'] +
            test_score * weights['testing'] +
            deploy_score * weights['deployment']
        )
        
        # 记录事件
        await self._record_event(
            'final_evaluation',
            '完成最终评估',
            {
                'final_score': final_score,
                'quality_score': quality_score,
                'test_score': test_score,
                'deploy_score': deploy_score
            }
        )
        
        return final_score
    
    def _update_progress(self, stage: str, progress: float):
        """更新进度"""
        self.current_session['current_stage'] = stage
        self.current_session['progress'] = progress
        
        logger.info(f"进入阶段: {stage}, 进度: {progress}%")
    
    async def _record_event(self, event_type: str, description: str, details: Dict[str, Any] = None):
        """记录事件"""
        event = DevelopmentEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type=event_type,
            actor="orchestrator",
            description=description,
            details={
                **(details or {}),
                'session_id': self.current_session['session_id'],
                'project_id': self.current_session['project_id']
            }
        )
        
        self.shared_memory.store_event(event)
        
        # 触发事件处理器
        await self._trigger_event_handlers(event)
    
    async def _trigger_event_handlers(self, event: DevelopmentEvent):
        """触发事件处理器"""
        for event_type, handlers in self.event_handlers.items():
            if event_type == event.event_type or event_type == '*':
                for handler in handlers:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"事件处理器执行失败: {e}")
    
    def _register_default_handlers(self):
        """注册默认事件处理器"""
        self.event_handlers = {
            'error': [self._handle_error_event],
            'test_failure': [self._handle_test_failure_event],
            '*': [self._log_event]
        }
    
    async def _handle_error_event(self, event: DevelopmentEvent):
        """处理错误事件"""
        logger.error(f"错误事件: {event.description}")
        # 这里可以实现错误恢复逻辑
    
    async def _handle_test_failure_event(self, event: DevelopmentEvent):
        """处理测试失败事件"""
        logger.warning(f"测试失败: {event.description}")
        # 这里可以实现自动修复逻辑
    
    async def _log_event(self, event: DevelopmentEvent):
        """记录所有事件"""
        logger.debug(f"事件: {event.event_type} - {event.description}")
    
    def _analyze_backend_api(self, code_result: FilesDict) -> Dict[str, Any]:
        """分析后端API结构"""
        # 简化的API分析
        api_spec = {
            'endpoints': [],
            'models': [],
            'base_url': 'http://localhost:8000'
        }
        
        for filename, content in code_result.items():
            if 'app.py' in filename or 'main.py' in filename:
                # 简单的路由提取
                import re
                routes = re.findall(r'@app\.route\(["\']([^"\']+)["\']\)', content)
                api_spec['endpoints'].extend(routes)
        
        return api_spec
    
    def _generate_integration_config(self, backend_files: FilesDict, 
                                   frontend_files: FilesDict) -> FilesDict:
        """生成集成配置文件"""
        config_files = FilesDict({})
        
        # 生成nginx配置（如果需要）
        if any(f.endswith('.html') for f in frontend_files):
            nginx_config = """
server {
    listen 80;
    
    location /api/ {
        proxy_pass http://backend:8000;
    }
    
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
"""
            config_files['nginx.conf'] = nginx_config
        
        # 生成docker-compose配置
        docker_compose = """
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
  
  frontend:
    build: ./frontend  
    ports:
      - "3000:3000"
    depends_on:
      - backend
"""
        config_files['docker-compose.yml'] = docker_compose
        
        return config_files
    
    async def _store_project_result(self, project_result: ProjectResult):
        """存储项目结果到共享记忆"""
        knowledge = {
            'category': 'project_results',
            'project_id': project_result.project_id,
            'success': project_result.success,
            'final_score': project_result.final_score,
            'development_time': project_result.development_time,
            'files_count': len(project_result.files),
            'test_results_count': len(project_result.test_results),
            'deployment_success': project_result.deployment and project_result.deployment.success,
            'metadata': project_result.metadata,
            'timestamp': datetime.now().isoformat(),
            'tags': ['project_completion', 'full_workflow']
        }
        
        self.shared_memory.store_knowledge(
            f"project_result_{project_result.project_id}",
            knowledge
        )
    
    async def _handle_workflow_error(self, error: Exception, project_id: str) -> Optional[ProjectResult]:
        """处理工作流错误"""
        logger.error(f"工作流错误: {error}")
        
        # 记录错误事件
        await self._record_event(
            'workflow_error',
            f'工作流执行出错: {str(error)}',
            {'error_type': type(error).__name__, 'error_message': str(error)}
        )
        
        # 尝试恢复（简化版本）
        self.current_session['status'] = 'error'
        return None
    
    def get_session_status(self) -> Dict[str, Any]:
        """获取当前会话状态"""
        return dict(self.current_session)
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)


# 临时AI实现类（简化版本）
class DocumentAI:
    def __init__(self, ai: AI):
        self.ai = ai
    
    async def generate_document(self, requirement: str) -> Dict[str, Any]:
        prompt = f"""
基于以下用户需求，生成详细的需求文档：

用户需求：
{requirement}

请生成包含以下部分的需求文档：
1. 项目概述
2. 功能需求
3. 技术需求
4. UI/UX要求
5. 约束条件

返回JSON格式的结构化文档。
"""
        
        messages = self.ai.start(
            system="你是一个专业的需求分析师，负责将用户需求转换为详细的需求文档。",
            user=prompt,
            step_name="generate_document"
        )
        
        content = messages[-1].content.strip()
        
        return {
            'content': content,
            'features': ['基础功能'],  # 简化
            'technical_requirements': {'language': 'python'},
            'constraints': {}
        }


class FrontendAI:
    def __init__(self, ai: AI):
        self.ai = ai
    
    async def develop_ui(self, api_spec: Dict[str, Any], ui_requirements: Dict[str, Any]) -> FilesDict:
        """开发前端UI"""
        prompt = f"""
基于以下API规格和UI需求，生成前端代码：

API规格：
{json.dumps(api_spec, indent=2)}

UI需求：
{json.dumps(ui_requirements, indent=2)}

请生成一个简单的HTML/CSS/JavaScript前端应用。
"""
        
        messages = self.ai.start(
            system="你是一个专业的前端开发工程师。",
            user=prompt,
            step_name="develop_ui"
        )
        
        # 简化的前端代码生成
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Generated App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Generated Application</h1>
        <p>This is a generated frontend application.</p>
    </div>
</body>
</html>
"""
        
        return FilesDict({
            'index.html': html_content,
            'style.css': 'body { font-family: Arial, sans-serif; }',
            'script.js': 'console.log("Frontend loaded");'
        })