"""
数据模型定义

定义平台中使用的所有数据模型
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass, field


class ProjectStatus(str, Enum):
    """项目状态枚举"""
    DOCUMENT_GENERATION = "document_generation"
    DOCUMENT_REVIEW = "document_review"
    DOCUMENT_CONFIRMED = "document_confirmed"
    DEVELOPMENT_STARTED = "development_started"
    BACKEND_DEVELOPMENT = "backend_development"
    TESTING_BACKEND = "testing_backend"
    FRONTEND_DEVELOPMENT = "frontend_development"
    FRONTEND_REVIEW = "frontend_review"
    INTEGRATION = "integration"
    FINAL_TESTING = "final_testing"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    COMPLETED = "completed"
    FAILED = "failed"


class AIType(str, Enum):
    """AI类型枚举"""
    DOCUMENT_AI = "document_ai"
    DEVELOPMENT_AI = "development_ai"
    SUPERVISOR_AI = "supervisor_ai"
    TEST_AI = "test_ai"
    FRONTEND_AI = "frontend_ai"
    TRANSFER_AI = "transfer_ai"
    DEPLOY_AI = "deploy_ai"
    SERVER_SUPERVISOR_AI = "server_supervisor_ai"
    WEB_TEST_AI = "web_test_ai"


class MessageType(str, Enum):
    """消息类型枚举"""
    USER_REQUEST = "user_request"
    AI_RESPONSE = "ai_response"
    STATUS_UPDATE = "status_update"
    ERROR_NOTIFICATION = "error_notification"
    SYSTEM_NOTIFICATION = "system_notification"


# 基础数据模型
class User(BaseModel):
    """用户模型"""
    id: str
    username: str
    email: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True


class Project(BaseModel):
    """项目模型"""
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.DOCUMENT_GENERATION
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # 项目配置
    domain_preference: Optional[str] = None
    technology_preference: Optional[str] = None
    deployment_config: Optional[Dict[str, Any]] = None
    
    # 项目统计
    total_development_time: float = 0.0
    ai_interactions_count: int = 0
    final_score: Optional[float] = None


class ProjectDocument(BaseModel):
    """项目文档模型"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    project_id: str
    content: str
    version: int = 1
    document_type: str = "requirement"  # requirement, technical, api, etc.
    
    # 文档结构化内容
    requirements: Dict[str, Any] = Field(default_factory=dict)
    technical_specs: Dict[str, Any] = Field(default_factory=dict)
    api_specifications: List[Dict[str, Any]] = Field(default_factory=list)
    database_schema: Optional[Dict[str, Any]] = None
    ui_mockups: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: str = "system"  # system, user, ai
    
    # 审核状态
    review_status: str = "pending"  # pending, approved, needs_revision
    user_feedback: Optional[str] = None


class DevelopmentTask(BaseModel):
    """开发任务模型"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    project_id: str
    task_name: str
    description: str
    task_type: str  # backend, frontend, testing, deployment
    
    # 任务状态
    status: str = "pending"  # pending, in_progress, completed, failed
    priority: int = 1  # 1-5, 1为最高优先级
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    
    # 任务依赖
    dependencies: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    
    # AI信息
    assigned_ai: AIType
    ai_session_id: Optional[str] = None
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 结果
    output_files: List[str] = Field(default_factory=list)
    test_results: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None


class AISession(BaseModel):
    """AI会话模型"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    project_id: str
    ai_type: AIType
    status: str = "active"  # active, paused, completed, failed
    
    # 会话配置
    model_name: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    
    # 会话历史
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    total_tokens_used: int = 0
    total_cost: float = 0.0
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now)
    last_interaction: datetime = Field(default_factory=datetime.now)
    
    # 监控信息
    error_count: int = 0
    last_error: Optional[str] = None
    recovery_attempts: int = 0


class FrontendPreview(BaseModel):
    """前端预览模型"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    project_id: str
    version: int = 1
    
    # 预览内容
    html_content: str
    css_content: str
    js_content: str
    assets: List[str] = Field(default_factory=list)
    
    # 预览配置
    responsive_design: bool = True
    accessibility_compliant: bool = True
    
    # 用户反馈
    user_feedback: Optional[str] = None
    modification_requests: List[Dict[str, Any]] = Field(default_factory=list)
    approval_status: str = "pending"  # pending, approved, needs_revision
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DeploymentStatus(BaseModel):
    """部署状态模型"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    project_id: str
    deployment_type: str = "cloud"  # local, cloud, hybrid
    
    # 部署配置
    server_config: Dict[str, Any] = Field(default_factory=dict)
    domain_config: Dict[str, Any] = Field(default_factory=dict)
    ssl_config: Dict[str, Any] = Field(default_factory=dict)
    
    # 部署状态
    status: str = "pending"  # pending, deploying, deployed, failed
    deployment_url: Optional[str] = None
    
    # 监控信息
    health_check_url: Optional[str] = None
    uptime_percentage: float = 0.0
    response_time_avg: float = 0.0
    
    # 时间信息
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 错误信息
    error_logs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TestReport(BaseModel):
    """测试报告模型"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    project_id: str
    test_type: str  # unit, integration, acceptance, performance
    
    # 测试结果
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    
    # 覆盖率信息
    code_coverage: float = 0.0
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    
    # 性能指标
    execution_time: float = 0.0
    memory_usage: float = 0.0
    
    # 详细结果
    test_details: List[Dict[str, Any]] = Field(default_factory=list)
    error_details: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 质量评分
    quality_score: float = 0.0
    recommendations: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)


class UserRequest(BaseModel):
    """用户请求模型"""
    description: str = Field(..., min_length=10, max_length=5000, description="项目描述")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="具体需求")
    domain_preference: Optional[str] = Field(None, description="域名偏好")
    technology_preference: Optional[str] = Field(None, description="技术栈偏好")
    
    # 项目类型
    project_type: str = Field(default="web_application", description="项目类型")
    complexity_level: str = Field(default="medium", description="复杂度等级")
    
    # 时间和预算
    expected_timeline: Optional[str] = None
    budget_range: Optional[str] = None
    
    # 特殊要求
    special_requirements: List[str] = Field(default_factory=list)
    target_audience: Optional[str] = None


class AIInteraction(BaseModel):
    """AI交互记录模型"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    session_id: str
    project_id: str
    ai_type: AIType
    
    # 交互内容
    user_message: Optional[str] = None
    ai_response: str
    message_type: MessageType
    
    # 元数据
    tokens_used: int = 0
    response_time: float = 0.0
    cost: float = 0.0
    
    # 质量指标
    response_quality: Optional[float] = None
    user_satisfaction: Optional[int] = None  # 1-5星评级
    
    created_at: datetime = Field(default_factory=datetime.now)


class SystemMetrics(BaseModel):
    """系统度量模型"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    
    # 时间范围
    start_time: datetime
    end_time: datetime
    
    # 项目统计
    total_projects: int = 0
    completed_projects: int = 0
    failed_projects: int = 0
    
    # AI使用统计
    total_ai_interactions: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    
    # 性能指标
    avg_project_completion_time: float = 0.0
    avg_code_quality_score: float = 0.0
    avg_user_satisfaction: float = 0.0
    
    # 系统健康度
    system_uptime: float = 0.0
    error_rate: float = 0.0
    avg_response_time: float = 0.0
    
    created_at: datetime = Field(default_factory=datetime.now)


# WebSocket消息模型
class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    sender: str = "system"
    recipient: Optional[str] = None


class ProjectProgress(BaseModel):
    """项目进度模型"""
    project_id: str
    current_stage: str
    completion_percentage: float = 0.0
    
    # 阶段详情
    stages_completed: List[str] = Field(default_factory=list)
    current_stage_details: Dict[str, Any] = Field(default_factory=dict)
    next_stages: List[str] = Field(default_factory=list)
    
    # 时间估算
    estimated_completion_time: Optional[datetime] = None
    actual_time_spent: float = 0.0
    
    # 质量指标
    current_quality_score: float = 0.0
    issues_count: int = 0
    
    last_updated: datetime = Field(default_factory=datetime.now)


# 数据传输对象（DTO）
class CreateProjectDTO(BaseModel):
    """创建项目DTO"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=5000)
    requirements: Dict[str, Any] = Field(default_factory=dict)
    technology_preference: Optional[str] = None
    domain_preference: Optional[str] = None


class UpdateDocumentDTO(BaseModel):
    """更新文档DTO"""
    content: str = Field(..., min_length=1)
    update_type: str = Field(..., pattern="^(manual|ai_assisted|ai_generated)$")
    user_feedback: Optional[str] = None
    section: Optional[str] = None


class FrontendFeedbackDTO(BaseModel):
    """前端反馈DTO"""
    feedback_type: str = Field(..., pattern="^(approve|modify|regenerate)$")
    modifications: Optional[Dict[str, Any]] = None
    user_comments: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=5)


class DeploymentConfigDTO(BaseModel):
    """部署配置DTO"""
    deployment_type: str = Field(default="cloud")
    server_type: str = Field(default="auto")
    domain_name: Optional[str] = None
    ssl_enabled: bool = Field(default=True)
    environment: str = Field(default="production")
    
    # 高级配置
    auto_scaling: bool = Field(default=False)
    backup_enabled: bool = Field(default=True)
    monitoring_enabled: bool = Field(default=True)


# 响应模型
class APIResponse(BaseModel):
    """标准API响应模型"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ProjectCreatedResponse(APIResponse):
    """项目创建响应"""
    project_id: str
    document: ProjectDocument


class DevelopmentStatusResponse(APIResponse):
    """开发状态响应"""
    project_id: str
    status: ProjectStatus
    progress: ProjectProgress
    current_tasks: List[DevelopmentTask]


class FrontendPreviewResponse(APIResponse):
    """前端预览响应"""
    preview: FrontendPreview
    preview_url: str