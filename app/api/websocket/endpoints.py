from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from uuid import uuid4
from app.api.deps import get_current_user, verify_token
from app.models.user import UserInDB
from app.api.websocket.manager import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
):
    # Verify token and get user
    try:
        user = await verify_token(token)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except HTTPException:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Generate unique connection ID
    connection_id = str(uuid4())

    try:
        await manager.connect(websocket, str(user.id), connection_id)
        
        # Handle incoming messages
        try:
            while True:
                message = await websocket.receive_json()
                
                # Handle subscription messages
                if message.get("type") == "subscribe":
                    event_types = message.get("event_types", [])
                    await manager.subscribe(str(user.id), event_types)
                    await websocket.send_json({
                        "type": "subscription_success",
                        "data": {"event_types": event_types}
                    })
                
                # Handle unsubscription messages
                elif message.get("type") == "unsubscribe":
                    event_types = message.get("event_types")
                    await manager.unsubscribe(str(user.id), event_types)
                    await websocket.send_json({
                        "type": "unsubscription_success",
                        "data": {"event_types": event_types}
                    })
                
                # Handle ping messages
                elif message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "data": {"timestamp": message.get("timestamp")}
                    })

        except WebSocketDisconnect:
            await manager.disconnect(str(user.id), connection_id)
            
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))
        return

@router.post("/broadcast")
async def broadcast_to_users(
    event_type: str,
    user_ids: List[str],
    data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Broadcast a message to specific users."""
    for user_id in user_ids:
        await manager.broadcast_to_user(user_id, event_type, data)
    return {"status": "success", "message": "Broadcast sent"}

@router.post("/broadcast/all")
async def broadcast_to_all(
    event_type: str,
    data: dict,
    current_user: UserInDB = Depends(get_current_user)
):
    """Broadcast a message to all connected users."""
    await manager.broadcast_to_all(event_type, data)
    return {"status": "success", "message": "Broadcast sent to all users"}
