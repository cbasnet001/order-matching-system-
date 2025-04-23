from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis
import psycopg2
import pika

# Import configuration
from app.config import APP_NAME, APP_VERSION, API_PREFIX

# Import routers
from app.api.orders import router as orders_router
from app.api.trades import router as trades_router
from app.api.websockets import router as websockets_router

# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    # Initialize database
    from app.db.init_db import init_db
    init_db()
    
    yield  # This is where the app runs
    
    # Shutdown logic
    # Cleanup resources
    pass

# Create the FastAPI app with lifespan
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan
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

# Include API routers
app.include_router(orders_router, prefix=f"{API_PREFIX}/orders", tags=["orders"])
app.include_router(trades_router, prefix=f"{API_PREFIX}/trades", tags=["trades"])
app.include_router(websockets_router, tags=["websockets"])