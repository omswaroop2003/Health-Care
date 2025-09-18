"""
Real-time WebSocket Service for Emergency Triage System
Provides live updates for patient queue, alerts, and system status
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.database import get_db, SessionLocal
from ..models import Patient, QueueEntry, Alert, TriageAssessment

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # Store active connections by type
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "dashboard": set(),
            "queue": set(),
            "alerts": set(),
            "all": set()
        }

        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}

        # Background tasks
        self.running_tasks: Set[asyncio.Task] = set()
        self.update_interval = 5  # seconds

    async def connect(self, websocket: WebSocket, client_type: str = "all", client_id: Optional[str] = None):
        """Accept new WebSocket connection"""
        try:
            await websocket.accept()

            # Add to appropriate connection group
            if client_type not in self.active_connections:
                client_type = "all"

            self.active_connections[client_type].add(websocket)
            self.active_connections["all"].add(websocket)

            # Store metadata
            self.connection_metadata[websocket] = {
                "client_type": client_type,
                "client_id": client_id,
                "connected_at": datetime.utcnow(),
                "last_ping": datetime.utcnow()
            }

            logger.info(f"New WebSocket connection: {client_type} ({client_id})")

            # Send initial data
            await self.send_initial_data(websocket, client_type)

        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {e}")
            raise

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        try:
            # Remove from all connection groups
            for connection_set in self.active_connections.values():
                connection_set.discard(websocket)

            # Remove metadata
            metadata = self.connection_metadata.pop(websocket, {})
            client_type = metadata.get("client_type", "unknown")
            client_id = metadata.get("client_id", "unknown")

            logger.info(f"WebSocket disconnected: {client_type} ({client_id})")

        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                **message
            }))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast_to_type(self, message: Dict[str, Any], client_type: str):
        """Broadcast message to all connections of specific type"""
        if client_type not in self.active_connections:
            return

        disconnected = set()
        connections = self.active_connections[client_type].copy()

        for websocket in connections:
            try:
                await websocket.send_text(json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    **message
                }))
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_type}: {e}")
                disconnected.add(websocket)

        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        await self.broadcast_to_type(message, "all")

    async def send_initial_data(self, websocket: WebSocket, client_type: str):
        """Send initial data when client connects"""
        try:
            db = SessionLocal()

            if client_type in ["dashboard", "all"]:
                # Send dashboard data
                stats = await self.get_dashboard_stats(db)
                await self.send_personal_message({
                    "type": "dashboard_stats",
                    "data": stats
                }, websocket)

            if client_type in ["queue", "all"]:
                # Send queue data
                queue_data = await self.get_queue_data(db)
                await self.send_personal_message({
                    "type": "queue_update",
                    "data": queue_data
                }, websocket)

            if client_type in ["alerts", "all"]:
                # Send active alerts
                alerts = await self.get_active_alerts(db)
                await self.send_personal_message({
                    "type": "alerts_update",
                    "data": alerts
                }, websocket)

            db.close()

        except Exception as e:
            logger.error(f"Failed to send initial data: {e}")

    async def get_dashboard_stats(self, db: Session) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            total_patients = db.query(Patient).count()
            waiting_patients = db.query(QueueEntry).filter(QueueEntry.status == "waiting").count()
            critical_patients = db.query(QueueEntry).filter(
                QueueEntry.esi_level <= 2,
                QueueEntry.status == "waiting"
            ).count()

            # ESI distribution
            esi_counts = {}
            for level in range(1, 6):
                count = db.query(QueueEntry).filter(
                    QueueEntry.esi_level == level,
                    QueueEntry.status == "waiting"
                ).count()
                esi_counts[f"level_{level}"] = count

            return {
                "total_patients": total_patients,
                "waiting_patients": waiting_patients,
                "critical_patients": critical_patients,
                "esi_distribution": esi_counts,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {e}")
            return {}

    async def get_queue_data(self, db: Session) -> List[Dict[str, Any]]:
        """Get current queue data"""
        try:
            queue_entries = db.query(QueueEntry).filter(
                QueueEntry.status == "waiting"
            ).order_by(QueueEntry.priority_score.desc()).limit(50).all()

            queue_data = []
            for idx, entry in enumerate(queue_entries):
                patient = db.query(Patient).filter(Patient.id == entry.patient_id).first()
                if patient:
                    wait_time = int((datetime.utcnow() - patient.arrival_time).total_seconds() / 60)

                    queue_data.append({
                        "patient_id": patient.id,
                        "patient_name": f"Patient #{patient.id}",
                        "esi_level": entry.esi_level,
                        "queue_position": idx + 1,
                        "wait_time_minutes": wait_time,
                        "chief_complaint": patient.chief_complaint,
                        "priority_score": float(entry.priority_score),
                        "status": entry.status
                    })

            return queue_data

        except Exception as e:
            logger.error(f"Failed to get queue data: {e}")
            return []

    async def get_active_alerts(self, db: Session) -> List[Dict[str, Any]]:
        """Get active alerts"""
        try:
            alerts = db.query(Alert).filter(
                Alert.acknowledged == False
            ).order_by(Alert.created_at.desc()).limit(20).all()

            alert_data = []
            for alert in alerts:
                patient = db.query(Patient).filter(Patient.id == alert.patient_id).first()

                alert_data.append({
                    "alert_id": alert.id,
                    "patient_id": alert.patient_id,
                    "patient_name": f"Patient #{patient.id}" if patient else "Unknown",
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "created_at": alert.created_at.isoformat()
                })

            return alert_data

        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []

    def get_connection_count(self) -> Dict[str, int]:
        """Get count of active connections by type"""
        return {
            client_type: len(connections)
            for client_type, connections in self.active_connections.items()
        }

    async def start_background_updates(self):
        """Start background task for periodic updates"""
        if not self.running_tasks:
            task = asyncio.create_task(self._periodic_updates())
            self.running_tasks.add(task)
            logger.info("Started background WebSocket updates")

    async def stop_background_updates(self):
        """Stop all background tasks"""
        for task in self.running_tasks:
            task.cancel()

        await asyncio.gather(*self.running_tasks, return_exceptions=True)
        self.running_tasks.clear()
        logger.info("Stopped background WebSocket updates")

    async def _periodic_updates(self):
        """Periodic background updates for all clients"""
        while True:
            try:
                if self.active_connections["all"]:
                    db = SessionLocal()

                    # Update dashboard stats
                    if self.active_connections["dashboard"] or self.active_connections["all"]:
                        stats = await self.get_dashboard_stats(db)
                        await self.broadcast_to_type({
                            "type": "dashboard_stats",
                            "data": stats
                        }, "dashboard")

                    # Update queue data
                    if self.active_connections["queue"] or self.active_connections["all"]:
                        queue_data = await self.get_queue_data(db)
                        await self.broadcast_to_type({
                            "type": "queue_update",
                            "data": queue_data
                        }, "queue")

                    # Update alerts
                    if self.active_connections["alerts"] or self.active_connections["all"]:
                        alerts = await self.get_active_alerts(db)
                        await self.broadcast_to_type({
                            "type": "alerts_update",
                            "data": alerts
                        }, "alerts")

                    db.close()

                await asyncio.sleep(self.update_interval)

            except asyncio.CancelledError:
                logger.info("Periodic updates cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic updates: {e}")
                await asyncio.sleep(self.update_interval)

    async def notify_patient_update(self, patient_id: int, update_type: str, data: Dict[str, Any]):
        """Notify clients about patient updates"""
        message = {
            "type": "patient_update",
            "update_type": update_type,
            "patient_id": patient_id,
            "data": data
        }

        await self.broadcast_to_all(message)

    async def notify_new_alert(self, alert_data: Dict[str, Any]):
        """Notify clients about new alerts"""
        message = {
            "type": "new_alert",
            "data": alert_data
        }

        await self.broadcast_to_type(message, "alerts")
        await self.broadcast_to_type(message, "all")

    async def notify_queue_change(self, change_type: str, patient_id: int, data: Dict[str, Any]):
        """Notify clients about queue changes"""
        message = {
            "type": "queue_change",
            "change_type": change_type,  # "new_patient", "status_change", "position_change"
            "patient_id": patient_id,
            "data": data
        }

        await self.broadcast_to_type(message, "queue")
        await self.broadcast_to_type(message, "all")

# Global connection manager instance
connection_manager = ConnectionManager()