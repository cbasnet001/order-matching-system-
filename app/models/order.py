from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.db.postgres import Base
import enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# SQLAlchemy Models
class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class OrderModel(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    trader_id = Column(String, index=True)
    symbol = Column(String, index=True)
    side = Column(Enum(OrderSide), index=True)
    order_type = Column(Enum(OrderType))
    quantity = Column(Float)
    price = Column(Float, nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    filled_quantity = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Pydantic Models
class OrderBase(BaseModel):
    trader_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    order_id: str
    status: OrderStatus
    filled_quantity: float = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
