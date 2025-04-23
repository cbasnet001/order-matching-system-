import uuid
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
import redis
import json
from app.models.order_book import OrderBook
from app.models.order import OrderSide, OrderStatus
from app.db.redis_client import get_redis

class MatchingEngine:
    """Matching engine for processing orders and executing trades"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client if redis_client else get_redis()
    
    def process_order(self, order, db=None) -> List[Dict]:
        """
        Process an incoming order against the order book
        Returns a list of executed trades
        """
        # Skip market orders for now if no price is set
        if order.order_type == "market" and not order.price:
            return []
        
        # Get the order book for this symbol
        order_book = OrderBook(self.redis, order.symbol)
        
        # For buy orders, we need to match against the lowest sell orders (asks)
        # For sell orders, we need to match against the highest buy orders (bids)
        trades = []
        
        if order.side == OrderSide.BUY:
            trades = self._match_buy_order(order, order_book, db)
        else:
            trades = self._match_sell_order(order, order_book, db)
        
        # If the order wasn't fully matched and it's a limit order, add it to the book
        remaining_quantity = order.quantity - order.filled_quantity
        if remaining_quantity > 0 and order.order_type == "limit":
            # Update order status
            if order.filled_quantity > 0:
                order.status = OrderStatus.PARTIALLY_FILLED
            else:
                order.status = OrderStatus.ACTIVE
                
            # Add to order book
            order_book.add_order(order)
        elif remaining_quantity <= 0:
            order.status = OrderStatus.FILLED
        
        # Update the order in database if db session is provided
        if db and hasattr(order, '__tablename__'):
            db.add(order)
            db.commit()
        
        return trades
    
    def _match_buy_order(self, buy_order, order_book: OrderBook, db=None) -> List[Dict]:
        """Match a buy order against the sell orders in the book"""
        trades = []
        remaining_quantity = buy_order.quantity
        
        while remaining_quantity > 0:
            # Get the best (lowest) ask
            sell_order_id, sell_price = order_book.get_best_ask()
            
            # If no sell orders or price is higher than buy order's price, stop matching
            if sell_order_id is None or (buy_order.price is not None and sell_price > buy_order.price):
                break
            
            # Get sell order details
            sell_order_json = order_book.redis.hget(order_book.order_details_key, sell_order_id)
            if not sell_order_json:
                break
                
            sell_order_dict = json.loads(sell_order_json)
            sell_order_quantity = float(sell_order_dict.get("quantity", 0))
            sell_order_filled = float(sell_order_dict.get("filled_quantity", 0))
            available_quantity = sell_order_quantity - sell_order_filled
            
            if available_quantity <= 0:
                # Remove the fully filled order and continue
                order_book.remove_order(sell_order_id)
                continue
            
            # Calculate trade quantity and price
            trade_quantity = min(remaining_quantity, available_quantity)
            trade_price = sell_price
            
            # Create trade
            trade_id = str(uuid.uuid4())
            trade = {
                "trade_id": trade_id,
                "buy_order_id": buy_order.order_id,
                "sell_order_id": sell_order_id,
                "symbol": buy_order.symbol,
                "quantity": trade_quantity,
                "price": trade_price,
                "executed_at": datetime.now(timezone.utc)
            }
            trades.append(trade)
            
            # Update the filled quantities
            buy_order.filled_quantity = buy_order.filled_quantity + trade_quantity
            sell_order_dict["filled_quantity"] = sell_order_filled + trade_quantity
            
            # If sell order is fully filled, remove it from the book
            if sell_order_dict["filled_quantity"] >= sell_order_quantity:
                sell_order_dict["status"] = OrderStatus.FILLED
                order_book.remove_order(sell_order_id)
            else:
                sell_order_dict["status"] = OrderStatus.PARTIALLY_FILLED
                # Update the order in the book
                order_book.redis.hset(order_book.order_details_key, sell_order_id, 
                                      json.dumps(sell_order_dict))
            
            # Update remaining quantity
            remaining_quantity -= trade_quantity
            
            # If this is a database model, update it
            if db and sell_order_id:
                from app.models.order import OrderModel
                from app.models.trade import TradeModel
                
                # Create and save trade
                db_trade = TradeModel(
                    trade_id=trade_id,
                    buy_order_id=buy_order.order_id,
                    sell_order_id=sell_order_id,
                    symbol=buy_order.symbol,
                    quantity=trade_quantity,
                    price=trade_price
                )
                db.add(db_trade)
                
                # Update sell order in database
                db_sell_order = db.query(OrderModel).filter(
                    OrderModel.order_id == sell_order_id).first()
                if db_sell_order:
                    db_sell_order.filled_quantity = sell_order_dict["filled_quantity"]
                    db_sell_order.status = sell_order_dict["status"]
                    db.add(db_sell_order)
        
        return trades
    
    def _match_sell_order(self, sell_order, order_book: OrderBook, db=None) -> List[Dict]:
        """Match a sell order against the buy orders in the book"""
        trades = []
        remaining_quantity = sell_order.quantity
        
        while remaining_quantity > 0:
            # Get the best (highest) bid
            buy_order_id, buy_price = order_book.get_best_bid()
            
            # If no buy orders or price is lower than sell order's price, stop matching
            if buy_order_id is None or (sell_order.price is not None and buy_price < sell_order.price):
                break
            
            # Get buy order details
            buy_order_json = order_book.redis.hget(order_book.order_details_key, buy_order_id)
            if not buy_order_json:
                break
                
            buy_order_dict = json.loads(buy_order_json)
            buy_order_quantity = float(buy_order_dict.get("quantity", 0))
            buy_order_filled = float(buy_order_dict.get("filled_quantity", 0))
            available_quantity = buy_order_quantity - buy_order_filled
            
            if available_quantity <= 0:
                # Remove the fully filled order and continue
                order_book.remove_order(buy_order_id)
                continue
            
            # Calculate trade quantity and price
            trade_quantity = min(remaining_quantity, available_quantity)
            trade_price = buy_price
            
            # Create trade
            trade_id = str(uuid.uuid4())
            trade = {
                "trade_id": trade_id,
                "buy_order_id": buy_order_id,
                "sell_order_id": sell_order.order_id,
                "symbol": sell_order.symbol,
                "quantity": trade_quantity,
                "price": trade_price,
                "executed_at": datetime.now(timezone.utc)
            }
            trades.append(trade)
            
            # Update the filled quantities
            sell_order.filled_quantity = sell_order.filled_quantity + trade_quantity
            buy_order_dict["filled_quantity"] = buy_order_filled + trade_quantity
            
            # If buy order is fully filled, remove it from the book
            if buy_order_dict["filled_quantity"] >= buy_order_quantity:
                buy_order_dict["status"] = OrderStatus.FILLED
                order_book.remove_order(buy_order_id)
            else:
                buy_order_dict["status"] = OrderStatus.PARTIALLY_FILLED
                # Update the order in the book
                order_book.redis.hset(order_book.order_details_key, buy_order_id, 
                                      json.dumps(buy_order_dict))
            
            # Update remaining quantity
            remaining_quantity -= trade_quantity
            
            # If this is a database model, update it
            if db and buy_order_id:
                from app.models.order import OrderModel
                from app.models.trade import TradeModel
                
                # Create and save trade
                db_trade = TradeModel(
                    trade_id=trade_id,
                    buy_order_id=buy_order_id,
                    sell_order_id=sell_order.order_id,
                    symbol=sell_order.symbol,
                    quantity=trade_quantity,
                    price=trade_price
                )
                db.add(db_trade)
                
                # Update buy order in database
                db_buy_order = db.query(OrderModel).filter(
                    OrderModel.order_id == buy_order_id).first()
                if db_buy_order:
                    db_buy_order.filled_quantity = buy_order_dict["filled_quantity"]
                    db_buy_order.status = buy_order_dict["status"]
                    db.add(db_buy_order)
        
        return trades