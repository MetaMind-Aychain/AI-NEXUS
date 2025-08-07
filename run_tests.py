"""
多AI协作系统测试运行器

这个脚本提供了多种测试选项：
- 快速测试：基本功能验证
- 完整测试：所有组件的详细测试
- 性能测试：系统性能评估
- 演示模式：展示系统工作流程
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def check_environment():
    """检查环境配置"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return False
    
    print(f"✅ Python版本: {sys.version}")
    
    # 检查必要的模块
    required_modules = [
        'sqlite3', 'json', 'datetime', 'pathlib', 'tempfile', 'unittest'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ 缺少必要模块: {', '.join(missing_modules)}")
        return False
    
    print("✅ 所有必要模块已安装")
    
    # 检查OpenAI API密钥
    has_openai_key = bool(os.getenv('OPENAI_API_KEY'))
    if has_openai_key:
        print("✅ 检测到OPENAI_API_KEY")
    else:
        print("⚠️  未检测到OPENAI_API_KEY，将使用模拟模式")
    
    return True

def run_quick_test():
    """快速测试 - 验证基本功能"""
    print("\n🏃‍♂️ 执行快速测试...")
    print("=" * 40)
    
    try:
        from test_multi_ai_system import (
            TestSharedMemorySystem, 
            TestSupervisorAI,
            run_mock_workflow_test
        )
        import unittest
        
        # 运行核心组件测试
        test_suite = unittest.TestSuite()
        test_suite.addTest(unittest.makeSuite(TestSharedMemorySystem))
        test_suite.addTest(unittest.makeSuite(TestSupervisorAI))
        
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(test_suite)
        
        # 运行模拟工作流程
        run_mock_workflow_test()
        
        if result.failures or result.errors:
            print("❌ 快速测试发现问题")
            return False
        else:
            print("✅ 快速测试通过！")
            return True
            
    except Exception as e:
        print(f"❌ 快速测试执行失败: {e}")
        return False

def run_full_test():
    """完整测试 - 所有组件详细测试"""
    print("\n🔬 执行完整测试...")
    print("=" * 40)
    
    try:
        from test_multi_ai_system import main as run_all_tests
        return run_all_tests()
        
    except Exception as e:
        print(f"❌ 完整测试执行失败: {e}")
        return False

def run_performance_test():
    """性能测试"""
    print("\n⚡ 执行性能测试...")
    print("=" * 40)
    
    try:
        from test_multi_ai_system import run_performance_test
        run_performance_test()
        return True
        
    except Exception as e:
        print(f"❌ 性能测试执行失败: {e}")
        return False

async def run_demo():
    """演示模式 - 展示系统工作流程"""
    print("\n🎭 演示模式...")
    print("=" * 40)
    
    try:
        # 导入必要模块
        from multi_ai_system import create_orchestrator
        from test_multi_ai_system import MockAI
        import tempfile
        
        # 创建临时工作目录
        temp_dir = tempfile.mkdtemp()
        print(f"📁 工作目录: {temp_dir}")
        
        # 创建编排器
        orchestrator = create_orchestrator(
            work_dir=temp_dir,
            ai_config={'model_name': 'mock-gpt-4o'}
        )
        
        # 使用模拟AI
        orchestrator.main_ai = MockAI()
        orchestrator._init_ai_components()
        
        print("🤖 多AI系统初始化完成")
        
        # 演示需求
        requirement = """
开发一个简单的任务管理系统，包含以下功能：
1. 添加任务
2. 查看任务列表
3. 标记任务完成
4. 删除任务
5. 简单的命令行界面
        """
        
        print(f"📝 演示需求:\n{requirement}")
        print("\n🔄 开始工作流程演示...")
        
        # 获取会话状态
        status = orchestrator.get_session_status()
        print(f"📊 当前状态: {status['status']}")
        print(f"🎯 当前阶段: {status['current_stage']}")
        
        # 演示各个AI组件
        print("\n1️⃣ 监管AI质量分析演示...")
        from gpt_engineer.core.files_dict import FilesDict
        
        sample_code = FilesDict({
            'task_manager.py': '''
def add_task(tasks, task):
    """添加新任务"""
    tasks.append({"id": len(tasks) + 1, "text": task, "done": False})
    return tasks

def list_tasks(tasks):
    """显示任务列表"""
    for task in tasks:
        status = "✓" if task["done"] else "○"
        print(f"{status} {task['id']}. {task['text']}")

def main():
    tasks = []
    while True:
        print("\\n任务管理器")
        print("1. 添加任务")
        print("2. 查看任务")
        print("3. 退出")
        
        choice = input("请选择: ")
        if choice == "1":
            task = input("输入任务: ")
            add_task(tasks, task)
        elif choice == "2":
            list_tasks(tasks)
        elif choice == "3":
            break

if __name__ == "__main__":
    main()
'''
        })
        
        quality_report = orchestrator.supervisor_ai.analyze_quality(sample_code)
        print(f"   📊 代码质量评分: {quality_report.overall_score:.1f}/100")
        print(f"   🔍 发现问题: {len(quality_report.issues)} 个")
        print(f"   💡 改进建议: {len(quality_report.suggestions)} 条")
        
        print("\n2️⃣ 测试AI测试生成演示...")
        requirements = {'description': '任务管理系统', 'features': ['添加任务', '查看任务']}
        test_files = orchestrator.test_ai.generate_tests(sample_code, requirements)
        print(f"   🧪 生成测试文件: {len(test_files)} 个")
        for filename in test_files.keys():
            print(f"      - {filename}")
        
        print("\n3️⃣ 部署AI配置生成演示...")
        deploy_config = orchestrator.deploy_ai.generate_deployment_config(sample_code)
        print(f"   🚀 项目类型: {deploy_config['project_type']}")
        print(f"   📦 入口文件: {deploy_config['entrypoint']}")
        print(f"   🔌 检测端口: {deploy_config['ports']}")
        
        print("\n4️⃣ 共享记忆系统演示...")
        stats = orchestrator.shared_memory.get_statistics()
        print(f"   💾 存储事件: {stats['events']['total']} 个")
        print(f"   📚 知识条目: {stats['knowledge']['total']} 个")
        
        print("\n🎉 演示完成！")
        print("💡 这只是系统功能的一个简单展示")
        print("💡 完整的工作流程会自动执行所有这些步骤")
        
        # 清理
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return True
        
    except Exception as e:
        print(f"❌ 演示执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='多AI协作系统测试运行器')
    parser.add_argument('--mode', '-m', 
                       choices=['quick', 'full', 'performance', 'demo', 'check'],
                       default='quick',
                       help='测试模式 (默认: quick)')
    
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='详细输出')
    
    args = parser.parse_args()
    
    print("🚀 多AI协作系统测试运行器")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请解决上述问题后重试")
        return False
    
    success = False
    
    if args.mode == 'check':
        print("\n✅ 环境检查完成，系统可以运行")
        success = True
        
    elif args.mode == 'quick':
        success = run_quick_test()
        
    elif args.mode == 'full':
        success = run_full_test()
        
    elif args.mode == 'performance':
        success = run_performance_test()
        
    elif args.mode == 'demo':
        success = asyncio.run(run_demo())
    
    print("\n" + "=" * 50)
    
    if success:
        print("🎉 测试执行成功！")
        print("\n📋 后续建议:")
        print("   1. 查看 README_多AI协作系统.md 了解详细用法")
        print("   2. 运行 python -m multi_ai_system.examples.usage_example")
        print("   3. 设置 OPENAI_API_KEY 体验完整功能")
    else:
        print("❌ 测试执行失败，请检查错误信息")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)