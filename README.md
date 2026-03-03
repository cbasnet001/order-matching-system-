# Order Matching System

A high-performance, real-time order matching engine built with FastAPI, Redis, PostgreSQL, and RabbitMQ. This system matches buy and sell orders, executes trades, and maintains a distributed order book with real-time WebSocket support.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Development](#development)

## 🎯 Overview

The Order Matching System is a financial trading platform that processes and matches buy/sell orders in real-time. It implements an order matching engine that:

- Accepts buy and sell orders from traders
- Automatically matches compatible orders based on price and quantity
- Executes trades immediately when matches are found
- Maintains a distributed order book using Redis
- Persists orders and trades to PostgreSQL
- Streams events via RabbitMQ for service integration
- Provides real-time updates through WebSocket connections

## 🏗️ Architecture

### System Components

```
┌─────────────────┐
│    FastAPI      │ REST API & WebSocket Server
└────────┬────────┘
         │
    ┌────┴────┬─────────────┬──────────────┐
    │          │             │              │
┌───▼──┐  ┌───▼────┐  ┌───▼─────┐  ┌────▼───┐
│Order │  │Matching│  │Trade    │  │Market  │
│Service│  │Engine  │  │Service  │  │Data    │
└───┬──┘  └───┬────┘  └───┬─────┘  └────┬───┘
    │          │           │             │
    └──────┬───┴───┬───────┴─────────────┘
           │       │
    ┌──────▼─┐  ┌──▼──────┐
    │ Redis  │  │PostgreSQL│
    │Order   │  │Orders &  │
    │Book    │  │Trades    │
    └────────┘  └──────────┘
           │
    ┌──────▼─────────┐
    │   RabbitMQ     │
    │Event Streaming │
    └────────────────┘
```

### Data Flow

1. **Order Creation**: Client submits an order via REST API
2. **Validation**: Order service validates the order
3. **Matching**: Matching engine matches against existing orders in Redis order book
4. **Execution**: Trades are executed and persisted
5. **Persistence**: Orders and trades stored in PostgreSQL
6. **Broadcasting**: Events published to RabbitMQ and WebSocket clients

## ✨ Features

- **Order Management**
  - Create limit and market orders
  - Support for BUY and SELL sides
  - Cancel pending orders
  - Track order status (PENDING, ACTIVE, PARTIALLY_FILLED, FILLED, CANCELLED)

- **Matching Engine**
  - Price-time priority matching algorithm
  - Automatic partial fill handling
  - Multi-symbol support
  - Real-time order book management

- **Trade Execution**
  - Immediate trade settlement
  - Trade logging and audit trail
  - Support for multiple order symbols

- **Real-time Updates**
  - WebSocket connections for live order updates
  - Event streaming via RabbitMQ
  - Order book notifications

- **Data Persistence**
  - PostgreSQL for orders and trades history
  - Redis for high-speed order book operations

- **API Health**
  - Health check endpoint
  - Dependency verification (PostgreSQL, Redis, RabbitMQ)

## 🛠️ Tech Stack

- **Backend**: Python 3.9+
- **Web Framework**: FastAPI 0.95.1+
- **Server**: Uvicorn 0.22.0+
- **Database**: PostgreSQL 14
- **Cache & Order Book**: Redis 7
- **Message Queue**: RabbitMQ 3
- **ORM**: SQLAlchemy 2.0+
- **Data Validation**: Pydantic 2.0+
- **Real-time**: WebSockets 11.0+
- **Testing**: pytest 7.3+

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.9+ (if running locally without Docker)
- Git

## 🚀 Installation

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd order-matching-system
   ```

2. **Build and start all services**
   ```bash
   cd docker
   docker-compose up -d
   ```

   This will start:
   - FastAPI application on port 8000
   - PostgreSQL on port 5432
   - Redis on port 6379
   - RabbitMQ on ports 5672 and 15672

### Local Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd order-matching-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure services are running**
   - PostgreSQL: Running on localhost:5432
   - Redis: Running on localhost:6379
   - RabbitMQ: Running on localhost:5672

## ⚙️ Configuration

The application uses environment variables for configuration. Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/orderbook

# Redis
REDIS_URL=redis://localhost:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Application
DEBUG=False
```

### Default Configuration

When running with Docker Compose, the default environment variables are already set up in `docker/docker-compose.yml`.

## 🏃 Running the Application

### With Docker Compose

```bash
cd docker
docker-compose up
```

The application will be available at `http://localhost:8000`

### Manually (Local Development)

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Run the application
uvicorn app.main:app --reload
```

The application will start on `http://localhost:8000`

### Verify All Services

Check that all dependencies are connected:

```bash
curl http://localhost:8000/test-connections
```

Response should show all services as "connected".

### Health Check

```bash
curl http://localhost:8000/health
```

## 📡 API Endpoints

### Orders

**Create Order**
```
POST /api/v1/orders/
Content-Type: application/json

{
  "trader_id": "trader_123",
  "symbol": "AAPL",
  "side": "buy",
  "order_type": "limit",
  "quantity": 100,
  "price": 150.50
}
```

**Get Order**
```
GET /api/v1/orders/{order_id}
```

**Get Trader's Orders**
```
GET /api/v1/orders/?trader_id=trader_123&symbol=AAPL
```

**Cancel Order**
```
DELETE /api/v1/orders/{order_id}
```

### Trades

**Get Trades**
```
GET /api/v1/trades/?symbol=AAPL
```

**Get Trade by ID**
```
GET /api/v1/trades/{trade_id}
```

### WebSocket

**Real-time Order Updates**
```
WS /ws/orders/{trader_id}
```

**Order Book Updates**
```
WS /ws/orderbook/{symbol}
```

### System

**Health Check**
```
GET /health
```

**Test Connections**
```
GET /test-connections
```

## 📁 Project Structure

```
order-matching-system/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration and environment variables
│   ├── api/                    # API route handlers
│   │   ├── orders.py           # Order endpoints
│   │   ├── trades.py           # Trade endpoints
│   │   └── websockets.py       # WebSocket endpoints
│   ├── db/                     # Database and cache connections
│   │   ├── postgres.py         # PostgreSQL connection
│   │   ├── redis_client.py     # Redis connection pool
│   │   ├── init_db.py          # Database initialization
│   │   └── test_connections.py # Connection testing utilities
│   ├── models/                 # Database and API models
│   │   ├── order.py            # Order models (SQLAlchemy & Pydantic)
│   │   ├── order_book.py       # Order book implementation
│   │   └── trade.py            # Trade models
│   ├── services/               # Business logic
│   │   ├── matching_engine.py  # Core matching algorithm
│   │   ├── order_service.py    # Order management
│   │   ├── trade_service.py    # Trade management
│   │   └── market_data.py      # Market data service
│   ├── messaging/              # Message queue integration
│   │   ├── publisher.py        # RabbitMQ event publisher
│   │   └── consumer.py         # RabbitMQ event consumer
│   └── utils/
│       └── seed_data.py        # Sample data generation
├── docker/                     # Docker configuration
│   ├── Dockerfile              # Application container
│   └── docker-compose.yml      # Multi-service orchestration
├── tests/                      # Test suite
│   ├── test_matching_engine.py # Matching engine tests
│   └── test_order_api.py       # API endpoint tests
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_matching_engine.py -v
```

### Run Tests with Coverage

```bash
pytest --cov=app tests/
```

### Test Files

- **test_matching_engine.py**: Tests for the order matching algorithm
- **test_order_api.py**: Tests for REST API endpoints

## 🔧 Development

### Database

Initialize the database schema:

```bash
python -c "from app.db.init_db import init_db; init_db()"
```

### Seed Sample Data

Load test data into the system:

```bash
python -c "from app.utils.seed_data import seed_data; seed_data()"
```

### Code Style

The project follows PEP 8 conventions. Format code with:

```bash
black app/
```

### Debugging

Enable debug mode in `.env`:

```env
DEBUG=True
```

Then run with:

```bash
uvicorn app.main:app --reload --log-level debug
```

## 🐛 Troubleshooting

### PostgreSQL Connection Error

```
error: could not translate host name "postgres" to address
```

Ensure PostgreSQL is running and accessible at the configured DATABASE_URL.

### Redis Connection Error

```
redis.exceptions.ConnectionError
```

Ensure Redis is running on the configured REDIS_URL.

### RabbitMQ Connection Error

No consumer will connect, but the system continues functioning. Ensure RabbitMQ is running for message streaming.

### Reset Database

To reset the database and start fresh:

```bash
docker-compose down -v  # Remove volumes
docker-compose up      # Recreate everything
```

## 📝 License

[Add your license information]

## 👥 Contributing

[Add contribution guidelines]

## 📞 Support

[Add support contact information]