"""
订单API接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models import Order, OrderItem, Product, User

router = APIRouter()

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate]
    shipping_address: str

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product_name: str

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    shipping_address: str
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

@router.post("/", response_model=OrderResponse)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """创建订单"""
    # 验证用户存在
    user = db.query(User).filter(User.id == order.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 计算总金额并验证商品
    total_amount = 0
    order_items_data = []
    
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品 {item.product_id} 不存在")
        
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"商品 {product.name} 库存不足")
        
        item_total = product.price * item.quantity
        total_amount += item_total
        
        order_items_data.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": product.price,
            "product": product
        })
    
    # 创建订单
    db_order = Order(
        user_id=order.user_id,
        total_amount=total_amount,
        shipping_address=order.shipping_address,
        status="pending"
    )
    
    db.add(db_order)
    db.flush()  # 获取订单ID
    
    # 创建订单项并更新库存
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=db_order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            price=item_data["price"]
        )
        db.add(order_item)
        
        # 更新商品库存
        product = item_data["product"]
        product.stock -= item_data["quantity"]
    
    db.commit()
    db.refresh(db_order)
    
    # 构建响应
    return get_order_response(db_order, db)

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """获取订单详情"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    return get_order_response(order, db)

@router.get("/user/{user_id}", response_model=List[OrderResponse])
async def get_user_orders(user_id: int, db: Session = Depends(get_db)):
    """获取用户订单列表"""
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    return [get_order_response(order, db) for order in orders]

@router.put("/{order_id}/status")
async def update_order_status(
    order_id: int, 
    status: str, 
    db: Session = Depends(get_db)
):
    """更新订单状态"""
    valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="无效的订单状态")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    order.status = status
    order.updated_at = datetime.utcnow()
    
    db.commit()
    return {"message": "订单状态已更新", "order_id": order_id, "status": status}

def get_order_response(order: Order, db: Session) -> OrderResponse:
    """构建订单响应数据"""
    items = []
    for order_item in order.order_items:
        product = db.query(Product).filter(Product.id == order_item.product_id).first()
        items.append(OrderItemResponse(
            id=order_item.id,
            product_id=order_item.product_id,
            quantity=order_item.quantity,
            price=order_item.price,
            product_name=product.name if product else "未知商品"
        ))
    
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=order.status,
        shipping_address=order.shipping_address,
        created_at=order.created_at,
        items=items
    )
