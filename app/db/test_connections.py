import redis
from sqlalchemy import create_engine, text
from app.config import DATABASE_URL, REDIS_URL

def test_postgres_connection():
    try:
        # Connect to the PostgreSQL database
        engine = create_engine(DATABASE_URL)
        
        # Execute a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("PostgreSQL Connection: SUCCESS")
            return True
    except Exception as e:
        print(f"PostgreSQL Connection: FAILED - {str(e)}")
        return False

def test_redis_connection():
    try:
        # Connect to Redis
        redis_client = redis.from_url(REDIS_URL)
        
        # Execute a ping
        result = redis_client.ping()
        print("Redis Connection: SUCCESS")
        return True
    except Exception as e:
        print(f"Redis Connection: FAILED - {str(e)}")
        return False

if __name__ == "__main__":
    postgres_ok = test_postgres_connection()
    redis_ok = test_redis_connection()
    
    if postgres_ok and redis_ok:
        print("All database connections are working!")
    else:
        print("Some database connections failed. Please check the output above.")
