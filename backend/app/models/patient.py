from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    arrival_time = Column(DateTime, default=datetime.utcnow)

    # Demographics
    age = Column(Integer)
    gender = Column(String(10))

    # Medical Information
    chief_complaint = Column(String(500))
    medical_history = Column(JSON)
    allergies = Column(JSON)
    current_medications = Column(JSON)

    # Vital Signs
    bp_systolic = Column(Integer)
    bp_diastolic = Column(Integer)
    heart_rate = Column(Integer)
    temperature = Column(Float)
    o2_saturation = Column(Integer)
    respiratory_rate = Column(Integer)

    # Symptoms
    pain_scale = Column(Integer)  # 0-10
    consciousness_level = Column(String(50))  # Alert, Voice, Pain, Unresponsive
    bleeding = Column(Boolean, default=False)
    breathing_difficulty = Column(Boolean, default=False)
    trauma_indicator = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    triage_assessments = relationship("TriageAssessment", back_populates="patient")
    queue_entry = relationship("QueueEntry", back_populates="patient", uselist=False)
    alerts = relationship("Alert", back_populates="patient")