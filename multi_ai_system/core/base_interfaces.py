"""
多AI协作系统的基础接口定义

本模块定义了多AI系统中各个AI角色的基础接口，包括：
- 监管AI接口
- 测试AI接口  
- 部署AI接口
- 共享记忆接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from gpt_engineer.core.files_dict import FilesDict
from gpt_engineer.core.prompt import Prompt


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class QualityLevel(Enum):
    """质量等级枚举"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class DevelopmentEvent:
    """开发事件数据类"""
    event_id: str
    timestamp: datetime
    event_type: str  # "code_generation", "test_execution", "quality_check", etc.
    actor: str  # "dev_ai", "test_ai", "supervisor_ai", etc.
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    files_affected: List[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class QualityReport:
    """代码质量报告"""
    overall_score: float  # 0-100
    quality_level: QualityLevel
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestResult:
    """测试结果数据类"""
    test_id: str
    passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    coverage_percentage: float
    execution_time: float
    test_details: List[Dict[str, Any]] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PackageResult:
    """打包结果数据类"""
    package_path: Path
    package_type: str  # "docker", "pip", "npm", etc.
    version: str
    dependencies: List[str] = field(default_factory=list)
    size_mb: float = 0.0
    build_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class DeployResult:
    """部署结果数据类"""
    deployment_id: str
    url: Optional[str] = None
    status: str = "pending"  # "pending", "deploying", "deployed", "failed"
    server_info: Dict[str, Any] = field(default_factory=dict)
    deployment_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class SupervisionResult:
    """监管结果数据类"""
    supervision_id: str
    quality_report: QualityReport
    recommendations: List[str] = field(default_factory=list)
    risk_warnings: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    approval_required: bool = False


@dataclass
class DevPlan:
    """开发计划数据类"""
    plan_id: str
    requirements: Dict[str, Any]
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    current_task_index: int = 0
    estimated_time: float = 0.0
    actual_time: float = 0.0
    completion_percentage: float = 0.0
    status: TaskStatus = TaskStatus.PENDING
    
    @property
    def current_task(self) -> Optional[Dict[str, Any]]:
        """获取当前任务"""
        if 0 <= self.current_task_index < len(self.tasks):
            return self.tasks[self.current_task_index]
        return None
    
    def mark_task_complete(self):
        """标记当前任务为完成"""
        if self.current_task:
            self.current_task['status'] = TaskStatus.COMPLETED.value
            self.current_task_index += 1
            self._update_completion_percentage()
    
    def add_fixes(self, issues: List[str]):
        """添加修复任务"""
        for issue in issues:
            fix_task = {
                'type': 'bug_fix',
                'description': f"修复问题: {issue}",
                'priority': 'high',
                'status': TaskStatus.PENDING.value
            }
            # 在当前任务后插入修复任务
            self.tasks.insert(self.current_task_index + 1, fix_task)
    
    def _update_completion_percentage(self):
        """更新完成百分比"""
        completed_tasks = sum(1 for task in self.tasks if task.get('status') == TaskStatus.COMPLETED.value)
        self.completion_percentage = (completed_tasks / len(self.tasks)) * 100 if self.tasks else 0


class BaseSupervisorAI(ABC):
    """监管AI基础接口"""
    
    @abstractmethod
    def start_supervision(self, dev_plan: DevPlan) -> str:
        """开始监督开发过程"""
        pass
    
    @abstractmethod
    def monitor_development(self, dev_plan: DevPlan, code_changes: FilesDict) -> SupervisionResult:
        """监督开发过程"""
        pass
    
    @abstractmethod
    def record_development_step(self, event: DevelopmentEvent) -> None:
        """记录开发步骤"""
        pass
    
    @abstractmethod
    def analyze_quality(self, files_dict: FilesDict) -> QualityReport:
        """分析代码质量"""
        pass
    
    @abstractmethod
    def analyze_issues(self, test_result: TestResult) -> List[str]:
        """分析测试失败问题"""
        pass
    
    @abstractmethod
    def get_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """获取改进建议"""
        pass


class BaseTestAI(ABC):
    """测试AI基础接口"""
    
    @abstractmethod
    def generate_tests(self, files_dict: FilesDict, requirements: Dict[str, Any]) -> FilesDict:
        """生成测试用例"""
        pass
    
    @abstractmethod
    def execute_tests(self, files_dict: FilesDict) -> TestResult:
        """执行测试"""
        pass
    
    @abstractmethod
    def analyze_coverage(self, test_result: TestResult) -> Dict[str, float]:
        """分析测试覆盖率"""
        pass
    
    @abstractmethod
    def diagnose_failures(self, test_result: TestResult, files_dict: FilesDict) -> List[str]:
        """诊断测试失败原因"""
        pass
    
    @abstractmethod
    def final_evaluation(self, deploy_result: DeployResult) -> float:
        """最终评分"""
        pass


class BaseDeployAI(ABC):
    """部署AI基础接口"""
    
    @abstractmethod
    def package_project(self, files_dict: FilesDict, config: Dict[str, Any]) -> PackageResult:
        """打包项目"""
        pass
    
    @abstractmethod
    def upload_to_server(self, package: PackageResult, server_config: Dict[str, Any]) -> DeployResult:
        """上传到服务器"""
        pass
    
    @abstractmethod
    def monitor_deployment(self, deploy_result: DeployResult) -> Dict[str, Any]:
        """监控部署状态"""
        pass
    
    @abstractmethod
    def generate_deployment_config(self, files_dict: FilesDict) -> Dict[str, Any]:
        """生成部署配置"""
        pass


class BaseSharedMemory(ABC):
    """共享记忆基础接口"""
    
    @abstractmethod
    def store_event(self, event: DevelopmentEvent) -> None:
        """存储开发事件"""
        pass
    
    @abstractmethod
    def retrieve_events(self, filters: Dict[str, Any]) -> List[DevelopmentEvent]:
        """检索开发事件"""
        pass
    
    @abstractmethod
    def store_knowledge(self, key: str, knowledge: Dict[str, Any]) -> None:
        """存储知识"""
        pass
    
    @abstractmethod
    def retrieve_knowledge(self, key: str) -> Optional[Dict[str, Any]]:
        """检索知识"""
        pass
    
    @abstractmethod
    def find_similar_cases(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查找相似案例"""
        pass
    
    @abstractmethod
    def update_project_state(self, project_id: str, state: Dict[str, Any]) -> None:
        """更新项目状态"""
        pass
    
    @abstractmethod
    def get_project_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """获取项目状态"""
        pass


@dataclass
class ProjectResult:
    """项目结果数据类"""
    project_id: str
    files: FilesDict
    deployment: Optional[DeployResult] = None
    test_results: List[TestResult] = field(default_factory=list)
    quality_reports: List[QualityReport] = field(default_factory=list)
    final_score: float = 0.0
    development_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)