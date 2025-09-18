"""
Patient Management API Endpoints - MongoDB Version
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from ...models.mongo_models import (
    Patient,
    TriageAssessment,
    QueueEntry,
    Alert,
    PatientCreate,
    PatientResponse,
    QueueStatus
)
from ...services.ai_triage_simple import ai_triage_engine
from ...services.voice_service import voice_service
from ...services.realtime_service_mongo import connection_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=PatientResponse)
async def create_patient(patient_data: PatientCreate):
    """Create a new patient and perform AI triage assessment"""
    try:
        # Create patient document
        patient = Patient(
            name=patient_data.name,
            age=patient_data.age,
            gender=patient_data.gender,
            chief_complaint=patient_data.chief_complaint,
            symptoms=patient_data.symptoms,
            medical_history=patient_data.medical_history,
            allergies=patient_data.allergies,
            current_medications=patient_data.current_medications,
            vitals={
                "bp_systolic": patient_data.bp_systolic,
                "bp_diastolic": patient_data.bp_diastolic,
                "heart_rate": patient_data.heart_rate,
                "temperature": patient_data.temperature,
                "o2_saturation": patient_data.o2_saturation,
                "respiratory_rate": patient_data.respiratory_rate,
                "pain_scale": patient_data.pain_scale,
                "consciousness_level": patient_data.consciousness_level
            },
            bleeding=patient_data.bleeding,
            breathing_difficulty=patient_data.breathing_difficulty,
            trauma_indicator=patient_data.trauma_indicator
        )

        # Save patient to MongoDB
        await patient.save()
        logger.info(f"Created patient: {patient.id}")

        # Perform AI triage assessment

        # Prepare data for AI analysis
        ai_input_data = {
            "age": patient.age,
            "gender": patient.gender,
            "chief_complaint": patient.chief_complaint,
            "bp_systolic": patient_data.bp_systolic or 120,
            "bp_diastolic": patient_data.bp_diastolic or 80,
            "heart_rate": patient_data.heart_rate or 80,
            "temperature": patient_data.temperature or 98.6,
            "o2_saturation": patient_data.o2_saturation or 98,
            "respiratory_rate": patient_data.respiratory_rate or 16,
            "pain_scale": patient_data.pain_scale or 0,
            "consciousness_level": patient_data.consciousness_level,
            "bleeding": patient_data.bleeding,
            "breathing_difficulty": patient_data.breathing_difficulty,
            "trauma_indicator": patient_data.trauma_indicator,
            "chronic_conditions": patient_data.allergies,
            "allergies": patient_data.allergies,
            "medications_count": len(patient_data.current_medications),
            "previous_admissions": 0
        }

        # Get AI prediction
        esi_level, confidence, reasons = ai_triage_engine.predict_esi_level(ai_input_data)
        priority_score = ai_triage_engine.calculate_priority_score(esi_level, 0, patient.age, patient_data.pain_scale or 0)

        # Update patient with AI results
        patient.esi_level = esi_level
        patient.priority_score = priority_score
        patient.ai_confidence = confidence
        patient.ai_reasoning = reasons
        await patient.save()

        # Create triage assessment record
        assessment = TriageAssessment(
            patient_id=str(patient.id),
            esi_level=esi_level,
            confidence_score=confidence,
            reasoning=reasons,
            features_analyzed=ai_input_data
        )
        await assessment.save()

        # Calculate estimated treatment time
        treatment_times = {1: 0, 2: 10, 3: 30, 4: 60, 5: 120}
        estimated_time = treatment_times.get(esi_level, 60)

        # Add to queue
        queue_entry = QueueEntry(
            patient_id=str(patient.id),
            esi_level=esi_level,
            priority_score=priority_score,
            estimated_treatment_time=estimated_time
        )
        await queue_entry.save()

        # Trigger voice alert for critical patients
        if esi_level <= 2:
            try:
                await voice_service.announce_critical_patient(
                    patient_id=str(patient.id),
                    esi_level=esi_level,
                    chief_complaint=patient.chief_complaint
                )

                # Create alert record
                alert = Alert(
                    patient_id=str(patient.id),
                    alert_type="critical_patient",
                    severity="critical" if esi_level == 1 else "high",
                    message=f"Critical patient (ESI {esi_level}): {patient.chief_complaint}",
                    voice_announcement=True
                )
                await alert.save()

            except Exception as e:
                logger.error(f"Failed to create voice alert: {e}")

        # Notify WebSocket clients
        await connection_manager.notify_patient_update(
            str(patient.id),
            "new_patient",
            {
                "esi_level": esi_level,
                "priority_score": priority_score,
                "chief_complaint": patient.chief_complaint
            }
        )

        # Get queue position
        queue_position = await QueueEntry.find(
            QueueEntry.status == QueueStatus.WAITING,
            QueueEntry.priority_score >= priority_score
        ).count()

        # Prepare response
        response = PatientResponse(
            id=str(patient.id),
            name=patient.name,
            age=patient.age,
            gender=patient.gender,
            arrival_time=patient.arrival_time,
            chief_complaint=patient.chief_complaint,
            esi_level=patient.esi_level,
            priority_score=patient.priority_score,
            ai_confidence=patient.ai_confidence,
            queue_position=queue_position + 1,
            status=queue_entry.status.value
        )

        logger.info(f"Patient {patient.id} created with ESI Level {esi_level}")
        return response

    except Exception as e:
        logger.error(f"Failed to create patient: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create patient: {str(e)}")

@router.get("/", response_model=List[PatientResponse])
async def get_patients(
    limit: int = Query(50, le=100),
    skip: int = Query(0, ge=0),
    esi_level: Optional[int] = Query(None, ge=1, le=5)
):
    """Get list of patients with optional filtering"""
    try:
        # Build query
        query = {}
        if esi_level:
            query["esi_level"] = esi_level

        # Get patients
        patients = await Patient.find(
            query,
            limit=limit,
            skip=skip,
            sort=[("arrival_time", -1)]
        ).to_list()

        # Convert to response format
        patient_responses = []
        for patient in patients:
            # Get queue info
            queue_entry = await QueueEntry.find_one(
                QueueEntry.patient_id == str(patient.id),
                QueueEntry.status == QueueStatus.WAITING
            )

            queue_position = None
            status = "completed"

            if queue_entry:
                status = queue_entry.status.value
                # Calculate position in queue
                ahead_count = await QueueEntry.find(
                    QueueEntry.status == QueueStatus.WAITING,
                    QueueEntry.priority_score > queue_entry.priority_score
                ).count()
                queue_position = ahead_count + 1

            patient_responses.append(PatientResponse(
                id=str(patient.id),
                name=patient.name,
                age=patient.age,
                gender=patient.gender,
                arrival_time=patient.arrival_time,
                chief_complaint=patient.chief_complaint,
                esi_level=patient.esi_level,
                priority_score=patient.priority_score,
                ai_confidence=patient.ai_confidence,
                queue_position=queue_position,
                status=status
            ))

        return patient_responses

    except Exception as e:
        logger.error(f"Failed to get patients: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get patients: {str(e)}")

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str):
    """Get specific patient by ID"""
    try:
        patient = await Patient.get(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Get queue info
        queue_entry = await QueueEntry.find_one(
            QueueEntry.patient_id == patient_id
        )

        queue_position = None
        status = "completed"

        if queue_entry:
            status = queue_entry.status.value
            if queue_entry.status == QueueStatus.WAITING:
                ahead_count = await QueueEntry.find(
                    QueueEntry.status == QueueStatus.WAITING,
                    QueueEntry.priority_score > queue_entry.priority_score
                ).count()
                queue_position = ahead_count + 1

        return PatientResponse(
            id=str(patient.id),
            name=patient.name,
            age=patient.age,
            gender=patient.gender,
            arrival_time=patient.arrival_time,
            chief_complaint=patient.chief_complaint,
            esi_level=patient.esi_level,
            priority_score=patient.priority_score,
            ai_confidence=patient.ai_confidence,
            queue_position=queue_position,
            status=status
        )

    except Exception as e:
        logger.error(f"Failed to get patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get patient: {str(e)}")

@router.put("/{patient_id}/status")
async def update_patient_status(patient_id: str, status: QueueStatus):
    """Update patient queue status"""
    try:
        # Find queue entry
        queue_entry = await QueueEntry.find_one(QueueEntry.patient_id == patient_id)
        if not queue_entry:
            raise HTTPException(status_code=404, detail="Patient not in queue")

        # Update status
        old_status = queue_entry.status
        queue_entry.status = status

        if status == QueueStatus.IN_TREATMENT:
            queue_entry.treatment_started = datetime.utcnow()
        elif status in [QueueStatus.COMPLETED, QueueStatus.DISCHARGED]:
            queue_entry.treatment_completed = datetime.utcnow()

        await queue_entry.save()

        # Notify real-time clients
        await connection_manager.notify_queue_change(
            "status_change",
            patient_id,
            {"old_status": old_status.value, "new_status": status.value}
        )

        logger.info(f"Patient {patient_id} status updated from {old_status} to {status}")
        return {"message": "Status updated successfully"}

    except Exception as e:
        logger.error(f"Failed to update patient status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")

@router.delete("/{patient_id}")
async def delete_patient(patient_id: str):
    """Delete patient (for testing purposes)"""
    try:
        # Delete patient
        patient = await Patient.get(patient_id)
        if patient:
            await patient.delete()

        # Delete related records
        await TriageAssessment.find(TriageAssessment.patient_id == patient_id).delete()
        await QueueEntry.find(QueueEntry.patient_id == patient_id).delete()
        await Alert.find(Alert.patient_id == patient_id).delete()

        logger.info(f"Patient {patient_id} deleted")
        return {"message": "Patient deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete patient: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete patient: {str(e)}")

@router.get("/{patient_id}/history")
async def get_patient_history(patient_id: str):
    """Get patient's triage assessment history"""
    try:
        assessments = await TriageAssessment.find(
            TriageAssessment.patient_id == patient_id,
            sort=[("assessment_time", -1)]
        ).to_list()

        return {
            "patient_id": patient_id,
            "assessments": [
                {
                    "id": str(assessment.id),
                    "esi_level": assessment.esi_level,
                    "confidence": assessment.confidence_score,
                    "reasoning": assessment.reasoning,
                    "assessment_time": assessment.assessment_time,
                    "model_version": assessment.model_version
                }
                for assessment in assessments
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get patient history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")