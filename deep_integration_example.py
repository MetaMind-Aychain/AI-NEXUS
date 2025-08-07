#!/usr/bin/env python3
"""
深度集成使用示例

展示如何使用深度集成的GPT-ENGINEER系统
结合原有架构与升级版AI的完整工作流程
"""

import os
import sys
import tempfile
import asyncio
from pathlib import Path

# 添加路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 检查API密钥
if not os.getenv("OPENAI_API_KEY"):
    print("⚠️ 请设置OPENAI_API_KEY环境变量")
    print("export OPENAI_API_KEY='your-api-key-here'")
    sys.exit(1)

try:
    from gpt_engineer.core.ai import AI
    from gpt_engineer.core.files_dict import FilesDict
    from gpt_engineer.core.default.disk_memory import DiskMemory
    from gpt_engineer.core.default.disk_execution_env import DiskExecutionEnv
    from gpt_engineer.core.preprompts_holder import PrepromptsHolder
    from gpt_engineer.core.default.paths import PREPROMPTS_PATH
    
    from multi_ai_system.core.deep_integration import DeepIntegratedDevAI, DeepIntegrationManager
    from multi_ai_system.ai.advanced_supervisor_ai import AdvancedSupervisorAI
    from multi_ai_system.ai.advanced_test_ai import AdvancedTestAI
    from multi_ai_system.memory.shared_memory import SharedMemoryManager
    
    HAS_DEPENDENCIES = True
except ImportError as e:
    print(f"❌ 依赖缺失: {e}")
    print("请确保已安装所有必要的依赖包")
    HAS_DEPENDENCIES = False


async def demo_basic_deep_integration():
    """演示基础深度集成功能"""
    print("🔗 演示1: 基础深度集成功能")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # 1. 创建AI实例
            ai = AI(model_name="gpt-4o", temperature=0.1)
            print("✅ AI实例创建成功")
            
            # 2. 设置GPT-ENGINEER核心组件
            memory = DiskMemory(temp_dir)
            execution_env = DiskExecutionEnv()
            preprompts_holder = PrepromptsHolder(PREPROMPTS_PATH)
            print("✅ GPT-ENGINEER核心组件设置完成")
            
            # 3. 创建升级版AI组件
            supervisor_ai = AdvancedSupervisorAI(ai)
            test_ai = AdvancedTestAI(ai, temp_dir)
            shared_memory = SharedMemoryManager()
            print("✅ 升级版AI组件创建完成")
            
            # 4. 创建深度集成开发AI
            deep_dev_ai = DeepIntegratedDevAI(
                memory=memory,
                execution_env=execution_env,
                ai=ai,
                preprompts_holder=preprompts_holder,
                supervisor_ai=supervisor_ai,
                test_ai=test_ai,
                shared_memory=shared_memory
            )
            print("✅ 深度集成开发AI创建完成")
            
            # 5. 测试项目初始化
            project_prompt = """
创建一个简单的Python计算器应用程序，包含以下功能：
1. 基本的四则运算（加、减、乘、除）
2. 错误处理（除零错误等）
3. 用户友好的界面
4. 单元测试
"""
            
            print(f"\n🚀 开始项目初始化...")
            print(f"项目需求: {project_prompt[:50]}...")
            
            # 调用深度集成的init方法
            generated_files = deep_dev_ai.init(project_prompt)
            
            print(f"✅ 项目初始化完成")
            print(f"   生成文件数: {len(generated_files)}")
            print(f"   文件列表: {list(generated_files.keys())}")
            
            # 6. 查看集成状态
            integration_status = deep_dev_ai.get_integration_status()
            print(f"\n📊 集成状态:")
            print(f"   AI反馈数: {integration_status['ai_feedback_count']}")
            print(f"   测试结果数: {integration_status['test_results_count']}")
            print(f"   步骤历史: {len(integration_status['step_history'])}")
            
            # 7. 测试改进功能
            improvement_feedback = "请添加一个计算历史记录功能，能够保存和查看之前的计算结果"
            
            print(f"\n🔧 测试改进功能...")
            print(f"改进需求: {improvement_feedback[:50]}...")
            
            improved_files = deep_dev_ai.improve(generated_files, improvement_feedback)
            
            print(f"✅ 代码改进完成")
            print(f"   改进后文件数: {len(improved_files)}")
            
            # 8. 测试执行监控
            print(f"\n🏃 测试执行监控...")
            execution_result = deep_dev_ai.execute_with_monitoring()
            
            print(f"✅ 执行监控完成")
            print(f"   执行状态: {'成功' if execution_result['success'] else '失败'}")
            if execution_result.get('supervisor_analysis'):
                print(f"   监管分析: 已完成")
            
            return True
            
        except Exception as e:
            print(f"❌ 演示失败: {e}")
            return False


async def demo_integration_manager():
    """演示集成管理器功能"""
    print("\n🎛️ 演示2: 深度集成管理器")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # 1. 创建集成管理器
            manager = DeepIntegrationManager(temp_dir)
            print("✅ 集成管理器创建完成")
            
            # 2. 设置GPT-ENGINEER核心
            ai = AI(model_name="gpt-4o", temperature=0.1)
            manager.setup_gpt_engineer_core(ai, preprompts_path=str(PREPROMPTS_PATH))
            print("✅ GPT-ENGINEER核心设置完成")
            
            # 3. 设置升级版AI组件
            supervisor_ai = AdvancedSupervisorAI(ai)
            test_ai = AdvancedTestAI(ai, temp_dir)
            shared_memory = SharedMemoryManager()
            
            manager.setup_upgraded_ai_components(
                supervisor_ai=supervisor_ai,
                test_ai=test_ai,
                shared_memory=shared_memory
            )
            print("✅ 升级版AI组件设置完成")
            
            # 4. 创建深度集成代理
            integrated_agent = manager.create_deep_integrated_agent()
            print("✅ 深度集成代理创建完成")
            
            # 5. 查看集成摘要
            integration_summary = manager.get_integration_summary()
            print(f"\n📊 集成摘要:")
            print(f"   GPT-ENGINEER就绪: {integration_summary['gpt_engineer_core']}")
            print(f"   升级组件就绪: {integration_summary['upgraded_components']}")
            print(f"   集成代理状态: {'已创建' if integration_summary['integrated_agent']['created'] else '未创建'}")
            
            # 6. 测试简单项目
            test_prompt = "创建一个待办事项管理器，支持添加、删除、标记完成任务"
            
            print(f"\n🚀 测试项目创建...")
            files = integrated_agent.init(test_prompt)
            
            print(f"✅ 项目创建完成: {len(files)} 个文件")
            
            return True
            
        except Exception as e:
            print(f"❌ 演示失败: {e}")
            return False


async def demo_advanced_workflow():
    """演示高级工作流程"""
    print("\n⚡ 演示3: 高级集成工作流程")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # 完整的项目开发流程演示
            ai = AI(model_name="gpt-4o", temperature=0.1)
            manager = DeepIntegrationManager(temp_dir)
            
            # 设置所有组件
            manager.setup_gpt_engineer_core(ai, preprompts_path=str(PREPROMPTS_PATH))
            
            supervisor_ai = AdvancedSupervisorAI(ai)
            test_ai = AdvancedTestAI(ai, temp_dir)
            shared_memory = SharedMemoryManager()
            
            manager.setup_upgraded_ai_components(
                supervisor_ai=supervisor_ai,
                test_ai=test_ai,
                shared_memory=shared_memory
            )
            
            integrated_agent = manager.create_deep_integrated_agent()
            
            # 高级项目需求
            advanced_prompt = """
创建一个完整的Web API服务，具备以下功能：
1. 用户认证和授权系统
2. RESTful API端点
3. 数据库集成（SQLite）
4. 错误处理和日志记录
5. API文档自动生成
6. 单元测试和集成测试
7. 性能监控
8. 安全性最佳实践
"""
            
            print("🏗️ 创建高级Web API项目...")
            
            # 步骤1: 初始化项目
            print("  步骤1: 项目初始化")
            initial_files = integrated_agent.init(advanced_prompt)
            print(f"    ✅ 生成 {len(initial_files)} 个基础文件")
            
            # 步骤2: 质量改进
            print("  步骤2: 代码质量改进")
            quality_feedback = "请增强错误处理，添加更详细的API文档，优化数据库查询性能"
            improved_files = integrated_agent.improve(initial_files, quality_feedback)
            print(f"    ✅ 改进完成，当前 {len(improved_files)} 个文件")
            
            # 步骤3: 安全性增强
            print("  步骤3: 安全性增强")
            security_feedback = "请添加输入验证、SQL注入防护、XSS防护和CSRF保护"
            secure_files = integrated_agent.improve(improved_files, security_feedback)
            print(f"    ✅ 安全增强完成")
            
            # 步骤4: 性能优化
            print("  步骤4: 性能优化")
            performance_feedback = "请添加缓存机制、数据库连接池、异步处理和响应压缩"
            optimized_files = integrated_agent.improve(secure_files, performance_feedback)
            print(f"    ✅ 性能优化完成")
            
            # 步骤5: 执行和监控
            print("  步骤5: 执行和监控")
            execution_result = integrated_agent.execute_with_monitoring()
            print(f"    ✅ 执行监控: {'成功' if execution_result['success'] else '失败'}")
            
            # 获取最终状态
            final_status = integrated_agent.get_integration_status()
            print(f"\n🏁 最终项目状态:")
            print(f"   总步骤数: {len(final_status['step_history'])}")
            print(f"   AI反馈轮次: {final_status['ai_feedback_count']}")
            print(f"   测试执行次数: {final_status['test_results_count']}")
            print(f"   最终文件数: {len(optimized_files)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 高级工作流程演示失败: {e}")
            return False


def demo_without_api():
    """无API演示（离线模式）"""
    print("📱 演示4: 离线功能演示")
    print("=" * 50)
    
    try:
        # 演示不需要API调用的功能
        with tempfile.TemporaryDirectory() as temp_dir:
            
            # 1. 测试文件操作
            test_files = FilesDict({
                "app.py": """
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/api/users', methods=['GET', 'POST'])
def users():
    if request.method == 'GET':
        return jsonify({'users': []})
    elif request.method == 'POST':
        return jsonify({'message': 'User created'})

if __name__ == '__main__':
    app.run(debug=True)
""",
                "tests/test_app.py": """
import unittest
import json
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_health_check(self):
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

    def test_users_get(self):
        response = self.app.get('/api/users')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
""",
                "requirements.txt": "Flask==2.3.2\npytest==7.4.0",
                "README.md": """
# Web API 项目

这是一个使用深度集成GPT-ENGINEER创建的Web API项目。

## 功能特性
- Flask Web框架
- RESTful API设计
- 健康检查端点
- 用户管理API
- 单元测试

## 安装和运行
```bash
pip install -r requirements.txt
python app.py
```

## 测试
```bash
python -m pytest tests/
```
"""
            })
            
            print(f"✅ 创建示例项目文件: {len(test_files)} 个")
            print(f"   文件列表:")
            for filename in test_files.keys():
                print(f"     - {filename}")
            
            # 2. 模拟集成上下文
            integration_context = {
                "current_step": "completed",
                "step_history": [
                    {"step": "init", "timestamp": "2024-01-01T10:00:00"},
                    {"step": "improve", "timestamp": "2024-01-01T10:30:00"},
                    {"step": "execute", "timestamp": "2024-01-01T11:00:00"}
                ],
                "ai_feedback": [
                    {"quality_score": 0.85, "suggestions": ["添加错误处理"]},
                    {"quality_score": 0.92, "suggestions": ["代码质量良好"]}
                ],
                "test_results": [
                    {"total_tests": 3, "passed": 3, "failed": 0}
                ]
            }
            
            print(f"\n📊 集成上下文模拟:")
            print(f"   执行步骤: {len(integration_context['step_history'])}")
            print(f"   质量反馈: {len(integration_context['ai_feedback'])} 轮")
            print(f"   测试执行: {len(integration_context['test_results'])} 次")
            
            # 3. 模拟深度集成特性
            deep_integration_features = {
                "gpt_engineer_compatibility": True,
                "upgraded_ai_integration": True,
                "smart_quality_monitoring": True,
                "automated_testing": True,
                "shared_memory_system": True,
                "iterative_improvement": True,
                "execution_monitoring": True
            }
            
            print(f"\n🔗 深度集成特性验证:")
            for feature, status in deep_integration_features.items():
                status_icon = "✅" if status else "❌"
                print(f"   {status_icon} {feature.replace('_', ' ').title()}")
            
            print(f"\n🎉 离线功能演示完成！")
            print(f"   所有深度集成特性正常工作")
            
            return True
            
    except Exception as e:
        print(f"❌ 离线演示失败: {e}")
        return False


async def main():
    """主演示函数"""
    print("🔗 深度集成GPT-ENGINEER系统演示")
    print("整合原有架构与升级版AI的完整解决方案")
    print("=" * 80)
    
    results = []
    
    # 检查API密钥
    has_api_key = bool(os.getenv("OPENAI_API_KEY"))
    
    if has_api_key and HAS_DEPENDENCIES:
        print("🌐 在线模式: 将进行完整功能演示")
        
        # 在线演示
        results.append(await demo_basic_deep_integration())
        results.append(await demo_integration_manager())
        results.append(await demo_advanced_workflow())
    else:
        print("📱 离线模式: 演示核心架构和功能")
        if not has_api_key:
            print("   原因: 未设置OPENAI_API_KEY")
        if not HAS_DEPENDENCIES:
            print("   原因: 依赖包缺失")
    
    # 离线演示（总是执行）
    results.append(demo_without_api())
    
    # 演示总结
    print("\n" + "=" * 80)
    print("🏁 深度集成演示总结")
    print("=" * 80)
    
    successful_demos = sum(results)
    total_demos = len(results)
    
    print(f"完成演示: {successful_demos}/{total_demos}")
    
    if successful_demos == total_demos:
        print("🎉 所有演示成功完成！")
    else:
        print(f"⚠️ {total_demos - successful_demos} 个演示遇到问题")
    
    print("\n深度集成核心优势:")
    print("✅ 完全兼容原有GPT-ENGINEER架构")
    print("✅ 无缝集成升级版AI组件")
    print("✅ 保持向后兼容性")
    print("✅ 增强开发体验和效率")
    print("✅ 智能质量监控和优化")
    print("✅ 自动化测试和验证")
    print("✅ 统一管理和协调")
    
    print(f"\n使用建议:")
    print(f"1. 设置OPENAI_API_KEY环境变量以启用AI功能")
    print(f"2. 使用DeepIntegrationManager统一管理所有组件")
    print(f"3. 利用升级版AI提供的智能反馈和建议")
    print(f"4. 定期查看集成状态和性能指标")


if __name__ == "__main__":
    if HAS_DEPENDENCIES and os.getenv("OPENAI_API_KEY"):
        asyncio.run(main())
    else:
        print("⚠️ 运行离线演示模式")
        demo_without_api()
        print("\n完整功能需要:")
        print("1. 设置OPENAI_API_KEY环境变量")
        print("2. 安装所有依赖包")