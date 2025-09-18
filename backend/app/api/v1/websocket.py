"""
WebSocket API Endpoints for Real-time Updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging

from ...services.realtime_service_mongo import connection_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket, client_id: Optional[str] = Query(None)):
    """WebSocket endpoint for dashboard real-time updates"""

    await connection_manager.connect(websocket, "dashboard", client_id)

    # Start background updates if not already running
    await connection_manager.start_background_updates()

    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()

            # Handle ping/pong for connection health
            if data == "ping":
                await connection_manager.send_personal_message({"type": "pong"}, websocket)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info(f"Dashboard client {client_id} disconnected")

@router.websocket("/queue")
async def websocket_queue(websocket: WebSocket, client_id: Optional[str] = Query(None)):
    """WebSocket endpoint for queue real-time updates"""

    await connection_manager.connect(websocket, "queue", client_id)
    await connection_manager.start_background_updates()

    try:
        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await connection_manager.send_personal_message({"type": "pong"}, websocket)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info(f"Queue client {client_id} disconnected")

@router.websocket("/alerts")
async def websocket_alerts(websocket: WebSocket, client_id: Optional[str] = Query(None)):
    """WebSocket endpoint for alerts real-time updates"""

    await connection_manager.connect(websocket, "alerts", client_id)
    await connection_manager.start_background_updates()

    try:
        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await connection_manager.send_personal_message({"type": "pong"}, websocket)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info(f"Alerts client {client_id} disconnected")

@router.websocket("/all")
async def websocket_all(websocket: WebSocket, client_id: Optional[str] = Query(None)):
    """WebSocket endpoint for all real-time updates"""

    await connection_manager.connect(websocket, "all", client_id)
    await connection_manager.start_background_updates()

    try:
        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await connection_manager.send_personal_message({"type": "pong"}, websocket)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info(f"All-updates client {client_id} disconnected")

@router.get("/connections")
async def get_connection_status():
    """Get current WebSocket connection status"""

    connections = connection_manager.get_connection_count()

    return {
        "active_connections": connections,
        "total_connections": connections.get("all", 0),
        "update_interval": connection_manager.update_interval
    }