"""
多AI协作系统使用示例

展示如何使用多AI协作系统进行完整的项目开发
"""

import asyncio
import json
from pathlib import Path

from multi_ai_system.orchestrator import MultiAIOrchestrator


async def example_full_development():
    """完整开发流程示例"""
    
    # 用户需求
    user_requirement = """
请开发一个简单的任务管理系统，包含以下功能：

1. 用户可以创建、编辑、删除任务
2. 任务包含标题、描述、优先级、截止日期
3. 用户可以标记任务为完成状态
4. 提供任务列表查看和筛选功能
5. 简单的Web界面
6. 使用Python Flask作为后端
7. 使用SQLite作为数据库

技术要求：
- 后端：Python Flask
- 前端：HTML/CSS/JavaScript
- 数据库：SQLite
- 支持RESTful API
- 响应式设计
"""
    
    # 配置工作目录
    work_dir = "./example_project"
    
    # AI配置
    ai_config = {
        'model_name': 'gpt-4o',
        'temperature': 0.1
    }
    
    # 工作流配置
    workflow_config = {
        'max_dev_iterations': 3,
        'package_type': 'docker',
        'include_frontend': True,
        'auto_deploy': True,
        'deploy_platform': 'docker',
        'deploy_port': 8080
    }
    
    # 创建编排器
    orchestrator = MultiAIOrchestrator(
        work_dir=work_dir,
        ai_config=ai_config,
        workflow_config=workflow_config
    )
    
    # 工作流选项
    workflow_options = {
        'include_frontend': True,
        'auto_deploy': True,
        'deploy_platform': 'docker',
        'deploy_port': 8080
    }
    
    print("开始多AI协作开发...")
    print(f"用户需求: {user_requirement}")
    print("=" * 50)
    
    try:
        # 执行完整工作流
        result = await orchestrator.execute_workflow(
            user_requirement=user_requirement,
            workflow_options=workflow_options
        )
        
        # 输出结果
        print("\n" + "=" * 50)
        print("开发完成！")
        print(f"项目ID: {result.project_id}")
        print(f"成功状态: {result.success}")
        print(f"最终评分: {result.final_score:.1f}/100")
        print(f"开发时间: {result.development_time:.1f} 秒")
        print(f"生成文件数: {len(result.files)}")
        
        if result.deployment:
            print(f"部署状态: {result.deployment.status}")
            if result.deployment.url:
                print(f"访问地址: {result.deployment.url}")
        
        # 显示生成的文件
        print("\n生成的文件:")
        for filename in result.files.keys():
            print(f"  - {filename}")
        
        # 显示测试结果
        if result.test_results:
            print(f"\n测试结果:")
            for i, test_result in enumerate(result.test_results):
                print(f"  测试 {i+1}: {test_result.passed_tests}/{test_result.total_tests} 通过")
                print(f"    覆盖率: {test_result.coverage_percentage:.1f}%")
        
        return result
        
    except Exception as e:
        print(f"开发过程中出现错误: {e}")
        return None


async def example_step_by_step():
    """分步骤执行示例"""
    
    work_dir = "./step_by_step_project"
    
    # 创建编排器
    orchestrator = MultiAIOrchestrator(work_dir=work_dir)
    
    # 监控进度
    def progress_callback():
        status = orchestrator.get_session_status()
        print(f"当前阶段: {status['current_stage']}, 进度: {status['progress']:.1f}%")
    
    # 注册进度监控事件处理器
    orchestrator.register_event_handler('*', lambda event: progress_callback())
    
    # 简单需求
    requirement = "创建一个计算器程序，支持基本的加减乘除运算"
    
    # 执行开发
    result = await orchestrator.execute_workflow(requirement)
    
    return result


async def example_custom_workflow():
    """自定义工作流示例"""
    
    work_dir = "./custom_workflow_project"
    
    # 自定义配置
    custom_config = {
        'max_dev_iterations': 2,  # 减少迭代次数
        'package_type': 'zip',    # 使用ZIP打包
    }
    
    orchestrator = MultiAIOrchestrator(
        work_dir=work_dir,
        workflow_config=custom_config
    )
    
    requirement = "开发一个简单的博客系统"
    
    # 自定义工作流选项
    options = {
        'include_frontend': False,  # 不包含前端
        'auto_deploy': False,       # 不自动部署
    }
    
    result = await orchestrator.execute_workflow(requirement, options)
    
    return result


def example_memory_analysis():
    """记忆分析示例"""
    
    from multi_ai_system.memory.shared_memory import SharedMemoryManager
    
    # 创建记忆管理器
    memory = SharedMemoryManager("./memory_example")
    
    # 获取统计信息
    stats = memory.get_statistics()
    
    print("记忆系统统计:")
    print(f"总事件数: {stats['events']['total']}")
    print(f"成功事件数: {stats['events']['successful']}")
    print(f"知识条目数: {stats['knowledge']['total']}")
    print(f"项目数: {stats['events']['projects']}")
    
    # 查找相似案例
    context = {
        'requirements': {
            'description': '开发一个Web应用',
            'technology': 'Python Flask'
        }
    }
    
    similar_cases = memory.find_similar_cases(context)
    print(f"\n找到 {len(similar_cases)} 个相似案例:")
    for case in similar_cases[:3]:
        print(f"  - {case.get('type', 'unknown')}: {case.get('description', 'N/A')}")


async def main():
    """主函数 - 运行所有示例"""
    
    print("多AI协作系统使用示例\n")
    
    # 示例1：完整开发流程
    print("1. 完整开发流程示例")
    print("-" * 30)
    # result1 = await example_full_development()
    
    # 示例2：分步骤执行
    print("\n2. 分步骤执行示例")
    print("-" * 30)
    # result2 = await example_step_by_step()
    
    # 示例3：自定义工作流
    print("\n3. 自定义工作流示例")
    print("-" * 30)
    # result3 = await example_custom_workflow()
    
    # 示例4：记忆分析
    print("\n4. 记忆分析示例")
    print("-" * 30)
    example_memory_analysis()
    
    print("\n所有示例完成!")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())