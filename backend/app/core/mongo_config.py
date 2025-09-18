"""
MongoDB Configuration for Emergency Triage System
Using Beanie ODM with Motor async driver
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from ..models.mongo_models import (
    Patient,
    TriageAssessment,
    QueueEntry,
    Alert,
    VoiceAnnouncement
)

logger = logging.getLogger(__name__)

class MongoConfig:
    """MongoDB configuration and connection management"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None

        # Configuration from environment
        self.mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.database_name = os.getenv("MONGO_DATABASE", "emergency_triage")

        # Connection settings
        self.max_pool_size = int(os.getenv("MONGO_MAX_POOL_SIZE", "100"))
        self.min_pool_size = int(os.getenv("MONGO_MIN_POOL_SIZE", "10"))
        self.max_idle_time_ms = int(os.getenv("MONGO_MAX_IDLE_TIME", "30000"))

        logger.info(f"MongoDB Config - URL: {self.mongo_url}, Database: {self.database_name}")

    async def connect_to_mongo(self):
        """Initialize MongoDB connection and Beanie ODM"""
        try:
            # Create MongoDB client
            self.client = AsyncIOMotorClient(
                self.mongo_url,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                maxIdleTimeMS=self.max_idle_time_ms,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,  # 10 second connection timeout
            )

            # Get database
            self.database = self.client[self.database_name]

            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB!")

            # Initialize Beanie with document models
            await init_beanie(
                database=self.database,
                document_models=[
                    Patient,
                    TriageAssessment,
                    QueueEntry,
                    Alert,
                    VoiceAnnouncement
                ]
            )

            logger.info("Beanie ODM initialized successfully!")

            # Create additional indexes for performance
            await self._create_indexes()

            return True

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def _create_indexes(self):
        """Create additional database indexes for optimal performance"""
        try:
            # Patient indexes
            await Patient.get_motor_collection().create_index([
                ("esi_level", 1),
                ("arrival_time", 1)
            ], name="esi_arrival_idx")

            # Queue indexes
            await QueueEntry.get_motor_collection().create_index([
                ("esi_level", 1),
                ("priority_score", -1),
                ("entered_queue", 1)
            ], name="queue_priority_idx")

            # Alert indexes
            await Alert.get_motor_collection().create_index([
                ("severity", 1),
                ("acknowledged", 1),
                ("created_at", -1)
            ], name="alert_priority_idx")

            logger.info("Additional MongoDB indexes created successfully")

        except Exception as e:
            logger.warning(f"Could not create some indexes (may already exist): {e}")

    async def close_mongo_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    async def get_database_stats(self):
        """Get database statistics"""
        try:
            stats = await self.database.command("dbStats")
            return {
                "database": self.database_name,
                "collections": stats.get("collections", 0),
                "documents": stats.get("objects", 0),
                "data_size": stats.get("dataSize", 0),
                "storage_size": stats.get("storageSize", 0),
                "indexes": stats.get("indexes", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

    async def health_check(self):
        """Check MongoDB connection health"""
        try:
            # Ping the database
            await self.client.admin.command('ping')

            # Check if we can query collections
            patient_count = await Patient.count()

            return {
                "status": "healthy",
                "database": self.database_name,
                "patient_count": patient_count,
                "connection": "active"
            }

        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }

# Global MongoDB configuration instance
mongo_config = MongoConfig()

# Dependency for FastAPI endpoints
async def get_mongo_client():
    """FastAPI dependency to get MongoDB client"""
    return mongo_config.client

async def get_mongo_database():
    """FastAPI dependency to get MongoDB database"""
    return mongo_config.database

# Database connection functions for application lifecycle
async def startup_db():
    """Initialize database connection on startup"""
    await mongo_config.connect_to_mongo()

async def shutdown_db():
    """Close database connection on shutdown"""
    await mongo_config.close_mongo_connection()

# Utility functions
async def create_sample_data():
    """Create sample data for testing"""
    try:
        # Check if data already exists
        existing_patients = await Patient.count()
        if existing_patients > 0:
            logger.info(f"Sample data already exists ({existing_patients} patients)")
            return

        # Create sample patients
        sample_patients = [
            {
                "name": "John Doe",
                "age": 45,
                "gender": "Male",
                "chief_complaint": "chest pain",
                "vitals": {
                    "bp_systolic": 140,
                    "bp_diastolic": 90,
                    "heart_rate": 85,
                    "temperature": 98.6,
                    "o2_saturation": 98,
                    "respiratory_rate": 18,
                    "pain_scale": 7
                },
                "esi_level": 2,
                "priority_score": 8.5
            },
            {
                "name": "Jane Smith",
                "age": 28,
                "gender": "Female",
                "chief_complaint": "sprained ankle",
                "vitals": {
                    "bp_systolic": 120,
                    "bp_diastolic": 80,
                    "heart_rate": 72,
                    "temperature": 98.4,
                    "o2_saturation": 99,
                    "respiratory_rate": 16,
                    "pain_scale": 4
                },
                "esi_level": 4,
                "priority_score": 3.2
            }
        ]

        for patient_data in sample_patients:
            patient = Patient(**patient_data)
            await patient.save()

            # Create corresponding queue entry
            queue_entry = QueueEntry(
                patient_id=str(patient.id),
                esi_level=patient.esi_level,
                priority_score=patient.priority_score,
                estimated_treatment_time=60 if patient.esi_level <= 2 else 30
            )
            await queue_entry.save()

        logger.info(f"Created {len(sample_patients)} sample patients")

    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")

async def clear_all_data():
    """Clear all data (for testing purposes)"""
    try:
        await Patient.delete_all()
        await TriageAssessment.delete_all()
        await QueueEntry.delete_all()
        await Alert.delete_all()
        await VoiceAnnouncement.delete_all()
        logger.info("All data cleared successfully")
    except Exception as e:
        logger.error(f"Failed to clear data: {e}")