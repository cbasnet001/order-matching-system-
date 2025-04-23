from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.models.order import OrderCreate, Order, OrderStatus
from app.services.order_service import OrderService
from typing import List, Dict, Optional

router = APIRouter()

@router.post("/", response_model=Order, status_code=201)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """Create a new order"""
    order_service = OrderService(db)
    
    try:
        created_order, trades = order_service.create_order(order)
        return created_order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{order_id}", response_model=Order)
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get an order by ID"""
    order_service = OrderService(db)
    order = order_service.get_order(order_id)
    
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order

@router.get("/", response_model=List[Order])
def get_orders(
    trader_id: str = Query(..., description="Trader ID to filter orders"),
    symbol: Optional[str] = Query(None, description="Symbol to filter orders"),
    db: Session = Depends(get_db)
):
    """Get orders for a trader, optionally filtered by symbol"""
    order_service = OrderService(db)
    orders = order_service.get_orders_by_trader(trader_id, symbol)
    return orders

@router.delete("/{order_id}", response_model=Order)
def cancel_order(order_id: str, db: Session = Depends(get_db)):
    """Cancel an order"""
    order_service = OrderService(db)
    order = order_service.cancel_order(order_id)
    
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found or cannot be canceled")
    
    return order

@router.get("/orderbook/{symbol}", response_model=Dict)
def get_order_book(
    symbol: str,
    depth: int = Query(10, description="Depth of the order book to return"),
    db: Session = Depends(get_db)
):
    """Get the current state of the order book for a symbol"""
    order_service = OrderService(db)
    order_book = order_service.get_order_book(symbol, depth)
    return order_book