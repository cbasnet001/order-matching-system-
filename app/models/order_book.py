import json
import redis
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from app.models.order import OrderSide, OrderStatus

class OrderBook:
    """
    OrderBook implementation using Redis sorted sets.
    - Buy orders sorted by price (descending) then time (ascending)
    - Sell orders sorted by price (ascending) then time (ascending)
    """
    
    def __init__(self, redis_client: redis.Redis, symbol: str):
        self.redis = redis_client
        self.symbol = symbol
        self.buy_orders_key = f"orderbook:{symbol}:buy"
        self.sell_orders_key = f"orderbook:{symbol}:sell"
        self.order_details_key = f"orderbook:{symbol}:details"
    
    def add_order(self, order) -> str:
        """Add order to the order book"""
        # Create score for sorting
        # For buy orders, negative price to sort in descending order
        timestamp = datetime.now(timezone.utc).timestamp()
        
        # Store order details
        order_details = {
            "order_id": order.order_id,
            "trader_id": order.trader_id,
            "symbol": order.symbol,
            "side": order.side,
            "order_type": order.order_type,
            "quantity": order.quantity,
            "price": order.price,
            "status": order.status,
            "filled_quantity": order.filled_quantity,
            "created_at": timestamp
        }
        
        # Add to sorted set based on side
        if order.side == OrderSide.BUY:
            # Sort by negative price (highest first), then timestamp
            score = (-float(order.price) * 1e10) + timestamp
            self.redis.zadd(self.buy_orders_key, {order.order_id: score})
        else:
            # Sort by price (lowest first), then timestamp
            score = (float(order.price) * 1e10) + timestamp
            self.redis.zadd(self.sell_orders_key, {order.order_id: score})
        
        # Store order details
        self.redis.hset(self.order_details_key, order.order_id, json.dumps(order_details))
        
        return order.order_id
    
    def remove_order(self, order_id: str) -> bool:
        """Remove order from the order book"""
        # Check which side the order is on
        buy_removed = self.redis.zrem(self.buy_orders_key, order_id)
        sell_removed = self.redis.zrem(self.sell_orders_key, order_id)
        
        # Remove order details
        details_removed = self.redis.hdel(self.order_details_key, order_id)
        
        return (buy_removed or sell_removed) and details_removed > 0

    def update_order(self, order_id: str, quantity: float = None, status: str = None) -> bool:
        """Update order quantity or status"""
        # Get order details
        order_json = self.redis.hget(self.order_details_key, order_id)
        if not order_json:
            return False
        
        order_details = json.loads(order_json)
        updated = False
        
        # Update quantity if provided
        if quantity is not None and quantity != order_details.get("quantity"):
            order_details["quantity"] = quantity
            updated = True
        
        # Update status if provided
        if status is not None and status != order_details.get("status"):
            order_details["status"] = status
            updated = True
        
        if updated:
            # Store updated details
            self.redis.hset(self.order_details_key, order_id, json.dumps(order_details))
        
        return updated
    
    def get_best_bid(self) -> Tuple[Optional[str], Optional[float]]:
        """Get the highest bid order id and price"""
        # Get highest bid (first element in sorted set)
        best_bid = self.redis.zrange(self.buy_orders_key, 0, 0, withscores=True)
        if not best_bid:
            return None, None
        
        order_id = best_bid[0][0].decode() if isinstance(best_bid[0][0], bytes) else best_bid[0][0]
        order_json = self.redis.hget(self.order_details_key, order_id)
        if not order_json:
            return None, None
        
        order_details = json.loads(order_json)
        return order_id, order_details.get("price")
    
    def get_best_ask(self) -> Tuple[Optional[str], Optional[float]]:
        """Get the lowest ask order id and price"""
        # Get lowest ask (first element in sorted set)
        best_ask = self.redis.zrange(self.sell_orders_key, 0, 0, withscores=True)
        if not best_ask:
            return None, None
        
        order_id = best_ask[0][0].decode() if isinstance(best_ask[0][0], bytes) else best_ask[0][0]
        order_json = self.redis.hget(self.order_details_key, order_id)
        if not order_json:
            return None, None
        
        order_details = json.loads(order_json)
        return order_id, order_details.get("price")
    
    def get_order_book_snapshot(self, depth: int = 10) -> Dict:
        """Get a snapshot of the order book at specific depth"""
        bid_orders = self.redis.zrange(self.buy_orders_key, 0, depth-1, withscores=True)
        ask_orders = self.redis.zrange(self.sell_orders_key, 0, depth-1, withscores=True)
        
        bids = []
        asks = []
        
        # Process bid orders
        for order_id_bytes, _ in bid_orders:
            order_id = order_id_bytes.decode() if isinstance(order_id_bytes, bytes) else order_id_bytes
            order_json = self.redis.hget(self.order_details_key, order_id)
            if order_json:
                order_details = json.loads(order_json)
                bids.append({
                    "price": order_details.get("price"),
                    "quantity": order_details.get("quantity"),
                    "order_id": order_id
                })
        
        # Process ask orders
        for order_id_bytes, _ in ask_orders:
            order_id = order_id_bytes.decode() if isinstance(order_id_bytes, bytes) else order_id_bytes
            order_json = self.redis.hget(self.order_details_key, order_id)
            if order_json:
                order_details = json.loads(order_json)
                asks.append({
                    "price": order_details.get("price"),
                    "quantity": order_details.get("quantity"),
                    "order_id": order_id
                })
        
        return {
            "symbol": self.symbol,
            "bids": bids,
            "asks": asks,
            "timestamp": datetime.now(timezone.utc).timestamp() 
        }