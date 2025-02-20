from typing import Dict, List, Optional
from fastapi import WebSocket
from app.models.user import UserInDB

class ConnectionManager:
    def __init__(self):
        # Store active connections: {user_id: {connection_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Store user subscriptions: {user_id: [event_types]}
        self.subscriptions: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        self.active_connections[user_id][connection_id] = websocket

    async def disconnect(self, user_id: str, connection_id: str):
        """Disconnect a WebSocket client."""
        if user_id in self.active_connections:
            if connection_id in self.active_connections[user_id]:
                del self.active_connections[user_id][connection_id]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            if user_id in self.subscriptions:
                del self.subscriptions[user_id]

    async def subscribe(self, user_id: str, event_types: List[str]):
        """Subscribe a user to specific event types."""
        self.subscriptions[user_id] = event_types

    async def unsubscribe(self, user_id: str, event_types: Optional[List[str]] = None):
        """Unsubscribe a user from specific or all event types."""
        if event_types is None:
            if user_id in self.subscriptions:
                del self.subscriptions[user_id]
        else:
            if user_id in self.subscriptions:
                self.subscriptions[user_id] = [
                    event_type for event_type in self.subscriptions[user_id]
                    if event_type not in event_types
                ]

    async def broadcast_to_user(self, user_id: str, event_type: str, data: dict):
        """Broadcast a message to all connections of a specific user."""
        if (
            user_id in self.active_connections and
            user_id in self.subscriptions and
            event_type in self.subscriptions[user_id]
        ):
            message = {
                "type": event_type,
                "data": data
            }
            for connection in self.active_connections[user_id].values():
                try:
                    await connection.send_json(message)
                except:
                    # Connection might be closed
                    continue

    async def broadcast_to_all(self, event_type: str, data: dict):
        """Broadcast a message to all connected clients subscribed to the event type."""
        for user_id, event_types in self.subscriptions.items():
            if event_type in event_types:
                await self.broadcast_to_user(user_id, event_type, data)

# Create a global connection manager instance
manager = ConnectionManager()
