"""
AI升级管理器

统一管理和协调所有升级版AI的工作
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from gpt_engineer.core.ai import AI
from gpt_engineer.core.files_dict import FilesDict

from .advanced_supervisor_ai import AdvancedSupervisorAI
from .advanced_test_ai import AdvancedTestAI
from .advanced_document_ai import AdvancedDocumentAI
from .advanced_dev_ai import AdvancedDevAI

from ..core.base_interfaces import BaseSharedMemory, DevPlan, TestResult


class AIUpgradeManager:
    """
    AI升级管理器
    
    负责：
    1. 统一管理所有升级版AI
    2. 协调AI之间的协作
    3. 监控AI性能和效果
    4. 提供统一的接口
    """
    
    def __init__(self, ai: AI, shared_memory: Optional[BaseSharedMemory] = None, work_dir: str = "./ai_workspace"):
        self.ai = ai
        self.shared_memory = shared_memory
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        
        # 初始化升级版AI
        self.document_ai = AdvancedDocumentAI(ai, shared_memory)
        self.supervisor_ai = AdvancedSupervisorAI(ai, shared_memory)
        self.test_ai = AdvancedTestAI(ai, str(self.work_dir / "testing"))
        
        # 开发AI需要更多参数，稍后初始化
        self.dev_ai = None
        
        # 管理状态
        self.active_projects: Dict[str, Dict] = {}
        self.ai_performance_metrics: Dict[str, Dict] = {}
        self.collaboration_sessions: Dict[str, Dict] = {}
        
        print("🚀 AI升级管理器已初始化")
        print(f"   - 高级文档AI: ✅")
        print(f"   - 高级监管AI: ✅")
        print(f"   - 高级测试AI: ✅")
        print(f"   - 高级开发AI: 待配置")
    
    def initialize_dev_ai(self, memory, execution_env, preprompts_holder=None):
        """初始化开发AI（需要额外参数）"""
        self.dev_ai = AdvancedDevAI(
            memory=memory,
            execution_env=execution_env,
            ai=self.ai,
            preprompts_holder=preprompts_holder,
            supervisor_ai=self.supervisor_ai,
            test_ai=self.test_ai,
            shared_memory=self.shared_memory
        )
        print("   - 高级开发AI: ✅")
    
    async def create_comprehensive_project(self, user_requirements: str, 
                                         project_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        创建全面的项目
        
        整合所有升级版AI的能力
        """
        project_id = str(uuid.uuid4())
        print(f"🎯 启动全面项目创建: {project_id}")
        
        # 1. 文档AI：需求分析和文档生成
        print("📋 阶段1: 智能需求分析和文档生成")
        requirement_analysis = await self.document_ai.analyze_requirements(
            user_requirements, project_config
        )
        
        project_docs = await self.document_ai.generate_comprehensive_documentation(
            requirement_analysis
        )
        
        # 2. 开发AI：制定开发计划
        print("🗓️ 阶段2: 制定智能开发计划")
        if self.dev_ai:
            dev_plan = await self.dev_ai.plan_development(
                user_requirements, project_config
            )
        else:
            dev_plan = self._create_basic_dev_plan(requirement_analysis)
        
        # 3. 监管AI：启动项目监管
        print("👁️ 阶段3: 启动智能监管")
        supervision_id = await self.supervisor_ai.start_supervision(dev_plan)
        
        # 4. 测试AI：准备测试策略
        print("🧪 阶段4: 制定测试策略")
        # test_strategy = await self.test_ai.create_test_strategy(requirement_analysis)
        
        # 项目初始化
        project_info = {
            "id": project_id,
            "requirements": user_requirements,
            "config": project_config or {},
            "requirement_analysis": requirement_analysis,
            "documents": project_docs,
            "dev_plan": dev_plan,
            "supervision_id": supervision_id,
            # "test_strategy": test_strategy,
            "status": "initialized",
            "created_at": datetime.now(),
            "ai_versions": {
                "document_ai": "advanced_v2.0",
                "dev_ai": "advanced_v2.0", 
                "supervisor_ai": "advanced_v2.0",
                "test_ai": "advanced_v2.0"
            }
        }
        
        self.active_projects[project_id] = project_info
        
        print(f"✅ 项目创建完成: {project_id}")
        print(f"   生成文档: {len(project_docs)} 个")
        print(f"   开发任务: {len(dev_plan.tasks)} 个")
        print(f"   预估时间: {dev_plan.estimated_time} 小时")
        
        return project_info
    
    async def execute_intelligent_development(self, project_id: str) -> Dict[str, Any]:
        """
        执行智能开发流程
        
        协调所有AI进行协作开发
        """
        if project_id not in self.active_projects:
            raise ValueError(f"项目 {project_id} 不存在")
        
        project = self.active_projects[project_id]
        print(f"🚀 开始智能开发: {project_id}")
        
        # 开发结果
        development_results = {
            "project_id": project_id,
            "phases": [],
            "files_generated": {},
            "test_results": [],
            "quality_reports": [],
            "performance_metrics": {}
        }
        
        try:
            # 阶段1: 项目初始化
            if self.dev_ai:
                print("📦 阶段1: 项目初始化")
                initial_files = await self.dev_ai.init(project["requirements"])
                development_results["files_generated"].update(initial_files)
                development_results["phases"].append({
                    "name": "initialization",
                    "status": "completed",
                    "files_count": len(initial_files),
                    "timestamp": datetime.now()
                })
            
            # 阶段2: 代码质量监管
            print("👁️ 阶段2: 代码质量监管")
            if development_results["files_generated"]:
                quality_report = await self.supervisor_ai.analyze_quality(
                    project["supervision_id"],
                    FilesDict(development_results["files_generated"])
                )
                development_results["quality_reports"].append(quality_report)
            
            # 阶段3: 自动化测试
            print("🧪 阶段3: 智能测试生成和执行")
            if development_results["files_generated"]:
                test_files = await self.test_ai.generate_tests(
                    FilesDict(development_results["files_generated"]),
                    project["requirements"]
                )
                
                test_result = await self.test_ai.execute_tests(
                    FilesDict(development_results["files_generated"]),
                    test_files
                )
                development_results["test_results"].append(test_result)
                
                # 将测试文件加入项目文件
                development_results["files_generated"].update(test_files)
            
            # 阶段4: 基于反馈的改进
            if development_results["test_results"] and self.dev_ai:
                print("🔧 阶段4: 基于测试反馈的智能改进")
                latest_test = development_results["test_results"][-1]
                
                if not latest_test.success:
                    # 根据测试结果改进代码
                    feedback = self._generate_improvement_feedback(latest_test)
                    improved_files = await self.dev_ai.improve(
                        FilesDict(development_results["files_generated"]),
                        feedback
                    )
                    development_results["files_generated"].update(improved_files)
                    
                    # 重新测试改进后的代码
                    retest_result = await self.test_ai.execute_tests(
                        FilesDict(development_results["files_generated"]),
                        test_files
                    )
                    development_results["test_results"].append(retest_result)
            
            # 阶段5: 性能优化
            if self.dev_ai:
                print("⚡ 阶段5: 性能优化")
                optimization_result = await self.dev_ai.optimize_performance(
                    FilesDict(development_results["files_generated"])
                )
                development_results["performance_metrics"] = optimization_result
                
                if optimization_result.get("optimized_files"):
                    development_results["files_generated"].update(
                        optimization_result["optimized_files"]
                    )
            
            # 最终质量评估
            print("📊 最终质量评估")
            final_quality = await self.supervisor_ai.analyze_quality(
                project["supervision_id"],
                FilesDict(development_results["files_generated"])
            )
            development_results["quality_reports"].append(final_quality)
            
            # 更新项目状态
            project["status"] = "completed"
            project["development_results"] = development_results
            project["completed_at"] = datetime.now()
            
            print(f"✅ 智能开发完成: {project_id}")
            print(f"   生成文件: {len(development_results['files_generated'])} 个")
            print(f"   测试轮次: {len(development_results['test_results'])} 轮")
            print(f"   最终质量: {final_quality.overall_score:.2f}")
            
        except Exception as e:
            print(f"❌ 开发过程中发生错误: {e}")
            project["status"] = "failed"
            project["error"] = str(e)
            development_results["error"] = str(e)
        
        return development_results
    
    async def collaborative_document_editing(self, project_id: str, participants: List[str]) -> str:
        """启动协作文档编辑"""
        if project_id not in self.active_projects:
            raise ValueError(f"项目 {project_id} 不存在")
        
        # 获取项目的主要文档
        project = self.active_projects[project_id]
        main_doc_id = f"{project_id}_requirements"
        
        # 启动协作会话
        session_id = await self.document_ai.collaborative_editing_session(
            main_doc_id, participants
        )
        
        self.collaboration_sessions[session_id] = {
            "project_id": project_id,
            "document_id": main_doc_id,
            "participants": participants,
            "created_at": datetime.now()
        }
        
        print(f"👥 协作编辑会话已启动: {session_id}")
        return session_id
    
    async def process_collaborative_feedback(self, session_id: str, user_id: str, 
                                           feedback: Dict[str, Any]) -> Dict[str, Any]:
        """处理协作反馈"""
        if session_id not in self.collaboration_sessions:
            raise ValueError(f"协作会话 {session_id} 不存在")
        
        # 处理文档编辑变更
        result = await self.document_ai.process_collaborative_change(
            session_id, user_id, feedback
        )
        
        # 如果有监管AI，也让它评估变更
        if result.get("success"):
            session = self.collaboration_sessions[session_id]
            project_id = session["project_id"]
            
            if project_id in self.active_projects:
                project = self.active_projects[project_id]
                supervision_id = project.get("supervision_id")
                
                if supervision_id:
                    # 监管AI评估变更影响
                    impact_assessment = await self._assess_change_impact(
                        supervision_id, feedback, result
                    )
                    result["impact_assessment"] = impact_assessment
        
        return result
    
    async def get_ai_performance_summary(self) -> Dict[str, Any]:
        """获取AI性能摘要"""
        summary = {
            "document_ai": {
                "sessions_count": len(self.document_ai.documents),
                "translation_support": len(self.document_ai.supported_languages),
                "templates_available": len(self.document_ai.templates)
            },
            "supervisor_ai": {
                "active_supervisions": len(self.supervisor_ai.active_supervisions),
                "monitoring_mode": self.supervisor_ai.monitoring_mode.value,
                "supervision_history": len(self.supervisor_ai.supervision_history)
            },
            "test_ai": {
                "supported_frameworks": len(self.test_ai.test_frameworks),
                "test_history": len(self.test_ai.test_history),
                "optimization_suggestions": len(self.test_ai.optimization_suggestions)
            },
            "dev_ai": {
                "supported_languages": len(self.dev_ai.supported_languages) if self.dev_ai else 0,
                "metrics_history": len(self.dev_ai.code_metrics_history) if self.dev_ai else 0,
                "debugging_sessions": len(self.dev_ai.debugging_sessions) if self.dev_ai else 0
            },
            "overall": {
                "active_projects": len(self.active_projects),
                "collaboration_sessions": len(self.collaboration_sessions),
                "upgrade_version": "v2.0"
            }
        }
        
        return summary
    
    async def diagnose_and_fix_issues(self, project_id: str, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """诊断并修复项目问题"""
        if project_id not in self.active_projects:
            raise ValueError(f"项目 {project_id} 不存在")
        
        project = self.active_projects[project_id]
        print(f"🔧 诊断项目问题: {project_id}")
        
        diagnosis_result = {
            "project_id": project_id,
            "error_analysis": {},
            "fix_recommendations": [],
            "applied_fixes": {},
            "success": False
        }
        
        try:
            # 1. 开发AI诊断代码问题
            if self.dev_ai and "files" in project.get("development_results", {}):
                files = FilesDict(project["development_results"]["files_generated"])
                debug_result = await self.dev_ai.debug_code(files, error_info)
                diagnosis_result["error_analysis"] = debug_result
                diagnosis_result["applied_fixes"]["code_fixes"] = debug_result.get("fixed_files", {})
            
            # 2. 监管AI分析质量问题
            supervision_id = project.get("supervision_id")
            if supervision_id:
                failure_analysis = await self.supervisor_ai.handle_failure(
                    supervision_id, Exception(error_info.get("message", "Unknown error")), error_info
                )
                diagnosis_result["error_analysis"]["supervision_analysis"] = failure_analysis
                diagnosis_result["fix_recommendations"].extend(
                    failure_analysis.get("prevention_measures", [])
                )
            
            # 3. 测试AI验证修复
            if diagnosis_result["applied_fixes"].get("code_fixes"):
                fixed_files = FilesDict(diagnosis_result["applied_fixes"]["code_fixes"])
                verification_tests = await self.test_ai.generate_tests(fixed_files)
                verification_result = await self.test_ai.execute_tests(fixed_files, verification_tests)
                
                diagnosis_result["applied_fixes"]["verification_result"] = verification_result
                diagnosis_result["success"] = verification_result.success
            
            print(f"✅ 问题诊断完成，成功率: {diagnosis_result['success']}")
            
        except Exception as e:
            diagnosis_result["error"] = str(e)
            print(f"❌ 诊断过程中发生错误: {e}")
        
        return diagnosis_result
    
    def _create_basic_dev_plan(self, requirement_analysis: Dict) -> DevPlan:
        """创建基础开发计划（当开发AI未初始化时）"""
        return DevPlan(
            tasks=["项目初始化", "核心功能开发", "测试", "优化"],
            estimated_time=40.0,  # 小时
            dependencies={},
            milestones=["MVP完成", "测试通过", "部署就绪"],
            risks={"overall_risk": "medium"}
        )
    
    def _generate_improvement_feedback(self, test_result: TestResult) -> str:
        """基于测试结果生成改进反馈"""
        feedback_parts = []
        
        if test_result.failed_tests > 0:
            feedback_parts.append(f"修复 {test_result.failed_tests} 个失败的测试")
        
        if test_result.coverage_percentage < 0.8:
            feedback_parts.append(f"提升测试覆盖率至80%以上（当前：{test_result.coverage_percentage:.1%}）")
        
        if hasattr(test_result, 'performance_issues') and test_result.performance_issues:
            feedback_parts.append("优化性能问题")
        
        if hasattr(test_result, 'security_findings') and test_result.security_findings:
            feedback_parts.append("修复安全问题")
        
        return "; ".join(feedback_parts) if feedback_parts else "继续优化代码质量"
    
    async def _assess_change_impact(self, supervision_id: str, change: Dict, result: Dict) -> Dict[str, Any]:
        """评估变更影响"""
        return {
            "impact_level": "low",
            "affected_areas": [],
            "recommendations": []
        }


# 使用示例
async def main():
    """升级版AI系统使用示例"""
    from gpt_engineer.core.ai import AI
    
    # 初始化AI和管理器
    ai = AI(model_name="gpt-4o", temperature=0.1)
    upgrade_manager = AIUpgradeManager(ai)
    
    # 示例：创建一个复杂项目
    user_requirements = """
    创建一个在线博客平台，包含以下功能：
    1. 用户注册和登录
    2. 文章发布和编辑
    3. 评论系统
    4. 标签和分类
    5. 搜索功能
    6. 管理后台
    7. 响应式设计
    8. 性能优化
    9. 安全防护
    """
    
    # 创建项目
    project = await upgrade_manager.create_comprehensive_project(
        user_requirements,
        {"complexity": "medium", "timeline": "2 weeks"}
    )
    
    print(f"项目创建完成: {project['id']}")
    
    # 执行开发
    development_result = await upgrade_manager.execute_intelligent_development(project['id'])
    
    print("开发完成!")
    print(f"生成文件数: {len(development_result['files_generated'])}")
    print(f"测试轮次: {len(development_result['test_results'])}")


if __name__ == "__main__":
    asyncio.run(main())