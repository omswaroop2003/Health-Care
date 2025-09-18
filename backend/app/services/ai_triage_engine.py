import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class AITriageEngine:
    """AI-Powered Triage Engine using trained ML models"""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.load_models()

    def load_models(self):
        """Load trained ML models and preprocessor"""
        try:
            # Update paths to be relative to the project root
            model_path = os.path.join(os.path.dirname(__file__), "../../../ml_pipeline/models/triage_classifier.pkl")
            scaler_path = os.path.join(os.path.dirname(__file__), "../../../ml_pipeline/models/feature_processor.pkl")
            features_path = os.path.join(os.path.dirname(__file__), "../../../ml_pipeline/models/triage_classifier_features.pkl")

            # Load the trained model
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.feature_columns = joblib.load(features_path)

            logger.info("AI Triage models loaded successfully")
            logger.info(f"Model type: {type(self.model)}")
            logger.info(f"Feature count: {len(self.feature_columns)}")

        except Exception as e:
            logger.error(f"Failed to load AI models: {e}")
            logger.warning("Falling back to rule-based triage")
            self.model = None

    def prepare_features(self, patient_data: Dict) -> pd.DataFrame:
        """Prepare patient features for ML model prediction"""
        features = pd.DataFrame(index=[0])  # Single row

        # Vital signs features
        features["bp_systolic"] = patient_data.get("bp_systolic", 120)
        features["bp_diastolic"] = patient_data.get("bp_diastolic", 80)
        features["heart_rate"] = patient_data.get("heart_rate", 75)
        features["temperature"] = patient_data.get("temperature", 37.0)
        features["o2_saturation"] = patient_data.get("o2_saturation", 98)
        features["respiratory_rate"] = patient_data.get("respiratory_rate", 16)

        # Demographics
        features["age"] = patient_data.get("age", 40)
        features["is_male"] = 1 if patient_data.get("gender") == "Male" else 0

        # Age groups
        age = features["age"].iloc[0]
        features["is_infant"] = 1 if age < 2 else 0
        features["is_child"] = 1 if 2 <= age < 12 else 0
        features["is_elderly"] = 1 if age >= 65 else 0

        # Symptoms
        features["pain_scale"] = patient_data.get("pain_scale", 0)

        consciousness = patient_data.get("consciousness_level", "Alert")
        features["is_unresponsive"] = 1 if consciousness == "Unresponsive" else 0
        features["is_altered"] = 1 if consciousness in ["Voice", "Pain"] else 0

        features["has_bleeding"] = 1 if patient_data.get("bleeding", False) else 0
        features["has_breathing_difficulty"] = 1 if patient_data.get("breathing_difficulty", False) else 0
        features["has_trauma"] = 1 if patient_data.get("trauma_indicator", False) else 0

        # Medical history (simplified for demo - would need proper parsing in production)
        features["num_chronic_conditions"] = len(patient_data.get("chronic_conditions", []))
        features["medications_count"] = patient_data.get("medications_count", 0)
        features["has_allergies"] = 1 if len(patient_data.get("allergies", [])) > 0 else 0
        features["previous_admissions"] = patient_data.get("previous_admissions", 0)

        # Calculated features
        features["pulse_pressure"] = features["bp_systolic"] - features["bp_diastolic"]
        features["shock_index"] = features["heart_rate"] / features["bp_systolic"]

        # Vital signs abnormality scores
        features["bp_abnormal"] = (
            ((features["bp_systolic"] < 90) | (features["bp_systolic"] > 180)) |
            ((features["bp_diastolic"] < 60) | (features["bp_diastolic"] > 110))
        ).astype(int)

        features["hr_abnormal"] = (
            (features["heart_rate"] < 50) | (features["heart_rate"] > 120)
        ).astype(int)

        features["o2_abnormal"] = (features["o2_saturation"] < 92).astype(int)

        features["temp_abnormal"] = (
            (features["temperature"] < 35.5) | (features["temperature"] > 38.5)
        ).astype(int)

        features["rr_abnormal"] = (
            (features["respiratory_rate"] < 10) | (features["respiratory_rate"] > 30)
        ).astype(int)

        # Total abnormality score
        features["vital_abnormality_count"] = (
            features["bp_abnormal"] + features["hr_abnormal"] +
            features["o2_abnormal"] + features["temp_abnormal"] +
            features["rr_abnormal"]
        )

        # Ensure all expected features are present
        for col in self.feature_columns:
            if col not in features.columns:
                features[col] = 0

        # Return features in the same order as training
        return features[self.feature_columns]

    def predict_esi_level(self, patient_data: Dict) -> Tuple[int, float, List[str]]:
        """Predict ESI level using AI model"""

        if self.model is None:
            return self._fallback_rule_based(patient_data)

        try:
            # Prepare features
            features = self.prepare_features(patient_data)

            # Scale features
            features_scaled = self.scaler.transform(features)

            # Make prediction
            prediction = self.model.predict(features_scaled)[0]
            prediction_proba = self.model.predict_proba(features_scaled)[0]

            # Get confidence (probability of predicted class)
            confidence = float(prediction_proba[prediction - 1])  # ESI levels are 1-5, array indices are 0-4

            # Generate reasoning based on feature importance and patient data
            reasons = self._generate_reasoning(patient_data, features, prediction)

            logger.info(f"AI prediction: ESI Level {prediction}, Confidence: {confidence:.3f}")

            return int(prediction), confidence, reasons

        except Exception as e:
            logger.error(f"AI prediction failed: {e}")
            return self._fallback_rule_based(patient_data)

    def _generate_reasoning(self, patient_data: Dict, features: pd.DataFrame, prediction: int) -> List[str]:
        """Generate human-readable reasoning for the prediction"""
        reasons = []

        # Check critical vital signs
        if features["vital_abnormality_count"].iloc[0] >= 3:
            reasons.append("multiple_abnormal_vitals")
        elif features["vital_abnormality_count"].iloc[0] >= 1:
            reasons.append("abnormal_vitals_detected")

        # Check pain level
        pain = features["pain_scale"].iloc[0]
        if pain >= 8:
            reasons.append("severe_pain_reported")
        elif pain >= 5:
            reasons.append("moderate_pain_reported")

        # Check consciousness
        if features["is_unresponsive"].iloc[0]:
            reasons.append("patient_unresponsive")
        elif features["is_altered"].iloc[0]:
            reasons.append("altered_consciousness")

        # Check age-related factors
        if features["is_infant"].iloc[0] or features["is_elderly"].iloc[0]:
            reasons.append("age_risk_factor")

        # Check specific symptoms
        if features["has_bleeding"].iloc[0]:
            reasons.append("active_bleeding")
        if features["has_breathing_difficulty"].iloc[0]:
            reasons.append("respiratory_distress")
        if features["has_trauma"].iloc[0]:
            reasons.append("trauma_indicator")

        # Add AI-specific reason
        reasons.append(f"ai_model_prediction_level_{prediction}")

        # If no specific reasons found, add general ones
        if not reasons:
            if prediction <= 2:
                reasons.append("ai_detected_high_acuity")
            elif prediction == 3:
                reasons.append("ai_detected_urgent_care_needed")
            else:
                reasons.append("ai_detected_stable_condition")

        return reasons

    def _fallback_rule_based(self, patient_data: Dict) -> Tuple[int, float, List[str]]:
        """Fallback to rule-based triage if AI model fails"""
        logger.info("Using rule-based fallback triage")

        reasons = ["rule_based_fallback"]

        # Level 1: Immediate intervention needed
        if (patient_data.get("consciousness_level") == "Unresponsive" or
            patient_data.get("o2_saturation", 98) < 85 or
            patient_data.get("bp_systolic", 120) < 80 or
            patient_data.get("respiratory_rate", 16) < 8):
            return 1, 0.9, reasons + ["critical_condition_detected"]

        # Level 2: High risk
        if (patient_data.get("pain_scale", 0) >= 8 or
            patient_data.get("o2_saturation", 98) < 92 or
            patient_data.get("breathing_difficulty", False) or
            patient_data.get("chest_pain", False)):
            return 2, 0.8, reasons + ["high_risk_condition"]

        # Level 3: Urgent
        if (patient_data.get("pain_scale", 0) >= 5 or
            patient_data.get("temperature", 37.0) > 38.5 or
            patient_data.get("bleeding", False)):
            return 3, 0.7, reasons + ["urgent_care_needed"]

        # Level 4: Less urgent
        if patient_data.get("pain_scale", 0) >= 2:
            return 4, 0.6, reasons + ["less_urgent_care"]

        # Level 5: Non-urgent
        return 5, 0.5, reasons + ["non_urgent_care"]

    def calculate_priority_score(self, esi_level: int, wait_time: int = 0,
                                age: int = 40, comorbidities: int = 0) -> float:
        """Enhanced priority score calculation using AI insights"""

        # Base ESI weights
        esi_weights = {1: 1000, 2: 500, 3: 200, 4: 50, 5: 10}
        base_score = esi_weights.get(esi_level, 10)

        # Wait time factor (increases priority as wait time increases)
        wait_factor = min(wait_time * 0.5, 100)

        # Age factor (elderly and pediatric get higher priority)
        age_factor = 0
        if age < 5 or age > 75:
            age_factor = 20
        elif age < 12 or age > 65:
            age_factor = 10

        # Comorbidity factor
        comorbidity_factor = min(comorbidities * 5, 25)

        total_score = base_score + wait_factor + age_factor + comorbidity_factor

        return total_score

    def get_model_info(self) -> Dict:
        """Get information about the loaded AI model"""
        if self.model is None:
            return {"status": "not_loaded", "fallback": "rule_based"}

        return {
            "status": "loaded",
            "model_type": str(type(self.model)),
            "feature_count": len(self.feature_columns),
            "features": self.feature_columns[:10]  # First 10 features for brevity
        }