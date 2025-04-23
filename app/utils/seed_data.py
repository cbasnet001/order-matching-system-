import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.postgres import SessionLocal, engine, Base
from app.models.order import OrderModel, OrderSide, OrderType, OrderStatus
from app.db.redis_client import get_redis
from app.models.order_book import OrderBook

def create_seed_data():
    """Create sample data for testing"""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    redis_client = get_redis()
    
    try:
        # Create some sample orders
        symbols = ["BTC/USD", "ETH/USD", "AAPL", "MSFT"]
        
        for symbol in symbols:
            # Create buy orders
            for i in range(5):
                price = 100.0 - i * 0.5  # Decreasing prices for buy orders
                order_id = str(uuid.uuid4())
                order = OrderModel(
                    order_id=order_id,
                    trader_id=f"trader{i % 3 + 1}",
                    symbol=symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.LIMIT,
                    quantity=10.0,
                    price=price,
                    status=OrderStatus.ACTIVE,
                    filled_quantity=0,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(order)
            
            # Create sell orders
            for i in range(5):
                price = 101.0 + i * 0.5  # Increasing prices for sell orders
                order_id = str(uuid.uuid4())
                order = OrderModel(
                    order_id=order_id,
                    trader_id=f"trader{i % 3 + 1}",
                    symbol=symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.LIMIT,
                    quantity=10.0,
                    price=price,
                    status=OrderStatus.ACTIVE,
                    filled_quantity=0,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(order)
        
        db.commit()
        print("Seed data created successfully in PostgreSQL!")
        
        # Add orders to the Redis order book
        orders = db.query(OrderModel).all()
        
        for db_order in orders:
            # Create order book for this symbol
            order_book = OrderBook(redis_client, db_order.symbol)
            
            # Create an order object to add to the book
            order = {
                "order_id": db_order.order_id,
                "trader_id": db_order.trader_id,
                "symbol": db_order.symbol,
                "side": db_order.side,
                "order_type": db_order.order_type,
                "quantity": db_order.quantity,
                "price": db_order.price,
                "status": db_order.status,
                "filled_quantity": db_order.filled_quantity
            }
            
            # Add to order book in Redis
            order_book.add_order(type('obj', (object,), order))
            print(f"Added order {db_order.order_id} to order book for {db_order.symbol}")
        
        print("All orders added to Redis order book!")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating seed data: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_seed_data()