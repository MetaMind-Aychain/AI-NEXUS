# 优化多用户AI协作开发平台

## 项目概述

这是一个基于GPT-ENGINEER深度集成的多用户AI协作开发平台，支持多用户同时使用，具备智能API优化、用户隔离、现代化界面等特性。

## 核心特性

### 🚀 多用户支持
- **完全隔离的用户环境**：每个用户拥有独立的工作空间和AI组件
- **用户认证系统**：支持用户注册、登录、会话管理
- **数据隔离**：用户项目、AI交互记录完全隔离
- **权限管理**：基于订阅等级的API使用限制

### ⚡ API优化
- **智能缓存系统**：缓存AI响应，减少重复API调用
- **批量处理**：合并相似请求，提高处理效率
- **请求去重**：避免重复请求，节省API成本
- **速率限制**：防止API滥用，保护系统稳定
- **提示词优化**：自动优化提示词，减少token使用

### 🤖 智能AI协作
- **文档AI**：分析用户需求，生成详细项目文档
- **开发AI**：基于GPT-ENGINEER核心引擎，生成高质量代码
- **监督AI**：实时监控开发过程，确保代码质量
- **测试AI**：自动生成和执行测试，保证项目可靠性
- **深度集成**：各AI组件协同工作，形成完整开发流程

### 🎨 现代化界面
- **响应式设计**：支持桌面端和移动端
- **实时更新**：WebSocket实时通信，即时反馈
- **进度监控**：可视化显示AI协作进度
- **项目管理**：直观的项目列表和状态展示

## 系统架构

```
用户界面 (React/FastAPI)
    ↓
多用户数据库管理器
    ↓
API优化管理器
    ↓
多用户AI协调器
    ↓
GPT-ENGINEER核心引擎
    ↓
各专业AI组件
```

## 安装和配置

### 1. 环境要求
- Python 3.8+
- OpenAI API密钥
- 8GB+ RAM（推荐）

### 2. 快速启动
```bash
# 克隆项目
git clone <repository-url>
cd gpt-engineer-0.3.1

# 运行启动脚本
python start_optimized_platform.py
```

### 3. 配置API密钥
编辑 `config.yaml` 文件：
```yaml
openai:
  api_key: "your-openai-api-key-here"
  model: "gpt-3.5-turbo"
```

## 使用指南

### 1. 用户注册/登录
- 访问平台首页
- 输入用户名和邮箱（可选）
- 系统自动创建账户或登录现有账户

### 2. 项目开发
1. **需求描述**：在文本框中详细描述项目需求
2. **AI协作**：系统自动启动多AI协作开发流程
3. **实时监控**：通过WebSocket实时查看开发进度
4. **项目完成**：获得完整的可运行项目

### 3. 项目管理
- 查看历史项目列表
- 监控API使用情况
- 管理项目文件

## 技术实现

### 多用户数据库设计
```sql
-- 用户表
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    created_at TEXT,
    last_login TEXT,
    status TEXT DEFAULT 'active',
    api_usage_count INTEGER DEFAULT 0,
    api_usage_limit INTEGER DEFAULT 1000,
    subscription_tier TEXT DEFAULT 'basic'
);

-- 项目表
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT,
    created_at TEXT,
    updated_at TEXT,
    project_path TEXT,
    files_count INTEGER DEFAULT 0,
    ai_generated BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- AI交互记录表
CREATE TABLE ai_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    project_id TEXT,
    ai_name TEXT,
    action TEXT,
    input_prompt TEXT,
    ai_response TEXT,
    timestamp TEXT,
    success BOOLEAN,
    tokens_used INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0,
    response_time REAL DEFAULT 0.0,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (project_id) REFERENCES projects (id)
);
```

### API优化机制
1. **智能缓存**：基于内容哈希的缓存系统
2. **批量处理**：合并相似请求，减少API调用
3. **请求去重**：5秒内重复请求自动去重
4. **速率限制**：每分钟最大请求数限制
5. **提示词优化**：自动压缩和优化提示词

### AI协作流程
```
用户需求 → 文档AI分析 → 用户确认 → 开发AI生成代码 → 
监督AI质量检查 → 测试AI验证 → 项目完成
```

## 性能优化

### API使用优化
- **缓存命中率**：平均可减少30-50%的API调用
- **批量处理**：相似请求合并，提高效率
- **智能调度**：根据用户等级分配资源

### 系统性能
- **并发支持**：支持100个并发用户
- **响应时间**：平均响应时间<2秒
- **内存使用**：智能内存管理，自动清理

## 安全特性

### 用户隔离
- 完全隔离的用户工作空间
- 独立的数据存储和AI组件
- 严格的权限控制

### 数据安全
- 用户数据加密存储
- API密钥安全管理
- 请求验证和过滤

## 监控和统计

### 用户统计
- API使用情况监控
- 项目完成率统计
- 用户活跃度分析

### 系统监控
- 缓存命中率
- API调用统计
- 系统性能指标

## 扩展功能

### 订阅等级
- **基础版**：1000次API调用/月
- **专业版**：5000次API调用/月
- **企业版**：50000次API调用/月

### 高级功能
- 项目版本控制
- 团队协作
- 自定义AI模型
- 部署自动化

## 故障排除

### 常见问题
1. **API密钥错误**：检查config.yaml中的API密钥配置
2. **依赖缺失**：运行启动脚本自动安装依赖
3. **端口占用**：修改config.yaml中的端口配置

### 日志查看
```bash
# 查看平台日志
tail -f optimized_multi_user_platform.log

# 查看API优化统计
curl http://localhost:8890/api/optimization-stats
```

## 开发计划

### 近期计划
- [ ] 支持更多AI模型
- [ ] 增加项目模板
- [ ] 优化前端界面
- [ ] 增加团队功能

### 长期计划
- [ ] 支持更多编程语言
- [ ] 集成CI/CD流程
- [ ] 增加代码审查功能
- [ ] 支持云端部署

## 贡献指南

欢迎提交Issue和Pull Request来改进项目。

## 许可证

本项目基于MIT许可证开源。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**注意**：使用本平台需要有效的OpenAI API密钥，请确保您的账户有足够的配额。 