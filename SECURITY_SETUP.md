# 🔐 安全配置指南

## 重要安全提醒

⚠️ **API密钥安全**：您的OpenAI API密钥是敏感信息，请务必妥善保管，不要将其提交到Git仓库中。

## 快速设置

### 方法1：使用配置脚本（推荐）

```bash
python setup_config.py
```

这个脚本会：
- 自动创建 `config.yaml` 文件
- 安全地输入API密钥（不会在屏幕上显示）
- 生成随机的JWT密钥
- 设置端口等基本配置

### 方法2：手动设置

1. 复制示例配置文件：
```bash
cp config.yaml.example config.yaml
```

2. 编辑配置文件：
```bash
# 使用您喜欢的编辑器
notepad config.yaml  # Windows
# 或
nano config.yaml     # Linux/Mac
```

3. 更新以下关键配置：
```yaml
openai:
  api_key: "your-actual-openai-api-key"  # 替换为您的真实API密钥

security:
  jwt_secret: "your-jwt-secret-key"      # 替换为随机字符串
```

## 安全最佳实践

### ✅ 应该做的：
- 使用 `setup_config.py` 脚本安全输入密钥
- 将 `config.yaml` 添加到 `.gitignore`
- 定期轮换API密钥
- 使用环境变量存储敏感信息（可选）

### ❌ 不应该做的：
- 将API密钥提交到Git仓库
- 在代码中硬编码API密钥
- 在公开场合分享API密钥
- 使用默认的JWT密钥

## 环境变量方式（可选）

如果您更喜欢使用环境变量，可以这样设置：

```bash
# Windows
set OPENAI_API_KEY=your-api-key-here

# Linux/Mac
export OPENAI_API_KEY=your-api-key-here
```

然后在 `config.yaml` 中使用：
```yaml
openai:
  api_key: "${OPENAI_API_KEY}"
```

## 验证配置

运行以下命令验证配置是否正确：

```bash
python -c "
import yaml
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
print('✅ 配置文件格式正确')
print(f'🌐 端口: {config[\"platform\"][\"port\"]}')
print(f'🤖 模型: {config[\"openai\"][\"model\"]}')
"
```

## 故障排除

### 问题：Git推送被阻止
**原因**：GitHub检测到API密钥
**解决**：
1. 确保 `config.yaml` 在 `.gitignore` 中
2. 如果已经提交，使用 `git filter-repo` 清理历史

### 问题：API密钥无效
**原因**：密钥格式错误或已过期
**解决**：
1. 检查OpenAI账户中的API密钥
2. 确保密钥格式正确（以 `sk-` 开头）
3. 检查账户余额和配额

### 问题：端口被占用
**原因**：8892端口已被其他程序使用
**解决**：
1. 修改 `config.yaml` 中的端口号
2. 或停止占用端口的程序

## 获取OpenAI API密钥

1. 访问 [OpenAI官网](https://platform.openai.com/)
2. 登录或注册账户
3. 进入 "API Keys" 页面
4. 点击 "Create new secret key"
5. 复制生成的密钥（以 `sk-` 开头）

## 支持

如果您遇到配置问题，请：
1. 检查本指南
2. 查看项目README
3. 提交Issue（不要包含API密钥）

---

🔒 **记住**：安全第一，永远不要将敏感信息提交到版本控制系统！ 