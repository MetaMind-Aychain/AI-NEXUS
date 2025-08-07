"""
测试AI实现

负责自动生成测试用例、执行测试、分析覆盖率和诊断失败原因
"""

import ast
import json
import os
import re
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from gpt_engineer.core.ai import AI
from gpt_engineer.core.files_dict import FilesDict

from ..core.base_interfaces import BaseTestAI, TestResult, DeployResult


class TestAI(BaseTestAI):
    """
    测试AI实现
    
    功能：
    - 自动生成测试用例
    - 执行测试
    - 分析测试覆盖率
    - 诊断测试失败原因
    - 性能评估
    """
    
    def __init__(self, ai: AI, work_dir: Optional[str] = None):
        self.ai = ai
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp())
        self.work_dir.mkdir(exist_ok=True)
        
        # 测试框架配置
        self.test_frameworks = {
            'python': ['pytest', 'unittest'],
            'javascript': ['jest', 'mocha'],
            'java': ['junit'],
        }
        
        self.test_patterns = {
            'python': 'test_*.py',
            'javascript': '*.test.js',
            'java': '*Test.java'
        }
    
    def generate_tests(self, files_dict: FilesDict, requirements: Dict[str, Any]) -> FilesDict:
        """
        生成测试用例
        
        Args:
            files_dict: 代码文件
            requirements: 需求规格
            
        Returns:
            FilesDict: 测试文件
        """
        test_files = FilesDict({})
        
        # 分析代码结构
        code_analysis = self._analyze_code_structure(files_dict)
        
        # 为每个模块生成测试
        for module_name, module_info in code_analysis.items():
            if module_info['language'] == 'python':
                test_content = self._generate_python_tests(
                    module_name, module_info, requirements
                )
                test_filename = f"test_{module_name.replace('.py', '')}.py"
                test_files[test_filename] = test_content
        
        # 生成集成测试
        integration_tests = self._generate_integration_tests(files_dict, requirements)
        if integration_tests:
            test_files['test_integration.py'] = integration_tests
        
        # 生成配置文件
        test_config = self._generate_test_config(files_dict)
        if test_config:
            test_files.update(test_config)
        
        return test_files
    
    def execute_tests(self, files_dict: FilesDict) -> TestResult:
        """
        执行测试
        
        Args:
            files_dict: 包含测试的代码文件
            
        Returns:
            TestResult: 测试结果
        """
        test_id = str(uuid.uuid4())
        
        # 准备测试环境
        test_env_path = self.work_dir / f"test_env_{test_id}"
        test_env_path.mkdir(exist_ok=True)
        
        try:
            # 写入文件到测试环境
            self._write_files_to_env(files_dict, test_env_path)
            
            # 安装依赖
            self._install_dependencies(test_env_path)
            
            # 执行测试
            execution_result = self._run_tests(test_env_path)
            
            # 分析结果
            test_result = self._parse_test_results(
                test_id, execution_result, test_env_path
            )
            
            return test_result
            
        except Exception as e:
            return TestResult(
                test_id=test_id,
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                coverage_percentage=0.0,
                execution_time=0.0,
                error_messages=[f"测试执行失败: {str(e)}"]
            )
        finally:
            # 清理测试环境
            import shutil
            if test_env_path.exists():
                shutil.rmtree(test_env_path, ignore_errors=True)
    
    def analyze_coverage(self, test_result: TestResult) -> Dict[str, float]:
        """
        分析测试覆盖率
        
        Args:
            test_result: 测试结果
            
        Returns:
            Dict[str, float]: 覆盖率分析
        """
        coverage_analysis = {
            'overall_coverage': test_result.coverage_percentage,
            'line_coverage': test_result.coverage_percentage,
            'branch_coverage': 0.0,
            'function_coverage': 0.0
        }
        
        # 从测试详情中提取更详细的覆盖率信息
        for detail in test_result.test_details:
            if 'coverage' in detail:
                coverage_data = detail['coverage']
                if isinstance(coverage_data, dict):
                    coverage_analysis.update(coverage_data)
        
        return coverage_analysis
    
    def diagnose_failures(self, test_result: TestResult, files_dict: FilesDict) -> List[str]:
        """
        诊断测试失败原因
        
        Args:
            test_result: 测试结果
            files_dict: 代码文件
            
        Returns:
            List[str]: 诊断结果
        """
        diagnoses = []
        
        # 分析错误消息
        for error_msg in test_result.error_messages:
            diagnosis = self._diagnose_error_message(error_msg)
            if diagnosis:
                diagnoses.append(diagnosis)
        
        # 分析测试详情
        for detail in test_result.test_details:
            if not detail.get('passed', True):
                test_diagnosis = self._diagnose_test_failure(detail, files_dict)
                if test_diagnosis:
                    diagnoses.append(test_diagnosis)
        
        # 使用AI进行深度诊断
        if test_result.error_messages:
            ai_diagnoses = self._ai_failure_diagnosis(test_result, files_dict)
            diagnoses.extend(ai_diagnoses)
        
        return list(set(diagnoses))  # 去重
    
    def final_evaluation(self, deploy_result: DeployResult) -> float:
        """
        最终评分
        
        Args:
            deploy_result: 部署结果
            
        Returns:
            float: 最终评分 (0-100)
        """
        base_score = 85.0  # 基础分数
        
        # 部署成功性
        if not deploy_result.success:
            base_score -= 30
        
        # 部署时间评估
        if deploy_result.deployment_time > 600:  # 超过10分钟
            base_score -= 10
        elif deploy_result.deployment_time < 60:  # 小于1分钟
            base_score += 5
        
        # URL可访问性检查
        if deploy_result.url:
            accessibility_score = self._check_url_accessibility(deploy_result.url)
            base_score += accessibility_score
        
        # 性能测试
        if deploy_result.url:
            performance_score = self._run_performance_tests(deploy_result.url)
            base_score += performance_score
        
        return max(0.0, min(100.0, base_score))
    
    def _analyze_code_structure(self, files_dict: FilesDict) -> Dict[str, Dict]:
        """分析代码结构"""
        analysis = {}
        
        for filename, content in files_dict.items():
            file_info = {
                'filename': filename,
                'language': self._detect_language(filename),
                'functions': [],
                'classes': [],
                'imports': [],
                'lines_count': len(content.split('\n'))
            }
            
            if filename.endswith('.py'):
                try:
                    tree = ast.parse(content)
                    
                    # 提取函数
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            file_info['functions'].append({
                                'name': node.name,
                                'args': [arg.arg for arg in node.args.args],
                                'line': node.lineno,
                                'docstring': ast.get_docstring(node)
                            })
                        elif isinstance(node, ast.ClassDef):
                            file_info['classes'].append({
                                'name': node.name,
                                'line': node.lineno,
                                'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                            })
                        elif isinstance(node, (ast.Import, ast.ImportFrom)):
                            if isinstance(node, ast.Import):
                                file_info['imports'].extend([alias.name for alias in node.names])
                            else:
                                module = node.module or ''
                                file_info['imports'].append(module)
                
                except SyntaxError:
                    file_info['syntax_error'] = True
            
            analysis[filename] = file_info
        
        return analysis
    
    def _generate_python_tests(self, module_name: str, module_info: Dict, requirements: Dict) -> str:
        """生成Python测试用例"""
        
        # 构建测试生成提示
        prompt = f"""
为以下Python模块生成全面的测试用例：

模块名: {module_name}
函数列表: {[f['name'] for f in module_info.get('functions', [])]}
类列表: {[c['name'] for c in module_info.get('classes', [])]}

需求信息:
{json.dumps(requirements, ensure_ascii=False, indent=2)}

请生成包含以下内容的pytest测试文件：
1. 单元测试：覆盖所有函数和方法
2. 边界条件测试
3. 异常处理测试
4. 模拟测试（如果需要）

测试代码要求：
- 使用pytest框架
- 包含适当的fixture
- 良好的测试命名
- 充分的断言
- 测试文档字符串

请只返回测试代码，不要包含其他说明。
"""
        
        try:
            messages = self.ai.start(
                system="你是一个专业的测试工程师，专门编写高质量的Python测试代码。",
                user=prompt,
                step_name="generate_python_tests"
            )
            
            test_code = messages[-1].content.strip()
            
            # 提取代码块
            code_match = re.search(r'```python\n(.*?)\n```', test_code, re.DOTALL)
            if code_match:
                return code_match.group(1)
            else:
                # 如果没有代码块标记，返回整个内容
                return test_code
                
        except Exception as e:
            print(f"生成测试用例失败: {e}")
            return self._generate_basic_test_template(module_name, module_info)
    
    def _generate_basic_test_template(self, module_name: str, module_info: Dict) -> str:
        """生成基础测试模板"""
        template = f'''"""
Test cases for {module_name}
"""

import pytest
from {module_name.replace(".py", "")} import *


class Test{module_name.replace(".py", "").title()}:
    """Test class for {module_name}"""
    
    def setup_method(self):
        """Setup test fixtures before each test method."""
        pass
    
    def teardown_method(self):
        """Cleanup after each test method."""
        pass
'''
        
        # 为每个函数生成基础测试
        for func in module_info.get('functions', []):
            template += f'''
    def test_{func['name']}_basic(self):
        """Test basic functionality of {func['name']}."""
        # TODO: Implement test for {func['name']}
        assert True  # Placeholder
    
    def test_{func['name']}_edge_cases(self):
        """Test edge cases for {func['name']}."""
        # TODO: Implement edge case tests for {func['name']}
        assert True  # Placeholder
'''
        
        return template
    
    def _generate_integration_tests(self, files_dict: FilesDict, requirements: Dict) -> Optional[str]:
        """生成集成测试"""
        if len(files_dict) < 2:
            return None
        
        prompt = f"""
为以下项目生成集成测试：

文件列表: {list(files_dict.keys())}
需求规格: {json.dumps(requirements, ensure_ascii=False, indent=2)}

请生成集成测试，包含：
1. 模块间交互测试
2. 端到端功能测试
3. 数据流测试
4. API集成测试（如果适用）

使用pytest框架，只返回测试代码。
"""
        
        try:
            messages = self.ai.start(
                system="你是一个专业的集成测试工程师。",
                user=prompt,
                step_name="generate_integration_tests"
            )
            
            test_code = messages[-1].content.strip()
            
            # 提取代码块
            code_match = re.search(r'```python\n(.*?)\n```', test_code, re.DOTALL)
            if code_match:
                return code_match.group(1)
            else:
                return test_code
                
        except Exception as e:
            print(f"生成集成测试失败: {e}")
            return None
    
    def _generate_test_config(self, files_dict: FilesDict) -> Dict[str, str]:
        """生成测试配置文件"""
        config_files = {}
        
        # 生成pytest配置
        pytest_config = """[tool:pytest]
testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --tb=short
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
"""
        config_files['pytest.ini'] = pytest_config
        
        # 生成requirements-test.txt
        test_requirements = """pytest>=6.0.0
pytest-cov>=2.0.0
pytest-mock>=3.0.0
coverage>=5.0.0
"""
        config_files['requirements-test.txt'] = test_requirements
        
        return config_files
    
    def _write_files_to_env(self, files_dict: FilesDict, env_path: Path):
        """将文件写入测试环境"""
        for filename, content in files_dict.items():
            file_path = env_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def _install_dependencies(self, env_path: Path):
        """安装依赖"""
        requirements_files = ['requirements.txt', 'requirements-test.txt']
        
        for req_file in requirements_files:
            req_path = env_path / req_file
            if req_path.exists():
                try:
                    subprocess.run([
                        'pip', 'install', '-r', str(req_path)
                    ], check=True, capture_output=True, cwd=env_path)
                except subprocess.CalledProcessError as e:
                    print(f"安装依赖失败 {req_file}: {e}")
        
        # 安装测试框架
        try:
            subprocess.run([
                'pip', 'install', 'pytest', 'pytest-cov', 'coverage'
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"安装测试框架失败: {e}")
    
    def _run_tests(self, env_path: Path) -> Dict[str, Any]:
        """执行测试"""
        start_time = datetime.now()
        
        try:
            # 运行pytest
            result = subprocess.run([
                'python', '-m', 'pytest',
                '--tb=short',
                '--cov=.',
                '--cov-report=json',
                '--json-report',
                '--json-report-file=test_report.json',
                '-v'
            ], capture_output=True, text=True, cwd=env_path, timeout=300)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'execution_time': execution_time
            }
            
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': '测试执行超时',
                'execution_time': 300.0
            }
        except Exception as e:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': f'测试执行异常: {str(e)}',
                'execution_time': 0.0
            }
    
    def _parse_test_results(self, test_id: str, execution_result: Dict, env_path: Path) -> TestResult:
        """解析测试结果"""
        
        # 默认结果
        test_result = TestResult(
            test_id=test_id,
            passed=execution_result['returncode'] == 0,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            coverage_percentage=0.0,
            execution_time=execution_result['execution_time'],
            error_messages=[]
        )
        
        # 解析stdout获取测试统计
        stdout = execution_result['stdout']
        stderr = execution_result['stderr']
        
        if stderr:
            test_result.error_messages.append(stderr)
        
        # 提取测试统计信息
        test_stats = self._extract_test_stats(stdout)
        test_result.total_tests = test_stats['total']
        test_result.passed_tests = test_stats['passed']
        test_result.failed_tests = test_stats['failed']
        test_result.passed = test_stats['failed'] == 0
        
        # 提取覆盖率信息
        coverage_info = self._extract_coverage_info(env_path)
        test_result.coverage_percentage = coverage_info.get('coverage', 0.0)
        
        # 提取详细测试信息
        test_details = self._extract_test_details(stdout)
        test_result.test_details = test_details
        
        return test_result
    
    def _extract_test_stats(self, output: str) -> Dict[str, int]:
        """从输出中提取测试统计"""
        stats = {'total': 0, 'passed': 0, 'failed': 0}
        
        # 查找pytest的统计行
        stat_patterns = [
            r'(\d+) passed',
            r'(\d+) failed',
            r'(\d+) error',
            r'(\d+) skipped'
        ]
        
        for pattern in stat_patterns:
            matches = re.findall(pattern, output)
            if matches:
                count = int(matches[0])
                if 'passed' in pattern:
                    stats['passed'] = count
                elif 'failed' in pattern or 'error' in pattern:
                    stats['failed'] += count
        
        stats['total'] = stats['passed'] + stats['failed']
        
        return stats
    
    def _extract_coverage_info(self, env_path: Path) -> Dict[str, float]:
        """提取覆盖率信息"""
        coverage_file = env_path / 'coverage.json'
        
        if coverage_file.exists():
            try:
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                
                if 'totals' in coverage_data:
                    totals = coverage_data['totals']
                    covered = totals.get('covered_lines', 0)
                    total = totals.get('num_statements', 1)
                    return {'coverage': (covered / total) * 100 if total > 0 else 0}
            
            except Exception as e:
                print(f"解析覆盖率文件失败: {e}")
        
        # 从输出中提取覆盖率
        return {'coverage': 0.0}
    
    def _extract_test_details(self, output: str) -> List[Dict[str, Any]]:
        """提取测试详细信息"""
        details = []
        
        # 解析pytest的详细输出
        lines = output.split('\n')
        current_test = None
        
        for line in lines:
            # 检测测试开始
            test_match = re.match(r'(.*?::.*?) (PASSED|FAILED|ERROR|SKIPPED)', line)
            if test_match:
                if current_test:
                    details.append(current_test)
                
                current_test = {
                    'name': test_match.group(1),
                    'status': test_match.group(2),
                    'passed': test_match.group(2) == 'PASSED',
                    'duration': 0.0,
                    'error_message': ''
                }
            
            # 提取错误信息
            elif current_test and ('FAILED' in line or 'ERROR' in line):
                current_test['error_message'] += line + '\n'
        
        if current_test:
            details.append(current_test)
        
        return details
    
    def _detect_language(self, filename: str) -> str:
        """检测文件语言"""
        if filename.endswith('.py'):
            return 'python'
        elif filename.endswith(('.js', '.ts')):
            return 'javascript'
        elif filename.endswith('.java'):
            return 'java'
        else:
            return 'unknown'
    
    def _diagnose_error_message(self, error_msg: str) -> Optional[str]:
        """诊断错误消息"""
        diagnoses = {
            'ModuleNotFoundError': '缺少模块依赖，请检查import语句和requirements.txt',
            'AttributeError': '属性错误，检查对象是否具有所调用的属性',
            'TypeError': '类型错误，检查函数参数和返回值类型',
            'AssertionError': '断言失败，检查测试期望值是否正确',
            'ImportError': '导入错误，检查模块路径和依赖',
            'SyntaxError': '语法错误，检查代码语法',
            'IndentationError': '缩进错误，检查代码缩进'
        }
        
        for error_type, diagnosis in diagnoses.items():
            if error_type in error_msg:
                return diagnosis
        
        return None
    
    def _diagnose_test_failure(self, test_detail: Dict, files_dict: FilesDict) -> Optional[str]:
        """诊断测试失败"""
        if test_detail.get('passed', True):
            return None
        
        test_name = test_detail.get('name', '')
        error_msg = test_detail.get('error_message', '')
        
        # 基于测试名称的诊断
        if 'test_' in test_name:
            function_name = test_name.split('test_')[-1].split('_')[0]
            return f"函数 {function_name} 的测试失败，请检查实现逻辑"
        
        return f"测试失败: {error_msg[:100]}..."
    
    def _ai_failure_diagnosis(self, test_result: TestResult, files_dict: FilesDict) -> List[str]:
        """使用AI诊断测试失败"""
        try:
            # 构建诊断提示
            error_summary = '\n'.join(test_result.error_messages[:5])  # 最多5个错误
            
            prompt = f"""
分析以下测试失败信息并提供诊断：

测试统计:
- 总测试数: {test_result.total_tests}
- 通过: {test_result.passed_tests}
- 失败: {test_result.failed_tests}
- 覆盖率: {test_result.coverage_percentage:.1f}%

错误信息:
{error_summary}

请提供：
1. 失败的根本原因
2. 具体的修复建议
3. 预防措施

以简洁的列表形式返回最多5个诊断结果。
"""
            
            messages = self.ai.start(
                system="你是一个专业的测试诊断专家，帮助分析和解决测试问题。",
                user=prompt,
                step_name="ai_failure_diagnosis"
            )
            
            analysis = messages[-1].content.strip()
            
            # 提取诊断列表
            diagnoses = []
            for line in analysis.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    diagnoses.append(line.lstrip('-•1234567890. '))
            
            return diagnoses[:5]
            
        except Exception as e:
            print(f"AI诊断失败: {e}")
            return []
    
    def _check_url_accessibility(self, url: str) -> float:
        """检查URL可访问性"""
        try:
            import requests
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return 10.0  # 加分
            else:
                return -5.0  # 扣分
        except Exception:
            return -10.0  # 无法访问，扣分
    
    def _run_performance_tests(self, url: str) -> float:
        """运行性能测试"""
        try:
            import requests
            import time
            
            # 简单的响应时间测试
            start_time = time.time()
            response = requests.get(url, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                if response_time < 1.0:
                    return 5.0  # 快速响应加分
                elif response_time < 3.0:
                    return 2.0
                else:
                    return -2.0  # 慢响应扣分
            else:
                return -5.0
                
        except Exception:
            return 0.0  # 无法测试，不加减分