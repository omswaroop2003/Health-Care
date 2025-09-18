from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TriageRequest(BaseModel):
    patient_id: int

class TriageResponse(BaseModel):
    patient_id: int
    esi_level: int = Field(ge=1, le=5)
    priority_score: float
    ml_confidence: float
    assessment_time: datetime
    reason_codes: List[str]
    recommended_actions: List[str]
    estimated_wait_time: int

    class Config:
        orm_mode = True

class TriageOverride(BaseModel):
    patient_id: int
    new_esi_level: int = Field(ge=1, le=5)
    reason: str = Field(..., min_length=1, max_length=500)
    assessed_by: str = Field(..., min_length=1, max_length=100)

class QueueStatus(BaseModel):
    patient_id: int
    patient_name: str
    esi_level: int
    queue_position: int
    wait_time_minutes: int
    estimated_remaining_wait: int
    status: str

    class Config:
        orm_mode = True

class TriageStatistics(BaseModel):
    total_patients: int
    by_esi_level: dict
    average_wait_times: dict
    critical_patients: int
    patients_seen_today: int
    average_processing_time: float