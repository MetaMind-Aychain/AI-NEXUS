"""
深度集成GPT-ENGINEER核心模块

将升级版AI与原有GPT-ENGINEER架构深度融合
确保完全兼容性和最优性能
"""

import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from gpt_engineer.core.ai import AI
from gpt_engineer.core.base_agent import BaseAgent
from gpt_engineer.core.base_execution_env import BaseExecutionEnv
from gpt_engineer.core.base_memory import BaseMemory
from gpt_engineer.core.default.simple_agent import SimpleAgent
from gpt_engineer.core.default.steps import (
    gen_code, gen_entrypoint, improve_fn, execute_entrypoint,
    setup_sys_prompt, setup_sys_prompt_existing_code
)
from gpt_engineer.core.files_dict import FilesDict
from gpt_engineer.core.preprompts_holder import PrepromptsHolder
from gpt_engineer.core.prompt import Prompt
from gpt_engineer.core.default.disk_memory import DiskMemory
from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv

from .base_interfaces import (
    BaseSupervisorAI, BaseTestAI, BaseSharedMemory,
    DevPlan, DevelopmentEvent, TestResult, TaskStatus
)


class DeepIntegratedDevAI(SimpleAgent):
    """
    深度集成的开发AI
    
    完全继承原有GPT-ENGINEER的SimpleAgent，同时扩展高级功能
    确保向后兼容性和无缝集成
    """
    
    def __init__(
        self,
        memory: BaseMemory,
        execution_env: BaseExecutionEnv,
        ai: AI = None,
        preprompts_holder: PrepromptsHolder = None,
        supervisor_ai: Optional[BaseSupervisorAI] = None,
        test_ai: Optional[BaseTestAI] = None,
        shared_memory: Optional[BaseSharedMemory] = None
    ):
        # 调用父类构造函数，确保完全兼容
        super().__init__(memory, execution_env, ai, preprompts_holder)
        
        # 扩展功能组件
        self.supervisor_ai = supervisor_ai
        self.test_ai = test_ai
        self.shared_memory = shared_memory
        
        # 深度集成状态
        self.integration_context = {
            "current_step": None,
            "step_history": [],
            "ai_feedback": [],
            "quality_metrics": [],
            "test_results": []
        }
        
        # 性能优化
        self.use_optimized_prompts = True
        self.enable_smart_caching = True
        self.enable_incremental_updates = True
        
        print("🔗 深度集成开发AI已初始化")
        print(f"   基于GPT-ENGINEER: {type(super()).__name__}")
        print(f"   监管AI集成: {'✅' if supervisor_ai else '❌'}")
        print(f"   测试AI集成: {'✅' if test_ai else '❌'}")
        print(f"   共享记忆: {'✅' if shared_memory else '❌'}")
    
    def init(self, prompt: str) -> FilesDict:
        """
        深度集成的项目初始化
        
        完全兼容原有的init方法，同时增强功能
        """
        print("🚀 开始深度集成项目初始化...")
        
        # 记录当前步骤
        self.integration_context["current_step"] = "init"
        self.integration_context["step_history"].append({
            "step": "init",
            "timestamp": datetime.now(),
            "prompt": prompt
        })
        
        # 智能提示优化
        if self.use_optimized_prompts:
            enhanced_prompt = self._enhance_init_prompt(prompt)
        else:
            enhanced_prompt = prompt
        
        # 调用原始的生成步骤，确保完全兼容
        messages = gen_code(
            ai=self.ai,
            prompt=Prompt(enhanced_prompt),
            memory=self.memory,
            preprompts=self.preprompts_holder.load()
        )
        
        # 获取生成的文件
        files_dict = self.memory.to_dict()
        
        # 生成入口点
        entrypoint_messages = gen_entrypoint(
            ai=self.ai,
            files_dict=files_dict,
            memory=self.memory,
            preprompts=self.preprompts_holder.load()
        )
        
        # 更新文件字典
        updated_files_dict = self.memory.to_dict()
        
        # 智能质量检查
        if self.supervisor_ai:
            print("👁️ 执行智能质量检查...")
            quality_feedback = self._get_supervisor_feedback(updated_files_dict)
            self.integration_context["ai_feedback"].append(quality_feedback)
            
            # 如果质量不达标，进行优化
            if quality_feedback.get("needs_improvement", False):
                updated_files_dict = self._apply_quality_improvements(
                    updated_files_dict, quality_feedback
                )
        
        # 智能测试生成
        if self.test_ai:
            print("🧪 执行智能测试生成...")
            test_feedback = self._generate_smart_tests(updated_files_dict, prompt)
            self.integration_context["test_results"].append(test_feedback)
        
        # 保存到共享记忆
        if self.shared_memory:
            self._save_to_shared_memory("init_result", {
                "files": updated_files_dict,
                "prompt": prompt,
                "quality_feedback": self.integration_context["ai_feedback"],
                "test_results": self.integration_context["test_results"]
            })
        
        print(f"✅ 深度集成初始化完成，生成 {len(updated_files_dict)} 个文件")
        
        return FilesDict(updated_files_dict)
    
    def improve(self, files_dict: FilesDict, user_feedback: str) -> FilesDict:
        """
        深度集成的代码改进
        
        完全兼容原有的improve方法，同时增强功能
        """
        print("🔧 开始深度集成代码改进...")
        
        # 记录当前步骤
        self.integration_context["current_step"] = "improve"
        self.integration_context["step_history"].append({
            "step": "improve",
            "timestamp": datetime.now(),
            "feedback": user_feedback
        })
        
        # 将FilesDict转换为内存中的文件
        self.memory.update(files_dict)
        
        # 智能反馈分析
        if self.supervisor_ai:
            analyzed_feedback = self._analyze_feedback_with_supervisor(user_feedback, files_dict)
        else:
            analyzed_feedback = user_feedback
        
        # 调用原始的改进步骤，确保完全兼容
        messages = improve_fn(
            ai=self.ai,
            prompt=Prompt(analyzed_feedback),
            memory=self.memory,
            preprompts=self.preprompts_holder.load()
        )
        
        # 获取改进后的文件
        improved_files_dict = self.memory.to_dict()
        
        # 智能质量验证
        if self.supervisor_ai:
            print("👁️ 验证改进质量...")
            quality_verification = self._verify_improvement_quality(
                files_dict, FilesDict(improved_files_dict), user_feedback
            )
            self.integration_context["ai_feedback"].append(quality_verification)
            
            # 如果改进不满意，进行迭代优化
            if quality_verification.get("needs_further_improvement", False):
                improved_files_dict = self._iterative_improvement(
                    improved_files_dict, quality_verification
                )
        
        # 智能测试更新
        if self.test_ai:
            print("🧪 更新智能测试...")
            test_update = self._update_tests_for_changes(
                files_dict, FilesDict(improved_files_dict)
            )
            self.integration_context["test_results"].append(test_update)
        
        # 保存到共享记忆
        if self.shared_memory:
            self._save_to_shared_memory("improve_result", {
                "original_files": files_dict,
                "improved_files": improved_files_dict,
                "feedback": user_feedback,
                "quality_verification": self.integration_context["ai_feedback"][-1] if self.integration_context["ai_feedback"] else None
            })
        
        print(f"✅ 深度集成改进完成")
        
        return FilesDict(improved_files_dict)
    
    def execute_with_monitoring(self) -> Dict[str, Any]:
        """
        带监控的代码执行
        
        集成原有的execute_entrypoint功能，增加智能监控
        """
        print("🏃 开始智能监控执行...")
        
        # 记录执行步骤
        self.integration_context["current_step"] = "execute"
        self.integration_context["step_history"].append({
            "step": "execute",
            "timestamp": datetime.now()
        })
        
        execution_result = {
            "success": False,
            "output": "",
            "error": None,
            "performance_metrics": {},
            "supervisor_analysis": {}
        }
        
        try:
            # 调用原始的执行函数
            result = execute_entrypoint(
                ai=self.ai,
                execution_env=self.execution_env,
                memory=self.memory,
                preprompts=self.preprompts_holder.load()
            )
            
            execution_result["success"] = True
            execution_result["output"] = str(result) if result else ""
            
            # 监管AI分析执行结果
            if self.supervisor_ai:
                supervisor_analysis = self._analyze_execution_with_supervisor(result)
                execution_result["supervisor_analysis"] = supervisor_analysis
            
            print("✅ 智能监控执行完成")
            
        except Exception as e:
            execution_result["error"] = str(e)
            print(f"❌ 执行失败: {e}")
            
            # 监管AI分析错误
            if self.supervisor_ai:
                error_analysis = self._analyze_error_with_supervisor(e)
                execution_result["supervisor_analysis"] = error_analysis
        
        return execution_result
    
    def _enhance_init_prompt(self, original_prompt: str) -> str:
        """智能提示增强"""
        enhancement_prefix = """
请根据以下需求生成高质量、可维护的代码。
重点关注：
1. 代码结构清晰
2. 错误处理完善
3. 文档注释齐全
4. 遵循最佳实践

用户需求：
"""
        return enhancement_prefix + original_prompt
    
    def _get_supervisor_feedback(self, files_dict: Dict[str, str]) -> Dict[str, Any]:
        """获取监管AI反馈"""
        try:
            # 创建临时的监管会话
            dev_plan = DevPlan(
                tasks=["代码质量检查"],
                estimated_time=1.0,
                dependencies={},
                milestones=["质量验证完成"]
            )
            
            supervision_id = asyncio.run(
                self.supervisor_ai.start_supervision(dev_plan)
            )
            
            quality_report = asyncio.run(
                self.supervisor_ai.analyze_quality(supervision_id, FilesDict(files_dict))
            )
            
            return {
                "supervision_id": supervision_id,
                "quality_score": quality_report.overall_score,
                "needs_improvement": quality_report.overall_score < 0.8,
                "suggestions": quality_report.suggestions,
                "detailed_analysis": quality_report.detailed_analysis
            }
            
        except Exception as e:
            print(f"监管AI反馈获取失败: {e}")
            return {"error": str(e), "needs_improvement": False}
    
    def _generate_smart_tests(self, files_dict: Dict[str, str], requirements: str) -> Dict[str, Any]:
        """生成智能测试"""
        try:
            test_files = asyncio.run(
                self.test_ai.generate_tests(FilesDict(files_dict), requirements)
            )
            
            # 将测试文件添加到内存中
            for test_filename, test_content in test_files.items():
                self.memory[test_filename] = test_content
            
            return {
                "test_files": test_files,
                "test_count": len(test_files),
                "success": True
            }
            
        except Exception as e:
            print(f"智能测试生成失败: {e}")
            return {"error": str(e), "success": False}
    
    def _apply_quality_improvements(self, files_dict: Dict[str, str], 
                                  quality_feedback: Dict[str, Any]) -> Dict[str, str]:
        """应用质量改进"""
        if not quality_feedback.get("suggestions"):
            return files_dict
        
        # 基于监管AI的建议进行改进
        improvement_prompt = f"""
请根据以下质量分析建议改进代码：

{json.dumps(quality_feedback.get('suggestions', []), ensure_ascii=False, indent=2)}

当前代码质量评分: {quality_feedback.get('quality_score', 'N/A')}
"""
        
        try:
            # 使用improve功能进行质量改进
            improved_files = self.improve(FilesDict(files_dict), improvement_prompt)
            return improved_files
        except Exception as e:
            print(f"质量改进失败: {e}")
            return files_dict
    
    def _analyze_feedback_with_supervisor(self, feedback: str, files_dict: FilesDict) -> str:
        """使用监管AI分析用户反馈"""
        try:
            # 构建分析提示
            analysis_prompt = f"""
请分析以下用户反馈，并提供详细的改进指导：

用户反馈: {feedback}

请提供：
1. 反馈的核心要求
2. 具体的改进方向
3. 实现建议
4. 潜在风险评估
"""
            
            response = self.ai.start(
                system="你是一个专业的代码分析师，擅长理解用户需求并提供精确的改进指导。",
                user=analysis_prompt,
                step_name="feedback_analysis"
            )
            
            return response[-1].content
            
        except Exception as e:
            print(f"反馈分析失败: {e}")
            return feedback
    
    def _verify_improvement_quality(self, original_files: FilesDict, 
                                  improved_files: FilesDict, feedback: str) -> Dict[str, Any]:
        """验证改进质量"""
        try:
            # 比较改进前后的质量
            original_quality = asyncio.run(
                self.supervisor_ai.analyze_quality("temp", original_files)
            )
            improved_quality = asyncio.run(
                self.supervisor_ai.analyze_quality("temp", improved_files)
            )
            
            improvement_score = improved_quality.overall_score - original_quality.overall_score
            
            return {
                "original_score": original_quality.overall_score,
                "improved_score": improved_quality.overall_score,
                "improvement": improvement_score,
                "needs_further_improvement": improvement_score < 0.1,
                "feedback_addressed": improvement_score > 0
            }
            
        except Exception as e:
            print(f"质量验证失败: {e}")
            return {"error": str(e), "needs_further_improvement": False}
    
    def _iterative_improvement(self, files_dict: Dict[str, str], 
                             quality_verification: Dict[str, Any]) -> Dict[str, str]:
        """迭代改进"""
        max_iterations = 3
        current_files = files_dict.copy()
        
        for i in range(max_iterations):
            if not quality_verification.get("needs_further_improvement", False):
                break
            
            print(f"🔄 执行迭代改进 {i+1}/{max_iterations}")
            
            # 构建迭代改进提示
            iteration_prompt = f"""
上一次改进的效果不够理想，请进一步优化：

当前质量评分: {quality_verification.get('improved_score', 'N/A')}
目标质量评分: 0.85+

请重点关注：
1. 代码结构优化
2. 性能提升
3. 错误处理
4. 代码规范
"""
            
            try:
                improved_files = self.improve(FilesDict(current_files), iteration_prompt)
                current_files = improved_files
                
                # 重新验证质量
                quality_verification = self._verify_improvement_quality(
                    FilesDict(files_dict), FilesDict(current_files), iteration_prompt
                )
                
            except Exception as e:
                print(f"迭代改进失败: {e}")
                break
        
        return current_files
    
    def _update_tests_for_changes(self, original_files: FilesDict, 
                                improved_files: FilesDict) -> Dict[str, Any]:
        """为代码变更更新测试"""
        try:
            # 检测代码变更
            changes_detected = len(improved_files) != len(original_files) or \
                             any(improved_files.get(k) != original_files.get(k) 
                                for k in improved_files.keys())
            
            if changes_detected:
                # 生成新的测试
                updated_tests = asyncio.run(
                    self.test_ai.generate_tests(improved_files, "更新测试以反映代码变更")
                )
                
                return {
                    "changes_detected": True,
                    "updated_tests": updated_tests,
                    "test_count": len(updated_tests)
                }
            else:
                return {
                    "changes_detected": False,
                    "message": "未检测到代码变更"
                }
                
        except Exception as e:
            print(f"测试更新失败: {e}")
            return {"error": str(e), "changes_detected": False}
    
    def _analyze_execution_with_supervisor(self, execution_result: Any) -> Dict[str, Any]:
        """使用监管AI分析执行结果"""
        try:
            analysis_prompt = f"""
请分析以下代码执行结果：

执行结果: {str(execution_result)}

请提供：
1. 执行状态评估
2. 性能分析
3. 潜在问题识别
4. 优化建议
"""
            
            response = self.ai.start(
                system="你是一个专业的代码执行分析师，擅长评估代码运行状态和性能。",
                user=analysis_prompt,
                step_name="execution_analysis"
            )
            
            return {
                "analysis": response[-1].content,
                "status": "success"
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def _analyze_error_with_supervisor(self, error: Exception) -> Dict[str, Any]:
        """使用监管AI分析错误"""
        try:
            error_prompt = f"""
请分析以下代码执行错误：

错误类型: {type(error).__name__}
错误信息: {str(error)}

请提供：
1. 错误原因分析
2. 解决方案建议
3. 预防措施
4. 代码修复指导
"""
            
            response = self.ai.start(
                system="你是一个专业的错误诊断专家，擅长分析和解决代码问题。",
                user=error_prompt,
                step_name="error_analysis"
            )
            
            return {
                "error_analysis": response[-1].content,
                "error_type": type(error).__name__,
                "status": "analyzed"
            }
            
        except Exception as e:
            return {"error": str(e), "status": "analysis_failed"}
    
    def _save_to_shared_memory(self, key: str, data: Any):
        """保存到共享记忆"""
        if self.shared_memory:
            try:
                asyncio.run(
                    self.shared_memory.store_memory(key, data)
                )
            except Exception as e:
                print(f"共享记忆保存失败: {e}")
    
    async def develop_project_from_document(self, project_id: str, document_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据文档AI生成的开发文档进行项目开发
        
        这是连接文档AI和开发AI的核心方法
        """
        print(f"🛠️ 开发AI开始根据文档开发项目: {project_id}")
        
        try:
            # 1. 解析文档内容
            project_name = document_result.get('project_name', f'Project_{project_id}')
            features = document_result.get('features', [])
            tech_stack = document_result.get('tech_stack', [])
            architecture = document_result.get('architecture', {})
            requirements = document_result.get('detailed_requirements', '')
            
            print(f"📋 项目信息: {project_name}")
            print(f"🔧 技术栈: {', '.join(tech_stack)}")
            print(f"⚡ 功能模块: {len(features)} 个")
            
            # 2. 构建开发提示
            development_prompt = self._build_development_prompt(
                project_name, features, tech_stack, architecture, requirements
            )
            
            # 3. 启动监督AI监控
            if self.supervisor_ai:
                await self._start_development_supervision(project_id, document_result)
            
            # 4. 使用GPT-Engineer的核心功能进行代码生成
            print("💻 调用GPT-ENGINEER核心引擎生成代码...")
            files_dict = self.init(development_prompt)
            
            # 5. 监督AI验证生成的代码
            if self.supervisor_ai:
                validation_result = await self._validate_with_supervisor(project_id, files_dict)
                if not validation_result.get('approved', True):
                    print("🔄 监督AI要求改进，进行迭代开发...")
                    improvement_feedback = validation_result.get('feedback', '')
                    files_dict = self.improve(files_dict, improvement_feedback)
            
            # 6. 生成项目结构
            project_path = await self._setup_project_structure(project_id, files_dict)
            
            # 7. 生成配置文件
            config_files = await self._generate_config_files(tech_stack, architecture)
            files_dict.update(config_files)
            
            # 8. 保存所有文件到项目目录
            await self._save_project_files(project_path, files_dict)
            
            # 9. 记录开发结果
            development_result = {
                "project_id": project_id,
                "project_name": project_name,
                "project_path": str(project_path),
                "files": dict(files_dict),
                "tech_stack": tech_stack,
                "features_implemented": features,
                "development_status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            # 10. 保存到共享记忆
            if self.shared_memory:
                await self.shared_memory.store_project_context(project_id, {
                    "development_result": development_result
                })
            
            print(f"✅ 项目开发完成: {project_path}")
            return development_result
            
        except Exception as e:
            print(f"❌ 项目开发失败: {e}")
            error_result = {
                "project_id": project_id,
                "error": str(e),
                "development_status": "failed",
                "timestamp": datetime.now().isoformat()
            }
            return error_result
    
    def _build_development_prompt(self, project_name: str, features: List[str], 
                                tech_stack: List[str], architecture: Dict, 
                                requirements: str) -> str:
        """构建开发提示"""
        prompt_parts = [
            f"请开发一个名为'{project_name}'的项目。",
            f"\n技术要求:",
            f"- 使用技术栈: {', '.join(tech_stack)}",
            f"- 架构模式: {architecture.get('pattern', '标准架构')}",
            f"\n功能需求:",
        ]
        
        for i, feature in enumerate(features, 1):
            prompt_parts.append(f"{i}. {feature}")
        
        prompt_parts.extend([
            f"\n详细要求:",
            requirements,
            f"\n请生成完整的项目代码，包括:",
            f"- 主要功能模块",
            f"- 配置文件",
            f"- 文档说明",
            f"- 测试代码",
            f"\n确保代码质量高，结构清晰，遵循最佳实践。"
        ])
        
        return "\n".join(prompt_parts)
    
    async def _start_development_supervision(self, project_id: str, document_result: Dict):
        """启动开发监督"""
        if hasattr(self.supervisor_ai, 'start_monitoring'):
            await self.supervisor_ai.start_monitoring(project_id, document_result)
    
    async def _validate_with_supervisor(self, project_id: str, files_dict: FilesDict) -> Dict:
        """监督AI验证代码"""
        if hasattr(self.supervisor_ai, 'validate_development'):
            return await self.supervisor_ai.validate_development(project_id, dict(files_dict))
        return {"approved": True}
    
    async def _setup_project_structure(self, project_id: str, files_dict: FilesDict) -> Path:
        """设置项目结构"""
        project_path = Path(f"real_ai_projects/{project_id}")
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path
    
    async def _generate_config_files(self, tech_stack: List[str], architecture: Dict) -> Dict[str, str]:
        """生成配置文件"""
        config_files = {}
        
        # 根据技术栈生成配置
        if 'python' in tech_stack:
            config_files['requirements.txt'] = self._generate_python_requirements()
        
        if 'docker' in tech_stack:
            config_files['Dockerfile'] = self._generate_dockerfile()
            config_files['docker-compose.yml'] = self._generate_docker_compose()
        
        if 'javascript' in tech_stack or 'react' in tech_stack:
            config_files['package.json'] = self._generate_package_json()
        
        return config_files
    
    async def _save_project_files(self, project_path: Path, files_dict: FilesDict):
        """保存项目文件"""
        for filename, content in files_dict.items():
            file_path = project_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                file_path.write_text(content, encoding='utf-8')
            except Exception as e:
                print(f"保存文件失败 {filename}: {e}")
    
    def _generate_python_requirements(self) -> str:
        """生成Python依赖"""
        return """fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
python-dotenv==1.0.0
pytest==7.4.3
"""
    
    def _generate_dockerfile(self) -> str:
        """生成Dockerfile"""
        return """FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    def _generate_docker_compose(self) -> str:
        """生成docker-compose.yml"""
        return """version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./app.db
    volumes:
      - ./:/app
"""
    
    def _generate_package_json(self) -> str:
        """生成package.json"""
        return """{
  "name": "ai-generated-project",
  "version": "1.0.0",
  "description": "AI generated project",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "dotenv": "^16.0.3"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.5.0"
  }
}
"""

    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        return {
            "integration_context": self.integration_context,
            "components_status": {
                "supervisor_ai": self.supervisor_ai is not None,
                "test_ai": self.test_ai is not None,
                "shared_memory": self.shared_memory is not None
            },
            "optimization_settings": {
                "optimized_prompts": self.use_optimized_prompts,
                "smart_caching": self.enable_smart_caching,
                "incremental_updates": self.enable_incremental_updates
            },
            "step_history": self.integration_context["step_history"],
            "ai_feedback_count": len(self.integration_context["ai_feedback"]),
            "test_results_count": len(self.integration_context["test_results"])
        }


class DeepIntegrationManager:
    """
    深度集成管理器
    
    统一管理原有GPT-ENGINEER组件与升级版AI的深度集成
    """
    
    def __init__(self, work_dir: str = "./deep_integration_workspace"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        
        # GPT-ENGINEER核心组件
        self.ai = None
        self.memory = None
        self.execution_env = None
        self.preprompts_holder = None
        
        # 升级版AI组件
        self.supervisor_ai = None
        self.test_ai = None
        self.shared_memory = None
        
        # 深度集成的开发AI
        self.integrated_dev_ai = None
        
        print("🔗 深度集成管理器已初始化")
    
    def setup_gpt_engineer_core(self, ai: AI, memory_dir: Optional[str] = None, 
                               preprompts_path: Optional[str] = None):
        """设置GPT-ENGINEER核心组件"""
        self.ai = ai
        
        # 设置内存
        if memory_dir:
            self.memory = DiskMemory(memory_dir)
        else:
            self.memory = DiskMemory(str(self.work_dir / "memory"))
        
        # 设置执行环境
        self.execution_env = DiskExecutionEnv()
        
        # 设置预提示
        if preprompts_path:
            self.preprompts_holder = PrepromptsHolder(Path(preprompts_path))
        else:
            # 使用默认路径
            from gpt_engineer.core.default.paths import PREPROMPTS_PATH
            self.preprompts_holder = PrepromptsHolder(PREPROMPTS_PATH)
        
        print("✅ GPT-ENGINEER核心组件设置完成")
    
    def setup_upgraded_ai_components(self, supervisor_ai=None, test_ai=None, shared_memory=None):
        """设置升级版AI组件"""
        self.supervisor_ai = supervisor_ai
        self.test_ai = test_ai
        self.shared_memory = shared_memory
        
        print("✅ 升级版AI组件设置完成")
        print(f"   监管AI: {'✅' if supervisor_ai else '❌'}")
        print(f"   测试AI: {'✅' if test_ai else '❌'}")
        print(f"   共享记忆: {'✅' if shared_memory else '❌'}")
    
    def create_deep_integrated_agent(self) -> DeepIntegratedDevAI:
        """创建深度集成的开发AI代理"""
        if not self.ai or not self.memory or not self.execution_env:
            raise ValueError("请先设置GPT-ENGINEER核心组件")
        
        self.integrated_dev_ai = DeepIntegratedDevAI(
            memory=self.memory,
            execution_env=self.execution_env,
            ai=self.ai,
            preprompts_holder=self.preprompts_holder,
            supervisor_ai=self.supervisor_ai,
            test_ai=self.test_ai,
            shared_memory=self.shared_memory
        )
        
        print("🚀 深度集成开发AI代理创建完成")
        return self.integrated_dev_ai
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """获取集成摘要"""
        return {
            "gpt_engineer_core": {
                "ai_ready": self.ai is not None,
                "memory_ready": self.memory is not None,
                "execution_env_ready": self.execution_env is not None,
                "preprompts_ready": self.preprompts_holder is not None
            },
            "upgraded_components": {
                "supervisor_ai": self.supervisor_ai is not None,
                "test_ai": self.test_ai is not None,
                "shared_memory": self.shared_memory is not None
            },
            "integrated_agent": {
                "created": self.integrated_dev_ai is not None,
                "status": self.integrated_dev_ai.get_integration_status() if self.integrated_dev_ai else None
            },
            "work_directory": str(self.work_dir)
        }