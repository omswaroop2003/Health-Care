# Emergency Triage System - Database Setup Guide

## Current Status
✅ **SQLite Working**: Basic functionality with AI predictions
❌ **Production Database**: Need PostgreSQL/MySQL for real deployment
❌ **Authentication**: No database credentials/security
❌ **Real-time Data**: No live updates or persistence

## Production Database Requirements

### 1. PostgreSQL Setup
```bash
# Install PostgreSQL (Windows)
# Download from: https://www.postgresql.org/download/windows/

# Or use Docker
docker run --name emergency-triage-db \
  -e POSTGRES_DB=emergency_triage \
  -e POSTGRES_USER=triage_admin \
  -e POSTGRES_PASSWORD=your_secure_password \
  -p 5432:5432 \
  -d postgres:15
```

### 2. Database Schema Enhancement
```sql
-- Enhanced Patient Records with Medical History
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    patient_mrn VARCHAR(20) UNIQUE NOT NULL,  -- Medical Record Number
    arrival_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Demographics
    age INTEGER NOT NULL,
    gender VARCHAR(10) NOT NULL,
    date_of_birth DATE,

    -- Contact Information (HIPAA Compliant)
    phone_hash VARCHAR(64),  -- Hashed for privacy
    emergency_contact_hash VARCHAR(64),

    -- Medical Information
    chief_complaint TEXT NOT NULL,
    medical_history JSONB,
    allergies JSONB,
    current_medications JSONB,

    -- Vital Signs
    bp_systolic INTEGER,
    bp_diastolic INTEGER,
    heart_rate INTEGER,
    temperature DECIMAL(4,2),
    o2_saturation INTEGER,
    respiratory_rate INTEGER,

    -- Symptoms
    pain_scale INTEGER CHECK (pain_scale >= 0 AND pain_scale <= 10),
    consciousness_level VARCHAR(50),
    bleeding BOOLEAN DEFAULT FALSE,
    breathing_difficulty BOOLEAN DEFAULT FALSE,
    trauma_indicator BOOLEAN DEFAULT FALSE,

    -- Audit Fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),  -- Staff ID
    updated_by VARCHAR(100)
);

-- AI Triage Assessments with Audit Trail
CREATE TABLE triage_assessments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),

    -- AI Results
    esi_level INTEGER NOT NULL CHECK (esi_level >= 1 AND esi_level <= 5),
    priority_score DECIMAL(10,2),
    ml_confidence DECIMAL(5,4),
    model_version VARCHAR(20),
    assessment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Decision Factors
    reason_codes JSONB,
    vital_signs_critical BOOLEAN DEFAULT FALSE,
    high_risk_condition BOOLEAN DEFAULT FALSE,

    -- Human Override
    nurse_override BOOLEAN DEFAULT FALSE,
    override_reason TEXT,
    assessed_by VARCHAR(100),

    -- Audit Trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Enhanced Queue Management
CREATE TABLE queue_entries (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) UNIQUE,

    -- Queue Information
    esi_level INTEGER NOT NULL,
    priority_score DECIMAL(10,2),
    queue_position INTEGER,
    wait_time_minutes INTEGER DEFAULT 0,
    estimated_treatment_time INTEGER,

    -- Status Tracking
    status VARCHAR(20) DEFAULT 'waiting',
    assigned_resource VARCHAR(50),
    bed_number VARCHAR(10),
    assigned_nurse VARCHAR(100),
    assigned_doctor VARCHAR(100),

    -- Timestamps
    queue_entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    treatment_start_time TIMESTAMP,
    discharge_time TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medical Alerts System
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),

    -- Alert Information
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    alert_data JSONB,

    -- Status
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Staff Activity Logs
CREATE TABLE staff_activities (
    id SERIAL PRIMARY KEY,
    staff_id VARCHAR(100) NOT NULL,
    patient_id INTEGER REFERENCES patients(id),

    -- Activity Details
    activity_type VARCHAR(50) NOT NULL,
    description TEXT,
    activity_data JSONB,

    -- Audit
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    session_id VARCHAR(100)
);

-- Real-time Monitoring
CREATE TABLE patient_monitoring (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),

    -- Live Vital Signs
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vital_signs JSONB NOT NULL,
    device_id VARCHAR(50),

    -- Alerts
    threshold_alerts JSONB,
    deterioration_score DECIMAL(5,2)
);
```

### 3. Database Connection Configuration
```python
# config/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

class DatabaseConfig:
    # Production Database
    POSTGRES_HOST = os.getenv("DB_HOST", "localhost")
    POSTGRES_PORT = os.getenv("DB_PORT", "5432")
    POSTGRES_DB = os.getenv("DB_NAME", "emergency_triage")
    POSTGRES_USER = os.getenv("DB_USER", "triage_admin")
    POSTGRES_PASSWORD = os.getenv("DB_PASSWORD")

    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

    # Connection Pool Settings
    POOL_SIZE = 20
    MAX_OVERFLOW = 30
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600
```

### 4. Security Features Needed
- [ ] Database encryption at rest
- [ ] SSL/TLS connections
- [ ] Row-level security for HIPAA compliance
- [ ] Audit logging for all medical data access
- [ ] Backup and disaster recovery
- [ ] Real-time replication for high availability

### 5. Integration Points
- [ ] Hospital EHR system integration
- [ ] Medical device data ingestion
- [ ] Real-time monitoring systems
- [ ] Staff authentication (LDAP/Active Directory)
- [ ] HIPAA compliance logging

## Next Steps for Implementation
1. Set up PostgreSQL instance (local or cloud)
2. Create production database schemas
3. Add connection pooling and authentication
4. Implement real-time data sync
5. Add 11Labs voice integration
6. Set up WebSocket real-time updates

## Voice Integration (11Labs API)
```python
# services/voice_service.py
import requests
from eleven_labs import ElevenLabs

class VoiceAlertService:
    def __init__(self, api_key: str):
        self.client = ElevenLabs(api_key=api_key)

    async def announce_critical_patient(self, patient_id: int, esi_level: int):
        message = f"Critical patient alert. Patient {patient_id} requires immediate attention. ESI Level {esi_level}."
        # Generate and play voice announcement

    async def queue_status_announcement(self, waiting_count: int, critical_count: int):
        message = f"Queue update: {waiting_count} patients waiting, {critical_count} critical patients."
        # Generate and play announcement
```

This setup will provide the production-ready database and real-time features you need for the medical triage system.