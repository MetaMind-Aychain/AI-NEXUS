"""
数据库配置
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)
    
    # 创建示例数据
    db = SessionLocal()
    try:
        from models import Product, User
        
        # 检查是否已有数据
        if db.query(Product).count() == 0:
            # 创建示例商品
            products = [
                Product(name="智能手机", description="最新款智能手机", price=2999.0, stock=100, category="电子产品"),
                Product(name="笔记本电脑", description="高性能笔记本电脑", price=5999.0, stock=50, category="电子产品"),
                Product(name="运动鞋", description="舒适运动鞋", price=299.0, stock=200, category="服装"),
                Product(name="背包", description="多功能背包", price=199.0, stock=150, category="配件")
            ]
            
            for product in products:
                db.add(product)
            
            db.commit()
            
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")
