from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class TriageAssessment(Base):
    __tablename__ = "triage_assessments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    # Triage Results
    esi_level = Column(Integer)  # 1-5
    priority_score = Column(Float)
    ml_confidence = Column(Float)
    assessment_time = Column(DateTime, default=datetime.utcnow)

    # Override Information
    nurse_override = Column(Boolean, default=False)
    override_reason = Column(String(500))
    assessed_by = Column(String(100))

    # Decision Factors
    reason_codes = Column(JSON)  # List of factors that led to this decision
    vital_signs_critical = Column(Boolean, default=False)
    high_risk_condition = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="triage_assessments")


class QueueEntry(Base):
    __tablename__ = "queue_entries"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True)

    # Queue Information
    esi_level = Column(Integer)
    priority_score = Column(Float)
    queue_position = Column(Integer)
    wait_time_minutes = Column(Integer, default=0)
    estimated_treatment_time = Column(Integer)

    # Status
    status = Column(String(20))  # waiting, in_treatment, discharged
    assigned_resource = Column(String(50))  # bed number, doctor name, etc.
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="queue_entry")