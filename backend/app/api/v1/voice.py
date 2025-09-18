"""
Voice Alert API Endpoints
Provides REST API for AI voice announcements and alerts
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
import logging

# MongoDB version - no database dependency needed
from ...models.mongo_models import Patient, QueueEntry, Alert
from ...services.voice_service import voice_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response Models
class VoiceAlertRequest(BaseModel):
    patient_id: int
    message: Optional[str] = None
    urgency: str = "normal"  # normal, high, critical

class QueueAnnouncementRequest(BaseModel):
    include_stats: bool = True
    custom_message: Optional[str] = None

class VoiceTestRequest(BaseModel):
    message: str = "Voice alert system test. Emergency triage system operational."

class VoiceSettingsRequest(BaseModel):
    stability: float = 0.5
    similarity_boost: float = 0.5
    style: float = 0.0

@router.post("/alerts/critical-patient")
async def announce_critical_patient(
    request: VoiceAlertRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger voice alert for critical patient"""

    # Get patient information
    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get ESI level from queue
    queue_entry = db.query(QueueEntry).filter(QueueEntry.patient_id == request.patient_id).first()
    if not queue_entry:
        raise HTTPException(status_code=404, detail="Patient not in queue")

    # Only announce for critical patients (ESI 1-3)
    if queue_entry.esi_level > 3:
        raise HTTPException(status_code=400, detail="Patient not critical enough for voice alert")

    # Background task to generate and announce
    background_tasks.add_task(
        voice_service.announce_critical_patient,
        request.patient_id,
        queue_entry.esi_level,
        patient.chief_complaint
    )

    return {
        "message": "Critical patient alert initiated",
        "patient_id": request.patient_id,
        "esi_level": queue_entry.esi_level,
        "chief_complaint": patient.chief_complaint
    }

@router.post("/alerts/queue-status")
async def announce_queue_status(
    background_tasks: BackgroundTasks,
    request: Optional[QueueAnnouncementRequest] = None,
    db: Session = Depends(get_db)
):
    """Announce current queue status"""

    # Get queue statistics
    waiting_count = db.query(QueueEntry).filter(QueueEntry.status == "waiting").count()
    critical_count = db.query(QueueEntry).filter(
        QueueEntry.esi_level <= 2,
        QueueEntry.status == "waiting"
    ).count()

    if request and request.custom_message:
        # Custom announcement
        background_tasks.add_task(
            voice_service.announce_staff_alert,
            request.custom_message,
            "normal"
        )
        message = request.custom_message
    else:
        # Standard queue announcement
        background_tasks.add_task(
            voice_service.announce_queue_status,
            waiting_count,
            critical_count
        )
        message = f"Queue status: {waiting_count} waiting, {critical_count} critical"

    return {
        "message": "Queue status announcement initiated",
        "waiting_count": waiting_count,
        "critical_count": critical_count,
        "announcement": message
    }

@router.post("/alerts/mass-casualty")
async def announce_mass_casualty(
    patient_count: int,
    event_description: str,
    background_tasks: BackgroundTasks
):
    """Announce mass casualty event"""

    # Validate input
    if patient_count < 5:
        raise HTTPException(status_code=400, detail="Mass casualty requires 5+ patients")

    # Background task for announcement
    background_tasks.add_task(
        voice_service.announce_mass_casualty_event,
        patient_count,
        event_description
    )

    return {
        "message": "Mass casualty alert initiated",
        "patient_count": patient_count,
        "event_description": event_description,
        "status": "emergency_protocols_activated"
    }

@router.post("/alerts/staff")
async def staff_alert(
    message: str,
    background_tasks: BackgroundTasks,
    urgency: str = "normal"
):
    """General staff alert announcement"""

    if urgency not in ["normal", "high", "critical"]:
        raise HTTPException(status_code=400, detail="Urgency must be: normal, high, or critical")

    # Background task for announcement
    background_tasks.add_task(
        voice_service.announce_staff_alert,
        message,
        urgency
    )

    return {
        "message": "Staff alert initiated",
        "alert_message": message,
        "urgency": urgency
    }

@router.post("/test")
async def test_voice_service(
    background_tasks: BackgroundTasks,
    request: Optional[VoiceTestRequest] = None
):
    """Test voice service functionality"""

    test_message = request.message if request else "Voice alert system test. Emergency triage system operational."

    # Run test in background
    background_tasks.add_task(
        voice_service.test_voice_service
    )

    return {
        "message": "Voice service test initiated",
        "test_message": test_message,
        "status": "testing"
    }

@router.get("/status")
async def get_voice_service_status():
    """Get voice service status and configuration"""

    status = {
        "enabled": voice_service.enabled,
        "api_configured": bool(voice_service.api_key),
        "voice_id": voice_service.voice_id,
        "voice_settings": voice_service.voice_settings
    }

    if voice_service.enabled:
        status["available_voices"] = voice_service.get_available_voices()

    return status

@router.get("/history")
async def get_announcement_history(limit: int = 20):
    """Get recent voice announcement history"""

    history = voice_service.get_announcement_history(limit)

    return {
        "announcements": history,
        "total_count": len(voice_service.announcement_history),
        "limit": limit
    }

@router.put("/settings")
async def update_voice_settings(settings: VoiceSettingsRequest):
    """Update voice generation settings"""

    voice_service.set_voice_settings(
        settings.stability,
        settings.similarity_boost,
        settings.style
    )

    return {
        "message": "Voice settings updated",
        "settings": voice_service.voice_settings
    }

@router.post("/alerts/patient-update")
async def announce_patient_condition_change(
    patient_id: int,
    old_esi_level: int,
    new_esi_level: int,
    reason: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Announce patient condition change"""

    # Validate patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Validate ESI levels
    if not (1 <= old_esi_level <= 5) or not (1 <= new_esi_level <= 5):
        raise HTTPException(status_code=400, detail="ESI levels must be 1-5")

    # Only announce significant changes (deterioration or major improvement)
    significant_change = (
        new_esi_level < old_esi_level or  # Deterioration
        abs(new_esi_level - old_esi_level) >= 2  # Major change
    )

    if significant_change:
        background_tasks.add_task(
            voice_service.announce_patient_update,
            patient_id,
            old_esi_level,
            new_esi_level,
            reason
        )

        return {
            "message": "Patient condition change alert initiated",
            "patient_id": patient_id,
            "old_esi": old_esi_level,
            "new_esi": new_esi_level,
            "reason": reason,
            "announced": True
        }
    else:
        return {
            "message": "Patient condition change noted (no announcement needed)",
            "patient_id": patient_id,
            "old_esi": old_esi_level,
            "new_esi": new_esi_level,
            "reason": reason,
            "announced": False
        }

@router.get("/voices")
async def get_available_voices():
    """Get list of available voices"""

    if not voice_service.enabled:
        raise HTTPException(status_code=503, detail="Voice service not available")

    voices = voice_service.get_available_voices()

    return {
        "voices": voices,
        "current_voice_id": voice_service.voice_id,
        "total_count": len(voices)
    }

# Automatic voice alerts for critical patients
async def trigger_auto_voice_alert(patient_id: int, esi_level: int, chief_complaint: str):
    """Automatically trigger voice alert for critical patients"""

    if esi_level <= 2:  # Critical and Emergent patients
        try:
            await voice_service.announce_critical_patient(
                patient_id,
                esi_level,
                chief_complaint
            )
            logger.info(f"Auto voice alert triggered for patient {patient_id}, ESI {esi_level}")
        except Exception as e:
            logger.error(f"Failed to trigger auto voice alert: {e}")

# Integration with triage system
async def check_queue_alerts(db: Session):
    """Check for queue conditions requiring voice alerts"""

    try:
        # Check for overcrowding
        waiting_count = db.query(QueueEntry).filter(QueueEntry.status == "waiting").count()
        critical_count = db.query(QueueEntry).filter(
            QueueEntry.esi_level <= 2,
            QueueEntry.status == "waiting"
        ).count()

        # Alert if too many critical patients waiting
        if critical_count >= 3:
            await voice_service.announce_staff_alert(
                f"Multiple critical patients waiting. {critical_count} ESI Level 1-2 patients require immediate attention.",
                "high"
            )

        # Alert if severe overcrowding
        if waiting_count >= 30:
            await voice_service.announce_staff_alert(
                f"Emergency department at critical capacity. {waiting_count} patients waiting. Consider overflow protocols.",
                "critical"
            )

    except Exception as e:
        logger.error(f"Queue alert check failed: {e}")