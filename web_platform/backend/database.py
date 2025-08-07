"""
数据库管理器

负责所有数据库操作，包括项目、文档、任务等数据的存储和检索
"""

import json
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from .models import (
    User, Project, ProjectDocument, DevelopmentTask, 
    AISession, FrontendPreview, DeploymentStatus, TestReport,
    ProjectStatus, AIType
)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "web_platform.db"):
        self.db_path = Path(db_path)
        self.connection_pool = {}
        self._init_lock = asyncio.Lock()
    
    async def initialize(self):
        """初始化数据库"""
        async with self._init_lock:
            await self._create_tables()
            print("✅ 数据库初始化完成")
    
    async def _create_tables(self):
        """创建数据库表"""
        sql_statements = [
            # 用户表
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
            """,
            
            # 项目表
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'document_generation',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                domain_preference TEXT,
                technology_preference TEXT,
                deployment_config TEXT,
                total_development_time REAL DEFAULT 0.0,
                ai_interactions_count INTEGER DEFAULT 0,
                final_score REAL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            
            # 项目文档表
            """
            CREATE TABLE IF NOT EXISTS project_documents (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                content TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                document_type TEXT DEFAULT 'requirement',
                requirements TEXT,
                technical_specs TEXT,
                api_specifications TEXT,
                database_schema TEXT,
                ui_mockups TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT DEFAULT 'system',
                review_status TEXT DEFAULT 'pending',
                user_feedback TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
            """,
            
            # 开发任务表
            """
            CREATE TABLE IF NOT EXISTS development_tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                task_name TEXT NOT NULL,
                description TEXT NOT NULL,
                task_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 1,
                estimated_hours REAL DEFAULT 0.0,
                actual_hours REAL DEFAULT 0.0,
                dependencies TEXT,
                blockers TEXT,
                assigned_ai TEXT NOT NULL,
                ai_session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                output_files TEXT,
                test_results TEXT,
                quality_score REAL,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
            """,
            
            # AI会话表
            """
            CREATE TABLE IF NOT EXISTS ai_sessions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                ai_type TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                model_name TEXT DEFAULT 'gpt-4o',
                temperature REAL DEFAULT 0.1,
                max_tokens INTEGER,
                messages TEXT,
                total_tokens_used INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_count INTEGER DEFAULT 0,
                last_error TEXT,
                recovery_attempts INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
            """,
            
            # 前端预览表
            """
            CREATE TABLE IF NOT EXISTS frontend_previews (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                html_content TEXT NOT NULL,
                css_content TEXT NOT NULL,
                js_content TEXT NOT NULL,
                assets TEXT,
                responsive_design BOOLEAN DEFAULT TRUE,
                accessibility_compliant BOOLEAN DEFAULT TRUE,
                user_feedback TEXT,
                modification_requests TEXT,
                approval_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
            """,
            
            # 部署状态表
            """
            CREATE TABLE IF NOT EXISTS deployment_status (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                deployment_type TEXT DEFAULT 'cloud',
                server_config TEXT,
                domain_config TEXT,
                ssl_config TEXT,
                status TEXT DEFAULT 'pending',
                deployment_url TEXT,
                health_check_url TEXT,
                uptime_percentage REAL DEFAULT 0.0,
                response_time_avg REAL DEFAULT 0.0,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_logs TEXT,
                warnings TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
            """,
            
            # 测试报告表
            """
            CREATE TABLE IF NOT EXISTS test_reports (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                test_type TEXT NOT NULL,
                total_tests INTEGER DEFAULT 0,
                passed_tests INTEGER DEFAULT 0,
                failed_tests INTEGER DEFAULT 0,
                skipped_tests INTEGER DEFAULT 0,
                code_coverage REAL DEFAULT 0.0,
                line_coverage REAL DEFAULT 0.0,
                branch_coverage REAL DEFAULT 0.0,
                execution_time REAL DEFAULT 0.0,
                memory_usage REAL DEFAULT 0.0,
                test_details TEXT,
                error_details TEXT,
                quality_score REAL DEFAULT 0.0,
                recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
            """
        ]
        
        # 创建索引
        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects (status)",
            "CREATE INDEX IF NOT EXISTS idx_documents_project_id ON project_documents (project_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON development_tasks (project_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_project_id ON ai_sessions (project_id)",
            "CREATE INDEX IF NOT EXISTS idx_previews_project_id ON frontend_previews (project_id)",
            "CREATE INDEX IF NOT EXISTS idx_deployment_project_id ON deployment_status (project_id)",
            "CREATE INDEX IF NOT EXISTS idx_reports_project_id ON test_reports (project_id)"
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            # 创建表
            for statement in sql_statements:
                conn.execute(statement)
            
            # 创建索引
            for statement in index_statements:
                conn.execute(statement)
            
            conn.commit()
    
    # 用户操作
    async def save_user(self, user: User) -> bool:
        """保存用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO users 
                    (id, username, email, created_at, last_login, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user.id, user.username, user.email,
                    user.created_at, user.last_login, user.is_active
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"保存用户失败: {e}")
            return False
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return User(**dict(row))
            return None
        except Exception as e:
            print(f"获取用户失败: {e}")
            return None
    
    # 项目操作
    async def save_project(self, project: Project) -> bool:
        """保存项目"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO projects 
                    (id, user_id, name, description, status, created_at, updated_at, 
                     completed_at, domain_preference, technology_preference, 
                     deployment_config, total_development_time, ai_interactions_count, final_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project.id, project.user_id, project.name, project.description,
                    project.status.value, project.created_at, project.updated_at,
                    project.completed_at, project.domain_preference, 
                    project.technology_preference,
                    json.dumps(project.deployment_config) if project.deployment_config else None,
                    project.total_development_time, project.ai_interactions_count, 
                    project.final_score
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"保存项目失败: {e}")
            return False
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
                row = cursor.fetchone()
                
                if row:
                    project_data = dict(row)
                    if project_data['deployment_config']:
                        project_data['deployment_config'] = json.loads(project_data['deployment_config'])
                    return Project(**project_data)
            return None
        except Exception as e:
            print(f"获取项目失败: {e}")
            return None
    
    async def get_user_projects(self, user_id: str) -> List[Project]:
        """获取用户的所有项目"""
        try:
            projects = []
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC", 
                    (user_id,)
                )
                
                for row in cursor.fetchall():
                    project_data = dict(row)
                    if project_data['deployment_config']:
                        project_data['deployment_config'] = json.loads(project_data['deployment_config'])
                    projects.append(Project(**project_data))
            
            return projects
        except Exception as e:
            print(f"获取用户项目失败: {e}")
            return []
    
    async def update_project_status(self, project_id: str, status: ProjectStatus) -> bool:
        """更新项目状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE projects 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status.value, project_id))
                conn.commit()
            return True
        except Exception as e:
            print(f"更新项目状态失败: {e}")
            return False
    
    # 文档操作
    async def save_document(self, project_id: str, document: ProjectDocument) -> bool:
        """保存项目文档"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO project_documents
                    (id, project_id, content, version, document_type, requirements,
                     technical_specs, api_specifications, database_schema, ui_mockups,
                     created_at, updated_at, created_by, review_status, user_feedback)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    document.id, project_id, document.content, document.version,
                    document.document_type,
                    json.dumps(document.requirements),
                    json.dumps(document.technical_specs),
                    json.dumps(document.api_specifications),
                    json.dumps(document.database_schema) if document.database_schema else None,
                    json.dumps(document.ui_mockups),
                    document.created_at, document.updated_at, document.created_by,
                    document.review_status, document.user_feedback
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"保存文档失败: {e}")
            return False
    
    async def get_document(self, project_id: str, version: Optional[int] = None) -> Optional[ProjectDocument]:
        """获取项目文档"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if version:
                    cursor = conn.execute(
                        "SELECT * FROM project_documents WHERE project_id = ? AND version = ?",
                        (project_id, version)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM project_documents WHERE project_id = ? ORDER BY version DESC LIMIT 1",
                        (project_id,)
                    )
                
                row = cursor.fetchone()
                if row:
                    doc_data = dict(row)
                    doc_data['requirements'] = json.loads(doc_data['requirements'])
                    doc_data['technical_specs'] = json.loads(doc_data['technical_specs'])
                    doc_data['api_specifications'] = json.loads(doc_data['api_specifications'])
                    if doc_data['database_schema']:
                        doc_data['database_schema'] = json.loads(doc_data['database_schema'])
                    doc_data['ui_mockups'] = json.loads(doc_data['ui_mockups'])
                    
                    return ProjectDocument(**doc_data)
            return None
        except Exception as e:
            print(f"获取文档失败: {e}")
            return None
    
    async def get_next_document_version(self, project_id: str) -> int:
        """获取下一个文档版本号"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT MAX(version) FROM project_documents WHERE project_id = ?",
                    (project_id,)
                )
                result = cursor.fetchone()
                return (result[0] or 0) + 1
        except Exception as e:
            print(f"获取文档版本失败: {e}")
            return 1
    
    # 任务操作
    async def save_task(self, task: DevelopmentTask) -> bool:
        """保存开发任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO development_tasks
                    (id, project_id, task_name, description, task_type, status,
                     priority, estimated_hours, actual_hours, dependencies, blockers,
                     assigned_ai, ai_session_id, created_at, started_at, completed_at,
                     output_files, test_results, quality_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.id, task.project_id, task.task_name, task.description,
                    task.task_type, task.status, task.priority, task.estimated_hours,
                    task.actual_hours, json.dumps(task.dependencies), json.dumps(task.blockers),
                    task.assigned_ai.value, task.ai_session_id, task.created_at,
                    task.started_at, task.completed_at, json.dumps(task.output_files),
                    json.dumps(task.test_results) if task.test_results else None,
                    task.quality_score
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"保存任务失败: {e}")
            return False
    
    async def get_project_tasks(self, project_id: str) -> List[DevelopmentTask]:
        """获取项目的所有任务"""
        try:
            tasks = []
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM development_tasks WHERE project_id = ? ORDER BY priority, created_at",
                    (project_id,)
                )
                
                for row in cursor.fetchall():
                    task_data = dict(row)
                    task_data['dependencies'] = json.loads(task_data['dependencies'])
                    task_data['blockers'] = json.loads(task_data['blockers'])
                    task_data['output_files'] = json.loads(task_data['output_files'])
                    if task_data['test_results']:
                        task_data['test_results'] = json.loads(task_data['test_results'])
                    task_data['assigned_ai'] = AIType(task_data['assigned_ai'])
                    
                    tasks.append(DevelopmentTask(**task_data))
            
            return tasks
        except Exception as e:
            print(f"获取项目任务失败: {e}")
            return []
    
    # AI会话操作
    async def save_ai_session(self, session: AISession) -> bool:
        """保存AI会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO ai_sessions
                    (id, project_id, ai_type, status, model_name, temperature, max_tokens,
                     messages, total_tokens_used, total_cost, created_at, last_interaction,
                     error_count, last_error, recovery_attempts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.id, session.project_id, session.ai_type.value, session.status,
                    session.model_name, session.temperature, session.max_tokens,
                    json.dumps(session.messages), session.total_tokens_used, session.total_cost,
                    session.created_at, session.last_interaction, session.error_count,
                    session.last_error, session.recovery_attempts
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"保存AI会话失败: {e}")
            return False
    
    # 前端预览操作
    async def save_frontend_preview(self, preview: FrontendPreview) -> bool:
        """保存前端预览"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO frontend_previews
                    (id, project_id, version, html_content, css_content, js_content,
                     assets, responsive_design, accessibility_compliant, user_feedback,
                     modification_requests, approval_status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    preview.id, preview.project_id, preview.version,
                    preview.html_content, preview.css_content, preview.js_content,
                    json.dumps(preview.assets), preview.responsive_design,
                    preview.accessibility_compliant, preview.user_feedback,
                    json.dumps(preview.modification_requests), preview.approval_status,
                    preview.created_at, preview.updated_at
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"保存前端预览失败: {e}")
            return False
    
    async def get_frontend_preview(self, project_id: str) -> Optional[FrontendPreview]:
        """获取前端预览"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM frontend_previews WHERE project_id = ? ORDER BY version DESC LIMIT 1",
                    (project_id,)
                )
                
                row = cursor.fetchone()
                if row:
                    preview_data = dict(row)
                    preview_data['assets'] = json.loads(preview_data['assets'])
                    preview_data['modification_requests'] = json.loads(preview_data['modification_requests'])
                    return FrontendPreview(**preview_data)
            return None
        except Exception as e:
            print(f"获取前端预览失败: {e}")
            return None
    
    # 清理操作
    async def cleanup(self):
        """清理资源"""
        for conn in self.connection_pool.values():
            conn.close()
        self.connection_pool.clear()
        print("✅ 数据库连接已清理")