"""
Triage Management API Endpoints - MongoDB Version
Updated with patient status management endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ...models.mongo_models import (
    Patient,
    TriageAssessment,
    QueueEntry,
    Alert,
    QueueItemResponse,
    DashboardStats,
    QueueStatus,
    AlertSeverity
)
from ...services.ai_triage_simple import ai_triage_engine

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/queue", response_model=List[QueueItemResponse])
async def get_queue(
    limit: int = Query(50, le=100),
    esi_level: Optional[int] = Query(None, ge=1, le=5)
):
    """Get current emergency queue"""
    try:
        # Build query
        query = {"status": QueueStatus.WAITING}
        if esi_level:
            query["esi_level"] = esi_level

        # Get queue entries sorted by priority
        queue_entries = await QueueEntry.find(
            query,
            limit=limit,
            sort=[("esi_level", 1), ("priority_score", -1), ("entered_queue", 1)]
        ).to_list()

        # Build response with patient details
        queue_responses = []
        for idx, entry in enumerate(queue_entries):
            patient = await Patient.get(entry.patient_id)
            if patient:
                # Calculate wait time
                wait_time = int((datetime.utcnow() - entry.entered_queue).total_seconds() / 60)

                queue_responses.append(QueueItemResponse(
                    patient_id=str(patient.id),
                    patient_name=patient.name or f"Patient #{patient.id}",
                    esi_level=entry.esi_level,
                    queue_position=idx + 1,
                    wait_time_minutes=wait_time,
                    chief_complaint=patient.chief_complaint,
                    priority_score=entry.priority_score,
                    status=entry.status.value,
                    estimated_treatment_time=entry.estimated_treatment_time
                ))

        return queue_responses

    except Exception as e:
        logger.error(f"Failed to get queue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue: {str(e)}")

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Count patients
        total_patients = await Patient.count()
        waiting_patients = await QueueEntry.find(QueueEntry.status == QueueStatus.WAITING).count()
        critical_patients = await QueueEntry.find(
            QueueEntry.status == QueueStatus.WAITING,
            QueueEntry.esi_level <= 2
        ).count()

        # ESI distribution
        esi_distribution = {}
        for level in range(1, 6):
            count = await QueueEntry.find(
                QueueEntry.esi_level == level,
                QueueEntry.status == QueueStatus.WAITING
            ).count()
            esi_distribution[f"level_{level}"] = count

        # Calculate average wait time
        waiting_entries = await QueueEntry.find(
            QueueEntry.status == QueueStatus.WAITING
        ).to_list()

        total_wait_time = 0
        if waiting_entries:
            for entry in waiting_entries:
                wait_time = (datetime.utcnow() - entry.entered_queue).total_seconds() / 60
                total_wait_time += wait_time
            average_wait_time = total_wait_time / len(waiting_entries)
        else:
            average_wait_time = 0

        return DashboardStats(
            total_patients=total_patients,
            waiting_patients=waiting_patients,
            critical_patients=critical_patients,
            esi_distribution=esi_distribution,
            average_wait_time=round(average_wait_time, 1),
            beds_available=12,  # Mock data
            staff_on_duty=8,    # Mock data
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.post("/assess/{patient_id}")
async def reassess_patient(patient_id: str):
    """Reassess patient with AI triage"""
    try:
        # Get patient
        patient = await Patient.get(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Prepare data for AI
        ai_input_data = {
            "age": patient.age,
            "gender": patient.gender,
            "chief_complaint": patient.chief_complaint,
            "bp_systolic": patient.vitals.get("bp_systolic", 120),
            "bp_diastolic": patient.vitals.get("bp_diastolic", 80),
            "heart_rate": patient.vitals.get("heart_rate", 80),
            "temperature": patient.vitals.get("temperature", 98.6),
            "o2_saturation": patient.vitals.get("o2_saturation", 98),
            "respiratory_rate": patient.vitals.get("respiratory_rate", 16),
            "pain_scale": patient.vitals.get("pain_scale", 0),
            "consciousness_level": patient.vitals.get("consciousness_level", "Alert"),
            "bleeding": patient.bleeding,
            "breathing_difficulty": patient.breathing_difficulty,
            "trauma_indicator": patient.trauma_indicator,
            "chronic_conditions": patient.allergies,
            "allergies": patient.allergies,
            "medications_count": len(patient.current_medications),
            "previous_admissions": 0
        }

        # Get new AI assessment
        old_esi = patient.esi_level
        esi_level, confidence, reasons = ai_triage_engine.predict_esi_level(ai_input_data)
        priority_score = ai_triage_engine.calculate_priority_score(esi_level, 0, patient.age, patient.vitals.get("pain_scale", 0))

        # Update patient
        patient.esi_level = esi_level
        patient.priority_score = priority_score
        patient.ai_confidence = confidence
        patient.ai_reasoning = reasons
        patient.updated_at = datetime.utcnow()
        await patient.save()

        # Create new assessment record
        assessment = TriageAssessment(
            patient_id=patient_id,
            esi_level=esi_level,
            confidence_score=confidence,
            reasoning=reasons,
            features_analyzed=ai_input_data,
            assessor_type="ai_reassessment"
        )
        await assessment.save()

        # Update queue entry
        queue_entry = await QueueEntry.find_one(QueueEntry.patient_id == patient_id)
        if queue_entry and queue_entry.status == QueueStatus.WAITING:
            queue_entry.esi_level = esi_level
            queue_entry.priority_score = priority_score
            await queue_entry.save()

        # Create alert if condition changed significantly
        if old_esi and abs(old_esi - esi_level) >= 1:
            severity = AlertSeverity.HIGH if esi_level < old_esi else AlertSeverity.MEDIUM
            alert = Alert(
                patient_id=patient_id,
                alert_type="condition_change",
                severity=severity,
                message=f"Patient condition change: ESI {old_esi} → {esi_level}"
            )
            await alert.save()

        return {
            "patient_id": patient_id,
            "old_esi_level": old_esi,
            "new_esi_level": esi_level,
            "confidence": confidence,
            "reasoning": reasons,
            "priority_score": priority_score,
            "assessment_time": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to reassess patient: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reassess: {str(e)}")

@router.get("/ai-model/info")
async def get_ai_model_info():
    """Get AI model information"""
    try:

        # Get model performance stats
        total_assessments = await TriageAssessment.count()

        # Recent assessments confidence
        recent_assessments = await TriageAssessment.find(
            TriageAssessment.assessment_time >= datetime.utcnow() - timedelta(days=7),
            sort=[("assessment_time", -1)],
            limit=100
        ).to_list()

        avg_confidence = 0
        if recent_assessments:
            total_confidence = sum(a.confidence_score for a in recent_assessments)
            avg_confidence = total_confidence / len(recent_assessments)

        return {
            "model_name": "Emergency Triage AI Ensemble",
            "version": "1.0",
            "accuracy": 94.7,
            "algorithms": ["Random Forest", "XGBoost", "Logistic Regression"],
            "features_count": 29,
            "esi_levels": [1, 2, 3, 4, 5],
            "total_assessments": total_assessments,
            "recent_avg_confidence": round(avg_confidence * 100, 1),
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get AI model info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@router.get("/alerts")
async def get_active_alerts(limit: int = Query(20, le=50)):
    """Get active alerts"""
    try:
        alerts = await Alert.find(
            Alert.acknowledged == False,
            sort=[("created_at", -1)],
            limit=limit
        ).to_list()

        alert_responses = []
        for alert in alerts:
            patient_name = "System Alert"
            if alert.patient_id:
                patient = await Patient.get(alert.patient_id)
                if patient:
                    patient_name = patient.name or f"Patient #{patient.id}"

            alert_responses.append({
                "id": str(alert.id),
                "patient_id": alert.patient_id,
                "patient_name": patient_name,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value,
                "message": alert.message,
                "voice_announcement": alert.voice_announcement,
                "created_at": alert.created_at.isoformat(),
                "acknowledged": alert.acknowledged
            })

        return alert_responses

    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, acknowledged_by: str = "staff"):
    """Acknowledge an alert"""
    try:
        alert = await Alert.get(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        await alert.save()

        return {"message": "Alert acknowledged successfully"}

    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")

@router.get("/performance")
async def get_performance_metrics():
    """Get system performance metrics"""
    try:
        # Time periods
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)

        # Patient metrics
        patients_last_hour = await Patient.find(Patient.created_at >= last_hour).count()
        patients_last_day = await Patient.find(Patient.created_at >= last_day).count()

        # Queue metrics
        current_queue_size = await QueueEntry.find(QueueEntry.status == QueueStatus.WAITING).count()

        # AI assessments
        assessments_last_hour = await TriageAssessment.find(
            TriageAssessment.assessment_time >= last_hour
        ).count()

        # Critical alerts
        critical_alerts = await Alert.find(
            Alert.severity == AlertSeverity.CRITICAL,
            Alert.created_at >= last_day
        ).count()

        return {
            "current_queue_size": current_queue_size,
            "patients_last_hour": patients_last_hour,
            "patients_last_day": patients_last_day,
            "assessments_last_hour": assessments_last_hour,
            "critical_alerts_last_day": critical_alerts,
            "system_status": "operational",
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@router.post("/queue/{patient_id}/start-treatment")
async def start_patient_treatment(patient_id: str):
    """Mark patient as starting treatment"""
    try:
        # Update queue entry status
        queue_entry = await QueueEntry.find_one(QueueEntry.patient_id == patient_id)
        if not queue_entry:
            raise HTTPException(status_code=404, detail="Patient not found in queue")

        queue_entry.status = QueueStatus.IN_TREATMENT
        queue_entry.treatment_started = datetime.utcnow()
        await queue_entry.save()

        # Get patient for logging
        patient = await Patient.get(patient_id)
        patient_name = patient.name if patient else f"Patient {patient_id}"

        logger.info(f"Started treatment for {patient_name} (ID: {patient_id})")

        return {
            "message": f"Treatment started for {patient_name}",
            "patient_id": patient_id,
            "status": "in_treatment",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to start treatment for patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start treatment: {str(e)}")

@router.post("/queue/{patient_id}/complete-treatment")
async def complete_patient_treatment(patient_id: str):
    """Mark patient treatment as completed"""
    try:
        # Update queue entry status
        queue_entry = await QueueEntry.find_one(QueueEntry.patient_id == patient_id)
        if not queue_entry:
            raise HTTPException(status_code=404, detail="Patient not found in queue")

        queue_entry.status = QueueStatus.COMPLETED
        queue_entry.treatment_completed = datetime.utcnow()

        # Calculate treatment duration
        if queue_entry.treatment_started:
            duration = queue_entry.treatment_completed - queue_entry.treatment_started
            queue_entry.actual_treatment_time = int(duration.total_seconds() / 60)

        await queue_entry.save()

        # Get patient for logging
        patient = await Patient.get(patient_id)
        patient_name = patient.name if patient else f"Patient {patient_id}"

        logger.info(f"Completed treatment for {patient_name} (ID: {patient_id})")

        return {
            "message": f"Treatment completed for {patient_name}",
            "patient_id": patient_id,
            "status": "completed",
            "treatment_duration_minutes": queue_entry.actual_treatment_time,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to complete treatment for patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete treatment: {str(e)}")

@router.post("/queue/{patient_id}/discharge")
async def discharge_patient(patient_id: str):
    """Discharge patient and remove from queue"""
    try:
        # Update queue entry status
        queue_entry = await QueueEntry.find_one(QueueEntry.patient_id == patient_id)
        if not queue_entry:
            raise HTTPException(status_code=404, detail="Patient not found in queue")

        queue_entry.status = QueueStatus.DISCHARGED
        await queue_entry.save()

        # Get patient for logging
        patient = await Patient.get(patient_id)
        if patient:
            patient.status = "discharged"
            patient.updated_at = datetime.utcnow()
            await patient.save()

        patient_name = patient.name if patient else f"Patient {patient_id}"
        logger.info(f"Discharged patient {patient_name} (ID: {patient_id})")

        return {
            "message": f"Patient {patient_name} discharged successfully",
            "patient_id": patient_id,
            "status": "discharged",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to discharge patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to discharge patient: {str(e)}")