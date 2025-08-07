"""
服务器AI接口

提供与服务器AI的交互接口，用于项目打包上传和部署管理
"""

import json
import requests
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import tarfile
import zipfile

from ..core.base_interfaces import PackageResult, DeployResult


class ServerAIInterface:
    """
    服务器AI接口
    
    负责：
    - 项目打包上传
    - 服务器部署管理
    - 部署状态监控
    - 服务器资源管理
    """
    
    def __init__(self, server_config: Dict[str, Any]):
        """
        初始化服务器AI接口
        
        Args:
            server_config: 服务器配置
                - api_base_url: 服务器API基础URL
                - api_key: API密钥
                - deployment_endpoint: 部署端点
                - monitoring_endpoint: 监控端点
        """
        self.server_config = server_config
        self.api_base_url = server_config['api_base_url']
        self.api_key = server_config['api_key']
        
        # API端点配置
        self.endpoints = {
            'upload': f"{self.api_base_url}/api/v1/upload",
            'deploy': f"{self.api_base_url}/api/v1/deploy", 
            'status': f"{self.api_base_url}/api/v1/status",
            'monitor': f"{self.api_base_url}/api/v1/monitor",
            'logs': f"{self.api_base_url}/api/v1/logs",
            'cleanup': f"{self.api_base_url}/api/v1/cleanup"
        }
        
        # 请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'MultiAI-System/1.0'
        })
    
    def upload_project_package(self, package_result: PackageResult, 
                             upload_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        上传项目包到服务器
        
        Args:
            package_result: 项目打包结果
            upload_config: 上传配置
                - project_name: 项目名称
                - environment: 部署环境 (dev/staging/prod)
                - auto_deploy: 是否自动部署
                - health_check_url: 健康检查URL
        
        Returns:
            Dict[str, Any]: 上传结果
        """
        if not package_result.success:
            return {
                'success': False,
                'error': 'Package creation failed',
                'upload_id': None
            }
        
        upload_config = upload_config or {}
        upload_id = str(uuid.uuid4())
        
        try:
            # 准备上传元数据
            metadata = {
                'upload_id': upload_id,
                'project_name': upload_config.get('project_name', f'project_{upload_id[:8]}'),
                'package_type': package_result.package_type,
                'package_version': package_result.version,
                'package_size_mb': package_result.size_mb,
                'dependencies': package_result.dependencies,
                'environment': upload_config.get('environment', 'dev'),
                'auto_deploy': upload_config.get('auto_deploy', False),
                'health_check_url': upload_config.get('health_check_url'),
                'upload_timestamp': datetime.now().isoformat()
            }
            
            # 第一步：创建上传会话
            session_response = self._create_upload_session(metadata)
            if not session_response['success']:
                return session_response
            
            upload_url = session_response['upload_url']
            session_id = session_response['session_id']
            
            # 第二步：上传文件
            upload_response = self._upload_file(upload_url, package_result.package_path)
            if not upload_response['success']:
                return upload_response
            
            # 第三步：完成上传
            complete_response = self._complete_upload(session_id, metadata)
            
            return {
                'success': complete_response['success'],
                'upload_id': upload_id,
                'session_id': session_id,
                'project_url': complete_response.get('project_url'),
                'deployment_info': complete_response.get('deployment_info'),
                'message': complete_response.get('message', 'Upload completed successfully')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Upload failed: {str(e)}',
                'upload_id': upload_id
            }
    
    def deploy_project(self, upload_id: str, deploy_config: Dict[str, Any] = None) -> DeployResult:
        """
        部署项目到服务器
        
        Args:
            upload_id: 上传ID
            deploy_config: 部署配置
                - environment: 部署环境
                - instance_type: 实例类型
                - replicas: 副本数量
                - resources: 资源限制
                - environment_variables: 环境变量
        
        Returns:
            DeployResult: 部署结果
        """
        deploy_config = deploy_config or {}
        deployment_id = str(uuid.uuid4())
        
        try:
            # 准备部署请求
            deploy_request = {
                'deployment_id': deployment_id,
                'upload_id': upload_id,
                'environment': deploy_config.get('environment', 'dev'),
                'instance_type': deploy_config.get('instance_type', 'small'),
                'replicas': deploy_config.get('replicas', 1),
                'resources': deploy_config.get('resources', {
                    'cpu': '0.5',
                    'memory': '512Mi'
                }),
                'environment_variables': deploy_config.get('environment_variables', {}),
                'auto_scale': deploy_config.get('auto_scale', False),
                'health_check': deploy_config.get('health_check', {
                    'path': '/health',
                    'interval': 30,
                    'timeout': 10
                })
            }
            
            # 发送部署请求
            response = self.session.post(
                self.endpoints['deploy'],
                json=deploy_request,
                timeout=300  # 5分钟超时
            )
            response.raise_for_status()
            
            deploy_data = response.json()
            
            if deploy_data['success']:
                return DeployResult(
                    deployment_id=deployment_id,
                    url=deploy_data.get('url'),
                    status=deploy_data.get('status', 'deployed'),
                    server_info=deploy_data.get('server_info', {}),
                    deployment_time=deploy_data.get('deployment_time', 0.0),
                    success=True
                )
            else:
                return DeployResult(
                    deployment_id=deployment_id,
                    status="failed",
                    success=False,
                    error_message=deploy_data.get('error', 'Deployment failed')
                )
                
        except Exception as e:
            return DeployResult(
                deployment_id=deployment_id,
                status="failed",
                success=False,
                error_message=f'Deployment request failed: {str(e)}'
            )
    
    def monitor_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """
        监控部署状态
        
        Args:
            deployment_id: 部署ID
            
        Returns:
            Dict[str, Any]: 监控数据
        """
        try:
            response = self.session.get(
                f"{self.endpoints['monitor']}/{deployment_id}",
                timeout=30
            )
            response.raise_for_status()
            
            monitoring_data = response.json()
            
            return {
                'deployment_id': deployment_id,
                'status': monitoring_data.get('status', 'unknown'),
                'health': monitoring_data.get('health', 'unknown'),
                'metrics': monitoring_data.get('metrics', {}),
                'uptime': monitoring_data.get('uptime', 0),
                'last_check': monitoring_data.get('last_check'),
                'alerts': monitoring_data.get('alerts', []),
                'resource_usage': monitoring_data.get('resource_usage', {})
            }
            
        except Exception as e:
            return {
                'deployment_id': deployment_id,
                'status': 'error',
                'error': str(e)
            }
    
    def get_deployment_logs(self, deployment_id: str, 
                          lines: int = 100, follow: bool = False) -> Dict[str, Any]:
        """
        获取部署日志
        
        Args:
            deployment_id: 部署ID
            lines: 日志行数
            follow: 是否实时跟踪
            
        Returns:
            Dict[str, Any]: 日志数据
        """
        try:
            params = {
                'lines': lines,
                'follow': follow
            }
            
            response = self.session.get(
                f"{self.endpoints['logs']}/{deployment_id}",
                params=params,
                timeout=60
            )
            response.raise_for_status()
            
            logs_data = response.json()
            
            return {
                'deployment_id': deployment_id,
                'logs': logs_data.get('logs', []),
                'total_lines': logs_data.get('total_lines', 0),
                'timestamp': logs_data.get('timestamp'),
                'success': True
            }
            
        except Exception as e:
            return {
                'deployment_id': deployment_id,
                'logs': [],
                'success': False,
                'error': str(e)
            }
    
    def cleanup_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """
        清理部署
        
        Args:
            deployment_id: 部署ID
            
        Returns:
            Dict[str, Any]: 清理结果
        """
        try:
            response = self.session.delete(
                f"{self.endpoints['cleanup']}/{deployment_id}",
                timeout=120
            )
            response.raise_for_status()
            
            cleanup_data = response.json()
            
            return {
                'deployment_id': deployment_id,
                'success': cleanup_data.get('success', False),
                'message': cleanup_data.get('message', 'Cleanup completed'),
                'resources_freed': cleanup_data.get('resources_freed', {}),
                'cleanup_time': cleanup_data.get('cleanup_time', 0.0)
            }
            
        except Exception as e:
            return {
                'deployment_id': deployment_id,
                'success': False,
                'error': str(e)
            }
    
    def list_deployments(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        列出部署
        
        Args:
            filters: 过滤条件
                - environment: 环境过滤
                - status: 状态过滤
                - project_name: 项目名称过滤
        
        Returns:
            List[Dict[str, Any]]: 部署列表
        """
        try:
            params = filters or {}
            
            response = self.session.get(
                self.endpoints['status'],
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            deployments_data = response.json()
            
            return deployments_data.get('deployments', [])
            
        except Exception as e:
            return []
    
    def get_server_capacity(self) -> Dict[str, Any]:
        """
        获取服务器容量信息
        
        Returns:
            Dict[str, Any]: 服务器容量数据
        """
        try:
            response = self.session.get(
                f"{self.api_base_url}/api/v1/capacity",
                timeout=30
            )
            response.raise_for_status()
            
            capacity_data = response.json()
            
            return {
                'total_cpu': capacity_data.get('total_cpu', 0),
                'used_cpu': capacity_data.get('used_cpu', 0),
                'total_memory': capacity_data.get('total_memory', 0),
                'used_memory': capacity_data.get('used_memory', 0),
                'total_storage': capacity_data.get('total_storage', 0),
                'used_storage': capacity_data.get('used_storage', 0),
                'active_deployments': capacity_data.get('active_deployments', 0),
                'max_deployments': capacity_data.get('max_deployments', 0),
                'availability_zones': capacity_data.get('availability_zones', [])
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'available': False
            }
    
    def _create_upload_session(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """创建上传会话"""
        try:
            response = self.session.post(
                f"{self.endpoints['upload']}/session",
                json=metadata,
                timeout=60
            )
            response.raise_for_status()
            
            session_data = response.json()
            return {
                'success': session_data.get('success', False),
                'session_id': session_data.get('session_id'),
                'upload_url': session_data.get('upload_url'),
                'expires_at': session_data.get('expires_at')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create upload session: {str(e)}'
            }
    
    def _upload_file(self, upload_url: str, file_path: Path) -> Dict[str, Any]:
        """上传文件"""
        try:
            # 使用多部分上传
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                
                # 临时移除Content-Type头，让requests自动设置
                headers = dict(self.session.headers)
                if 'Content-Type' in headers:
                    del headers['Content-Type']
                
                response = requests.post(
                    upload_url,
                    files=files,
                    headers=headers,
                    timeout=600  # 10分钟超时
                )
                response.raise_for_status()
            
            upload_data = response.json()
            return {
                'success': upload_data.get('success', False),
                'file_id': upload_data.get('file_id'),
                'checksum': upload_data.get('checksum')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'File upload failed: {str(e)}'
            }
    
    def _complete_upload(self, session_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """完成上传"""
        try:
            complete_request = {
                'session_id': session_id,
                'metadata': metadata,
                'verify_integrity': True
            }
            
            response = self.session.post(
                f"{self.endpoints['upload']}/complete",
                json=complete_request,
                timeout=120
            )
            response.raise_for_status()
            
            complete_data = response.json()
            return {
                'success': complete_data.get('success', False),
                'project_url': complete_data.get('project_url'),
                'deployment_info': complete_data.get('deployment_info'),
                'message': complete_data.get('message')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Upload completion failed: {str(e)}'
            }


class ServerAIDeploymentManager:
    """服务器AI部署管理器"""
    
    def __init__(self, server_interface: ServerAIInterface):
        self.server_interface = server_interface
        self.active_deployments = {}
    
    def deploy_with_monitoring(self, package_result: PackageResult, 
                             config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        带监控的完整部署流程
        
        Args:
            package_result: 打包结果
            config: 部署配置
            
        Returns:
            Dict[str, Any]: 部署结果和监控信息
        """
        config = config or {}
        
        # 第一步：上传项目
        print("正在上传项目包...")
        upload_result = self.server_interface.upload_project_package(
            package_result, config.get('upload_config', {})
        )
        
        if not upload_result['success']:
            return {
                'stage': 'upload',
                'success': False,
                'error': upload_result['error']
            }
        
        print(f"上传成功，上传ID: {upload_result['upload_id']}")
        
        # 第二步：部署项目
        print("正在部署项目...")
        deploy_result = self.server_interface.deploy_project(
            upload_result['upload_id'], config.get('deploy_config', {})
        )
        
        if not deploy_result.success:
            return {
                'stage': 'deployment',
                'success': False,
                'error': deploy_result.error_message
            }
        
        print(f"部署成功，部署ID: {deploy_result.deployment_id}")
        if deploy_result.url:
            print(f"访问地址: {deploy_result.url}")
        
        # 第三步：监控部署状态
        print("开始监控部署状态...")
        monitoring_data = self.server_interface.monitor_deployment(
            deploy_result.deployment_id
        )
        
        # 保存活跃部署信息
        self.active_deployments[deploy_result.deployment_id] = {
            'upload_id': upload_result['upload_id'],
            'deploy_result': deploy_result,
            'monitoring': monitoring_data,
            'created_at': datetime.now()
        }
        
        return {
            'stage': 'completed',
            'success': True,
            'upload_result': upload_result,
            'deploy_result': deploy_result.__dict__,
            'monitoring': monitoring_data
        }
    
    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """获取部署状态"""
        if deployment_id in self.active_deployments:
            # 更新监控数据
            monitoring_data = self.server_interface.monitor_deployment(deployment_id)
            self.active_deployments[deployment_id]['monitoring'] = monitoring_data
            return self.active_deployments[deployment_id]
        else:
            return self.server_interface.monitor_deployment(deployment_id)
    
    def cleanup_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """清理部署"""
        cleanup_result = self.server_interface.cleanup_deployment(deployment_id)
        
        if cleanup_result['success'] and deployment_id in self.active_deployments:
            del self.active_deployments[deployment_id]
        
        return cleanup_result
    
    def list_active_deployments(self) -> List[Dict[str, Any]]:
        """列出活跃部署"""
        return list(self.active_deployments.values())


# 使用示例
def example_server_deployment():
    """服务器部署示例"""
    
    # 服务器配置
    server_config = {
        'api_base_url': 'https://api.your-server-ai.com',
        'api_key': 'your-api-key-here',  # 实际使用时应从环境变量获取
    }
    
    # 创建服务器接口
    server_interface = ServerAIInterface(server_config)
    
    # 创建部署管理器
    deploy_manager = ServerAIDeploymentManager(server_interface)
    
    # 模拟打包结果
    package_result = PackageResult(
        package_path=Path("./example_app.tar.gz"),
        package_type="docker",
        version="1.0.0",
        dependencies=["flask", "sqlite3"],
        size_mb=25.5,
        success=True
    )
    
    # 部署配置
    deployment_config = {
        'upload_config': {
            'project_name': 'my-awesome-app',
            'environment': 'staging',
            'auto_deploy': True
        },
        'deploy_config': {
            'environment': 'staging',
            'instance_type': 'medium',
            'replicas': 2,
            'resources': {
                'cpu': '1.0',
                'memory': '1Gi'
            },
            'environment_variables': {
                'DEBUG': 'false',
                'DATABASE_URL': 'sqlite:///app.db'
            }
        }
    }
    
    # 执行部署
    result = deploy_manager.deploy_with_monitoring(package_result, deployment_config)
    
    if result['success']:
        deployment_id = result['deploy_result']['deployment_id']
        
        # 获取部署状态
        status = deploy_manager.get_deployment_status(deployment_id)
        print(f"部署状态: {status}")
        
        # 获取日志
        logs = server_interface.get_deployment_logs(deployment_id, lines=50)
        print(f"最近日志: {logs}")
        
        return deployment_id
    else:
        print(f"部署失败: {result['error']}")
        return None


if __name__ == "__main__":
    # 运行示例
    deployment_id = example_server_deployment()
    if deployment_id:
        print(f"部署成功，ID: {deployment_id}")
    else:
        print("部署失败")