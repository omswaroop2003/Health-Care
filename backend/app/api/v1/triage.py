from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta
import json

from ...core.database import get_db
from ...models import Patient, TriageAssessment, QueueEntry, Alert
from ...schemas.triage import TriageRequest, TriageResponse, QueueStatus, TriageStatistics
from ...services.triage_engine import ESITriageEngine
from ...core.config import settings

router = APIRouter()

@router.post("/assess", response_model=TriageResponse)
async def perform_triage(request: TriageRequest, db: Session = Depends(get_db)):
    """Perform triage assessment for a patient"""

    # Get patient data
    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Perform triage assessment
    triage_engine = ESITriageEngine()
    patient_data = {
        "age": patient.age,
        "chief_complaint": patient.chief_complaint,
        "bp_systolic": patient.bp_systolic,
        "bp_diastolic": patient.bp_diastolic,
        "heart_rate": patient.heart_rate,
        "temperature": patient.temperature,
        "o2_saturation": patient.o2_saturation,
        "respiratory_rate": patient.respiratory_rate,
        "pain_scale": patient.pain_scale,
        "consciousness_level": patient.consciousness_level,
        "bleeding": patient.bleeding,
        "breathing_difficulty": patient.breathing_difficulty,
        "trauma_indicator": patient.trauma_indicator
    }

    esi_level, confidence, reasons = triage_engine.assess_patient(patient_data)

    # Calculate wait time based on queue
    wait_time = estimate_wait_time(esi_level, db)

    # Store assessment
    assessment = TriageAssessment(
        patient_id=patient.id,
        esi_level=esi_level,
        priority_score=triage_engine.calculate_priority_score(esi_level, 0),
        ml_confidence=confidence,
        assessment_time=datetime.utcnow(),
        reason_codes=json.dumps(reasons),
        vital_signs_critical=(esi_level <= 2)
    )
    db.add(assessment)

    # Update or create queue entry
    queue_entry = db.query(QueueEntry).filter(QueueEntry.patient_id == patient.id).first()
    if queue_entry:
        queue_entry.esi_level = esi_level
        queue_entry.priority_score = assessment.priority_score
        queue_entry.last_updated = datetime.utcnow()
    else:
        queue_entry = QueueEntry(
            patient_id=patient.id,
            esi_level=esi_level,
            priority_score=assessment.priority_score,
            status="waiting",
            wait_time_minutes=0,
            estimated_treatment_time=wait_time
        )
        db.add(queue_entry)

    # Create alert if critical
    if esi_level <= 2:
        alert = Alert(
            patient_id=patient.id,
            alert_type="critical_patient",
            severity="critical" if esi_level == 1 else "high",
            message=f"Critical patient requires immediate attention - ESI Level {esi_level}"
        )
        db.add(alert)

    db.commit()

    # Determine recommended actions
    actions = get_recommended_actions(esi_level)

    return TriageResponse(
        patient_id=patient.id,
        esi_level=esi_level,
        priority_score=assessment.priority_score,
        ml_confidence=confidence,
        assessment_time=assessment.assessment_time,
        reason_codes=reasons,
        recommended_actions=actions,
        estimated_wait_time=wait_time
    )

@router.get("/queue", response_model=List[QueueStatus])
async def get_queue_status(db: Session = Depends(get_db)):
    """Get current queue status"""

    queue_entries = db.query(QueueEntry).filter(
        QueueEntry.status == "waiting"
    ).order_by(QueueEntry.priority_score.desc()).all()

    result = []
    for idx, entry in enumerate(queue_entries):
        patient = db.query(Patient).filter(Patient.id == entry.patient_id).first()

        # Calculate actual wait time
        wait_time = int((datetime.utcnow() - patient.arrival_time).total_seconds() / 60)

        result.append(QueueStatus(
            patient_id=patient.id,
            patient_name=f"Patient #{patient.id}",  # For privacy
            esi_level=entry.esi_level,
            queue_position=idx + 1,
            wait_time_minutes=wait_time,
            estimated_remaining_wait=max(0, entry.estimated_treatment_time - wait_time),
            status=entry.status
        ))

    return result

@router.get("/statistics", response_model=TriageStatistics)
async def get_triage_statistics(db: Session = Depends(get_db)):
    """Get triage system statistics"""

    # Total patients
    total_patients = db.query(Patient).count()

    # Patients by ESI level
    by_esi = {}
    for level in range(1, 6):
        count = db.query(QueueEntry).filter(QueueEntry.esi_level == level).count()
        by_esi[f"level_{level}"] = count

    # Average wait times by ESI level
    avg_wait_times = {}
    for level in range(1, 6):
        entries = db.query(QueueEntry).filter(
            QueueEntry.esi_level == level,
            QueueEntry.status == "waiting"
        ).all()

        if entries:
            total_wait = sum(e.wait_time_minutes for e in entries)
            avg_wait_times[f"level_{level}"] = total_wait / len(entries)
        else:
            avg_wait_times[f"level_{level}"] = 0

    # Critical patients
    critical_patients = db.query(QueueEntry).filter(
        QueueEntry.esi_level <= 2,
        QueueEntry.status == "waiting"
    ).count()

    # Patients seen today
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    patients_today = db.query(Patient).filter(
        Patient.arrival_time >= today_start
    ).count()

    return TriageStatistics(
        total_patients=total_patients,
        by_esi_level=by_esi,
        average_wait_times=avg_wait_times,
        critical_patients=critical_patients,
        patients_seen_today=patients_today,
        average_processing_time=2.5  # Would calculate from actual data
    )

@router.get("/alerts/active")
async def get_active_alerts(db: Session = Depends(get_db)):
    """Get active alerts"""
    alerts = db.query(Alert).filter(
        Alert.acknowledged == False
    ).order_by(Alert.created_at.desc()).all()

    result = []
    for alert in alerts:
        patient = db.query(Patient).filter(Patient.id == alert.patient_id).first()
        result.append({
            "alert_id": alert.id,
            "patient_id": alert.patient_id,
            "patient_name": f"Patient #{patient.id}",
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "created_at": alert.created_at.isoformat()
        })

    return result

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.commit()

    return {"message": "Alert acknowledged"}

def estimate_wait_time(esi_level: int, db: Session) -> int:
    """Estimate wait time based on ESI level and current queue"""
    base_wait_times = {
        1: 0,    # Immediate
        2: 10,   # 10 minutes
        3: 30,   # 30 minutes
        4: 60,   # 1 hour
        5: 120   # 2 hours
    }

    # Adjust based on current queue
    queue_size = db.query(QueueEntry).filter(
        QueueEntry.status == "waiting",
        QueueEntry.esi_level <= esi_level
    ).count()

    # Add 5 minutes per patient ahead in queue
    additional_wait = queue_size * 5

    return base_wait_times.get(esi_level, 60) + additional_wait

def get_recommended_actions(esi_level: int) -> List[str]:
    """Get recommended actions based on ESI level"""
    actions = {
        1: [
            "Immediate resuscitation room",
            "Call trauma/code team",
            "Continuous monitoring",
            "Prepare emergency medications"
        ],
        2: [
            "High acuity area placement",
            "Immediate physician assessment",
            "Cardiac monitoring",
            "IV access and labs"
        ],
        3: [
            "Urgent care area",
            "Labs and imaging as needed",
            "Pain management",
            "Regular vital sign checks"
        ],
        4: [
            "Fast track if available",
            "Single resource likely",
            "Reassess if wait exceeds 1 hour"
        ],
        5: [
            "Non-urgent care",
            "Consider referral to clinic",
            "Patient education materials"
        ]
    }

    return actions.get(esi_level, [])