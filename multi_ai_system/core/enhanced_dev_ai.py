"""
增强的开发AI实现

基于GPT-Engineer的SimpleAgent进行扩展，集成监管AI和测试AI的反馈机制
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from gpt_engineer.core.ai import AI
from gpt_engineer.core.default.simple_agent import SimpleAgent
from gpt_engineer.core.default.disk_memory import DiskMemory
from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv
from gpt_engineer.core.files_dict import FilesDict
from gpt_engineer.core.prompt import Prompt
from gpt_engineer.core.preprompts_holder import PrepromptsHolder
from gpt_engineer.core.base_memory import BaseMemory
from gpt_engineer.core.base_execution_env import BaseExecutionEnv

from .base_interfaces import (
    BaseSupervisorAI, BaseTestAI, BaseSharedMemory,
    DevPlan, DevelopmentEvent, TestResult, TaskStatus
)


class EnhancedDevAI(SimpleAgent):
    """
    增强的开发AI，基于GPT-Engineer的SimpleAgent扩展
    
    新增功能：
    - 监管AI集成
    - 测试AI反馈处理
    - 共享记忆访问
    - 迭代开发支持
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
        super().__init__(memory, execution_env, ai, preprompts_holder)
        self.supervisor_ai = supervisor_ai
        self.test_ai = test_ai
        self.shared_memory = shared_memory
        self.current_plan: Optional[DevPlan] = None
        self.development_history: List[DevelopmentEvent] = []
    
    def create_development_plan(self, requirements: Dict[str, Any]) -> DevPlan:
        """
        创建开发计划
        
        Args:
            requirements: 需求文档
            
        Returns:
            DevPlan: 开发计划
        """
        plan_prompt = self._build_planning_prompt(requirements)
        
        # 使用AI生成开发计划
        messages = self.ai.start(
            system="你是一个专业的软件开发规划师。请基于需求文档制定详细的开发计划。",
            user=plan_prompt,
            step_name="create_development_plan"
        )
        
        plan_content = messages[-1].content.strip()
        
        # 解析AI生成的计划
        tasks = self._parse_development_plan(plan_content)
        
        plan = DevPlan(
            plan_id=str(uuid.uuid4()),
            requirements=requirements,
            tasks=tasks,
            estimated_time=sum(task.get('estimated_hours', 1) for task in tasks)
        )
        
        self.current_plan = plan
        
        # 记录计划创建事件
        self._record_event(
            event_type="plan_creation",
            description="创建开发计划",
            details={"plan_id": plan.plan_id, "tasks_count": len(tasks)}
        )
        
        return plan
    
    def generate_with_supervision(self, prompt: Prompt, context: Optional[Dict[str, Any]] = None) -> FilesDict:
        """
        在监管AI监督下生成代码
        
        Args:
            prompt: 开发提示
            context: 上下文信息
            
        Returns:
            FilesDict: 生成的代码文件
        """
        # 获取历史经验
        similar_cases = []
        if self.shared_memory:
            similar_cases = self.shared_memory.find_similar_cases({
                "requirements": context or {},
                "prompt_text": prompt.text
            })
        
        # 增强提示词，加入历史经验
        enhanced_prompt = self._enhance_prompt_with_history(prompt, similar_cases)
        
        # 生成代码
        files_dict = self.init(enhanced_prompt)
        
        # 监管AI质量检查
        if self.supervisor_ai:
            quality_report = self.supervisor_ai.analyze_quality(files_dict)
            
            # 如果质量不达标，进行改进
            if quality_report.quality_level.value in ['poor', 'critical']:
                improvement_prompt = self._create_improvement_prompt(
                    enhanced_prompt, files_dict, quality_report
                )
                files_dict = self.improve(files_dict, improvement_prompt)
        
        # 记录代码生成事件
        self._record_event(
            event_type="code_generation",
            description="生成代码文件",
            details={
                "files_count": len(files_dict),
                "prompt_length": len(prompt.text)
            },
            files_affected=list(files_dict.keys())
        )
        
        return files_dict
    
    def iterative_develop(self, requirements: Dict[str, Any], max_iterations: int = 5) -> FilesDict:
        """
        迭代开发过程，结合测试反馈
        
        Args:
            requirements: 需求规格
            max_iterations: 最大迭代次数
            
        Returns:
            FilesDict: 最终代码文件
        """
        # 创建开发计划
        if not self.current_plan:
            self.current_plan = self.create_development_plan(requirements)
        
        # 开始监管
        if self.supervisor_ai:
            self.supervisor_ai.start_supervision(self.current_plan)
        
        current_files = FilesDict({})
        iteration = 0
        
        while iteration < max_iterations and not self._is_development_complete():
            iteration += 1
            print(f"\n=== 开发迭代 {iteration} ===")
            
            # 获取当前任务
            current_task = self.current_plan.current_task
            if not current_task:
                break
            
            # 生成当前任务的代码
            task_prompt = self._create_task_prompt(current_task, requirements)
            
            # 如果已有代码，使用改进模式
            if current_files:
                new_files = self.improve(current_files, task_prompt)
            else:
                new_files = self.generate_with_supervision(task_prompt, requirements)
            
            current_files.update(new_files)
            
            # 执行测试
            if self.test_ai:
                test_result = self.test_ai.execute_tests(current_files)
                
                if test_result.passed:
                    print(f"✅ 测试通过 ({test_result.passed_tests}/{test_result.total_tests})")
                    self.current_plan.mark_task_complete()
                else:
                    print(f"❌ 测试失败 ({test_result.failed_tests}/{test_result.total_tests})")
                    
                    # 分析失败原因
                    issues = []
                    if self.supervisor_ai:
                        issues = self.supervisor_ai.analyze_issues(test_result)
                    
                    if self.test_ai:
                        diagnosis = self.test_ai.diagnose_failures(test_result, current_files)
                        issues.extend(diagnosis)
                    
                    # 添加修复任务
                    if issues:
                        self.current_plan.add_fixes(issues)
                    
                    # 记录测试失败事件
                    self._record_event(
                        event_type="test_failure",
                        description=f"测试失败，需要修复 {len(issues)} 个问题",
                        details={
                            "test_result": test_result.__dict__,
                            "issues": issues
                        },
                        success=False
                    )
            else:
                # 没有测试AI时，标记任务完成
                self.current_plan.mark_task_complete()
            
            # 监管AI记录进展
            if self.supervisor_ai:
                supervision_result = self.supervisor_ai.monitor_development(
                    self.current_plan, current_files
                )
                
                # 处理监管建议
                if supervision_result.recommendations:
                    print(f"📋 监管建议: {supervision_result.recommendations}")
                
                if supervision_result.risk_warnings:
                    print(f"⚠️ 风险警告: {supervision_result.risk_warnings}")
        
        # 开发完成，存储最终结果
        if self.shared_memory:
            self.shared_memory.store_knowledge(
                f"project_{self.current_plan.plan_id}",
                {
                    "requirements": requirements,
                    "plan": self.current_plan.__dict__,
                    "files": dict(current_files),
                    "development_history": [event.__dict__ for event in self.development_history],
                    "completion_time": datetime.now().isoformat()
                }
            )
        
        return current_files
    
    def _build_planning_prompt(self, requirements: Dict[str, Any]) -> str:
        """构建开发计划提示词"""
        prompt = f"""
基于以下需求文档，制定详细的开发计划：

需求文档：
{json.dumps(requirements, ensure_ascii=False, indent=2)}

请生成包含以下信息的开发计划：
1. 任务分解（每个任务包含：类型、描述、预估时间、优先级、依赖关系）
2. 技术栈选择
3. 架构设计要点
4. 关键风险点

输出格式为JSON，包含tasks数组，每个task包含：
- type: 任务类型
- description: 任务描述  
- estimated_hours: 预估时间（小时）
- priority: 优先级（high/medium/low）
- dependencies: 依赖的其他任务
- acceptance_criteria: 验收标准
"""
        return prompt
    
    def _parse_development_plan(self, plan_content: str) -> List[Dict[str, Any]]:
        """解析AI生成的开发计划"""
        try:
            # 尝试从内容中提取JSON
            import re
            json_match = re.search(r'\{.*\}', plan_content, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
                return plan_data.get('tasks', [])
        except Exception as e:
            print(f"解析开发计划失败: {e}")
        
        # 如果解析失败，创建默认计划
        return [
            {
                "type": "basic_implementation",
                "description": "基础功能实现",
                "estimated_hours": 4,
                "priority": "high",
                "dependencies": [],
                "acceptance_criteria": ["功能正常运行", "通过基础测试"]
            }
        ]
    
    def _enhance_prompt_with_history(self, prompt: Prompt, similar_cases: List[Dict[str, Any]]) -> Prompt:
        """使用历史经验增强提示词"""
        if not similar_cases:
            return prompt
        
        history_context = "\n\n=== 相关历史经验 ===\n"
        for i, case in enumerate(similar_cases[:3]):  # 最多使用3个相似案例
            history_context += f"\n案例 {i+1}:\n"
            history_context += f"需求: {case.get('requirements', {}).get('description', 'N/A')}\n"
            history_context += f"解决方案要点: {case.get('key_solutions', 'N/A')}\n"
            history_context += f"注意事项: {case.get('lessons_learned', 'N/A')}\n"
        
        enhanced_text = prompt.text + history_context
        
        return Prompt(
            text=enhanced_text,
            image_urls=prompt.image_urls,
            entrypoint_prompt=prompt.entrypoint_prompt
        )
    
    def _create_improvement_prompt(self, original_prompt: Prompt, files_dict: FilesDict, quality_report) -> Prompt:
        """创建改进提示词"""
        improvement_text = f"""
基于质量分析报告，请改进以下代码：

原始需求：
{original_prompt.text}

当前代码质量评分：{quality_report.overall_score}/100
质量等级：{quality_report.quality_level.value}

发现的问题：
{chr(10).join(f"- {issue['description']}" for issue in quality_report.issues)}

改进建议：
{chr(10).join(f"- {suggestion}" for suggestion in quality_report.suggestions)}

请针对以上问题进行代码改进，确保：
1. 修复所有标识的问题
2. 提高代码质量和可维护性
3. 保持功能完整性
"""
        
        return Prompt(text=improvement_text)
    
    def _create_task_prompt(self, task: Dict[str, Any], requirements: Dict[str, Any]) -> Prompt:
        """为特定任务创建提示词"""
        prompt_text = f"""
当前开发任务：

任务类型：{task['type']}
任务描述：{task['description']}
优先级：{task['priority']}
验收标准：{task.get('acceptance_criteria', [])}

项目需求：
{json.dumps(requirements, ensure_ascii=False, indent=2)}

请实现这个任务，确保：
1. 满足所有验收标准
2. 代码质量高，可维护性好
3. 包含适当的错误处理
4. 添加必要的注释和文档
"""
        
        return Prompt(text=prompt_text)
    
    def _is_development_complete(self) -> bool:
        """检查开发是否完成"""
        if not self.current_plan:
            return False
        
        return self.current_plan.current_task_index >= len(self.current_plan.tasks)
    
    def _record_event(self, event_type: str, description: str, details: Dict[str, Any] = None, 
                     files_affected: List[str] = None, success: bool = True, error_message: str = None):
        """记录开发事件"""
        event = DevelopmentEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type=event_type,
            actor="enhanced_dev_ai",
            description=description,
            details=details or {},
            files_affected=files_affected or [],
            success=success,
            error_message=error_message
        )
        
        self.development_history.append(event)
        
        # 存储到共享记忆
        if self.shared_memory:
            self.shared_memory.store_event(event)
        
        # 通知监管AI
        if self.supervisor_ai:
            self.supervisor_ai.record_development_step(event)
    
    @classmethod
    def with_enhanced_config(
        cls,
        path: str,
        ai: AI = None,
        preprompts_holder: PrepromptsHolder = None,
        supervisor_ai: Optional[BaseSupervisorAI] = None,
        test_ai: Optional[BaseTestAI] = None,
        shared_memory: Optional[BaseSharedMemory] = None
    ):
        """
        使用增强配置创建实例
        
        Args:
            path: 项目路径
            ai: AI实例
            preprompts_holder: 提示词持有者
            supervisor_ai: 监管AI
            test_ai: 测试AI
            shared_memory: 共享记忆
            
        Returns:
            EnhancedDevAI: 增强开发AI实例
        """
        from gpt_engineer.core.default.paths import memory_path
        
        return cls(
            memory=DiskMemory(memory_path(path)),
            execution_env=DiskExecutionEnv(),
            ai=ai,
            preprompts_holder=preprompts_holder,
            supervisor_ai=supervisor_ai,
            test_ai=test_ai,
            shared_memory=shared_memory
        )