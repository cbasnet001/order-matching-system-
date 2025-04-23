from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.postgres import Base
from datetime import datetime
from pydantic import BaseModel

# SQLAlchemy Model
class TradeModel(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String, unique=True, index=True)
    buy_order_id = Column(String, ForeignKey("orders.order_id"), index=True)
    sell_order_id = Column(String, ForeignKey("orders.order_id"), index=True)
    symbol = Column(String, index=True)
    quantity = Column(Float)
    price = Column(Float)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())

# Pydantic Models
class TradeBase(BaseModel):
    buy_order_id: str
    sell_order_id: str
    symbol: str
    quantity: float
    price: float

class TradeCreate(TradeBase):
    pass

class Trade(TradeBase):
    trade_id: str
    executed_at: datetime

    class Config:
        orm_mode = True