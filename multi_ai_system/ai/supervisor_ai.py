"""
监管AI实现

负责监督开发过程、质量控制、记忆管理和风险预警
"""

import ast
import json
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from gpt_engineer.core.ai import AI
from gpt_engineer.core.files_dict import FilesDict

from ..core.base_interfaces import (
    BaseSupervisorAI, BaseSharedMemory, DevPlan, DevelopmentEvent,
    SupervisionResult, QualityReport, QualityLevel, TestResult
)


class SupervisorAI(BaseSupervisorAI):
    """
    监管AI实现
    
    功能：
    - 代码质量分析
    - 开发进度监控
    - 风险预警
    - 记忆管理
    - 改进建议
    """
    
    def __init__(self, ai: AI, shared_memory: Optional[BaseSharedMemory] = None):
        self.ai = ai
        self.shared_memory = shared_memory
        self.active_supervisions: Dict[str, Dict] = {}
        self.quality_rules = self._load_quality_rules()
        self.risk_patterns = self._load_risk_patterns()
    
    def start_supervision(self, dev_plan: DevPlan) -> str:
        """
        开始监督开发过程
        
        Args:
            dev_plan: 开发计划
            
        Returns:
            str: 监督会话ID
        """
        supervision_id = str(uuid.uuid4())
        
        self.active_supervisions[supervision_id] = {
            "plan": dev_plan,
            "start_time": datetime.now(),
            "events": [],
            "quality_history": [],
            "risk_warnings": [],
            "recommendations": []
        }
        
        # 分析开发计划的风险点
        initial_risks = self._analyze_plan_risks(dev_plan)
        if initial_risks:
            self.active_supervisions[supervision_id]["risk_warnings"].extend(initial_risks)
        
        # 记录监督开始事件
        self._record_supervision_event(
            supervision_id,
            "supervision_started",
            f"开始监督项目 {dev_plan.plan_id}",
            {"plan_id": dev_plan.plan_id, "tasks_count": len(dev_plan.tasks)}
        )
        
        return supervision_id
    
    def monitor_development(self, dev_plan: DevPlan, code_changes: FilesDict) -> SupervisionResult:
        """
        监督开发过程
        
        Args:
            dev_plan: 开发计划
            code_changes: 代码变更
            
        Returns:
            SupervisionResult: 监督结果
        """
        supervision_id = self._find_supervision_id(dev_plan.plan_id)
        
        # 分析代码质量
        quality_report = self.analyze_quality(code_changes)
        
        # 检查进度合理性
        progress_analysis = self._analyze_progress(dev_plan)
        
        # 检测风险
        current_risks = self._detect_risks(code_changes, dev_plan)
        
        # 生成建议
        recommendations = self._generate_recommendations(
            quality_report, progress_analysis, current_risks
        )
        
        supervision_result = SupervisionResult(
            supervision_id=supervision_id,
            quality_report=quality_report,
            recommendations=recommendations,
            risk_warnings=current_risks,
            next_actions=self._suggest_next_actions(dev_plan, quality_report),
            approval_required=quality_report.quality_level in [QualityLevel.POOR, QualityLevel.CRITICAL]
        )
        
        # 更新监督状态
        if supervision_id and supervision_id in self.active_supervisions:
            session = self.active_supervisions[supervision_id]
            session["quality_history"].append(quality_report)
            session["recommendations"].extend(recommendations)
            session["risk_warnings"].extend(current_risks)
        
        return supervision_result
    
    def record_development_step(self, event: DevelopmentEvent) -> None:
        """
        记录开发步骤
        
        Args:
            event: 开发事件
        """
        # 存储到共享记忆
        if self.shared_memory:
            self.shared_memory.store_event(event)
        
        # 分析事件模式
        self._analyze_event_patterns(event)
        
        # 更新活跃监督会话
        for supervision_id, session in self.active_supervisions.items():
            session["events"].append(event)
    
    def analyze_quality(self, files_dict: FilesDict) -> QualityReport:
        """
        分析代码质量
        
        Args:
            files_dict: 代码文件
            
        Returns:
            QualityReport: 质量报告
        """
        issues = []
        suggestions = []
        metrics = {}
        
        # 分析每个文件
        for filename, content in files_dict.items():
            file_issues, file_metrics = self._analyze_file_quality(filename, content)
            issues.extend(file_issues)
            metrics[filename] = file_metrics
        
        # 整体质量分析
        overall_issues = self._analyze_overall_quality(files_dict)
        issues.extend(overall_issues)
        
        # 使用AI进行深度质量分析
        ai_analysis = self._ai_quality_analysis(files_dict)
        if ai_analysis:
            issues.extend(ai_analysis.get('issues', []))
            suggestions.extend(ai_analysis.get('suggestions', []))
        
        # 计算总体评分
        overall_score = self._calculate_quality_score(issues, metrics)
        quality_level = self._determine_quality_level(overall_score)
        
        return QualityReport(
            overall_score=overall_score,
            quality_level=quality_level,
            issues=issues,
            suggestions=suggestions,
            metrics=metrics
        )
    
    def analyze_issues(self, test_result: TestResult) -> List[str]:
        """
        分析测试失败问题
        
        Args:
            test_result: 测试结果
            
        Returns:
            List[str]: 问题列表
        """
        issues = []
        
        # 分析错误消息
        for error_msg in test_result.error_messages:
            issue_analysis = self._analyze_error_message(error_msg)
            if issue_analysis:
                issues.append(issue_analysis)
        
        # 分析测试覆盖率
        if test_result.coverage_percentage < 80:
            issues.append(f"测试覆盖率过低({test_result.coverage_percentage:.1f}%)，建议增加测试用例")
        
        # 使用AI分析复杂问题
        if test_result.error_messages:
            ai_analysis = self._ai_error_analysis(test_result.error_messages)
            if ai_analysis:
                issues.extend(ai_analysis)
        
        return issues
    
    def get_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """
        获取改进建议
        
        Args:
            context: 上下文信息
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        # 基于历史数据的建议
        if self.shared_memory:
            similar_cases = self.shared_memory.find_similar_cases(context)
            for case in similar_cases:
                if case.get('lessons_learned'):
                    recommendations.append(f"历史经验: {case['lessons_learned']}")
        
        # 基于当前状态的建议
        if 'quality_score' in context and context['quality_score'] < 70:
            recommendations.append("建议重构代码以提高质量")
        
        if 'test_coverage' in context and context['test_coverage'] < 80:
            recommendations.append("建议增加测试用例以提高覆盖率")
        
        return recommendations
    
    def _load_quality_rules(self) -> Dict[str, Any]:
        """加载代码质量规则"""
        return {
            'max_function_length': 50,
            'max_file_length': 500,
            'max_complexity': 10,
            'min_docstring_coverage': 80,
            'required_patterns': ['error_handling', 'input_validation'],
            'forbidden_patterns': ['hardcoded_secrets', 'sql_injection_risk']
        }
    
    def _load_risk_patterns(self) -> Dict[str, List[str]]:
        """加载风险模式"""
        return {
            'security_risks': [
                r'password\s*=\s*["\'][^"\']+["\']',  # 硬编码密码
                r'api_key\s*=\s*["\'][^"\']+["\']',   # 硬编码API密钥
                r'eval\s*\(',                          # eval使用
                r'exec\s*\(',                          # exec使用
            ],
            'performance_risks': [
                r'for.*in.*range\(len\(',             # 低效循环
                r'\.append\(.*\)\s*\n.*for',          # 循环中的append
            ],
            'maintainability_risks': [
                r'def\s+\w+\([^)]*\):\s*\n(\s*.*\n){50,}',  # 过长函数
                r'class\s+\w+.*:\s*\n(\s*.*\n){200,}',      # 过长类
            ]
        }
    
    def _analyze_plan_risks(self, dev_plan: DevPlan) -> List[str]:
        """分析开发计划的风险点"""
        risks = []
        
        # 检查任务数量
        if len(dev_plan.tasks) > 20:
            risks.append("任务数量过多，建议分阶段开发")
        
        # 检查时间估算
        total_hours = sum(task.get('estimated_hours', 1) for task in dev_plan.tasks)
        if total_hours > 100:
            risks.append(f"预估工作量过大({total_hours}小时)，建议重新评估")
        
        # 检查依赖关系
        complex_dependencies = [
            task for task in dev_plan.tasks
            if len(task.get('dependencies', [])) > 3
        ]
        if complex_dependencies:
            risks.append("存在复杂的任务依赖关系，可能影响开发进度")
        
        return risks
    
    def _analyze_file_quality(self, filename: str, content: str) -> tuple[List[Dict], Dict[str, float]]:
        """分析单个文件的质量"""
        issues = []
        metrics = {}
        
        # 基本度量
        lines = content.split('\n')
        metrics['lines_count'] = len(lines)
        metrics['blank_lines'] = sum(1 for line in lines if not line.strip())
        metrics['comment_lines'] = sum(1 for line in lines if line.strip().startswith('#'))
        
        # Python文件特定分析
        if filename.endswith('.py'):
            try:
                tree = ast.parse(content)
                
                # 分析函数复杂度
                functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                if functions:
                    func_lengths = []
                    for func in functions:
                        func_lines = func.end_lineno - func.lineno if hasattr(func, 'end_lineno') else 0
                        func_lengths.append(func_lines)
                        
                        if func_lines > self.quality_rules['max_function_length']:
                            issues.append({
                                'type': 'function_too_long',
                                'description': f"函数 {func.name} 过长({func_lines}行)",
                                'severity': 'medium',
                                'line': func.lineno
                            })
                    
                    metrics['avg_function_length'] = sum(func_lengths) / len(func_lengths)
                    metrics['max_function_length'] = max(func_lengths)
                
                # 检查文档字符串
                docstring_count = sum(1 for node in ast.walk(tree) 
                                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)) 
                                    and ast.get_docstring(node))
                total_functions_classes = len([node for node in ast.walk(tree) 
                                             if isinstance(node, (ast.FunctionDef, ast.ClassDef))])
                
                if total_functions_classes > 0:
                    docstring_coverage = (docstring_count / total_functions_classes) * 100
                    metrics['docstring_coverage'] = docstring_coverage
                    
                    if docstring_coverage < self.quality_rules['min_docstring_coverage']:
                        issues.append({
                            'type': 'low_docstring_coverage',
                            'description': f"文档字符串覆盖率低({docstring_coverage:.1f}%)",
                            'severity': 'low',
                            'line': 1
                        })
            
            except SyntaxError as e:
                issues.append({
                    'type': 'syntax_error',
                    'description': f"语法错误: {str(e)}",
                    'severity': 'critical',
                    'line': e.lineno or 1
                })
        
        # 检查风险模式
        for risk_type, patterns in self.risk_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        'type': risk_type,
                        'description': f"检测到{risk_type.replace('_', ' ')}: {match.group()}",
                        'severity': 'high' if 'security' in risk_type else 'medium',
                        'line': line_num
                    })
        
        return issues, metrics
    
    def _analyze_overall_quality(self, files_dict: FilesDict) -> List[Dict]:
        """分析整体质量"""
        issues = []
        
        # 检查项目结构
        python_files = [f for f in files_dict.keys() if f.endswith('.py')]
        
        if len(python_files) == 1 and len(files_dict) > 1:
            issues.append({
                'type': 'structure_issue',
                'description': "建议将代码拆分为多个模块",
                'severity': 'low',
                'line': 1
            })
        
        # 检查配置文件
        config_files = ['requirements.txt', 'setup.py', 'pyproject.toml', 'Dockerfile']
        missing_configs = [f for f in config_files if f not in files_dict]
        
        if 'requirements.txt' in missing_configs and 'pyproject.toml' in missing_configs:
            issues.append({
                'type': 'missing_dependencies',
                'description': "缺少依赖配置文件",
                'severity': 'medium',
                'line': 1
            })
        
        return issues
    
    def _ai_quality_analysis(self, files_dict: FilesDict) -> Optional[Dict]:
        """使用AI进行深度质量分析"""
        try:
            # 构建分析提示
            code_summary = self._create_code_summary(files_dict)
            
            prompt = f"""
作为代码质量专家，请分析以下代码的质量：

{code_summary}

请从以下角度进行分析：
1. 代码架构和设计模式
2. 错误处理和异常管理
3. 性能优化潜力
4. 安全性考虑
5. 可维护性和可扩展性

返回JSON格式的分析结果，包含：
- issues: 发现的问题列表（每个问题包含type, description, severity）
- suggestions: 改进建议列表
- strengths: 代码的优点
"""
            
            messages = self.ai.start(
                system="你是一个专业的代码质量分析师，专门分析Python代码质量。",
                user=prompt,
                step_name="ai_quality_analysis"
            )
            
            analysis_text = messages[-1].content.strip()
            
            # 尝试解析JSON结果
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            print(f"AI质量分析失败: {e}")
        
        return None
    
    def _ai_error_analysis(self, error_messages: List[str]) -> List[str]:
        """使用AI分析错误消息"""
        try:
            errors_text = "\n".join(error_messages)
            
            prompt = f"""
请分析以下测试错误信息，并提供解决建议：

错误信息：
{errors_text}

请提供：
1. 错误的根本原因
2. 具体的修复建议
3. 预防类似问题的方法

以简洁的列表形式返回建议。
"""
            
            messages = self.ai.start(
                system="你是一个专业的调试专家，帮助分析和解决代码错误。",
                user=prompt,
                step_name="ai_error_analysis"
            )
            
            analysis = messages[-1].content.strip()
            
            # 提取建议列表
            suggestions = []
            for line in analysis.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    suggestions.append(line.lstrip('-•1234567890. '))
            
            return suggestions[:5]  # 最多返回5个建议
            
        except Exception as e:
            print(f"AI错误分析失败: {e}")
            return []
    
    def _create_code_summary(self, files_dict: FilesDict) -> str:
        """创建代码摘要"""
        summary = "代码文件列表：\n"
        
        for filename, content in files_dict.items():
            lines = len(content.split('\n'))
            summary += f"- {filename} ({lines} 行)\n"
            
            # 添加关键信息摘要
            if filename.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                    
                    if functions:
                        summary += f"  函数: {', '.join(functions[:5])}\n"
                    if classes:
                        summary += f"  类: {', '.join(classes[:5])}\n"
                except:
                    pass
        
        return summary
    
    def _calculate_quality_score(self, issues: List[Dict], metrics: Dict) -> float:
        """计算质量评分"""
        base_score = 100.0
        
        # 扣分规则
        for issue in issues:
            severity = issue.get('severity', 'low')
            if severity == 'critical':
                base_score -= 20
            elif severity == 'high':
                base_score -= 10
            elif severity == 'medium':
                base_score -= 5
            else:  # low
                base_score -= 2
        
        # 基于度量的调整
        for file_metrics in metrics.values():
            if isinstance(file_metrics, dict):
                # 文档字符串覆盖率奖励
                if 'docstring_coverage' in file_metrics:
                    coverage = file_metrics['docstring_coverage']
                    if coverage >= 90:
                        base_score += 5
                    elif coverage >= 70:
                        base_score += 2
        
        return max(0.0, min(100.0, base_score))
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """确定质量等级"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 75:
            return QualityLevel.GOOD
        elif score >= 60:
            return QualityLevel.ACCEPTABLE
        elif score >= 40:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def _analyze_progress(self, dev_plan: DevPlan) -> Dict[str, Any]:
        """分析开发进度"""
        return {
            "completion_percentage": dev_plan.completion_percentage,
            "current_task": dev_plan.current_task_index,
            "total_tasks": len(dev_plan.tasks),
            "is_on_track": dev_plan.completion_percentage >= (dev_plan.current_task_index / len(dev_plan.tasks)) * 100
        }
    
    def _detect_risks(self, code_changes: FilesDict, dev_plan: DevPlan) -> List[str]:
        """检测当前风险"""
        risks = []
        
        # 检查代码量风险
        total_lines = sum(len(content.split('\n')) for content in code_changes.values())
        if total_lines > 1000 and dev_plan.completion_percentage < 50:
            risks.append("代码量增长过快，可能影响质量")
        
        # 检查文件数量风险
        if len(code_changes) > 20:
            risks.append("文件数量过多，建议重构项目结构")
        
        return risks
    
    def _generate_recommendations(self, quality_report: QualityReport, 
                                progress_analysis: Dict, current_risks: List[str]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于质量报告的建议
        if quality_report.quality_level in [QualityLevel.POOR, QualityLevel.CRITICAL]:
            recommendations.append("代码质量需要改进，建议重构")
        
        if quality_report.issues:
            high_priority_issues = [i for i in quality_report.issues if i.get('severity') in ['critical', 'high']]
            if high_priority_issues:
                recommendations.append(f"优先修复{len(high_priority_issues)}个高优先级问题")
        
        # 基于进度的建议
        if not progress_analysis["is_on_track"]:
            recommendations.append("开发进度落后，建议调整计划或增加资源")
        
        # 基于风险的建议
        if current_risks:
            recommendations.append("注意当前风险点，采取预防措施")
        
        return recommendations
    
    def _suggest_next_actions(self, dev_plan: DevPlan, quality_report: QualityReport) -> List[str]:
        """建议下一步行动"""
        actions = []
        
        if quality_report.quality_level in [QualityLevel.POOR, QualityLevel.CRITICAL]:
            actions.append("立即进行代码质量改进")
        
        if dev_plan.current_task:
            actions.append(f"继续执行当前任务: {dev_plan.current_task.get('description', 'N/A')}")
        
        if quality_report.issues:
            critical_issues = [i for i in quality_report.issues if i.get('severity') == 'critical']
            if critical_issues:
                actions.append("修复关键问题")
        
        return actions
    
    def _find_supervision_id(self, plan_id: str) -> Optional[str]:
        """查找监督会话ID"""
        for supervision_id, session in self.active_supervisions.items():
            if session["plan"].plan_id == plan_id:
                return supervision_id
        return None
    
    def _record_supervision_event(self, supervision_id: str, event_type: str, 
                                description: str, details: Dict[str, Any] = None):
        """记录监督事件"""
        event = DevelopmentEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type=event_type,
            actor="supervisor_ai",
            description=description,
            details=details or {}
        )
        
        if supervision_id in self.active_supervisions:
            self.active_supervisions[supervision_id]["events"].append(event)
        
        if self.shared_memory:
            self.shared_memory.store_event(event)
    
    def _analyze_event_patterns(self, event: DevelopmentEvent):
        """分析事件模式，发现潜在问题"""
        # 这里可以实现复杂的模式分析逻辑
        # 例如：频繁的测试失败、重复的错误类型等
        pass
    
    def _analyze_error_message(self, error_msg: str) -> Optional[str]:
        """分析单个错误消息"""
        # 常见错误模式匹配
        if "ModuleNotFoundError" in error_msg:
            return "缺少必要的模块依赖，请检查import语句和requirements.txt"
        elif "AttributeError" in error_msg:
            return "属性错误，检查对象是否具有调用的属性或方法"
        elif "TypeError" in error_msg:
            return "类型错误，检查函数参数类型和返回值类型"
        elif "IndentationError" in error_msg:
            return "缩进错误，检查代码缩进格式"
        elif "NameError" in error_msg:
            return "名称错误，检查变量是否已定义"
        
        return None