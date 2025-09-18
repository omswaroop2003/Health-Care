"""
MongoDB Models for Emergency Triage System
Using Beanie ODM for async MongoDB operations
"""

from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class ESILevel(int, Enum):
    """Emergency Severity Index Levels"""
    IMMEDIATE = 1       # Life-threatening
    EMERGENT = 2        # High risk
    URGENT = 3          # Stable but needs attention
    SEMI_URGENT = 4     # Can wait
    NON_URGENT = 5      # Routine care

class QueueStatus(str, Enum):
    """Patient queue status"""
    WAITING = "waiting"
    IN_TREATMENT = "in_treatment"
    COMPLETED = "completed"
    DISCHARGED = "discharged"

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# MongoDB Document Models

class Patient(Document):
    """Patient record with all medical data"""

    # Basic Demographics
    name: Optional[str] = None
    age: int
    gender: str
    arrival_time: datetime = Field(default_factory=datetime.utcnow)

    # Chief Complaint
    chief_complaint: str
    symptoms: List[str] = []

    # Vital Signs (embedded document)
    vitals: Dict[str, Any] = {
        "bp_systolic": None,
        "bp_diastolic": None,
        "heart_rate": None,
        "temperature": None,
        "o2_saturation": None,
        "respiratory_rate": None,
        "pain_scale": None,
        "consciousness_level": "Alert"
    }

    # Medical History (flexible structure)
    medical_history: Dict[str, Any] = {}
    allergies: List[str] = []
    current_medications: List[Dict[str, Any]] = []

    # Physical Assessment
    bleeding: bool = False
    breathing_difficulty: bool = False
    trauma_indicator: bool = False

    # AI Triage Results
    esi_level: Optional[int] = None
    priority_score: Optional[float] = None
    ai_confidence: Optional[float] = None
    ai_reasoning: List[str] = []

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Settings:
        name = "patients"
        indexes = [
            "arrival_time",
            "esi_level",
            "created_at",
            [("esi_level", 1), ("arrival_time", 1)]  # Compound index for queue sorting
        ]

class TriageAssessment(Document):
    """AI triage assessment results"""

    patient_id: str  # Reference to Patient document

    # AI Model Results
    esi_level: int
    confidence_score: float
    reasoning: List[str]
    model_version: str = "ensemble_v1.0"

    # Feature Analysis
    features_analyzed: Dict[str, Any] = {}
    risk_factors: List[str] = []

    # Assessment Details
    assessment_time: datetime = Field(default_factory=datetime.utcnow)
    assessor_type: str = "ai_model"  # Could be "ai_model" or "human_override"

    # Quality Metrics
    processing_time_ms: Optional[float] = None

    class Settings:
        name = "triage_assessments"
        indexes = ["patient_id", "assessment_time", "esi_level"]

class QueueEntry(Document):
    """Emergency department queue management"""

    patient_id: str  # Reference to Patient document

    # Queue Position
    esi_level: int
    priority_score: float
    queue_position: Optional[int] = None

    # Status Tracking
    status: QueueStatus = QueueStatus.WAITING
    wait_time_minutes: int = 0
    estimated_treatment_time: int = 60  # Default 1 hour

    # Bed Assignment
    assigned_bed: Optional[str] = None
    assigned_staff: Optional[str] = None

    # Timestamps
    entered_queue: datetime = Field(default_factory=datetime.utcnow)
    treatment_started: Optional[datetime] = None
    treatment_completed: Optional[datetime] = None

    class Settings:
        name = "queue_entries"
        indexes = [
            [("esi_level", 1), ("priority_score", -1)],  # Queue ordering
            "status",
            "entered_queue"
        ]

class Alert(Document):
    """System alerts and notifications"""

    patient_id: Optional[str] = None  # May not always be patient-specific

    # Alert Details
    alert_type: str  # "critical_patient", "queue_status", "mass_casualty", etc.
    severity: AlertSeverity
    message: str

    # Voice Alert
    voice_announcement: bool = False
    voice_message: Optional[str] = None

    # Status
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    class Settings:
        name = "alerts"
        indexes = ["created_at", "severity", "acknowledged", "patient_id"]

class VoiceAnnouncement(Document):
    """Voice announcement history and tracking"""

    patient_id: Optional[str] = None

    # Announcement Details
    announcement_type: str  # "critical_patient", "queue_status", etc.
    message_text: str
    voice_settings: Dict[str, Any] = {}

    # 11Labs Details
    voice_id: str
    audio_generated: bool = False
    audio_duration_seconds: Optional[float] = None

    # Playback Status
    played: bool = False
    played_at: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "voice_announcements"
        indexes = ["created_at", "announcement_type", "patient_id"]

# Pydantic Models for API Requests/Responses

class PatientCreate(BaseModel):
    """Request model for creating a patient"""
    name: Optional[str] = None
    age: int
    gender: str
    chief_complaint: str
    symptoms: List[str] = []
    medical_history: Dict[str, Any] = {}
    allergies: List[str] = []
    current_medications: List[Dict[str, Any]] = []

    # Vitals
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    o2_saturation: Optional[int] = None
    respiratory_rate: Optional[int] = None
    pain_scale: Optional[int] = None
    consciousness_level: str = "Alert"

    # Physical Assessment
    bleeding: bool = False
    breathing_difficulty: bool = False
    trauma_indicator: bool = False

class PatientResponse(BaseModel):
    """Response model for patient data"""
    id: str
    name: Optional[str]
    age: int
    gender: str
    arrival_time: datetime
    chief_complaint: str
    esi_level: Optional[int]
    priority_score: Optional[float]
    ai_confidence: Optional[float]
    queue_position: Optional[int]
    status: Optional[str]

class QueueItemResponse(BaseModel):
    """Response model for queue items"""
    patient_id: str
    patient_name: Optional[str]
    esi_level: int
    queue_position: int
    wait_time_minutes: int
    chief_complaint: str
    priority_score: float
    status: str
    estimated_treatment_time: int

class DashboardStats(BaseModel):
    """Dashboard statistics response"""
    total_patients: int
    waiting_patients: int
    critical_patients: int
    esi_distribution: Dict[str, int]
    average_wait_time: float
    beds_available: int
    staff_on_duty: int
    timestamp: datetime