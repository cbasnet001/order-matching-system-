import redis
from app.config import REDIS_URL

# Create Redis connection pool
redis_pool = redis.ConnectionPool.from_url(REDIS_URL)

# Create Redis client
def get_redis():
    return redis.Redis(connection_pool=redis_pool)