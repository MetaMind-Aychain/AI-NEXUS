#!/usr/bin/env python3
"""
API密钥设置脚本
"""

import yaml
import os
from pathlib import Path

def setup_api_key():
    """设置API密钥"""
    print("🔑 设置OpenAI API密钥")
    print("=" * 50)
    
    # 检查配置文件是否存在
    config_file = Path("config.yaml")
    if not config_file.exists():
        print("❌ 配置文件不存在，请先创建config.yaml")
        return False
    
    # 读取现有配置
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return False
    
    # 获取当前API密钥
    current_key = config.get('openai', {}).get('api_key', '')
    
    if current_key and current_key != "your-openai-api-key-here":
        print(f"当前API密钥: {current_key[:10]}...{current_key[-4:]}")
        change = input("是否要更改API密钥？(y/N): ").strip().lower()
        if change != 'y':
            print("✅ 保持现有API密钥")
            return True
    
    # 获取新的API密钥
    print("\n📝 请输入您的OpenAI API密钥:")
    print("您可以在 https://platform.openai.com/api-keys 获取API密钥")
    print("密钥格式: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    
    api_key = input("API密钥: ").strip()
    
    if not api_key:
        print("❌ API密钥不能为空")
        return False
    
    if not api_key.startswith('sk-'):
        print("❌ API密钥格式不正确，应以'sk-'开头")
        return False
    
    # 更新配置
    if 'openai' not in config:
        config['openai'] = {}
    
    config['openai']['api_key'] = api_key
    
    # 保存配置
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print("✅ API密钥设置成功")
        return True
        
    except Exception as e:
        print(f"❌ 保存配置文件失败: {e}")
        return False

def main():
    """主函数"""
    print("🤖 优化多用户AI协作开发平台 - API密钥设置")
    print("=" * 60)
    
    if setup_api_key():
        print("\n🎉 配置完成！现在可以启动平台了:")
        print("python start_optimized_platform.py")
    else:
        print("\n❌ 配置失败，请检查错误信息")

if __name__ == "__main__":
    main()