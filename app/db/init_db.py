from sqlalchemy import create_engine, text
from app.config import DATABASE_URL
from app.db.postgres import Base, engine
from app.models.order import OrderModel

def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create indexes or other initialization here
    
    print("Database initialized successfully")

if __name__ == "__main__":
    init_db()
