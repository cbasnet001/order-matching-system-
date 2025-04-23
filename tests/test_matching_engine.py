# tests/test_matching_engine.py
import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.services.matching_engine import MatchingEngine
from app.models.order import OrderSide, OrderType, OrderStatus

class MockOrder:
    def __init__(self, side, price, quantity):
        self.order_id = str(uuid.uuid4())
        self.trader_id = "test_trader"
        self.symbol = "BTC/USD"
        self.side = side
        self.order_type = OrderType.LIMIT
        self.price = price
        self.quantity = quantity
        self.status = OrderStatus.ACTIVE
        self.filled_quantity = 0
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = None

class TestMatchingEngine(unittest.TestCase):
    def setUp(self):
        # Create mock Redis client
        self.redis_mock = MagicMock()
        
        # Configure mock for get_best_ask and get_best_bid
        self.redis_mock.hget.return_value = None
        
        # Create matching engine with mock Redis
        self.matching_engine = MatchingEngine(self.redis_mock)
    
    def test_no_matching_orders(self):
        """Test when there are no matching orders"""
        # Configure order book to have no matching orders
        self.redis_mock.zrange.return_value = []
        
        # Create a buy order
        buy_order = MockOrder(OrderSide.BUY, 100.0, 10.0)
        
        # Process the order
        trades = self.matching_engine.process_order(buy_order)
        
        # Assert no trades were executed
        self.assertEqual(len(trades), 0)
        self.assertEqual(buy_order.filled_quantity, 0)
        self.assertEqual(buy_order.status, OrderStatus.ACTIVE)

if __name__ == '__main__':
    unittest.main()