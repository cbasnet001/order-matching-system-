import redis
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.db.redis_client import get_redis

class MarketDataService:
    """Service for managing and distributing market data"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client if redis_client else get_redis()
    
    def publish_order_book_update(self, symbol: str, order_book_data: Dict):
        """Publish order book updates to Redis channel"""
        channel_name = f"orderbook_updates:{symbol}"
        self.redis.publish(channel_name, json.dumps(order_book_data))
    
    def publish_trade_update(self, symbol: str, trade_data: Dict):
        """Publish trade updates to Redis channel"""
        channel_name = f"trade_updates:{symbol}"
        self.redis.publish(channel_name, json.dumps(trade_data))
    
    def get_last_price(self, symbol: str) -> Optional[float]:
        """Get the last traded price for a symbol"""
        last_price_key = f"last_price:{symbol}"
        price = self.redis.get(last_price_key)
        
        if price:
            return float(price)
        
        return None
    
    def update_last_price(self, symbol: str, price: float):
        """Update the last traded price for a symbol"""
        last_price_key = f"last_price:{symbol}"
        self.redis.set(last_price_key, str(price))
    
    def get_ohlc_data(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[Dict]:
        """Get OHLC (Open, High, Low, Close) data for a symbol"""
        ohlc_key = f"ohlc:{symbol}:{interval}"
        ohlc_data = self.redis.lrange(ohlc_key, 0, limit - 1)
        
        result = []
        for data in ohlc_data:
            result.append(json.loads(data))
        
        return result
    
    def update_ohlc_data(self, symbol: str, price: float, quantity: float):
        """Update OHLC data for a symbol with a new trade"""
        # Get current timestamp
        now = datetime.now(timezone.utc)
        
        # Define intervals to update
        intervals = {
            "1m": 60,  # 1 minute in seconds
            "5m": 300,  # 5 minutes
            "15m": 900,  # 15 minutes
            "1h": 3600,  # 1 hour
            "4h": 14400,  # 4 hours
            "1d": 86400,  # 1 day
        }
        
        for interval_name, interval_seconds in intervals.items():
            # Calculate the current interval timestamp
            interval_timestamp = int(now.timestamp() / interval_seconds) * interval_seconds
            
            ohlc_key = f"ohlc:{symbol}:{interval_name}"
            current_key = f"current_ohlc:{symbol}:{interval_name}"
            
            # Get current OHLC data for this interval
            current_ohlc = self.redis.get(current_key)
            
            if current_ohlc:
                current_data = json.loads(current_ohlc)
                
                # Check if we're still in the same interval
                if current_data["timestamp"] == interval_timestamp:
                    # Update high and low prices
                    current_data["high"] = max(current_data["high"], price)
                    current_data["low"] = min(current_data["low"], price)
                    
                    # Update close price and volume
                    current_data["close"] = price
                    current_data["volume"] += quantity
                    
                    # Save updated data
                    self.redis.set(current_key, json.dumps(current_data))
                else:
                    # We've moved to a new interval
                    # Save the previous interval data to the OHLC list
                    self.redis.lpush(ohlc_key, json.dumps(current_data))
                    self.redis.ltrim(ohlc_key, 0, 999)  # Keep last 1000 intervals
                    
                    # Create new interval data
                    new_data = {
                        "timestamp": interval_timestamp,
                        "open": price,
                        "high": price,
                        "low": price,
                        "close": price,
                        "volume": quantity
                    }
                    
                    # Save new interval data
                    self.redis.set(current_key, json.dumps(new_data))
            else:
                # No current data, create new interval
                new_data = {
                    "timestamp": interval_timestamp,
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": quantity
                }
                
                # Save new interval data
                self.redis.set(current_key, json.dumps(new_data))