# AI电商平台 - AI生成的电商平台

## 项目简介

这是一个由AI自动生成的完整电商平台，包含用户管理、商品管理、订单处理等核心功能。

### 原始需求
```
我需要一个电商平台，包含商品管理、用户注册、购物车、订单处理等功能
```

## 功能特性

- ✅ 用户注册和登录系统
- ✅ 商品展示和搜索
- ✅ 商品分类管理
- ✅ 购物车功能
- ✅ 订单管理系统
- ✅ 响应式Web界面
- ✅ RESTful API接口
- ✅ 数据库持久化
- ✅ Docker部署支持

## 技术栈

### 后端
- **FastAPI** - 现代Python Web框架
- **SQLAlchemy** - ORM数据库工具
- **SQLite/PostgreSQL** - 数据库
- **Pydantic** - 数据验证

### 前端
- **HTML5/CSS3** - 标准Web技术
- **JavaScript (ES6+)** - 前端交互
- **响应式设计** - 移动端适配

### 部署
- **Docker** - 容器化部署
- **Nginx** - 反向代理和静态文件服务
- **Uvicorn** - ASGI服务器

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd ai电商平台

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库初始化

```bash
# 初始化数据库和示例数据
python database.py
```

### 3. 启动应用

```bash
# 启动后端服务
python main.py

# 或使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问应用

- **前端界面**: http://localhost:8000/static/
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health

## Docker部署

### 使用Docker Compose（推荐）

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 单独Docker部署

```bash
# 构建镜像
docker build -t ecommerce-platform .

# 运行容器
docker run -p 8000:8000 ecommerce-platform
```

## API接口

### 商品相关
- `GET /api/products/` - 获取商品列表
- `GET /api/products/{id}` - 获取商品详情
- `POST /api/products/` - 创建商品
- `PUT /api/products/{id}` - 更新商品
- `DELETE /api/products/{id}` - 删除商品

### 用户相关
- `POST /api/users/register` - 用户注册
- `POST /api/users/login` - 用户登录
- `GET /api/users/{id}` - 获取用户信息

### 订单相关
- `POST /api/orders/` - 创建订单
- `GET /api/orders/{id}` - 获取订单详情
- `GET /api/orders/user/{user_id}` - 获取用户订单列表

## 数据库结构

### 用户表 (users)
- id, username, email, hashed_password
- full_name, phone, address, is_active
- created_at

### 商品表 (products)
- id, name, description, price, stock
- category, image_url, is_active
- created_at

### 订单表 (orders)
- id, user_id, total_amount, status
- shipping_address, created_at, updated_at

### 订单项表 (order_items)
- id, order_id, product_id, quantity, price

## 开发指南

### 添加新功能

1. **后端API**：在 `api/` 目录下添加新的路由文件
2. **数据模型**：在 `models.py` 中定义新的数据模型
3. **前端界面**：修改 `frontend/` 目录下的HTML/CSS/JS文件

### 数据库迁移

```bash
# 修改models.py后，重新创建表
python database.py
```

### 测试

```bash
# 运行测试
python -m pytest tests/

# 测试API端点
curl http://localhost:8000/api/health
```

## 配置说明

### 环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

主要配置项：
- `DATABASE_URL`: 数据库连接字符串
- `SECRET_KEY`: 应用密钥
- `API_HOST/API_PORT`: 服务地址和端口

## 故障排除

### 常见问题

1. **端口占用**
   ```bash
   # 检查端口占用
   lsof -i :8000
   
   # 更改端口
   uvicorn main:app --port 8001
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库配置
   python -c "from database import engine; print(engine.url)"
   ```

3. **依赖安装失败**
   ```bash
   # 使用国内镜像
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```

## 性能优化

### 生产环境建议

1. **使用PostgreSQL**：替换SQLite以支持并发
2. **启用缓存**：Redis缓存常用数据
3. **CDN加速**：静态文件使用CDN服务
4. **负载均衡**：多实例部署

### 监控和日志

```bash
# 查看应用日志
docker-compose logs web

# 监控数据库
docker-compose exec db psql -U ecommerce_user -d ecommerce
```

## 许可证

本项目由AI自动生成，遵循MIT许可证。

## 支持

如有问题，请检查：
1. 日志文件中的错误信息
2. API文档中的接口说明
3. 数据库连接状态

---

**注意**: 这是一个AI生成的示例项目，生产环境使用前请进行充分的安全审计和测试。

生成时间: 2025-08-02 01:39:30
