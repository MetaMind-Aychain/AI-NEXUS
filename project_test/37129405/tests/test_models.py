"""
模型测试
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Product, Order, OrderItem

# 创建测试数据库
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

class TestModels:
    def test_create_user(self, db_session):
        """测试创建用户"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashedpass",
            full_name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        
        # 验证用户已创建
        saved_user = db_session.query(User).filter(User.username == "testuser").first()
        assert saved_user is not None
        assert saved_user.email == "test@example.com"
    
    def test_create_product(self, db_session):
        """测试创建商品"""
        product = Product(
            name="测试商品",
            description="这是一个测试商品",
            price=99.99,
            stock=100,
            category="测试分类"
        )
        db_session.add(product)
        db_session.commit()
        
        # 验证商品已创建
        saved_product = db_session.query(Product).filter(Product.name == "测试商品").first()
        assert saved_product is not None
        assert saved_product.price == 99.99
    
    def test_create_order(self, db_session):
        """测试创建订单"""
        # 先创建用户
        user = User(
            username="orderuser",
            email="order@example.com",
            hashed_password="hashedpass"
        )
        db_session.add(user)
        db_session.flush()
        
        # 创建商品
        product = Product(
            name="订单商品",
            price=50.0,
            stock=10
        )
        db_session.add(product)
        db_session.flush()
        
        # 创建订单
        order = Order(
            user_id=user.id,
            total_amount=100.0,
            shipping_address="测试地址"
        )
        db_session.add(order)
        db_session.flush()
        
        # 创建订单项
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=2,
            price=50.0
        )
        db_session.add(order_item)
        db_session.commit()
        
        # 验证订单已创建
        saved_order = db_session.query(Order).filter(Order.user_id == user.id).first()
        assert saved_order is not None
        assert saved_order.total_amount == 100.0
        assert len(saved_order.order_items) == 1

if __name__ == "__main__":
    pytest.main([__file__])
