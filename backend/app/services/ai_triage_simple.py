"""
Simple AI Triage Engine for MongoDB version
Lightweight version without config dependencies
"""

import os
import pickle
import joblib
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class SimpleAITriageEngine:
    """Simplified AI Triage Engine for Emergency Severity Index (ESI) prediction"""

    def __init__(self):
        self.model = None
        self.feature_processor = None

        # Simple feature names
        self.feature_names = [
            'age', 'bp_systolic', 'bp_diastolic', 'heart_rate', 'temperature',
            'o2_saturation', 'respiratory_rate', 'pain_scale',
            'bleeding', 'breathing_difficulty', 'trauma_indicator',
            'consciousness_alert', 'consciousness_confused', 'consciousness_unconscious',
            'gender_male', 'chief_complaint_chest_pain', 'chief_complaint_shortness_of_breath',
            'chief_complaint_abdominal_pain', 'medications_count'
        ]

        # Load model if available
        self._load_model()

    def _load_model(self):
        """Load AI model or use rule-based fallback"""
        try:
            # Try multiple possible paths for the model
            possible_paths = [
                "ml_pipeline/models/triage_classifier.pkl",
                "../ml_pipeline/models/triage_classifier.pkl",
                "../../ml_pipeline/models/triage_classifier.pkl",
                os.path.join(os.path.dirname(__file__), "../../../ml_pipeline/models/triage_classifier.pkl"),
                os.path.join(os.path.dirname(__file__), "../../../../ml_pipeline/models/triage_classifier.pkl"),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ml_pipeline/models/triage_classifier.pkl"))
            ]

            model_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break

            if model_path and os.path.exists(model_path):
                self.model = joblib.load(model_path)

                # Also load the scaler and feature columns
                scaler_path = model_path.replace('triage_classifier.pkl', 'feature_processor.pkl')
                features_path = model_path.replace('triage_classifier.pkl', 'triage_classifier_features.pkl')

                if os.path.exists(scaler_path):
                    self.feature_processor = joblib.load(scaler_path)

                if os.path.exists(features_path):
                    self.feature_names = joblib.load(features_path)

                logger.info(f"AI model loaded successfully from: {model_path}")
            else:
                logger.warning("AI model not found, using rule-based triage")
        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")
            self.model = None

    def predict_esi_level(self, patient_data: Dict[str, Any]) -> Tuple[int, float, List[str]]:
        """Predict ESI level for patient"""

        if self.model:
            return self._ai_prediction(patient_data)
        else:
            return self._rule_based_prediction(patient_data)

    def _ai_prediction(self, patient_data: Dict[str, Any]) -> Tuple[int, float, List[str]]:
        """AI model prediction with enhanced feature processing"""
        try:
            # Extract and process features for ML model
            features = self._extract_ml_features(patient_data)

            # Scale features if scaler is available
            if self.feature_processor is not None:
                features_scaled = self.feature_processor.transform([features])
            else:
                features_scaled = [features]

            # Make prediction
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            confidence = float(np.max(probabilities))

            # Get ensemble model insights
            reasoning = [
                f"AI ensemble model prediction with {confidence:.1%} confidence",
                f"Based on {len(features)} medical features",
                f"Prediction: ESI Level {prediction}"
            ]

            # Add specific reasoning based on individual model components
            if hasattr(self.model, 'estimators_'):
                rf_pred = self.model.estimators_[0].predict(features_scaled)[0]
                xgb_pred = self.model.estimators_[1].predict(features_scaled)[0]
                lr_pred = self.model.estimators_[2].predict(features_scaled)[0]

                reasoning.append(f"Model consensus: RF={rf_pred}, XGB={xgb_pred}, LR={lr_pred}")

            # Add confidence-based reasoning
            if confidence > 0.9:
                reasoning.append("High confidence prediction - strong clinical indicators")
            elif confidence > 0.7:
                reasoning.append("Moderate confidence - typical presentation patterns")
            else:
                reasoning.append("Lower confidence - complex case requiring medical review")

            return int(prediction), confidence, reasoning

        except Exception as e:
            logger.error(f"AI prediction failed: {e}")
            return self._rule_based_prediction(patient_data)

    def _rule_based_prediction(self, patient_data: Dict[str, Any]) -> Tuple[int, float, List[str]]:
        """Rule-based triage prediction"""

        age = patient_data.get('age', 50)
        bp_systolic = patient_data.get('bp_systolic', 120)
        heart_rate = patient_data.get('heart_rate', 80)
        o2_saturation = patient_data.get('o2_saturation', 98)
        pain_scale = patient_data.get('pain_scale', 0)
        chief_complaint = patient_data.get('chief_complaint', '').lower()
        bleeding = patient_data.get('bleeding', False)
        breathing_difficulty = patient_data.get('breathing_difficulty', False)
        trauma_indicator = patient_data.get('trauma_indicator', False)
        consciousness_level = patient_data.get('consciousness_level', 'Alert').lower()

        reasoning = []
        esi_level = 5  # Start with lowest priority

        # ESI Level 1 - Life-threatening conditions
        if (consciousness_level in ['unconscious', 'unresponsive'] or
            bp_systolic < 80 or bp_systolic > 200 or
            heart_rate > 150 or heart_rate < 40 or
            o2_saturation < 85):
            esi_level = 1
            reasoning.append("Critical vital signs indicating immediate life threat")

        # ESI Level 2 - High-risk situations
        elif (bleeding or
              'chest pain' in chief_complaint or
              'heart attack' in chief_complaint or
              'stroke' in chief_complaint or
              breathing_difficulty or
              bp_systolic < 90 or
              o2_saturation < 92 or
              pain_scale >= 8):
            esi_level = 2
            reasoning.append("High-risk condition requiring urgent care")

        # ESI Level 3 - Urgent but stable
        elif (trauma_indicator or
              pain_scale >= 6 or
              age > 65 and ('fall' in chief_complaint or 'injury' in chief_complaint) or
              bp_systolic > 160 or
              heart_rate > 100):
            esi_level = 3
            reasoning.append("Urgent condition but patient is stable")

        # ESI Level 4 - Less urgent
        elif (pain_scale >= 3 or
              'fever' in chief_complaint or
              'infection' in chief_complaint):
            esi_level = 4
            reasoning.append("Less urgent condition, can wait")

        # ESI Level 5 - Non-urgent
        else:
            esi_level = 5
            reasoning.append("Non-urgent condition, routine care")

        # Add specific reasoning
        if bleeding:
            reasoning.append("Active bleeding detected")
        if breathing_difficulty:
            reasoning.append("Respiratory distress present")
        if pain_scale >= 7:
            reasoning.append(f"Severe pain reported (level {pain_scale}/10)")

        confidence = 0.85  # Rule-based confidence

        return esi_level, confidence, reasoning

    def _extract_features(self, patient_data: Dict[str, Any]) -> List[float]:
        """Extract features for AI model"""
        features = []

        # Basic demographics and vitals
        features.append(float(patient_data.get('age', 50)))
        features.append(float(patient_data.get('bp_systolic', 120)))
        features.append(float(patient_data.get('bp_diastolic', 80)))
        features.append(float(patient_data.get('heart_rate', 80)))
        features.append(float(patient_data.get('temperature', 98.6)))
        features.append(float(patient_data.get('o2_saturation', 98)))
        features.append(float(patient_data.get('respiratory_rate', 16)))
        features.append(float(patient_data.get('pain_scale', 0)))

        # Boolean features
        features.append(1.0 if patient_data.get('bleeding', False) else 0.0)
        features.append(1.0 if patient_data.get('breathing_difficulty', False) else 0.0)
        features.append(1.0 if patient_data.get('trauma_indicator', False) else 0.0)

        # Consciousness level (one-hot encoded)
        consciousness = patient_data.get('consciousness_level', 'Alert').lower()
        features.append(1.0 if consciousness == 'alert' else 0.0)
        features.append(1.0 if consciousness == 'confused' else 0.0)
        features.append(1.0 if consciousness == 'unconscious' else 0.0)

        # Gender (one-hot encoded)
        gender = patient_data.get('gender', '').lower()
        features.append(1.0 if gender == 'male' else 0.0)

        # Chief complaint (simplified one-hot encoding)
        chief_complaint = patient_data.get('chief_complaint', '').lower()
        features.append(1.0 if 'chest pain' in chief_complaint else 0.0)
        features.append(1.0 if 'shortness of breath' in chief_complaint or 'breathing' in chief_complaint else 0.0)
        features.append(1.0 if 'abdominal pain' in chief_complaint or 'stomach' in chief_complaint else 0.0)

        # Medications count
        medications = patient_data.get('medications_count', 0)
        features.append(float(medications))

        return features

    def _extract_ml_features(self, patient_data: Dict[str, Any]) -> List[float]:
        """Extract enhanced features for ML model (matches training pipeline)"""
        features = []

        # Basic vital signs
        bp_systolic = float(patient_data.get('bp_systolic', 120))
        bp_diastolic = float(patient_data.get('bp_diastolic', 80))
        heart_rate = float(patient_data.get('heart_rate', 80))
        temperature = float(patient_data.get('temperature', 98.6))
        o2_saturation = float(patient_data.get('o2_saturation', 98))
        respiratory_rate = float(patient_data.get('respiratory_rate', 16))
        age = float(patient_data.get('age', 50))

        # Convert temperature to Celsius if needed
        if temperature > 50:  # Likely Fahrenheit
            temperature = (temperature - 32) * 5/9

        # Core vital signs
        features.extend([bp_systolic, bp_diastolic, heart_rate, temperature, o2_saturation, respiratory_rate])

        # Demographics
        features.append(age)
        features.append(1.0 if patient_data.get('gender', '').lower() == 'male' else 0.0)

        # Age groups
        features.append(1.0 if age < 2 else 0.0)  # is_infant
        features.append(1.0 if 2 <= age < 12 else 0.0)  # is_child
        features.append(1.0 if age >= 65 else 0.0)  # is_elderly

        # Symptoms
        features.append(float(patient_data.get('pain_scale', 0)))
        consciousness = patient_data.get('consciousness_level', 'Alert').lower()
        features.append(1.0 if consciousness == 'unresponsive' else 0.0)  # is_unresponsive
        features.append(1.0 if consciousness in ['voice', 'pain'] else 0.0)  # is_altered
        features.append(1.0 if patient_data.get('bleeding', False) else 0.0)
        features.append(1.0 if patient_data.get('breathing_difficulty', False) else 0.0)
        features.append(1.0 if patient_data.get('trauma_indicator', False) else 0.0)

        # Medical history
        chronic_conditions = patient_data.get('chronic_conditions', [])
        if isinstance(chronic_conditions, dict):
            chronic_conditions = list(chronic_conditions.keys())
        features.append(float(len(chronic_conditions)))

        features.append(float(patient_data.get('medications_count', 0)))

        allergies = patient_data.get('allergies', [])
        features.append(1.0 if len(allergies) > 0 else 0.0)
        features.append(float(patient_data.get('previous_admissions', 0)))

        # Calculated features
        pulse_pressure = bp_systolic - bp_diastolic
        features.append(pulse_pressure)

        shock_index = heart_rate / bp_systolic if bp_systolic > 0 else 0
        features.append(shock_index)

        # Vital signs abnormality indicators
        bp_abnormal = 1.0 if (bp_systolic < 90 or bp_systolic > 180 or bp_diastolic < 60 or bp_diastolic > 110) else 0.0
        features.append(bp_abnormal)

        hr_abnormal = 1.0 if (heart_rate < 50 or heart_rate > 120) else 0.0
        features.append(hr_abnormal)

        o2_abnormal = 1.0 if o2_saturation < 92 else 0.0
        features.append(o2_abnormal)

        temp_abnormal = 1.0 if (temperature < 35.5 or temperature > 38.5) else 0.0
        features.append(temp_abnormal)

        rr_abnormal = 1.0 if (respiratory_rate < 10 or respiratory_rate > 30) else 0.0
        features.append(rr_abnormal)

        # Total abnormality count
        vital_abnormality_count = bp_abnormal + hr_abnormal + o2_abnormal + temp_abnormal + rr_abnormal
        features.append(vital_abnormality_count)

        return features

    def calculate_priority_score(self, esi_level: int, wait_time: int, age: int, pain_level: int) -> float:
        """Calculate priority score for queue ordering"""

        # Base score from ESI level (lower ESI = higher priority)
        base_scores = {1: 100, 2: 80, 3: 60, 4: 40, 5: 20}
        priority_score = base_scores.get(esi_level, 20)

        # Adjust for wait time (longer wait = higher priority)
        priority_score += min(wait_time * 0.5, 20)

        # Adjust for age (elderly get slight priority boost)
        if age >= 65:
            priority_score += 5
        elif age <= 2:
            priority_score += 10

        # Adjust for pain level
        priority_score += pain_level * 2

        return round(priority_score, 2)

# Global instance
ai_triage_engine = SimpleAITriageEngine()