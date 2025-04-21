from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import redis
import psycopg2
import pika

# Import configuration
try:
    from app.config import APP_NAME, APP_VERSION, API_PREFIX
except ImportError:
    APP_NAME = "Order Matching System"
    APP_VERSION = "0.1.0"
    API_PREFIX = "/api/v1"

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check route
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": APP_VERSION}

# Docker services connection test
@app.get("/test-connections")
async def test_connections():
    from app.config import DATABASE_URL, REDIS_URL, RABBITMQ_URL
    
    results = {
        "postgres": "not connected",
        "redis": "not connected",
        "rabbitmq": "not connected"
    }
    
    # Test PostgreSQL connection
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        results["postgres"] = "connected"
        cur.close()
        conn.close()
    except Exception as e:
        results["postgres"] = f"error: {str(e)}"
    
    # Test Redis connection
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        results["redis"] = "connected"
    except Exception as e:
        results["redis"] = f"error: {str(e)}"
    
    # Test RabbitMQ connection
    try:
        parameters = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(parameters)
        connection.close()
        results["rabbitmq"] = "connected"
    except Exception as e:
        results["rabbitmq"] = f"error: {str(e)}"
    
    return results

# Include other API routes later
# app.include_router(orders_router, prefix=API_PREFIX)
# app.include_router(trades_router, prefix=API_PREFIX)
