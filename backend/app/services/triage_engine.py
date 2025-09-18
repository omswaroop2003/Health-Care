from typing import Dict, List, Tuple, Optional
from datetime import datetime
from ..core.config import settings

class ESITriageEngine:
    """Emergency Severity Index (ESI) Triage Algorithm Implementation"""

    def __init__(self):
        self.critical_conditions = [
            "cardiac arrest", "respiratory failure", "severe trauma",
            "unresponsive", "active seizure", "severe allergic reaction"
        ]

        self.high_risk_conditions = [
            "chest pain", "stroke symptoms", "difficulty breathing",
            "severe bleeding", "altered mental status", "severe pain"
        ]

    def assess_patient(self, patient_data: Dict) -> Tuple[int, float, List[str]]:
        """
        Perform ESI triage assessment
        Returns: (esi_level, confidence_score, reason_codes)
        """
        reasons = []

        # Level 1: Requires immediate life-saving intervention
        if self._requires_immediate_intervention(patient_data):
            reasons.append("immediate_intervention_required")
            return 1, 0.99, reasons

        # Level 2: High risk or severe pain/distress
        if self._is_high_risk(patient_data):
            reasons.append("high_risk_condition")
            return 2, 0.95, reasons

        # Check vital signs
        vital_status = self._assess_vital_signs(patient_data)
        if vital_status == "critical":
            reasons.append("critical_vital_signs")
            return 2, 0.95, reasons

        # Resource prediction for Levels 3-5
        resources_needed = self._predict_resources(patient_data)

        if resources_needed >= 2:
            reasons.append(f"requires_{resources_needed}_resources")
            return 3, 0.85, reasons
        elif resources_needed == 1:
            reasons.append("requires_1_resource")
            return 4, 0.80, reasons
        else:
            reasons.append("no_resources_needed")
            return 5, 0.75, reasons

    def _requires_immediate_intervention(self, patient_data: Dict) -> bool:
        """Check if patient needs immediate life-saving intervention"""

        # Check consciousness level
        if patient_data.get("consciousness_level") == "Unresponsive":
            return True

        # Check for critical conditions in chief complaint
        chief_complaint = patient_data.get("chief_complaint", "").lower()
        for condition in self.critical_conditions:
            if condition in chief_complaint:
                return True

        # Check critical vital signs
        vitals_critical = self._check_critical_vitals(patient_data)
        if vitals_critical:
            return True

        return False

    def _is_high_risk(self, patient_data: Dict) -> bool:
        """Check if patient has high-risk conditions"""

        # Check chief complaint for high-risk conditions
        chief_complaint = patient_data.get("chief_complaint", "").lower()
        for condition in self.high_risk_conditions:
            if condition in chief_complaint:
                return True

        # Severe pain (8-10 on scale)
        pain_scale = patient_data.get("pain_scale", 0)
        if pain_scale >= 8:
            return True

        # Check age-related risks
        age = patient_data.get("age", 0)
        if age < 3 or age > 80:
            if pain_scale >= 6 or patient_data.get("breathing_difficulty"):
                return True

        return False

    def _check_critical_vitals(self, patient_data: Dict) -> bool:
        """Check if vital signs are in critical range"""
        critical = settings.VITAL_SIGNS_CRITICAL

        bp_systolic = patient_data.get("bp_systolic", 120)
        if bp_systolic < critical["bp_systolic_low"] or bp_systolic > critical["bp_systolic_high"]:
            return True

        heart_rate = patient_data.get("heart_rate", 75)
        if heart_rate < critical["heart_rate_low"] or heart_rate > critical["heart_rate_high"]:
            return True

        o2_sat = patient_data.get("o2_saturation", 98)
        if o2_sat < critical["o2_saturation_low"]:
            return True

        respiratory_rate = patient_data.get("respiratory_rate", 16)
        if (respiratory_rate < critical["respiratory_rate_low"] or
            respiratory_rate > critical["respiratory_rate_high"]):
            return True

        temperature = patient_data.get("temperature", 37.0)
        if (temperature < critical["temperature_low"] or
            temperature > critical["temperature_high"]):
            return True

        return False

    def _assess_vital_signs(self, patient_data: Dict) -> str:
        """Assess vital signs and return status"""
        if self._check_critical_vitals(patient_data):
            return "critical"

        # Check for abnormal but not critical vitals
        abnormal_count = 0

        if patient_data.get("bp_systolic", 120) < 100 or patient_data.get("bp_systolic", 120) > 160:
            abnormal_count += 1
        if patient_data.get("heart_rate", 75) < 60 or patient_data.get("heart_rate", 75) > 100:
            abnormal_count += 1
        if patient_data.get("o2_saturation", 98) < 95:
            abnormal_count += 1

        if abnormal_count >= 2:
            return "abnormal"

        return "normal"

    def _predict_resources(self, patient_data: Dict) -> int:
        """Predict number of resources needed"""
        resources = 0

        # Check if labs might be needed
        chief_complaint = patient_data.get("chief_complaint", "").lower()
        if any(word in chief_complaint for word in ["fever", "infection", "diabetes", "kidney"]):
            resources += 1

        # Check if imaging might be needed
        if any(word in chief_complaint for word in ["fracture", "trauma", "fall", "head injury"]):
            resources += 1

        # Check if IV fluids/medications might be needed
        if patient_data.get("pain_scale", 0) >= 4:
            resources += 1

        # Check for procedures
        if any(word in chief_complaint for word in ["laceration", "wound", "suture"]):
            resources += 1

        return min(resources, 3)  # Cap at 3 for ESI purposes

    def calculate_priority_score(self, esi_level: int, wait_time: int = 0) -> float:
        """Calculate priority score for queue management"""
        esi_weights = {1: 1000, 2: 500, 3: 200, 4: 50, 5: 10}
        base_score = esi_weights.get(esi_level, 10)

        # Add wait time factor (increases priority as wait time increases)
        wait_factor = min(wait_time * 0.5, 100)

        return base_score + wait_factor