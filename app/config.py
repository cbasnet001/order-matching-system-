import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Application settings
APP_NAME = "Order Matching System"
APP_VERSION = "0.1.0"
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/orderbook")

# Redis settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# RabbitMQ settings
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

# API settings
API_PREFIX = "/api/v1"
