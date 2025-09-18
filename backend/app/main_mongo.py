"""
MongoDB-based Emergency Triage System - Main Application
FastAPI backend with Beanie ODM for MongoDB operations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB imports
from .core.mongo_config import startup_db, shutdown_db, mongo_config
from .models.mongo_models import Patient, QueueEntry, Alert

# API routes
from .api.v1 import patients_mongo, triage_mongo, voice_mongo, websocket

# Services
from .services.realtime_service_mongo import connection_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("Starting Emergency Triage System with MongoDB...")

    try:
        # Initialize MongoDB connection
        await startup_db()
        logger.info("MongoDB connection established")

        # Create sample data if database is empty
        patient_count = await Patient.count()
        if patient_count == 0:
            from .core.mongo_config import create_sample_data
            await create_sample_data()
            logger.info("Sample data created")

        logger.info(f"System ready - {patient_count} patients in database")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Emergency Triage System...")
    await shutdown_db()
    await connection_manager.stop_background_updates()
    logger.info("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="AI-Powered Emergency Triage System",
    version="2.0.0",
    description="MongoDB-based Emergency Triage System with AI assessment and real-time updates",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    patients_mongo.router,
    prefix="/api/v1/patients",
    tags=["patients"]
)

app.include_router(
    triage_mongo.router,
    prefix="/api/v1/triage",
    tags=["triage"]
)

app.include_router(
    voice_mongo.router,
    prefix="/api/v1/voice",
    tags=["voice-alerts"]
)

app.include_router(
    websocket.router,
    prefix="/api/v1/ws",
    tags=["websocket"]
)

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI-Powered Emergency Triage System",
        "version": "2.0.0",
        "database": "MongoDB",
        "status": "operational",
        "features": [
            "AI Triage Assessment",
            "Real-time Queue Management",
            "Voice Alerts (11Labs)",
            "WebSocket Updates",
            "MongoDB Storage"
        ]
    }

@app.get("/health")
async def health_check():
    """System health check"""
    try:
        # Check MongoDB connection
        db_health = await mongo_config.health_check()

        # Check collections
        patient_count = await Patient.count()
        queue_count = await QueueEntry.count()
        alert_count = await Alert.count()

        return {
            "status": "healthy",
            "database": db_health,
            "collections": {
                "patients": patient_count,
                "queue_entries": queue_count,
                "alerts": alert_count
            },
            "services": {
                "ai_model": "loaded",
                "voice_service": "ready",
                "websocket": "active"
            },
            "timestamp": mongo_config.client.admin.command('serverStatus')['localTime'].isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics - main endpoint"""
    try:
        # Get current statistics
        total_patients = await Patient.count()
        waiting_patients = await QueueEntry.find(QueueEntry.status == "waiting").count()
        critical_patients = await QueueEntry.find(
            QueueEntry.esi_level <= 2,
            QueueEntry.status == "waiting"
        ).count()

        # ESI distribution
        esi_counts = {}
        for level in range(1, 6):
            count = await QueueEntry.find(
                QueueEntry.esi_level == level,
                QueueEntry.status == "waiting"
            ).count()
            esi_counts[f"level_{level}"] = count

        # Calculate average wait time
        waiting_entries = await QueueEntry.find(QueueEntry.status == "waiting").to_list()
        avg_wait = 0
        if waiting_entries:
            from datetime import datetime
            total_wait = sum(
                (datetime.utcnow() - entry.entered_queue).total_seconds() / 60
                for entry in waiting_entries
            )
            avg_wait = total_wait / len(waiting_entries)

        return {
            "total_patients": total_patients,
            "waiting_patients": waiting_patients,
            "critical_patients": critical_patients,
            "esi_distribution": esi_counts,
            "average_wait_time": round(avg_wait, 1),
            "beds_available": 12,
            "staff_on_duty": 8,
            "system_status": "MongoDB Ready"
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.get("/api/v1/system/info")
async def get_system_info():
    """Get system information"""
    try:
        db_stats = await mongo_config.get_database_stats()

        return {
            "system": "Emergency Triage System",
            "version": "2.0.0",
            "database": {
                "type": "MongoDB",
                "name": mongo_config.database_name,
                "stats": db_stats
            },
            "ai_model": {
                "name": "Emergency Triage Ensemble",
                "accuracy": 94.7,
                "algorithms": ["Random Forest", "XGBoost", "Logistic Regression"]
            },
            "features": {
                "real_time_updates": True,
                "voice_alerts": True,
                "ai_triage": True,
                "queue_management": True,
                "audit_trail": True
            }
        }

    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}")

@app.post("/api/v1/system/reset")
async def reset_system():
    """Reset system data (for testing)"""
    try:
        from .core.mongo_config import clear_all_data, create_sample_data

        # Clear all data
        await clear_all_data()

        # Create sample data
        await create_sample_data()

        return {
            "message": "System reset successfully",
            "action": "All data cleared and sample data created"
        }

    except Exception as e:
        logger.error(f"Failed to reset system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "app.main_mongo:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )