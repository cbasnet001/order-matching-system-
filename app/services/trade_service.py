from sqlalchemy.orm import Session
from app.models.trade import TradeModel, Trade
from typing import List, Optional

class TradeService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """Get a trade by ID"""
        db_trade = self.db.query(TradeModel).filter(TradeModel.trade_id == trade_id).first()
        if not db_trade:
            return None
        
        return Trade(
            trade_id=db_trade.trade_id,
            buy_order_id=db_trade.buy_order_id,
            sell_order_id=db_trade.sell_order_id,
            symbol=db_trade.symbol,
            quantity=db_trade.quantity,
            price=db_trade.price,
            executed_at=db_trade.executed_at
        )
    
    def get_trades_by_order(self, order_id: str) -> List[Trade]:
        """Get all trades for an order"""
        db_trades = self.db.query(TradeModel).filter(
            (TradeModel.buy_order_id == order_id) | (TradeModel.sell_order_id == order_id)
        ).all()
        
        trades = []
        for db_trade in db_trades:
            trades.append(Trade(
                trade_id=db_trade.trade_id,
                buy_order_id=db_trade.buy_order_id,
                sell_order_id=db_trade.sell_order_id,
                symbol=db_trade.symbol,
                quantity=db_trade.quantity,
                price=db_trade.price,
                executed_at=db_trade.executed_at
            ))
        
        return trades
    
    def get_trades_by_symbol(self, symbol: str, limit: int = 100) -> List[Trade]:
        """Get recent trades for a symbol"""
        db_trades = self.db.query(TradeModel).filter(
            TradeModel.symbol == symbol
        ).order_by(TradeModel.executed_at.desc()).limit(limit).all()
        
        trades = []
        for db_trade in db_trades:
            trades.append(Trade(
                trade_id=db_trade.trade_id,
                buy_order_id=db_trade.buy_order_id,
                sell_order_id=db_trade.sell_order_id,
                symbol=db_trade.symbol,
                quantity=db_trade.quantity,
                price=db_trade.price,
                executed_at=db_trade.executed_at
            ))
        
        return trades