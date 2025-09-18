from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class VitalSigns(BaseModel):
    bp_systolic: int = Field(ge=40, le=300)
    bp_diastolic: int = Field(ge=20, le=200)
    heart_rate: int = Field(ge=20, le=250)
    temperature: float = Field(ge=30.0, le=45.0)
    o2_saturation: int = Field(ge=50, le=100)
    respiratory_rate: int = Field(ge=0, le=60)

class PatientCreate(BaseModel):
    age: int = Field(ge=0, le=120)
    gender: str = Field(..., pattern="^(Male|Female|Other)$")
    chief_complaint: str = Field(..., min_length=1, max_length=500)

    # Vital Signs
    bp_systolic: int = Field(ge=40, le=300)
    bp_diastolic: int = Field(ge=20, le=200)
    heart_rate: int = Field(ge=20, le=250)
    temperature: float = Field(ge=30.0, le=45.0)
    o2_saturation: int = Field(ge=50, le=100)
    respiratory_rate: int = Field(ge=0, le=60)

    # Symptoms
    pain_scale: int = Field(ge=0, le=10)
    consciousness_level: str = Field(..., pattern="^(Alert|Voice|Pain|Unresponsive)$")
    bleeding: bool = False
    breathing_difficulty: bool = False
    trauma_indicator: bool = False

    # Medical History
    medical_history: Optional[Dict] = {}
    allergies: Optional[List[str]] = []
    current_medications: Optional[List[str]] = []

class PatientResponse(BaseModel):
    id: int
    arrival_time: datetime
    age: int
    gender: str
    chief_complaint: str

    # Vital Signs
    bp_systolic: int
    bp_diastolic: int
    heart_rate: int
    temperature: float
    o2_saturation: int
    respiratory_rate: int

    # Symptoms
    pain_scale: int
    consciousness_level: str
    bleeding: bool
    breathing_difficulty: bool
    trauma_indicator: bool

    # Triage Result (if available)
    esi_level: Optional[int] = None
    priority_score: Optional[float] = None
    queue_position: Optional[int] = None
    estimated_wait_time: Optional[int] = None

    class Config:
        orm_mode = True

class PatientUpdate(BaseModel):
    chief_complaint: Optional[str] = None
    vital_signs: Optional[VitalSigns] = None
    pain_scale: Optional[int] = Field(None, ge=0, le=10)
    consciousness_level: Optional[str] = Field(None, pattern="^(Alert|Voice|Pain|Unresponsive)$")

    class Config:
        orm_mode = True