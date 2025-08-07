"""
多AI协作开发系统

基于GPT-Engineer的深度集成多AI协作开发平台
"""

__version__ = "1.0.0"
__author__ = "Multi-AI Development Team"
__description__ = "AI-driven collaborative software development platform"

# 主要组件导入
from .orchestrator import MultiAIOrchestrator
from .core.enhanced_dev_ai import EnhancedDevAI
from .ai.supervisor_ai import SupervisorAI
from .ai.test_ai import TestAI
from .ai.deploy_ai import DeployAI
from .memory.shared_memory import SharedMemoryManager
from .deployment.server_interface import ServerAIInterface

# 基础接口导入
from .core.base_interfaces import (
    ProjectResult,
    DevPlan,
    DevelopmentEvent,
    TestResult,
    PackageResult,
    DeployResult,
    QualityReport,
    SupervisionResult,
    TaskStatus,
    QualityLevel
)

__all__ = [
    # 主要组件
    'MultiAIOrchestrator',
    'EnhancedDevAI', 
    'SupervisorAI',
    'TestAI',
    'DeployAI',
    'SharedMemoryManager',
    'ServerAIInterface',
    
    # 数据类型
    'ProjectResult',
    'DevPlan',
    'DevelopmentEvent',
    'TestResult',
    'PackageResult',
    'DeployResult',
    'QualityReport',
    'SupervisionResult',
    'TaskStatus',
    'QualityLevel'
]


def create_orchestrator(work_dir: str = "./multi_ai_project", **kwargs):
    """
    便捷函数：创建多AI编排器实例
    
    Args:
        work_dir: 工作目录
        **kwargs: 其他配置参数
        
    Returns:
        MultiAIOrchestrator: 编排器实例
    """
    return MultiAIOrchestrator(work_dir=work_dir, **kwargs)


def get_version():
    """获取版本信息"""
    return __version__


def get_info():
    """获取系统信息"""
    return {
        'name': '多AI协作开发系统',
        'version': __version__,
        'description': __description__,
        'author': __author__,
        'components': [
            'MultiAIOrchestrator - 多AI编排器',
            'EnhancedDevAI - 增强开发AI',
            'SupervisorAI - 监管AI',
            'TestAI - 测试AI', 
            'DeployAI - 部署AI',
            'SharedMemoryManager - 共享记忆系统',
            'ServerAIInterface - 服务器接口'
        ]
    }