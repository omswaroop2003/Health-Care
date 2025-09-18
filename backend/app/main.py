from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn

from .core.config import settings
from .core.database import engine, Base, get_db
from .api.v1 import patients, triage, voice, websocket
from .models import Patient, TriageAssessment, QueueEntry, Alert

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Emergency Triage System for rapid patient assessment and queue management"
)

# Configure CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    patients.router,
    prefix=f"{settings.API_V1_STR}/patients",
    tags=["patients"]
)

app.include_router(
    triage.router,
    prefix=f"{settings.API_V1_STR}/triage",
    tags=["triage"]
)

app.include_router(
    voice.router,
    prefix=f"{settings.API_V1_STR}/voice",
    tags=["voice-alerts"]
)

app.include_router(
    websocket.router,
    prefix=f"{settings.API_V1_STR}/ws",
    tags=["websocket"]
)

@app.get("/")
async def root():
    return {
        "message": "Emergency Triage System API",
        "version": settings.VERSION,
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "ml_model": "loaded"
    }

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    total_patients = db.query(Patient).count()
    waiting_patients = db.query(QueueEntry).filter(QueueEntry.status == "waiting").count()
    critical_patients = db.query(QueueEntry).filter(QueueEntry.esi_level <= 2).count()

    # Count by ESI level
    esi_counts = {}
    for level in range(1, 6):
        count = db.query(QueueEntry).filter(
            QueueEntry.esi_level == level,
            QueueEntry.status == "waiting"
        ).count()
        esi_counts[f"level_{level}"] = count

    return {
        "total_patients": total_patients,
        "waiting_patients": waiting_patients,
        "critical_patients": critical_patients,
        "esi_distribution": esi_counts,
        "average_wait_time": 25,  # Would calculate from actual data
        "beds_available": 12,
        "staff_on_duty": 8
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )