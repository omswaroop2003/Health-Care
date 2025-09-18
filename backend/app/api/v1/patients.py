from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json

from ...core.database import get_db
from ...models import Patient, QueueEntry
from ...schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from ...services.triage_engine import ESITriageEngine

router = APIRouter()

@router.post("/", response_model=PatientResponse)
async def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Register a new patient"""

    # Create patient record
    db_patient = Patient(
        age=patient.age,
        gender=patient.gender,
        chief_complaint=patient.chief_complaint,
        medical_history=patient.medical_history,
        allergies=json.dumps(patient.allergies),
        current_medications=json.dumps(patient.current_medications),
        bp_systolic=patient.bp_systolic,
        bp_diastolic=patient.bp_diastolic,
        heart_rate=patient.heart_rate,
        temperature=patient.temperature,
        o2_saturation=patient.o2_saturation,
        respiratory_rate=patient.respiratory_rate,
        pain_scale=patient.pain_scale,
        consciousness_level=patient.consciousness_level,
        bleeding=patient.bleeding,
        breathing_difficulty=patient.breathing_difficulty,
        trauma_indicator=patient.trauma_indicator,
        arrival_time=datetime.utcnow()
    )

    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    # Automatically perform triage assessment
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
    priority_score = triage_engine.calculate_priority_score(esi_level, 0)

    # Add to queue
    queue_entry = QueueEntry(
        patient_id=db_patient.id,
        esi_level=esi_level,
        priority_score=priority_score,
        status="waiting",
        wait_time_minutes=0
    )
    db.add(queue_entry)
    db.commit()

    # Prepare response
    response = PatientResponse(
        id=db_patient.id,
        arrival_time=db_patient.arrival_time,
        age=db_patient.age,
        gender=db_patient.gender,
        chief_complaint=db_patient.chief_complaint,
        bp_systolic=db_patient.bp_systolic,
        bp_diastolic=db_patient.bp_diastolic,
        heart_rate=db_patient.heart_rate,
        temperature=db_patient.temperature,
        o2_saturation=db_patient.o2_saturation,
        respiratory_rate=db_patient.respiratory_rate,
        pain_scale=db_patient.pain_scale,
        consciousness_level=db_patient.consciousness_level,
        bleeding=db_patient.bleeding,
        breathing_difficulty=db_patient.breathing_difficulty,
        trauma_indicator=db_patient.trauma_indicator,
        esi_level=esi_level,
        priority_score=priority_score
    )

    return response

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: int, db: Session = Depends(get_db)):
    """Get patient details"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    queue_entry = db.query(QueueEntry).filter(QueueEntry.patient_id == patient_id).first()

    response = PatientResponse(
        id=patient.id,
        arrival_time=patient.arrival_time,
        age=patient.age,
        gender=patient.gender,
        chief_complaint=patient.chief_complaint,
        bp_systolic=patient.bp_systolic,
        bp_diastolic=patient.bp_diastolic,
        heart_rate=patient.heart_rate,
        temperature=patient.temperature,
        o2_saturation=patient.o2_saturation,
        respiratory_rate=patient.respiratory_rate,
        pain_scale=patient.pain_scale,
        consciousness_level=patient.consciousness_level,
        bleeding=patient.bleeding,
        breathing_difficulty=patient.breathing_difficulty,
        trauma_indicator=patient.trauma_indicator,
        esi_level=queue_entry.esi_level if queue_entry else None,
        priority_score=queue_entry.priority_score if queue_entry else None,
        queue_position=queue_entry.queue_position if queue_entry else None,
        estimated_wait_time=queue_entry.estimated_treatment_time if queue_entry else None
    )

    return response

@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all patients"""
    patients = db.query(Patient).offset(skip).limit(limit).all()

    response = []
    for patient in patients:
        queue_entry = db.query(QueueEntry).filter(QueueEntry.patient_id == patient.id).first()

        response.append(PatientResponse(
            id=patient.id,
            arrival_time=patient.arrival_time,
            age=patient.age,
            gender=patient.gender,
            chief_complaint=patient.chief_complaint,
            bp_systolic=patient.bp_systolic,
            bp_diastolic=patient.bp_diastolic,
            heart_rate=patient.heart_rate,
            temperature=patient.temperature,
            o2_saturation=patient.o2_saturation,
            respiratory_rate=patient.respiratory_rate,
            pain_scale=patient.pain_scale,
            consciousness_level=patient.consciousness_level,
            bleeding=patient.bleeding,
            breathing_difficulty=patient.breathing_difficulty,
            trauma_indicator=patient.trauma_indicator,
            esi_level=queue_entry.esi_level if queue_entry else None,
            priority_score=queue_entry.priority_score if queue_entry else None,
            queue_position=queue_entry.queue_position if queue_entry else None,
            estimated_wait_time=queue_entry.estimated_treatment_time if queue_entry else None
        ))

    return response

@router.put("/{patient_id}/vitals")
async def update_patient_vitals(
    patient_id: int,
    vitals: dict,
    db: Session = Depends(get_db)
):
    """Update patient vital signs"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Update vital signs
    for key, value in vitals.items():
        if hasattr(patient, key):
            setattr(patient, key, value)

    patient.updated_at = datetime.utcnow()
    db.commit()

    # Re-assess triage if vital signs changed significantly
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

    new_esi_level, confidence, reasons = triage_engine.assess_patient(patient_data)

    # Update queue entry if ESI level changed
    queue_entry = db.query(QueueEntry).filter(QueueEntry.patient_id == patient_id).first()
    if queue_entry and queue_entry.esi_level != new_esi_level:
        queue_entry.esi_level = new_esi_level
        queue_entry.priority_score = triage_engine.calculate_priority_score(new_esi_level, queue_entry.wait_time_minutes)
        db.commit()

    return {"message": "Vital signs updated successfully", "new_esi_level": new_esi_level}