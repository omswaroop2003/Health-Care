from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Emergency Triage System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./emergency_triage.db"

    CORS_ORIGINS: list = ["http://localhost:8501", "http://localhost:3000", "http://localhost:5173"]

    ESI_LEVELS: dict = {
        1: {"name": "Resuscitation", "color": "#FF0000", "max_wait": 0},
        2: {"name": "Emergent", "color": "#FF6600", "max_wait": 10},
        3: {"name": "Urgent", "color": "#FFCC00", "max_wait": 30},
        4: {"name": "Less Urgent", "color": "#99CC00", "max_wait": 60},
        5: {"name": "Non-Urgent", "color": "#00CC00", "max_wait": 120}
    }

    VITAL_SIGNS_CRITICAL: dict = {
        "bp_systolic_low": 90,
        "bp_systolic_high": 180,
        "heart_rate_low": 50,
        "heart_rate_high": 120,
        "o2_saturation_low": 92,
        "respiratory_rate_low": 10,
        "respiratory_rate_high": 30,
        "temperature_low": 35.0,
        "temperature_high": 39.0
    }

    ML_MODEL_PATH: str = "ml_pipeline/models/triage_classifier.pkl"
    FEATURE_PROCESSOR_PATH: str = "ml_pipeline/models/feature_processor.pkl"

    ALERT_REFRESH_SECONDS: int = 5
    QUEUE_UPDATE_SECONDS: int = 10

    class Config:
        env_file = ".env"

settings = Settings()