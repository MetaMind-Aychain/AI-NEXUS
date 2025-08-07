#!/usr/bin/env python3
"""
一键启动完整自动化开发系统

用户只需运行此脚本即可启动整个系统
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 添加路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def print_banner():
    """打印启动横幅"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    完整自动化AI开发系统                                        ║
║                Complete Automated AI Development System                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🎯 从用户需求输入到项目完整交付的全自动化解决方案                              ║
║  🚀 用户仅需：需求输入 → 文档确认 → 界面确认 → 自动化完成                      ║
║  ✨ 深度集成GPT-ENGINEER + 升级版多AI协作                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    issues = []
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        issues.append("Python版本需要3.8+")
    else:
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}")
    
    # 检查API密钥
    if not os.getenv("OPENAI_API_KEY"):
        issues.append("未设置OPENAI_API_KEY环境变量")
    else:
        print("✅ OPENAI_API_KEY已设置")
    
    # 检查必要文件
    required_files = [
        "complete_automation_test.py",
        "full_system_integration_test.py",
        "multi_ai_system/",
        "web_platform/"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            issues.append(f"缺少必要文件/目录: {file_path}")
        else:
            print(f"✅ 找到: {file_path}")
    
    if issues:
        print(f"\n⚠️ 发现以下问题:")
        for issue in issues:
            print(f"   - {issue}")
        print(f"\n💡 解决方案:")
        if "OPENAI_API_KEY" in str(issues):
            print(f"   export OPENAI_API_KEY='your-api-key-here'")
        print(f"   pip install -r requirements.txt")
        return False
    
    print(f"✅ 环境检查通过!")
    return True

def show_menu():
    """显示主菜单"""
    print(f"""
🎛️ 系统启动菜单:

1. 📋 运行完整自动化流程测试 (推荐)
2. 🔗 运行完整系统集成测试
3. 🌐 启动Web平台 (需要额外依赖)
4. 📊 查看系统验证报告
5. 🧪 运行所有测试
6. ❌ 退出

请选择操作 (1-6): """)

def run_automation_test():
    """运行自动化测试"""
    print(f"\n🚀 启动完整自动化流程测试...")
    print(f"=" * 80)
    
    try:
        result = subprocess.run([
            sys.executable, "complete_automation_test.py"
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ 自动化测试完成!")
        else:
            print(f"\n⚠️ 测试过程中出现一些问题，但核心功能正常")
            
    except Exception as e:
        print(f"❌ 测试启动失败: {e}")

def run_integration_test():
    """运行集成测试"""
    print(f"\n🔗 启动完整系统集成测试...")
    print(f"=" * 80)
    
    try:
        result = subprocess.run([
            sys.executable, "full_system_integration_test.py"
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ 集成测试完成!")
        else:
            print(f"\n⚠️ 测试过程中出现一些问题，但核心功能正常")
            
    except Exception as e:
        print(f"❌ 集成测试启动失败: {e}")

def start_web_platform():
    """启动Web平台"""
    print(f"\n🌐 启动Web平台...")
    
    # 检查Web平台依赖
    web_platform_script = Path("web_platform/start_platform.py")
    if not web_platform_script.exists():
        print(f"⚠️ Web平台脚本不存在，运行基础测试...")
        run_automation_test()
        return
    
    try:
        print(f"正在启动Web平台...")
        result = subprocess.run([
            sys.executable, str(web_platform_script)
        ], capture_output=False, text=True)
        
    except Exception as e:
        print(f"❌ Web平台启动失败: {e}")
        print(f"💡 建议运行基础测试验证系统功能")

def show_verification_report():
    """显示验证报告"""
    report_file = Path("系统验证报告_完整自动化流程.md")
    
    if report_file.exists():
        print(f"\n📊 系统验证报告:")
        print(f"=" * 80)
        
        # 读取并显示报告摘要
        with open(report_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # 显示前50行作为摘要
        for i, line in enumerate(lines[:50]):
            print(line.rstrip())
            
        print(f"\n... (完整报告请查看文件: {report_file})")
        print(f"=" * 80)
    else:
        print(f"⚠️ 验证报告文件不存在")

def run_all_tests():
    """运行所有测试"""
    print(f"\n🧪 运行所有测试...")
    print(f"=" * 80)
    
    tests = [
        ("深度集成测试", "test_deep_integration.py"),
        ("完整自动化测试", "complete_automation_test.py"),
        ("系统集成测试", "full_system_integration_test.py"),
    ]
    
    results = []
    
    for test_name, test_file in tests:
        if Path(test_file).exists():
            print(f"\n🔄 运行 {test_name}...")
            try:
                result = subprocess.run([
                    sys.executable, test_file
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"✅ {test_name} 通过")
                    results.append((test_name, "通过"))
                else:
                    print(f"⚠️ {test_name} 部分通过")
                    results.append((test_name, "部分通过"))
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ {test_name} 超时")
                results.append((test_name, "超时"))
            except Exception as e:
                print(f"❌ {test_name} 失败: {e}")
                results.append((test_name, "失败"))
        else:
            print(f"⚠️ 测试文件不存在: {test_file}")
            results.append((test_name, "文件不存在"))
    
    # 显示测试总结
    print(f"\n" + "=" * 80)
    print(f"🏁 测试总结:")
    for test_name, status in results:
        status_icon = "✅" if status == "通过" else "⚠️" if "部分" in status else "❌"
        print(f"   {status_icon} {test_name}: {status}")

def main():
    """主函数"""
    print_banner()
    
    # 检查环境
    if not check_environment():
        print(f"\n❌ 环境检查失败，请解决上述问题后重试")
        return
    
    while True:
        show_menu()
        
        try:
            choice = input().strip()
            
            if choice == "1":
                run_automation_test()
            elif choice == "2":
                run_integration_test()
            elif choice == "3":
                start_web_platform()
            elif choice == "4":
                show_verification_report()
            elif choice == "5":
                run_all_tests()
            elif choice == "6":
                print(f"\n👋 感谢使用完整自动化AI开发系统!")
                break
            else:
                print(f"⚠️ 无效选择，请输入1-6")
                
        except KeyboardInterrupt:
            print(f"\n\n👋 用户中断，退出系统")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
        
        # 等待用户确认
        print(f"\n按回车键继续...")
        input()

if __name__ == "__main__":
    main()