import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.redis_client import get_redis
from app.models.order import OrderModel, OrderCreate, Order, OrderSide, OrderType, OrderStatus
from app.models.order_book import OrderBook
from app.services.matching_engine import MatchingEngine
from typing import List, Optional, Dict, Tuple

class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.redis = get_redis()
        self.matching_engine = MatchingEngine(self.redis)
    
    def create_order(self, order_create: OrderCreate) -> Tuple[Order, List[Dict]]:
        """Create a new order and process it through the matching engine"""
        # Validate the order
        is_valid, error_message = self.validate_order(order_create)
        if not is_valid:
            raise ValueError(error_message)
        
        # Generate a unique order ID
        order_id = str(uuid.uuid4())
        
        # Create new order model
        db_order = OrderModel(
            order_id=order_id,
            trader_id=order_create.trader_id,
            symbol=order_create.symbol,
            side=order_create.side,
            order_type=order_create.order_type,
            quantity=order_create.quantity,
            price=order_create.price,
            status=OrderStatus.ACTIVE,  # Will be updated by matching engine
            filled_quantity=0
        )
        
        # Save to database
        self.db.add(db_order)
        self.db.commit()
        self.db.refresh(db_order)
        
        # Create Pydantic model for response
        order = Order(
            order_id=db_order.order_id,
            trader_id=db_order.trader_id,
            symbol=db_order.symbol,
            side=db_order.side,
            order_type=db_order.order_type,
            quantity=db_order.quantity,
            price=db_order.price,
            status=db_order.status,
            filled_quantity=db_order.filled_quantity,
            created_at=db_order.created_at,
            updated_at=db_order.updated_at
        )
        
        # Process the order through the matching engine
        trades = self.matching_engine.process_order(db_order, self.db)
        
        # Refresh the order after processing
        self.db.refresh(db_order)
        
        # Update the Pydantic model with the latest data
        order.status = db_order.status
        order.filled_quantity = db_order.filled_quantity
        order.updated_at = db_order.updated_at
        
        return order, trades
    
    def validate_order(self, order_create: OrderCreate) -> Tuple[bool, str]:
        """Validate an order before creating it"""
        # Check for required fields based on order type
        if order_create.order_type == OrderType.LIMIT and order_create.price is None:
            return False, "Limit orders require a price"
        
        # Check for positive quantity
        if order_create.quantity <= 0:
            return False, "Order quantity must be positive"
        
        # Check for positive price if limit order
        if order_create.order_type == OrderType.LIMIT and order_create.price <= 0:
            return False, "Limit order price must be positive"
        
        # Add more validation as needed
        
        return True, "Order is valid"
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID"""
        db_order = self.db.query(OrderModel).filter(OrderModel.order_id == order_id).first()
        if not db_order:
            return None
        
        return Order(
            order_id=db_order.order_id,
            trader_id=db_order.trader_id,
            symbol=db_order.symbol,
            side=db_order.side,
            order_type=db_order.order_type,
            quantity=db_order.quantity,
            price=db_order.price,
            status=db_order.status,
            filled_quantity=db_order.filled_quantity,
            created_at=db_order.created_at,
            updated_at=db_order.updated_at
        )
    
    def get_orders_by_trader(self, trader_id: str, symbol: Optional[str] = None) -> List[Order]:
        """Get all orders for a trader, optionally filtered by symbol"""
        query = self.db.query(OrderModel).filter(OrderModel.trader_id == trader_id)
        
        if symbol:
            query = query.filter(OrderModel.symbol == symbol)
        
        db_orders = query.all()
        
        orders = []
        for db_order in db_orders:
            orders.append(Order(
                order_id=db_order.order_id,
                trader_id=db_order.trader_id,
                symbol=db_order.symbol,
                side=db_order.side,
                order_type=db_order.order_type,
                quantity=db_order.quantity,
                price=db_order.price,
                status=db_order.status,
                filled_quantity=db_order.filled_quantity,
                created_at=db_order.created_at,
                updated_at=db_order.updated_at
            ))
        
        return orders
    
    def cancel_order(self, order_id: str) -> Optional[Order]:
        """Cancel an order"""
        db_order = self.db.query(OrderModel).filter(OrderModel.order_id == order_id).first()
        if not db_order:
            return None
        
        # Only active or partially filled orders can be cancelled
        if db_order.status not in [OrderStatus.ACTIVE, OrderStatus.PARTIALLY_FILLED]:
            return None
        
        # Update order status
        db_order.status = OrderStatus.CANCELLED
        self.db.commit()
        self.db.refresh(db_order)
        
        # Remove from order book
        order_book = OrderBook(self.redis, db_order.symbol)
        order_book.remove_order(order_id)
        
        return Order(
            order_id=db_order.order_id,
            trader_id=db_order.trader_id,
            symbol=db_order.symbol,
            side=db_order.side,
            order_type=db_order.order_type,
            quantity=db_order.quantity,
            price=db_order.price,
            status=db_order.status,
            filled_quantity=db_order.filled_quantity,
            created_at=db_order.created_at,
            updated_at=db_order.updated_at
        )
    
    def get_order_book(self, symbol: str, depth: int = 10) -> Dict:
        """Get the current state of the order book for a symbol"""
        order_book = OrderBook(self.redis, symbol)
        return order_book.get_order_book_snapshot(depth)