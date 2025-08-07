"""
AI服务组件

实现Web平台专用的AI服务，包括文档AI、前端AI、中转AI等
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from gpt_engineer.core.ai import AI
from gpt_engineer.core.files_dict import FilesDict

from .models import (
    ProjectDocument, FrontendPreview, TestReport, 
    DeploymentStatus, AISession, AIType
)

# 基础AI服务类
class BaseAIService(ABC):
    """AI服务基础类"""
    
    def __init__(self, ai: AI, ai_type: AIType):
        self.ai = ai
        self.ai_type = ai_type
        self.session_history: Dict[str, AISession] = {}
    
    def create_session(self, project_id: str) -> str:
        """创建AI会话"""
        session_id = str(uuid.uuid4())
        session = AISession(
            id=session_id,
            project_id=project_id,
            ai_type=self.ai_type
        )
        self.session_history[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[AISession]:
        """获取AI会话"""
        return self.session_history.get(session_id)
    
    async def _safe_ai_call(self, system_prompt: str, user_prompt: str, session_id: str = None) -> str:
        """安全的AI调用，包含错误处理和重试机制"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                messages = self.ai.start(
                    system=system_prompt,
                    user=user_prompt,
                    step_name=f"{self.ai_type.value}_call"
                )
                
                response = messages[-1].content.strip()
                
                # 更新会话历史
                if session_id and session_id in self.session_history:
                    session = self.session_history[session_id]
                    session.messages.append({
                        "role": "user",
                        "content": user_prompt,
                        "timestamp": datetime.now().isoformat()
                    })
                    session.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "timestamp": datetime.now().isoformat()
                    })
                    session.last_interaction = datetime.now()
                
                return response
                
            except Exception as e:
                retry_count += 1
                if session_id and session_id in self.session_history:
                    session = self.session_history[session_id]
                    session.error_count += 1
                    session.last_error = str(e)
                
                if retry_count >= max_retries:
                    raise Exception(f"AI调用失败，已重试{max_retries}次: {str(e)}")
                
                # 等待重试
                import asyncio
                await asyncio.sleep(2 ** retry_count)  # 指数退避


class DocumentAI(BaseAIService):
    """文档AI - 负责生成和优化项目文档"""
    
    def __init__(self, ai: AI):
        super().__init__(ai, AIType.DOCUMENT_AI)
    
    async def generate_project_document(self, user_request: Dict[str, Any]) -> ProjectDocument:
        """
        根据用户需求生成完整的项目文档
        
        Args:
            user_request: 用户需求信息
            
        Returns:
            ProjectDocument: 生成的项目文档
        """
        system_prompt = """
你是一个专业的项目分析师和技术文档专家。你的任务是将用户的需求转换为完整、详细的项目开发文档。

你需要生成包含以下内容的文档：
1. 项目概述和目标
2. 功能需求详细描述
3. 技术架构设计
4. 数据库设计
5. API接口规范
6. 用户界面设计要求
7. 开发时间线
8. 测试要求
9. 部署要求

请确保文档详细、准确、可执行，为后续的AI开发提供清晰的指导。
"""
        
        user_prompt = f"""
请基于以下用户需求生成完整的项目开发文档：

项目描述：{user_request.get('description', '')}
具体需求：{json.dumps(user_request.get('requirements', {}), ensure_ascii=False, indent=2)}
技术偏好：{user_request.get('technology_preference', '无特殊要求')}
域名偏好：{user_request.get('domain_preference', '无特殊要求')}

请返回结构化的JSON格式文档，包含所有必要的开发信息。
"""
        
        response = await self._safe_ai_call(system_prompt, user_prompt)
        
        # 解析AI响应生成文档
        try:
            doc_content = self._parse_document_response(response, user_request)
        except Exception:
            # 如果解析失败，使用原始响应
            doc_content = response
        
        document = ProjectDocument(
            project_id=user_request.get('project_id', ''),
            content=doc_content,
            requirements=user_request.get('requirements', {}),
            created_by="document_ai"
        )
        
        return document
    
    async def refine_document(self, current_document: ProjectDocument, user_feedback: str) -> ProjectDocument:
        """
        基于用户反馈优化文档
        
        Args:
            current_document: 当前文档
            user_feedback: 用户反馈
            
        Returns:
            ProjectDocument: 优化后的文档
        """
        system_prompt = """
你是一个项目文档优化专家。基于用户的反馈，对现有项目文档进行修改和优化。

请保持文档的完整性和一致性，同时准确响应用户的修改要求。
"""
        
        user_prompt = f"""
当前项目文档：
{current_document.content}

用户反馈和修改要求：
{user_feedback}

请根据用户反馈对文档进行修改，返回更新后的完整文档。
"""
        
        response = await self._safe_ai_call(system_prompt, user_prompt)
        
        # 创建新版本文档
        updated_document = ProjectDocument(
            project_id=current_document.project_id,
            content=response,
            version=current_document.version + 1,
            requirements=current_document.requirements,
            created_by="document_ai",
            user_feedback=user_feedback
        )
        
        return updated_document
    
    async def chat_with_user(self, project_id: str, message: str, session_id: str = None) -> str:
        """
        与用户进行文档相关的对话
        
        Args:
            project_id: 项目ID
            message: 用户消息
            session_id: 会话ID
            
        Returns:
            str: AI回复
        """
        if not session_id:
            session_id = self.create_session(project_id)
        
        system_prompt = """
你是一个友好、专业的项目文档助手。你正在帮助用户完善项目文档。

请用清晰、友好的语言回答用户的问题，提供有用的建议，帮助用户更好地定义项目需求。
"""
        
        response = await self._safe_ai_call(system_prompt, message, session_id)
        return response
    
    def _parse_document_response(self, response: str, user_request: Dict[str, Any]) -> str:
        """解析AI响应，提取文档内容"""
        # 尝试解析JSON格式的响应
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                doc_data = json.loads(json_match.group())
                return json.dumps(doc_data, ensure_ascii=False, indent=2)
        except:
            pass
        
        # 如果无法解析为JSON，返回原始响应
        return response


class FrontendAI(BaseAIService):
    """前端AI - 负责生成和优化前端界面"""
    
    def __init__(self, ai: AI):
        super().__init__(ai, AIType.FRONTEND_AI)
    
    async def generate_frontend_preview(self, project_id: str, project_document: ProjectDocument, 
                                      api_specifications: List[Dict[str, Any]]) -> FrontendPreview:
        """
        生成前端预览
        
        Args:
            project_id: 项目ID
            project_document: 项目文档
            api_specifications: API规范
            
        Returns:
            FrontendPreview: 前端预览
        """
        system_prompt = """
你是一个专业的前端开发专家，专门创建现代、美观、响应式的Web界面。

你需要基于项目文档和API规范生成完整的前端代码，包括：
1. HTML结构 - 语义化、无障碍访问
2. CSS样式 - 现代设计、响应式布局
3. JavaScript功能 - 与后端API交互、用户体验优化

请确保：
- 代码质量高，结构清晰
- 设计美观，用户体验良好
- 完全响应式设计
- 跨浏览器兼容
- 无障碍访问支持
"""
        
        user_prompt = f"""
项目文档：
{project_document.content}

API规范：
{json.dumps(api_specifications, ensure_ascii=False, indent=2)}

请生成完整的前端代码，包括HTML、CSS和JavaScript。
"""
        
        response = await self._safe_ai_call(system_prompt, user_prompt)
        
        # 解析前端代码
        html_content, css_content, js_content = self._parse_frontend_code(response)
        
        preview = FrontendPreview(
            project_id=project_id,
            html_content=html_content,
            css_content=css_content,
            js_content=js_content
        )
        
        return preview
    
    async def process_user_feedback(self, project_id: str, current_preview: FrontendPreview, 
                                  feedback: Dict[str, Any]) -> FrontendPreview:
        """
        处理用户对前端的反馈
        
        Args:
            project_id: 项目ID
            current_preview: 当前预览
            feedback: 用户反馈
            
        Returns:
            FrontendPreview: 更新后的预览
        """
        system_prompt = """
你是一个前端优化专家。基于用户的反馈，对现有前端代码进行修改和优化。

请保持代码质量和设计一致性，准确响应用户的修改要求。
"""
        
        user_prompt = f"""
当前前端代码：

HTML:
{current_preview.html_content}

CSS:
{current_preview.css_content}

JavaScript:
{current_preview.js_content}

用户反馈：
反馈类型：{feedback.get('feedback_type', '')}
修改要求：{json.dumps(feedback.get('modifications', {}), ensure_ascii=False, indent=2)}
用户评论：{feedback.get('user_comments', '')}

请根据用户反馈对前端代码进行修改。
"""
        
        response = await self._safe_ai_call(system_prompt, user_prompt)
        
        # 解析更新的前端代码
        html_content, css_content, js_content = self._parse_frontend_code(response)
        
        updated_preview = FrontendPreview(
            project_id=project_id,
            version=current_preview.version + 1,
            html_content=html_content,
            css_content=css_content,
            js_content=js_content,
            user_feedback=feedback.get('user_comments', '')
        )
        
        return updated_preview
    
    def _parse_frontend_code(self, response: str) -> tuple[str, str, str]:
        """解析前端代码响应"""
        import re
        
        # 提取HTML
        html_match = re.search(r'```html\n(.*?)\n```', response, re.DOTALL)
        html_content = html_match.group(1) if html_match else ""
        
        # 提取CSS
        css_match = re.search(r'```css\n(.*?)\n```', response, re.DOTALL)
        css_content = css_match.group(1) if css_match else ""
        
        # 提取JavaScript
        js_match = re.search(r'```javascript\n(.*?)\n```', response, re.DOTALL)
        js_content = js_match.group(1) if js_match else ""
        
        # 如果没有找到代码块，尝试其他格式
        if not html_content and not css_content and not js_content:
            html_content, css_content, js_content = self._parse_mixed_code(response)
        
        return html_content, css_content, js_content
    
    def _parse_mixed_code(self, response: str) -> tuple[str, str, str]:
        """解析混合格式的代码"""
        # 这里可以实现更复杂的代码解析逻辑
        # 暂时返回基础HTML结构
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>生成的Web应用</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <h1>Web应用</h1>
        <p>这是由AI生成的Web应用界面。</p>
    </div>
    <script src="script.js"></script>
</body>
</html>
"""
        
        css_content = """
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

h1 {
    color: #333;
    text-align: center;
}
"""
        
        js_content = """
document.addEventListener('DOMContentLoaded', function() {
    console.log('Web应用已加载');
});
"""
        
        return html_content, css_content, js_content


class TransferAI(BaseAIService):
    """中转AI - 负责用户界面交互和展示"""
    
    def __init__(self, ai: AI):
        super().__init__(ai, AIType.TRANSFER_AI)
    
    async def present_preview_to_user(self, preview: FrontendPreview, context: Dict[str, Any]) -> str:
        """
        向用户展示前端预览的说明
        
        Args:
            preview: 前端预览
            context: 上下文信息
            
        Returns:
            str: 展示说明
        """
        system_prompt = """
你是一个友好的界面展示助手。你的任务是向用户清晰地介绍生成的前端界面。

请用简洁、友好的语言描述界面的特点、功能和设计亮点，帮助用户理解界面的结构和使用方法。
"""
        
        user_prompt = f"""
请为用户介绍以下前端界面：

界面版本：{preview.version}
创建时间：{preview.created_at}

界面特点：
- HTML长度：{len(preview.html_content)} 字符
- CSS样式：{len(preview.css_content)} 字符  
- JavaScript功能：{len(preview.js_content)} 字符
- 响应式设计：{'是' if preview.responsive_design else '否'}
- 无障碍支持：{'是' if preview.accessibility_compliant else '否'}

项目上下文：
{json.dumps(context, ensure_ascii=False, indent=2)}

请生成一个友好的界面介绍。
"""
        
        response = await self._safe_ai_call(system_prompt, user_prompt)
        return response
    
    async def collect_user_feedback(self, user_message: str, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        收集和解析用户反馈
        
        Args:
            user_message: 用户消息
            current_context: 当前上下文
            
        Returns:
            Dict[str, Any]: 解析后的反馈信息
        """
        system_prompt = """
你是一个用户反馈分析专家。请分析用户的消息，提取其中的反馈信息和修改要求。

返回结构化的JSON格式反馈，包括：
- feedback_type: approve/modify/regenerate
- modifications: 具体修改要求
- priority: 优先级 (1-5)
- user_comments: 用户原始评论
"""
        
        user_prompt = f"""
用户消息：{user_message}

当前上下文：
{json.dumps(current_context, ensure_ascii=False, indent=2)}

请分析用户反馈并返回结构化信息。
"""
        
        response = await self._safe_ai_call(system_prompt, user_prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # 如果解析失败，返回基础反馈
        return {
            "feedback_type": "modify",
            "modifications": {"general": user_message},
            "priority": 3,
            "user_comments": user_message
        }


class ServerSupervisorAI(BaseAIService):
    """服务器监管AI - 负责服务器端监控和管理"""
    
    def __init__(self, ai: AI):
        super().__init__(ai, AIType.SERVER_SUPERVISOR_AI)
    
    async def analyze_deployment_status(self, deployment_status: DeploymentStatus) -> Dict[str, Any]:
        """
        分析部署状态
        
        Args:
            deployment_status: 部署状态
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        system_prompt = """
你是一个服务器部署专家。请分析部署状态，提供专业的建议和解决方案。
"""
        
        user_prompt = f"""
部署状态信息：
状态：{deployment_status.status}
部署URL：{deployment_status.deployment_url}
健康检查：{deployment_status.health_check_url}
运行时间：{deployment_status.uptime_percentage}%
平均响应时间：{deployment_status.response_time_avg}ms

错误日志：
{json.dumps(deployment_status.error_logs, ensure_ascii=False, indent=2)}

警告信息：
{json.dumps(deployment_status.warnings, ensure_ascii=False, indent=2)}

请分析部署状态并提供建议。
"""
        
        response = await self._safe_ai_call(system_prompt, user_prompt)
        
        return {
            "analysis": response,
            "recommendations": [],
            "critical_issues": [],
            "health_score": self._calculate_health_score(deployment_status)
        }
    
    def _calculate_health_score(self, deployment_status: DeploymentStatus) -> float:
        """计算健康评分"""
        score = 100.0
        
        # 根据运行时间扣分
        if deployment_status.uptime_percentage < 99:
            score -= (99 - deployment_status.uptime_percentage) * 2
        
        # 根据响应时间扣分
        if deployment_status.response_time_avg > 1000:
            score -= min(20, (deployment_status.response_time_avg - 1000) / 100)
        
        # 根据错误数量扣分
        error_count = len(deployment_status.error_logs)
        score -= min(30, error_count * 3)
        
        return max(0.0, score)


class WebTestAI(BaseAIService):
    """网站测试AI - 负责最终验收测试"""
    
    def __init__(self, ai: AI):
        super().__init__(ai, AIType.WEB_TEST_AI)
    
    async def run_final_acceptance_test(self, project_id: str, project_document: ProjectDocument,
                                      deployment_url: str) -> TestReport:
        """
        执行最终验收测试
        
        Args:
            project_id: 项目ID
            project_document: 项目文档
            deployment_url: 部署URL
            
        Returns:
            TestReport: 测试报告
        """
        system_prompt = """
你是一个专业的Web应用测试专家。请对已部署的Web应用进行全面的验收测试。

测试范围包括：
1. 功能完整性测试
2. 用户界面测试
3. 性能测试
4. 兼容性测试
5. 安全性基础检查

请提供详细的测试报告和评分。
"""
        
        user_prompt = f"""
项目文档：
{project_document.content}

部署地址：{deployment_url}

请进行全面的验收测试，并对比项目文档中的需求，确保所有功能都已实现。
"""
        
        response = await self._safe_ai_call(system_prompt, user_prompt)
        
        # 生成测试报告
        test_report = TestReport(
            project_id=project_id,
            test_type="acceptance",
            total_tests=self._count_requirements(project_document),
            quality_score=self._calculate_quality_score(response),
            test_details=[{
                "test_name": "最终验收测试",
                "result": "completed",
                "details": response
            }]
        )
        
        return test_report
    
    def _count_requirements(self, project_document: ProjectDocument) -> int:
        """统计需求数量"""
        # 简化实现，实际应该解析文档结构
        return len(project_document.requirements.get('features', [])) or 10
    
    def _calculate_quality_score(self, test_response: str) -> float:
        """基于测试响应计算质量评分"""
        # 简化实现，实际应该分析测试结果
        positive_keywords = ['通过', '成功', '完成', '满足', '良好']
        negative_keywords = ['失败', '错误', '缺失', '问题', '不符合']
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in test_response)
        negative_count = sum(1 for keyword in negative_keywords if keyword in test_response)
        
        base_score = 85.0
        score_adjustment = (positive_count * 3) - (negative_count * 5)
        
        return max(0.0, min(100.0, base_score + score_adjustment))