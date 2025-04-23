from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.models.trade import Trade
from app.services.trade_service import TradeService
from typing import List

router = APIRouter()

@router.get("/{trade_id}", response_model=Trade)
def get_trade(trade_id: str, db: Session = Depends(get_db)):
    """Get a trade by ID"""
    trade_service = TradeService(db)
    trade = trade_service.get_trade(trade_id)
    
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return trade

@router.get("/order/{order_id}", response_model=List[Trade])
def get_trades_by_order(order_id: str, db: Session = Depends(get_db)):
    """Get all trades for an order"""
    trade_service = TradeService(db)
    trades = trade_service.get_trades_by_order(order_id)
    return trades

@router.get("/symbol/{symbol}", response_model=List[Trade])
def get_trades_by_symbol(
    symbol: str,
    limit: int = Query(100, description="Maximum number of trades to return"),
    db: Session = Depends(get_db)
):
    """Get recent trades for a symbol"""
    trade_service = TradeService(db)
    trades = trade_service.get_trades_by_symbol(symbol, limit)
    return trades