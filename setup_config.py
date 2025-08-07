#!/usr/bin/env python3
"""
配置设置脚本
帮助用户安全地设置config.yaml文件
"""

import os
import shutil
from pathlib import Path
import getpass

def setup_config():
    """设置配置文件"""
    config_file = Path("config.yaml")
    example_file = Path("config.yaml.example")
    
    print("🔧 AI开发平台配置设置")
    print("=" * 50)
    
    # 检查示例文件是否存在
    if not example_file.exists():
        print("❌ 错误：config.yaml.example 文件不存在")
        return False
    
    # 如果配置文件已存在，询问是否覆盖
    if config_file.exists():
        response = input("⚠️  config.yaml 文件已存在，是否覆盖？(y/N): ").strip().lower()
        if response != 'y':
            print("✅ 保持现有配置文件不变")
            return True
    
    # 复制示例文件
    try:
        shutil.copy2(example_file, config_file)
        print("✅ 已创建 config.yaml 文件")
    except Exception as e:
        print(f"❌ 创建配置文件失败：{e}")
        return False
    
    # 获取用户输入
    print("\n📝 请输入您的配置信息：")
    
    # 读取配置文件内容
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 获取OpenAI API密钥
    api_key = getpass.getpass("🔑 请输入您的OpenAI API密钥（输入时不会显示）: ").strip()
    if api_key:
        content = content.replace("your-openai-api-key-here", api_key)
    
    # 获取JWT密钥
    jwt_secret = getpass.getpass("🔐 请输入JWT密钥（或按回车使用默认值）: ").strip()
    if jwt_secret:
        content = content.replace("your-jwt-secret-key-here", jwt_secret)
    else:
        # 生成一个随机密钥
        import secrets
        random_secret = secrets.token_urlsafe(32)
        content = content.replace("your-jwt-secret-key-here", random_secret)
        print("✅ 已生成随机JWT密钥")
    
    # 询问端口设置
    port_input = input("🌐 请输入端口号（默认8892）: ").strip()
    if port_input and port_input.isdigit():
        content = content.replace("port: 8892", f"port: {port_input}")
    
    # 写入更新后的内容
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ 配置文件设置完成！")
        return True
    except Exception as e:
        print(f"❌ 写入配置文件失败：{e}")
        return False

def main():
    """主函数"""
    try:
        if setup_config():
            print("\n🎉 配置完成！您现在可以运行平台了。")
            print("💡 提示：")
            print("   - 运行 python start_optimized_platform.py 启动平台")
            print("   - 配置文件已添加到 .gitignore，不会被提交到Git")
            print("   - 请妥善保管您的API密钥")
        else:
            print("\n❌ 配置失败，请检查错误信息")
    except KeyboardInterrupt:
        print("\n\n⏹️  配置已取消")
    except Exception as e:
        print(f"\n❌ 发生错误：{e}")

if __name__ == "__main__":
    main() 