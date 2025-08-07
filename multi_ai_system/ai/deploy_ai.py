"""
部署AI实现

负责项目打包、服务器部署、状态监控等功能
"""

import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import tarfile
import zipfile

from gpt_engineer.core.ai import AI
from gpt_engineer.core.files_dict import FilesDict

from ..core.base_interfaces import BaseDeployAI, PackageResult, DeployResult


class DeployAI(BaseDeployAI):
    """
    部署AI实现
    
    功能：
    - 项目自动打包
    - 多平台部署支持
    - 部署状态监控
    - 配置文件生成
    """
    
    def __init__(self, ai: AI, work_dir: Optional[str] = None):
        self.ai = ai
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp())
        self.work_dir.mkdir(exist_ok=True)
        
        # 支持的部署平台
        self.deploy_platforms = {
            'docker': self._deploy_to_docker,
            'heroku': self._deploy_to_heroku,
            'vercel': self._deploy_to_vercel,
            'aws': self._deploy_to_aws,
            'local': self._deploy_locally
        }
        
        # 支持的包格式
        self.package_formats = {
            'docker': self._create_docker_package,
            'pip': self._create_pip_package,
            'npm': self._create_npm_package,
            'zip': self._create_zip_package,
            'tar': self._create_tar_package
        }
    
    def package_project(self, files_dict: FilesDict, config: Dict[str, Any]) -> PackageResult:
        """
        打包项目
        
        Args:
            files_dict: 项目文件
            config: 打包配置
            
        Returns:
            PackageResult: 打包结果
        """
        package_type = config.get('package_type', 'docker')
        version = config.get('version', '1.0.0')
        
        # 创建临时打包目录
        package_id = str(uuid.uuid4())
        package_dir = self.work_dir / f"package_{package_id}"
        package_dir.mkdir(exist_ok=True)
        
        start_time = time.time()
        
        try:
            # 写入文件到打包目录
            self._write_files_to_dir(files_dict, package_dir)
            
            # 生成部署配置文件
            deploy_config = self.generate_deployment_config(files_dict)
            self._write_deployment_files(deploy_config, package_dir)
            
            # 执行特定格式的打包
            if package_type in self.package_formats:
                package_path = self.package_formats[package_type](
                    package_dir, config
                )
            else:
                raise ValueError(f"不支持的打包格式: {package_type}")
            
            # 分析依赖
            dependencies = self._analyze_dependencies(files_dict)
            
            # 计算包大小
            package_size = self._calculate_package_size(package_path)
            
            build_time = time.time() - start_time
            
            return PackageResult(
                package_path=package_path,
                package_type=package_type,
                version=version,
                dependencies=dependencies,
                size_mb=package_size,
                build_time=build_time,
                success=True
            )
            
        except Exception as e:
            return PackageResult(
                package_path=Path(""),
                package_type=package_type,
                version=version,
                success=False,
                error_message=str(e)
            )
        finally:
            # 清理临时目录
            if package_dir.exists():
                shutil.rmtree(package_dir, ignore_errors=True)
    
    def upload_to_server(self, package: PackageResult, server_config: Dict[str, Any]) -> DeployResult:
        """
        上传到服务器
        
        Args:
            package: 打包结果
            server_config: 服务器配置
            
        Returns:
            DeployResult: 部署结果
        """
        if not package.success:
            return DeployResult(
                deployment_id=str(uuid.uuid4()),
                status="failed",
                success=False,
                error_message=f"打包失败: {package.error_message}"
            )
        
        deployment_id = str(uuid.uuid4())
        platform = server_config.get('platform', 'docker')
        
        start_time = time.time()
        
        try:
            # 根据平台执行部署
            if platform in self.deploy_platforms:
                deploy_result = self.deploy_platforms[platform](
                    package, server_config, deployment_id
                )
            else:
                raise ValueError(f"不支持的部署平台: {platform}")
            
            deployment_time = time.time() - start_time
            deploy_result.deployment_time = deployment_time
            
            return deploy_result
            
        except Exception as e:
            return DeployResult(
                deployment_id=deployment_id,
                status="failed",
                success=False,
                error_message=str(e),
                deployment_time=time.time() - start_time
            )
    
    def monitor_deployment(self, deploy_result: DeployResult) -> Dict[str, Any]:
        """
        监控部署状态
        
        Args:
            deploy_result: 部署结果
            
        Returns:
            Dict[str, Any]: 监控数据
        """
        monitoring_data = {
            'deployment_id': deploy_result.deployment_id,
            'status': deploy_result.status,
            'timestamp': datetime.now().isoformat(),
            'uptime': 0.0,
            'response_time': None,
            'error_count': 0,
            'health_check': 'unknown'
        }
        
        # 如果有URL，进行健康检查
        if deploy_result.url:
            health_status = self._perform_health_check(deploy_result.url)
            monitoring_data.update(health_status)
        
        # 检查服务状态
        if deploy_result.server_info:
            service_status = self._check_service_status(deploy_result.server_info)
            monitoring_data.update(service_status)
        
        return monitoring_data
    
    def generate_deployment_config(self, files_dict: FilesDict) -> Dict[str, Any]:
        """
        生成部署配置
        
        Args:
            files_dict: 项目文件
            
        Returns:
            Dict[str, Any]: 部署配置
        """
        # 分析项目类型
        project_type = self._detect_project_type(files_dict)
        
        # 分析依赖
        dependencies = self._analyze_dependencies(files_dict)
        
        # 分析入口点
        entrypoint = self._find_entrypoint(files_dict)
        
        # 生成基础配置
        config = {
            'project_type': project_type,
            'dependencies': dependencies,
            'entrypoint': entrypoint,
            'docker_config': self._generate_docker_config(files_dict, project_type),
            'environment_variables': self._extract_env_variables(files_dict),
            'ports': self._detect_ports(files_dict),
            'volumes': self._detect_volumes(files_dict)
        }
        
        # 使用AI优化配置
        ai_config = self._ai_optimize_config(files_dict, config)
        if ai_config:
            config.update(ai_config)
        
        return config
    
    def _write_files_to_dir(self, files_dict: FilesDict, target_dir: Path):
        """将文件写入目录"""
        for filename, content in files_dict.items():
            file_path = target_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def _write_deployment_files(self, deploy_config: Dict[str, Any], target_dir: Path):
        """写入部署配置文件"""
        
        # 生成Dockerfile
        if 'docker_config' in deploy_config:
            dockerfile_content = self._generate_dockerfile(deploy_config)
            with open(target_dir / 'Dockerfile', 'w') as f:
                f.write(dockerfile_content)
        
        # 生成docker-compose.yml
        docker_compose_content = self._generate_docker_compose(deploy_config)
        with open(target_dir / 'docker-compose.yml', 'w') as f:
            f.write(docker_compose_content)
        
        # 生成.env文件
        if deploy_config.get('environment_variables'):
            env_content = self._generate_env_file(deploy_config['environment_variables'])
            with open(target_dir / '.env', 'w') as f:
                f.write(env_content)
        
        # 生成部署脚本
        deploy_script = self._generate_deploy_script(deploy_config)
        script_path = target_dir / 'deploy.sh'
        with open(script_path, 'w') as f:
            f.write(deploy_script)
        script_path.chmod(0o755)  # 添加执行权限
    
    def _create_docker_package(self, package_dir: Path, config: Dict[str, Any]) -> Path:
        """创建Docker包"""
        # 构建Docker镜像
        image_name = config.get('image_name', 'my-app')
        tag = config.get('version', 'latest')
        
        try:
            # 执行docker build
            subprocess.run([
                'docker', 'build', '-t', f'{image_name}:{tag}', '.'
            ], cwd=package_dir, check=True)
            
            # 保存镜像为tar文件
            output_path = self.work_dir / f"{image_name}_{tag}.tar"
            subprocess.run([
                'docker', 'save', '-o', str(output_path), f'{image_name}:{tag}'
            ], check=True)
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Docker打包失败: {e}")
    
    def _create_zip_package(self, package_dir: Path, config: Dict[str, Any]) -> Path:
        """创建ZIP包"""
        output_path = self.work_dir / f"package_{config.get('version', 'latest')}.zip"
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(package_dir)
                    zipf.write(file_path, arcname)
        
        return output_path
    
    def _create_tar_package(self, package_dir: Path, config: Dict[str, Any]) -> Path:
        """创建TAR包"""
        output_path = self.work_dir / f"package_{config.get('version', 'latest')}.tar.gz"
        
        with tarfile.open(output_path, 'w:gz') as tar:
            tar.add(package_dir, arcname='.')
        
        return output_path
    
    def _deploy_to_docker(self, package: PackageResult, server_config: Dict[str, Any], 
                         deployment_id: str) -> DeployResult:
        """部署到Docker"""
        
        container_name = server_config.get('container_name', f'app_{deployment_id}')
        port = server_config.get('port', 8000)
        
        try:
            # 加载Docker镜像
            if package.package_path.suffix == '.tar':
                subprocess.run([
                    'docker', 'load', '-i', str(package.package_path)
                ], check=True)
            
            # 停止现有容器（如果存在）
            subprocess.run([
                'docker', 'stop', container_name
            ], capture_output=True)
            
            subprocess.run([
                'docker', 'rm', container_name
            ], capture_output=True)
            
            # 运行新容器
            image_name = server_config.get('image_name', 'my-app:latest')
            subprocess.run([
                'docker', 'run', '-d',
                '--name', container_name,
                '-p', f'{port}:8000',
                image_name
            ], check=True)
            
            return DeployResult(
                deployment_id=deployment_id,
                url=f"http://localhost:{port}",
                status="deployed",
                server_info={'container_name': container_name, 'port': port},
                success=True
            )
            
        except subprocess.CalledProcessError as e:
            return DeployResult(
                deployment_id=deployment_id,
                status="failed",
                success=False,
                error_message=f"Docker部署失败: {e}"
            )
    
    def _deploy_locally(self, package: PackageResult, server_config: Dict[str, Any], 
                       deployment_id: str) -> DeployResult:
        """本地部署"""
        
        # 解压包到指定目录
        deploy_dir = Path(server_config.get('deploy_path', './deployed_app'))
        deploy_dir.mkdir(exist_ok=True)
        
        try:
            if package.package_path.suffix == '.zip':
                with zipfile.ZipFile(package.package_path, 'r') as zipf:
                    zipf.extractall(deploy_dir)
            elif package.package_path.suffix in ['.tar', '.gz']:
                with tarfile.open(package.package_path, 'r:*') as tar:
                    tar.extractall(deploy_dir)
            
            # 执行部署脚本
            deploy_script = deploy_dir / 'deploy.sh'
            if deploy_script.exists():
                subprocess.run(['bash', str(deploy_script)], cwd=deploy_dir, check=True)
            
            port = server_config.get('port', 8000)
            
            return DeployResult(
                deployment_id=deployment_id,
                url=f"http://localhost:{port}",
                status="deployed",
                server_info={'deploy_path': str(deploy_dir), 'port': port},
                success=True
            )
            
        except Exception as e:
            return DeployResult(
                deployment_id=deployment_id,
                status="failed",
                success=False,
                error_message=f"本地部署失败: {e}"
            )
    
    def _detect_project_type(self, files_dict: FilesDict) -> str:
        """检测项目类型"""
        if any(f.endswith('.py') for f in files_dict):
            if 'requirements.txt' in files_dict or 'pyproject.toml' in files_dict:
                return 'python'
        
        if any(f.endswith('.js') for f in files_dict):
            if 'package.json' in files_dict:
                return 'nodejs'
        
        if any(f.endswith('.java') for f in files_dict):
            return 'java'
        
        return 'generic'
    
    def _analyze_dependencies(self, files_dict: FilesDict) -> List[str]:
        """分析项目依赖"""
        dependencies = []
        
        # Python项目
        if 'requirements.txt' in files_dict:
            deps = files_dict['requirements.txt'].strip().split('\n')
            dependencies.extend([dep.strip() for dep in deps if dep.strip()])
        
        # Node.js项目
        if 'package.json' in files_dict:
            try:
                package_data = json.loads(files_dict['package.json'])
                if 'dependencies' in package_data:
                    dependencies.extend(list(package_data['dependencies'].keys()))
            except json.JSONDecodeError:
                pass
        
        return dependencies
    
    def _find_entrypoint(self, files_dict: FilesDict) -> str:
        """查找项目入口点"""
        # 常见的入口点文件
        entrypoint_candidates = [
            'main.py', 'app.py', 'server.py', 'index.py',
            'main.js', 'index.js', 'server.js',
            'Main.java'
        ]
        
        for candidate in entrypoint_candidates:
            if candidate in files_dict:
                return candidate
        
        # 查找包含main函数的Python文件
        for filename, content in files_dict.items():
            if filename.endswith('.py') and 'if __name__ == "__main__"' in content:
                return filename
        
        return 'main.py'  # 默认
    
    def _generate_docker_config(self, files_dict: FilesDict, project_type: str) -> Dict[str, str]:
        """生成Docker配置"""
        config = {
            'base_image': 'python:3.11-slim',
            'work_dir': '/app',
            'copy_files': '.',
            'install_cmd': 'pip install -r requirements.txt',
            'run_cmd': 'python main.py'
        }
        
        if project_type == 'nodejs':
            config.update({
                'base_image': 'node:16-alpine',
                'install_cmd': 'npm install',
                'run_cmd': 'npm start'
            })
        elif project_type == 'java':
            config.update({
                'base_image': 'openjdk:11-jre-slim',
                'install_cmd': 'javac *.java',
                'run_cmd': 'java Main'
            })
        
        return config
    
    def _generate_dockerfile(self, deploy_config: Dict[str, Any]) -> str:
        """生成Dockerfile内容"""
        docker_config = deploy_config.get('docker_config', {})
        
        dockerfile = f"""# 自动生成的Dockerfile
FROM {docker_config.get('base_image', 'python:3.11-slim')}

WORKDIR {docker_config.get('work_dir', '/app')}

# 复制项目文件
COPY {docker_config.get('copy_files', '.')} .

# 安装依赖
RUN {docker_config.get('install_cmd', 'pip install -r requirements.txt')}

# 暴露端口
EXPOSE {deploy_config.get('ports', [8000])[0] if deploy_config.get('ports') else 8000}

# 运行应用
CMD ["{docker_config.get('run_cmd', 'python main.py')}"]
"""
        return dockerfile
    
    def _generate_docker_compose(self, deploy_config: Dict[str, Any]) -> str:
        """生成docker-compose.yml内容"""
        compose = f"""version: '3.8'

services:
  app:
    build: .
    ports:
      - "{deploy_config.get('ports', [8000])[0] if deploy_config.get('ports') else 8000}:8000"
"""
        
        # 添加环境变量
        if deploy_config.get('environment_variables'):
            compose += "    environment:\n"
            for key, value in deploy_config['environment_variables'].items():
                compose += f"      - {key}={value}\n"
        
        # 添加卷挂载
        if deploy_config.get('volumes'):
            compose += "    volumes:\n"
            for volume in deploy_config['volumes']:
                compose += f"      - {volume}\n"
        
        return compose
    
    def _generate_env_file(self, env_vars: Dict[str, str]) -> str:
        """生成.env文件内容"""
        env_content = "# 环境变量配置\n"
        for key, value in env_vars.items():
            env_content += f"{key}={value}\n"
        return env_content
    
    def _generate_deploy_script(self, deploy_config: Dict[str, Any]) -> str:
        """生成部署脚本"""
        project_type = deploy_config.get('project_type', 'python')
        
        script = """#!/bin/bash
# 自动生成的部署脚本

set -e

echo "开始部署应用..."

"""
        
        if project_type == 'python':
            script += """
# 安装Python依赖
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# 运行应用
python """ + deploy_config.get('entrypoint', 'main.py') + """ &

echo "Python应用部署完成"
"""
        elif project_type == 'nodejs':
            script += """
# 安装Node.js依赖
if [ -f "package.json" ]; then
    npm install
fi

# 运行应用
npm start &

echo "Node.js应用部署完成"
"""
        
        script += """
echo "部署成功！"
"""
        
        return script
    
    def _extract_env_variables(self, files_dict: FilesDict) -> Dict[str, str]:
        """提取环境变量"""
        env_vars = {}
        
        # 从.env文件提取
        if '.env' in files_dict:
            for line in files_dict['.env'].split('\n'):
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        
        # 从代码中提取常用环境变量
        common_env_vars = ['PORT', 'DEBUG', 'SECRET_KEY', 'DATABASE_URL']
        for filename, content in files_dict.items():
            for var in common_env_vars:
                if f'os.environ.get("{var}")' in content or f'process.env.{var}' in content:
                    env_vars[var] = f"${{{var}}}"  # 占位符
        
        return env_vars
    
    def _detect_ports(self, files_dict: FilesDict) -> List[int]:
        """检测应用端口"""
        ports = []
        
        # 从代码中检测端口
        port_patterns = [
            r'port\s*=\s*(\d+)',
            r'PORT\s*=\s*(\d+)',
            r'listen\s*\(\s*(\d+)',
            r'\.run\s*\(\s*port\s*=\s*(\d+)'
        ]
        
        for filename, content in files_dict.items():
            for pattern in port_patterns:
                import re
                matches = re.findall(pattern, content)
                for match in matches:
                    port = int(match)
                    if 1000 <= port <= 65535:
                        ports.append(port)
        
        # 默认端口
        if not ports:
            ports = [8000]
        
        return list(set(ports))  # 去重
    
    def _detect_volumes(self, files_dict: FilesDict) -> List[str]:
        """检测需要挂载的卷"""
        volumes = []
        
        # 检测数据目录
        if any('data' in filename.lower() for filename in files_dict):
            volumes.append('./data:/app/data')
        
        # 检测日志目录
        if any('log' in content.lower() for content in files_dict.values()):
            volumes.append('./logs:/app/logs')
        
        return volumes
    
    def _ai_optimize_config(self, files_dict: FilesDict, base_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用AI优化部署配置"""
        try:
            # 构建分析提示
            files_summary = self._create_project_summary(files_dict)
            
            prompt = f"""
分析以下项目并优化部署配置：

项目文件概览：
{files_summary}

当前配置：
{json.dumps(base_config, indent=2)}

请提供优化建议，包括：
1. 更好的Docker基础镜像选择
2. 性能优化配置
3. 安全性配置
4. 资源限制建议

返回JSON格式的优化配置。
"""
            
            messages = self.ai.start(
                system="你是一个专业的DevOps工程师，专门优化应用部署配置。",
                user=prompt,
                step_name="ai_optimize_config"
            )
            
            optimization = messages[-1].content.strip()
            
            # 提取JSON结果
            import re
            json_match = re.search(r'\{.*\}', optimization, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            print(f"AI配置优化失败: {e}")
        
        return None
    
    def _create_project_summary(self, files_dict: FilesDict) -> str:
        """创建项目摘要"""
        summary = f"项目包含 {len(files_dict)} 个文件：\n"
        
        for filename in sorted(files_dict.keys()):
            file_size = len(files_dict[filename])
            summary += f"- {filename} ({file_size} 字符)\n"
        
        return summary
    
    def _calculate_package_size(self, package_path: Path) -> float:
        """计算包大小（MB）"""
        if package_path.exists():
            size_bytes = package_path.stat().st_size
            return size_bytes / (1024 * 1024)  # 转换为MB
        return 0.0
    
    def _perform_health_check(self, url: str) -> Dict[str, Any]:
        """执行健康检查"""
        health_status = {
            'health_check': 'failed',
            'response_time': None,
            'status_code': None
        }
        
        try:
            import requests
            start_time = time.time()
            response = requests.get(url, timeout=30)
            response_time = time.time() - start_time
            
            health_status.update({
                'health_check': 'passed' if response.status_code == 200 else 'failed',
                'response_time': response_time,
                'status_code': response.status_code
            })
            
        except Exception as e:
            health_status['error'] = str(e)
        
        return health_status
    
    def _check_service_status(self, server_info: Dict[str, Any]) -> Dict[str, Any]:
        """检查服务状态"""
        status = {'service_status': 'unknown'}
        
        # 检查Docker容器状态
        if 'container_name' in server_info:
            try:
                result = subprocess.run([
                    'docker', 'ps', '--filter', f"name={server_info['container_name']}", 
                    '--format', 'table {{.Status}}'
                ], capture_output=True, text=True)
                
                if result.returncode == 0 and 'Up' in result.stdout:
                    status['service_status'] = 'running'
                else:
                    status['service_status'] = 'stopped'
                    
            except Exception:
                status['service_status'] = 'error'
        
        return status
    
    # 其他部署平台的实现（Heroku, Vercel, AWS等）可以根据需要添加
    def _deploy_to_heroku(self, package: PackageResult, server_config: Dict[str, Any], 
                         deployment_id: str) -> DeployResult:
        """部署到Heroku（待实现）"""
        # 这里可以实现Heroku部署逻辑
        return DeployResult(
            deployment_id=deployment_id,
            status="not_implemented",
            success=False,
            error_message="Heroku部署功能尚未实现"
        )
    
    def _deploy_to_vercel(self, package: PackageResult, server_config: Dict[str, Any], 
                         deployment_id: str) -> DeployResult:
        """部署到Vercel（待实现）"""
        # 这里可以实现Vercel部署逻辑
        return DeployResult(
            deployment_id=deployment_id,
            status="not_implemented",
            success=False,
            error_message="Vercel部署功能尚未实现"
        )
    
    def _deploy_to_aws(self, package: PackageResult, server_config: Dict[str, Any], 
                      deployment_id: str) -> DeployResult:
        """部署到AWS（待实现）"""
        # 这里可以实现AWS部署逻辑
        return DeployResult(
            deployment_id=deployment_id,
            status="not_implemented",
            success=False,
            error_message="AWS部署功能尚未实现"
        )
    
    def _create_pip_package(self, package_dir: Path, config: Dict[str, Any]) -> Path:
        """创建pip包（待实现）"""
        # 这里可以实现pip包创建逻辑
        raise NotImplementedError("pip包创建功能尚未实现")
    
    def _create_npm_package(self, package_dir: Path, config: Dict[str, Any]) -> Path:
        """创建npm包（待实现）"""
        # 这里可以实现npm包创建逻辑
        raise NotImplementedError("npm包创建功能尚未实现")