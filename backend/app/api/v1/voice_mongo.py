"""
Voice Alert API Endpoints - MongoDB Version
11Labs integration for medical announcements
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
from pydantic import BaseModel
import logging

from ...models.mongo_models import Patient, QueueEntry, Alert, QueueStatus
from ...services.voice_service import voice_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Request Models
class CriticalPatientRequest(BaseModel):
    patient_id: str

class VoiceTestRequest(BaseModel):
    message: str = "Emergency triage system test announcement"

# Voice Alert Endpoints

@router.post("/alerts/critical-patient")
async def critical_patient_alert(
    request: CriticalPatientRequest,
    background_tasks: BackgroundTasks
):
    """Trigger voice alert for critical patient"""

    try:
        # Get patient information
        patient = await Patient.get(request.patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Get queue entry
        queue_entry = await QueueEntry.find_one(QueueEntry.patient_id == request.patient_id)
        if not queue_entry:
            raise HTTPException(status_code=404, detail="Patient not in queue")

        # Run voice alert in background
        background_tasks.add_task(
            voice_service.announce_critical_patient,
            patient_id=request.patient_id,
            esi_level=queue_entry.esi_level,
            chief_complaint=patient.chief_complaint
        )

        return {
            "message": "Critical patient alert triggered",
            "patient_id": request.patient_id,
            "esi_level": queue_entry.esi_level,
            "status": "voice_alert_queued"
        }

    except Exception as e:
        logger.error(f"Failed to trigger critical patient alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger alert: {str(e)}")

@router.post("/alerts/queue-status")
async def queue_status_announcement(background_tasks: BackgroundTasks):
    """Announce current queue status"""

    try:
        # Get queue statistics
        waiting_count = await QueueEntry.find(QueueEntry.status == QueueStatus.WAITING).count()
        critical_count = await QueueEntry.find(
            QueueEntry.status == QueueStatus.WAITING,
            QueueEntry.esi_level <= 2
        ).count()

        # Run announcement in background
        background_tasks.add_task(
            voice_service.announce_queue_status,
            waiting_count=waiting_count,
            critical_count=critical_count
        )

        return {
            "message": "Queue status announcement triggered",
            "waiting_patients": waiting_count,
            "critical_patients": critical_count,
            "status": "announcement_queued"
        }

    except Exception as e:
        logger.error(f"Failed to announce queue status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to announce: {str(e)}")

@router.post("/alerts/mass-casualty")
async def mass_casualty_alert(
    patient_count: int,
    event_description: str,
    background_tasks: BackgroundTasks
):
    """Announce mass casualty event"""

    try:
        # Run mass casualty alert in background
        background_tasks.add_task(
            voice_service.announce_mass_casualty_event,
            patient_count=patient_count,
            event_description=event_description
        )

        # Create system alert
        alert = Alert(
            alert_type="mass_casualty",
            severity="critical",
            message=f"Mass casualty event: {patient_count} patients from {event_description}",
            voice_announcement=True
        )
        await alert.save()

        return {
            "message": "Mass casualty alert activated",
            "patient_count": patient_count,
            "event_description": event_description,
            "status": "emergency_protocols_activated"
        }

    except Exception as e:
        logger.error(f"Failed to trigger mass casualty alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger alert: {str(e)}")

@router.post("/alerts/staff")
async def staff_alert(
    message: str,
    background_tasks: BackgroundTasks,
    urgency: str = "normal"
):
    """General staff alert announcement"""

    if urgency not in ["normal", "high", "critical"]:
        raise HTTPException(status_code=400, detail="Urgency must be: normal, high, or critical")

    try:
        # Run staff alert in background
        background_tasks.add_task(
            voice_service.announce_staff_alert,
            message=message,
            urgency=urgency
        )

        return {
            "message": "Staff alert sent",
            "alert_message": message,
            "urgency": urgency
        }

    except Exception as e:
        logger.error(f"Failed to send staff alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send alert: {str(e)}")

@router.post("/test")
async def test_voice_service(
    background_tasks: BackgroundTasks,
    request: Optional[VoiceTestRequest] = None
):
    """Test voice service functionality"""

    test_message = request.message if request else "Voice alert system test. Emergency triage system operational."

    try:
        # Run test in background
        background_tasks.add_task(
            voice_service.test_voice_service,
            test_message
        )

        return {
            "message": "Voice test triggered",
            "test_message": test_message,
            "status": "test_queued"
        }

    except Exception as e:
        logger.error(f"Voice test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice test failed: {str(e)}")

@router.get("/status")
async def get_voice_service_status():
    """Get voice service status"""

    try:
        status = {
            "service": "11Labs Voice Alerts",
            "enabled": voice_service.enabled,
            "api_configured": bool(voice_service.api_key),
            "voice_id": voice_service.voice_id,
            "announcement_history_count": len(voice_service.announcement_history)
        }

        if voice_service.enabled:
            status["last_announcement"] = (
                voice_service.announcement_history[-1]
                if voice_service.announcement_history
                else None
            )

        return status

    except Exception as e:
        logger.error(f"Failed to get voice service status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.get("/history")
async def get_announcement_history(limit: int = 20):
    """Get recent voice announcement history"""

    try:
        history = voice_service.announcement_history[-limit:] if voice_service.announcement_history else []

        return {
            "announcements": history,
            "total_count": len(voice_service.announcement_history),
            "showing": len(history)
        }

    except Exception as e:
        logger.error(f"Failed to get announcement history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.get("/voices")
async def get_available_voices():
    """Get list of available voice options"""

    try:
        voices = voice_service.get_available_voices()

        return {
            "available_voices": voices,
            "current_voice_id": voice_service.voice_id,
            "recommended": "21m00Tcm4TlvDq8ikWAM"  # Rachel - Professional
        }

    except Exception as e:
        logger.error(f"Failed to get available voices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")