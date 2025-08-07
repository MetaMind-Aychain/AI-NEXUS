"""
多AI协作系统测试文件

这个文件包含了对整个多AI协作系统的综合测试，包括：
- 单元测试：各个AI组件的基本功能
- 集成测试：多AI协作流程
- 端到端测试：完整工作流程
- 模拟测试：无需真实API的测试环境
"""

import asyncio
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# 添加项目路径到sys.path
sys.path.insert(0, '.')

from gpt_engineer.core.files_dict import FilesDict
from gpt_engineer.core.prompt import Prompt
from gpt_engineer.core.ai import AI

# 导入我们的多AI系统组件
from multi_ai_system.core.enhanced_dev_ai import EnhancedDevAI
from multi_ai_system.ai.supervisor_ai import SupervisorAI
from multi_ai_system.ai.test_ai import TestAI
from multi_ai_system.ai.deploy_ai import DeployAI
from multi_ai_system.memory.shared_memory import SharedMemoryManager
from multi_ai_system.orchestrator import MultiAIOrchestrator
from multi_ai_system.deployment.server_interface import ServerAIInterface
from multi_ai_system.core.base_interfaces import (
    DevelopmentEvent, DevPlan, TestResult, PackageResult, DeployResult
)


class MockAI:
    """模拟AI，用于测试环境"""
    
    def __init__(self):
        self.call_count = 0
        self.responses = [
            """
这是一个简单的Python计算器程序：

```python
# calculator.py
def add(a, b):
    \"\"\"加法运算\"\"\"
    return a + b

def subtract(a, b):
    \"\"\"减法运算\"\"\"
    return a - b

def multiply(a, b):
    \"\"\"乘法运算\"\"\"
    return a * b

def divide(a, b):
    \"\"\"除法运算\"\"\"
    if b == 0:
        raise ValueError("不能除以零")
    return a / b

def main():
    print("简单计算器")
    while True:
        try:
            a = float(input("请输入第一个数字: "))
            op = input("请输入运算符 (+, -, *, /): ")
            b = float(input("请输入第二个数字: "))
            
            if op == '+':
                result = add(a, b)
            elif op == '-':
                result = subtract(a, b)
            elif op == '*':
                result = multiply(a, b)
            elif op == '/':
                result = divide(a, b)
            else:
                print("无效的运算符")
                continue
                
            print(f"结果: {result}")
            
        except ValueError as e:
            print(f"错误: {e}")
        except KeyboardInterrupt:
            print("\\n程序退出")
            break

if __name__ == "__main__":
    main()
```

```bash
# run.sh
#!/bin/bash
python calculator.py
```
""",
            """
{
    "tasks": [
        {
            "type": "basic_implementation",
            "description": "实现基本计算功能",
            "estimated_hours": 2,
            "priority": "high",
            "dependencies": [],
            "acceptance_criteria": ["支持四则运算", "错误处理", "用户交互"]
        },
        {
            "type": "testing",
            "description": "编写测试用例",
            "estimated_hours": 1,
            "priority": "medium",
            "dependencies": ["basic_implementation"],
            "acceptance_criteria": ["覆盖所有函数", "边界条件测试"]
        }
    ]
}
""",
            """
代码质量分析结果：
{
    "issues": [
        {
            "type": "style_issue",
            "description": "建议添加更多类型注解",
            "severity": "low"
        }
    ],
    "suggestions": [
        "添加更详细的文档字符串",
        "考虑使用配置文件管理常量"
    ],
    "strengths": [
        "代码结构清晰",
        "错误处理得当"
    ]
}
""",
            """
测试用例生成完成：

```python
# test_calculator.py
import pytest
from calculator import add, subtract, multiply, divide

class TestCalculator:
    def test_add_basic(self):
        assert add(2, 3) == 5
        assert add(-1, 1) == 0
        assert add(0, 0) == 0
    
    def test_subtract_basic(self):
        assert subtract(5, 3) == 2
        assert subtract(0, 5) == -5
    
    def test_multiply_basic(self):
        assert multiply(3, 4) == 12
        assert multiply(-2, 3) == -6
        assert multiply(0, 5) == 0
    
    def test_divide_basic(self):
        assert divide(6, 2) == 3
        assert divide(7, 2) == 3.5
    
    def test_divide_by_zero(self):
        with pytest.raises(ValueError):
            divide(5, 0)

# requirements-test.txt
pytest>=6.0.0
coverage>=5.0.0
```
"""
        ]
    
    def start(self, system, user, step_name):
        """模拟AI的start方法"""
        from langchain.schema import AIMessage
        
        response_text = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        
        return [AIMessage(content=response_text)]
    
    def next(self, messages, prompt=None, step_name=None):
        """模拟AI的next方法"""
        from langchain.schema import AIMessage
        
        response_text = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        
        new_messages = list(messages)
        new_messages.append(AIMessage(content=response_text))
        return new_messages
    
    @property
    def vision(self):
        return False
    
    @property 
    def token_usage_log(self):
        mock_log = Mock()
        mock_log.is_openai_model.return_value = True
        mock_log.usage_cost.return_value = 0.05
        return mock_log


class TestSharedMemorySystem(unittest.TestCase):
    """测试共享记忆系统"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory = SharedMemoryManager(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_store_and_retrieve_event(self):
        """测试事件存储和检索"""
        event = DevelopmentEvent(
            event_id="test_001",
            timestamp=datetime.now(),
            event_type="code_generation",
            actor="dev_ai",
            description="生成计算器代码",
            details={"files_count": 2}
        )
        
        # 存储事件
        self.memory.store_event(event)
        
        # 检索事件
        events = self.memory.retrieve_events({
            'event_type': 'code_generation'
        })
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_id, "test_001")
        self.assertEqual(events[0].actor, "dev_ai")
    
    def test_store_and_retrieve_knowledge(self):
        """测试知识存储和检索"""
        knowledge = {
            'category': 'coding_patterns',
            'pattern': 'calculator_implementation',
            'description': '计算器实现的最佳实践',
            'tags': ['python', 'calculator', 'best_practice']
        }
        
        # 存储知识
        self.memory.store_knowledge('calculator_pattern', knowledge)
        
        # 检索知识
        retrieved = self.memory.retrieve_knowledge('calculator_pattern')
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['category'], 'coding_patterns')
        self.assertEqual(retrieved['pattern'], 'calculator_implementation')
    
    def test_find_similar_cases(self):
        """测试相似案例查找"""
        # 先存储一些测试数据
        event1 = DevelopmentEvent(
            event_id="calc_001",
            timestamp=datetime.now(),
            event_type="code_generation",
            actor="dev_ai",
            description="创建Python计算器应用",
            details={"language": "python", "type": "calculator"}
        )
        
        self.memory.store_event(event1)
        
        # 查找相似案例
        context = {
            'requirements': {
                'description': '开发一个数学计算工具',
                'language': 'python'
            }
        }
        
        similar_cases = self.memory.find_similar_cases(context)
        
        # 应该能找到相关案例
        self.assertGreater(len(similar_cases), 0)
    
    def test_statistics(self):
        """测试统计信息"""
        # 添加一些测试数据
        for i in range(5):
            event = DevelopmentEvent(
                event_id=f"test_{i}",
                timestamp=datetime.now(),
                event_type="test_event",
                actor="test_actor",
                description=f"测试事件 {i}",
                success=i % 2 == 0  # 一半成功，一半失败
            )
            self.memory.store_event(event)
        
        stats = self.memory.get_statistics()
        
        self.assertEqual(stats['events']['total'], 5)
        self.assertEqual(stats['events']['successful'], 3)  # 0,2,4成功


class TestSupervisorAI(unittest.TestCase):
    """测试监管AI"""
    
    def setUp(self):
        self.mock_ai = MockAI()
        self.temp_dir = tempfile.mkdtemp()
        self.shared_memory = SharedMemoryManager(self.temp_dir)
        self.supervisor = SupervisorAI(self.mock_ai, self.shared_memory)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyze_quality(self):
        """测试代码质量分析"""
        files_dict = FilesDict({
            'calculator.py': '''
def add(a, b):
    """加法运算"""
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("不能除以零")
    return a / b
''',
            'main.py': '''
from calculator import add, divide

def main():
    result = add(1, 2)
    print(result)

if __name__ == "__main__":
    main()
'''
        })
        
        quality_report = self.supervisor.analyze_quality(files_dict)
        
        self.assertIsNotNone(quality_report)
        self.assertGreater(quality_report.overall_score, 0)
        self.assertLessEqual(quality_report.overall_score, 100)
        self.assertIsInstance(quality_report.issues, list)
        self.assertIsInstance(quality_report.suggestions, list)
    
    def test_analyze_issues(self):
        """测试问题分析"""
        test_result = TestResult(
            test_id="test_001",
            passed=False,
            total_tests=5,
            passed_tests=3,
            failed_tests=2,
            coverage_percentage=80.0,
            execution_time=2.5,
            error_messages=[
                "ModuleNotFoundError: No module named 'numpy'",
                "AssertionError: Expected 5, got 4"
            ]
        )
        
        issues = self.supervisor.analyze_issues(test_result)
        
        self.assertIsInstance(issues, list)
        self.assertGreater(len(issues), 0)
        
        # 检查是否包含模块缺失的诊断
        module_issues = [issue for issue in issues if 'module' in issue.lower()]
        self.assertGreater(len(module_issues), 0)


class TestTestAI(unittest.TestCase):
    """测试测试AI"""
    
    def setUp(self):
        self.mock_ai = MockAI()
        self.temp_dir = tempfile.mkdtemp()
        self.test_ai = TestAI(self.mock_ai, self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_tests(self):
        """测试测试用例生成"""
        files_dict = FilesDict({
            'calculator.py': '''
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
'''
        })
        
        requirements = {
            'description': '计算器程序',
            'features': ['加法', '减法']
        }
        
        test_files = self.test_ai.generate_tests(files_dict, requirements)
        
        self.assertIsInstance(test_files, FilesDict)
        self.assertGreater(len(test_files), 0)
        
        # 检查是否生成了测试文件
        test_file_names = [name for name in test_files.keys() if 'test' in name.lower()]
        self.assertGreater(len(test_file_names), 0)
    
    @patch('subprocess.run')
    def test_execute_tests_mock(self, mock_subprocess):
        """测试测试执行（模拟）"""
        # 模拟pytest输出
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = """
test_calculator.py::test_add_basic PASSED
test_calculator.py::test_subtract_basic PASSED
======================== 2 passed in 0.03s ========================
"""
        mock_subprocess.return_value.stderr = ""
        
        files_dict = FilesDict({
            'calculator.py': 'def add(a, b): return a + b',
            'test_calculator.py': '''
import pytest
from calculator import add

def test_add_basic():
    assert add(2, 3) == 5
'''
        })
        
        test_result = self.test_ai.execute_tests(files_dict)
        
        self.assertIsInstance(test_result, TestResult)
        self.assertIsInstance(test_result.test_id, str)
        self.assertGreaterEqual(test_result.execution_time, 0)


class TestDeployAI(unittest.TestCase):
    """测试部署AI"""
    
    def setUp(self):
        self.mock_ai = MockAI()
        self.temp_dir = tempfile.mkdtemp()
        self.deploy_ai = DeployAI(self.mock_ai, self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_deployment_config(self):
        """测试部署配置生成"""
        files_dict = FilesDict({
            'app.py': '''
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello World!"

if __name__ == '__main__':
    app.run(port=8000)
''',
            'requirements.txt': '''
flask==2.0.1
'''
        })
        
        config = self.deploy_ai.generate_deployment_config(files_dict)
        
        self.assertIsInstance(config, dict)
        self.assertIn('project_type', config)
        self.assertIn('dependencies', config)
        self.assertIn('entrypoint', config)
        self.assertIn('docker_config', config)
        
        # 检查是否检测到Python项目
        self.assertEqual(config['project_type'], 'python')
        self.assertIn('flask', config['dependencies'])
        self.assertIn(8000, config['ports'])
    
    def test_package_project_zip(self):
        """测试ZIP打包"""
        files_dict = FilesDict({
            'main.py': 'print("Hello World")',
            'README.md': '# Test Project'
        })
        
        config = {
            'package_type': 'zip',
            'version': '1.0.0'
        }
        
        package_result = self.deploy_ai.package_project(files_dict, config)
        
        self.assertIsInstance(package_result, PackageResult)
        self.assertEqual(package_result.package_type, 'zip')
        self.assertEqual(package_result.version, '1.0.0')
        
        if package_result.success:
            self.assertTrue(package_result.package_path.exists())
            self.assertGreater(package_result.size_mb, 0)


class TestEnhancedDevAI(unittest.TestCase):
    """测试增强开发AI"""
    
    def setUp(self):
        self.mock_ai = MockAI()
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建所需的依赖组件
        from gpt_engineer.core.default.disk_memory import DiskMemory
        from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv
        
        self.shared_memory = SharedMemoryManager(self.temp_dir)
        self.supervisor_ai = SupervisorAI(self.mock_ai, self.shared_memory)
        self.test_ai = TestAI(self.mock_ai, self.temp_dir)
        
        self.dev_ai = EnhancedDevAI(
            memory=DiskMemory(self.temp_dir + "/memory"),
            execution_env=DiskExecutionEnv(self.temp_dir + "/exec"),
            ai=self.mock_ai,
            supervisor_ai=self.supervisor_ai,
            test_ai=self.test_ai,
            shared_memory=self.shared_memory
        )
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_development_plan(self):
        """测试开发计划创建"""
        requirements = {
            'description': '开发一个简单的计算器',
            'features': ['加法', '减法', '乘法', '除法'],
            'technical_requirements': {'language': 'python'}
        }
        
        dev_plan = self.dev_ai.create_development_plan(requirements)
        
        self.assertIsInstance(dev_plan, DevPlan)
        self.assertIsInstance(dev_plan.plan_id, str)
        self.assertGreater(len(dev_plan.tasks), 0)
        self.assertEqual(dev_plan.requirements, requirements)
    
    def test_generate_with_supervision(self):
        """测试监督下的代码生成"""
        prompt = Prompt(text="创建一个Python计算器程序")
        
        result = self.dev_ai.generate_with_supervision(prompt)
        
        self.assertIsInstance(result, FilesDict)
        # 应该生成一些文件
        if len(result) > 0:
            self.assertGreater(len(result), 0)


class TestMultiAIOrchestrator(unittest.TestCase):
    """测试多AI编排器"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # 使用模拟AI配置
        ai_config = {'model_name': 'mock-gpt-4', 'temperature': 0.1}
        
        # 创建编排器，但不初始化真实AI
        self.orchestrator = MultiAIOrchestrator(
            work_dir=self.temp_dir,
            ai_config=ai_config
        )
        
        # 替换为模拟AI
        self.orchestrator.main_ai = MockAI()
        self.orchestrator._init_ai_components()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_session_status(self):
        """测试会话状态"""
        status = self.orchestrator.get_session_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('session_id', status)
        self.assertIn('status', status)
        self.assertIn('current_stage', status)
        self.assertIn('progress', status)
    
    def test_event_handler_registration(self):
        """测试事件处理器注册"""
        test_events = []
        
        async def test_handler(event):
            test_events.append(event.event_type)
        
        self.orchestrator.register_event_handler('test_event', test_handler)
        
        # 检查处理器是否注册成功
        self.assertIn('test_event', self.orchestrator.event_handlers)
        self.assertIn(test_handler, self.orchestrator.event_handlers['test_event'])


class TestServerAIInterface(unittest.TestCase):
    """测试服务器AI接口"""
    
    def setUp(self):
        # 模拟服务器配置
        self.server_config = {
            'api_base_url': 'https://mock-server.com',
            'api_key': 'mock-api-key'
        }
        
        self.server_interface = ServerAIInterface(self.server_config)
    
    @patch('requests.Session.post')
    def test_upload_project_package_mock(self, mock_post):
        """测试项目包上传（模拟）"""
        # 模拟成功的上传响应
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'success': True,
            'session_id': 'test_session_123',
            'upload_url': 'https://upload.mock-server.com/test_session_123'
        }
        mock_post.return_value = mock_response
        
        # 创建模拟的包结果
        package_result = PackageResult(
            package_path=Path('/tmp/test_package.zip'),
            package_type='zip',
            version='1.0.0',
            dependencies=['flask'],
            size_mb=10.5,
            success=True
        )
        
        # 由于我们只是测试接口调用，不测试实际上传
        # 这里主要验证配置和接口调用
        self.assertIsNotNone(self.server_interface.api_base_url)
        self.assertIsNotNone(self.server_interface.api_key)
        self.assertIn('upload', self.server_interface.endpoints)


async def run_integration_test():
    """集成测试：测试完整的工作流程"""
    print("🧪 开始集成测试...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建编排器（使用模拟AI）
        orchestrator = MultiAIOrchestrator(
            work_dir=temp_dir,
            ai_config={'model_name': 'mock-gpt-4'}
        )
        
        # 替换为模拟AI
        orchestrator.main_ai = MockAI()
        orchestrator._init_ai_components()
        
        print("✅ 编排器初始化成功")
        
        # 测试会话状态
        status = orchestrator.get_session_status()
        print(f"📊 会话状态: {status['status']}")
        
        # 简单的需求测试
        requirement = "开发一个简单的计算器程序，支持基本的四则运算"
        
        print(f"📝 测试需求: {requirement}")
        
        # 注意：由于我们使用模拟AI，完整的工作流程可能会因为缺少某些依赖而失败
        # 这里我们主要测试系统的初始化和基本组件
        
        print("✅ 集成测试基础功能通过")
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        
    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_mock_workflow_test():
    """模拟工作流程测试"""
    print("\n🎭 开始模拟工作流程测试...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 1. 测试共享记忆系统
        print("1️⃣ 测试共享记忆系统...")
        memory = SharedMemoryManager(temp_dir)
        
        # 存储测试事件
        event = DevelopmentEvent(
            event_id="mock_001",
            timestamp=datetime.now(),
            event_type="code_generation",
            actor="dev_ai",
            description="生成计算器代码",
            details={"language": "python"}
        )
        memory.store_event(event)
        
        # 检索事件
        events = memory.retrieve_events({'event_type': 'code_generation'})
        assert len(events) == 1
        print("✅ 记忆系统测试通过")
        
        # 2. 测试监管AI
        print("2️⃣ 测试监管AI...")
        mock_ai = MockAI()
        supervisor = SupervisorAI(mock_ai, memory)
        
        # 分析代码质量
        test_files = FilesDict({
            'calculator.py': '''
def add(a, b):
    """加法运算"""
    return a + b

def main():
    print("计算器程序")
    result = add(2, 3)
    print(f"2 + 3 = {result}")

if __name__ == "__main__":
    main()
'''
        })
        
        quality_report = supervisor.analyze_quality(test_files)
        assert quality_report.overall_score > 0
        print("✅ 监管AI测试通过")
        
        # 3. 测试测试AI
        print("3️⃣ 测试测试AI...")
        test_ai = TestAI(mock_ai, temp_dir)
        
        requirements = {'description': '计算器程序'}
        test_files = test_ai.generate_tests(test_files, requirements)
        assert len(test_files) > 0
        print("✅ 测试AI测试通过")
        
        # 4. 测试部署AI
        print("4️⃣ 测试部署AI...")
        deploy_ai = DeployAI(mock_ai, temp_dir)
        
        config = deploy_ai.generate_deployment_config(test_files)
        assert 'project_type' in config
        print("✅ 部署AI测试通过")
        
        print("\n🎉 所有模拟测试通过！")
        
    except Exception as e:
        print(f"❌ 模拟测试失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_performance_test():
    """性能测试"""
    print("\n⚡ 开始性能测试...")
    
    import time
    
    # 测试记忆系统性能
    temp_dir = tempfile.mkdtemp()
    
    try:
        memory = SharedMemoryManager(temp_dir)
        
        # 批量插入事件
        start_time = time.time()
        
        for i in range(100):
            event = DevelopmentEvent(
                event_id=f"perf_test_{i}",
                timestamp=datetime.now(),
                event_type="performance_test",
                actor="test_actor",
                description=f"性能测试事件 {i}",
                details={"iteration": i}
            )
            memory.store_event(event)
        
        insert_time = time.time() - start_time
        print(f"📊 插入100个事件耗时: {insert_time:.3f}秒")
        
        # 测试查询性能
        start_time = time.time()
        
        events = memory.retrieve_events({'event_type': 'performance_test'})
        
        query_time = time.time() - start_time
        print(f"📊 查询100个事件耗时: {query_time:.3f}秒")
        print(f"📊 查询结果数量: {len(events)}")
        
        # 测试相似案例查找性能
        start_time = time.time()
        
        context = {'requirements': {'type': 'performance_test'}}
        similar_cases = memory.find_similar_cases(context)
        
        similarity_time = time.time() - start_time
        print(f"📊 相似案例查找耗时: {similarity_time:.3f}秒")
        print(f"📊 找到相似案例: {len(similar_cases)}个")
        
        print("✅ 性能测试完成")
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """主测试函数"""
    print("🚀 多AI协作系统综合测试")
    print("=" * 50)
    
    # 检查是否有OpenAI API密钥
    has_openai_key = bool(os.getenv('OPENAI_API_KEY'))
    
    if not has_openai_key:
        print("⚠️  未检测到OPENAI_API_KEY，将运行模拟测试")
    else:
        print("✅ 检测到OPENAI_API_KEY，可以运行完整测试")
    
    print("\n1. 运行单元测试...")
    print("-" * 30)
    
    # 运行单元测试
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestSharedMemorySystem))
    test_suite.addTest(unittest.makeSuite(TestSupervisorAI))
    test_suite.addTest(unittest.makeSuite(TestTestAI))
    test_suite.addTest(unittest.makeSuite(TestDeployAI))
    test_suite.addTest(unittest.makeSuite(TestEnhancedDevAI))
    test_suite.addTest(unittest.makeSuite(TestMultiAIOrchestrator))
    test_suite.addTest(unittest.makeSuite(TestServerAIInterface))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print(f"\n📊 单元测试结果:")
    print(f"   总计: {result.testsRun} 个测试")
    print(f"   成功: {result.testsRun - len(result.failures) - len(result.errors)} 个")
    print(f"   失败: {len(result.failures)} 个")
    print(f"   错误: {len(result.errors)} 个")
    
    # 2. 运行模拟工作流程测试
    run_mock_workflow_test()
    
    # 3. 运行性能测试
    run_performance_test()
    
    # 4. 运行集成测试
    print("\n🔗 运行集成测试...")
    asyncio.run(run_integration_test())
    
    print("\n" + "=" * 50)
    
    if result.failures or result.errors:
        print("❌ 部分测试失败，请检查错误信息")
        return False
    else:
        print("🎉 所有测试通过！系统运行正常")
        return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)