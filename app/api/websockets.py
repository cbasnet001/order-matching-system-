from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.db.redis_client import get_redis
import redis
import json
import asyncio
from typing import Dict, List, Set

router = APIRouter()

# Store connected WebSocket clients
connected_clients: Dict[str, Set[WebSocket]] = {}

@router.websocket("/ws/orderbook/{symbol}")
async def orderbook_websocket(websocket: WebSocket, symbol: str):
    await websocket.accept()
    
    # Add client to connected clients for this symbol
    if symbol not in connected_clients:
        connected_clients[symbol] = set()
    connected_clients[symbol].add(websocket)
    
    try:
        # Create Redis pubsub connection
        redis_client = get_redis()
        pubsub = redis_client.pubsub()
        
        # Subscribe to orderbook updates for this symbol
        channel_name = f"orderbook_updates:{symbol}"
        pubsub.subscribe(channel_name)
        
        # Listen for messages in a separate task
        task = asyncio.create_task(listen_for_messages(pubsub, websocket))
        
        # Keep the connection open and handle client messages
        while True:
            data = await websocket.receive_text()
            # Client can send commands like "depth:20" to change order book depth
            if data.startswith("depth:"):
                try:
                    depth = int(data.split(":")[1])
                    # Could implement changing depth here
                except ValueError:
                    pass
    
    except WebSocketDisconnect:
        # Remove client from connected clients
        if symbol in connected_clients:
            connected_clients[symbol].remove(websocket)
            if not connected_clients[symbol]:
                del connected_clients[symbol]
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        # Clean up
        task.cancel()
        if symbol in connected_clients and websocket in connected_clients[symbol]:
            connected_clients[symbol].remove(websocket)
            if not connected_clients[symbol]:
                del connected_clients[symbol]

async def listen_for_messages(pubsub, websocket: WebSocket):
    """Listen for Redis pubsub messages and forward to WebSocket client"""
    try:
        for message in pubsub.listen():
            if message["type"] == "message":
                # Forward the message to the WebSocket client
                await websocket.send_text(message["data"].decode())
    except Exception as e:
        print(f"PubSub error: {str(e)}")
    finally:
        pubsub.close()

@router.websocket("/ws/trades/{symbol}")
async def trades_websocket(websocket: WebSocket, symbol: str):
    await websocket.accept()
    
    try:
        # Create Redis pubsub connection
        redis_client = get_redis()
        pubsub = redis_client.pubsub()
        
        # Subscribe to trade updates for this symbol
        channel_name = f"trade_updates:{symbol}"
        pubsub.subscribe(channel_name)
        
        # Listen for messages in a separate task
        task = asyncio.create_task(listen_for_messages(pubsub, websocket))
        
        # Keep the connection open
        while True:
            await websocket.receive_text()
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        # Clean up
        task.cancel()

# Function to publish order book updates
def publish_orderbook_update(redis_client: redis.Redis, symbol: str, order_book_data: Dict):
    """Publish order book updates to subscribers"""
    channel_name = f"orderbook_updates:{symbol}"
    redis_client.publish(channel_name, json.dumps(order_book_data))

# Function to publish trade updates
def publish_trade_update(redis_client: redis.Redis, symbol: str, trade_data: Dict):
    """Publish trade updates to subscribers"""
    channel_name = f"trade_updates:{symbol}"
    redis_client.publish(channel_name, json.dumps(trade_data))