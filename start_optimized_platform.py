#!/usr/bin/env python3
"""
优化的多用户AI协作开发平台启动脚本
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """检查必要依赖"""
    print("🔍 检查必要依赖...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'pyyaml', 'websockets',
        'openai', 'langchain', 'langchain_openai'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")
    
    if missing_packages:
        print(f"\n📦 安装缺失的依赖包: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ 依赖安装完成")
        except subprocess.CalledProcessError:
            print("❌ 依赖安装失败，请手动安装")
            return False
    
    return True

def check_config():
    """检查配置文件"""
    print("\n⚙️  检查配置文件...")
    
    config_file = Path("config.yaml")
    if not config_file.exists():
        print("❌ 配置文件不存在")
        return False
    
    # 检查API密钥配置
    import yaml
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        api_key = config.get('openai', {}).get('api_key', '')
        if not api_key or api_key == "your-openai-api-key-here":
            print("⚠️  OpenAI API密钥未配置，请在config.yaml中设置")
            print("   您可以在 https://platform.openai.com/api-keys 获取API密钥")
            return False
        
        print("✅ 配置文件检查通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return False

def create_directories():
    """创建必要的目录"""
    print("\n📁 创建必要目录...")
    
    directories = [
        "multi_user_projects",
        "user_memory",
        "user_workspace",
        "optimized_frontend"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"  ✅ {directory}")

def start_platform():
    """启动平台"""
    print("\n🚀 启动优化的多用户AI协作开发平台...")
    
    try:
        # 导入并启动平台
        from optimized_multi_user_platform import OptimizedMultiUserPlatform
        
        platform = OptimizedMultiUserPlatform()
        platform.run()
        
    except KeyboardInterrupt:
        print("\n👋 平台已关闭")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 优化多用户AI协作开发平台")
    print("=" * 60)
    print("特性:")
    print("  ✅ 多用户支持 - 完全隔离的用户环境")
    print("  ✅ API优化 - 智能缓存、批量处理、减少调用")
    print("  ✅ 智能调度 - AI协作、质量保证、自动优化")
    print("  ✅ 现代化界面 - 响应式设计、实时更新")
    print("  ✅ 深度集成 - GPT-ENGINEER核心引擎")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败，请解决后重试")
        return
    
    # 检查配置
    if not check_config():
        print("❌ 配置检查失败，请解决后重试")
        return
    
    # 创建目录
    create_directories()
    
    # 启动平台
    start_platform()

if __name__ == "__main__":
    main() 