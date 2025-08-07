"""
API测试
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAPI:
    def test_health_check(self):
        """测试健康检查接口"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_get_products(self):
        """测试获取商品列表"""
        response = client.get("/api/products/")
        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)
    
    def test_get_categories(self):
        """测试获取分类列表"""
        response = client.get("/api/products/categories/")
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)
    
    def test_user_registration(self):
        """测试用户注册"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
        response = client.post("/api/users/register", json=user_data)
        assert response.status_code == 200
        user = response.json()
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"
    
    def test_user_login(self):
        """测试用户登录"""
        # 先注册用户
        user_data = {
            "username": "logintest",
            "email": "login@example.com",
            "password": "loginpass123"
        }
        client.post("/api/users/register", json=user_data)
        
        # 然后登录
        login_data = {
            "username": "logintest",
            "password": "loginpass123"
        }
        response = client.post("/api/users/login", json=login_data)
        assert response.status_code == 200
        result = response.json()
        assert result["message"] == "登录成功"
    
    def test_create_order(self):
        """测试创建订单"""
        # 先注册用户
        user_data = {
            "username": "orderuser",
            "email": "order@example.com",
            "password": "orderpass123"
        }
        user_response = client.post("/api/users/register", json=user_data)
        user_id = user_response.json()["id"]
        
        # 创建订单
        order_data = {
            "user_id": user_id,
            "items": [
                {"product_id": 1, "quantity": 2}
            ],
            "shipping_address": "测试地址123号"
        }
        response = client.post("/api/orders/", json=order_data)
        assert response.status_code == 200
        order = response.json()
        assert order["user_id"] == user_id

if __name__ == "__main__":
    pytest.main([__file__])
