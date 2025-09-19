#!/usr/bin/env python3
"""
Test script to verify AI model integration and performance
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.ai_triage_simple import ai_triage_engine

def test_ai_model():
    """Test the AI model with sample patient data"""

    # Test patient data
    test_patients = [
        {
            "name": "Test Patient 1",
            "age": 45,
            "chief_complaint": "chest pain",
            "bp_systolic": 180,
            "bp_diastolic": 95,
            "heart_rate": 120,
            "temperature": 98.6,
            "o2_saturation": 95,
            "respiratory_rate": 22,
            "pain_scale": 8,
            "bleeding": False,
            "breathing_difficulty": True,
            "trauma_indicator": False,
            "consciousness_level": "Alert",
            "gender": "Male"
        },
        {
            "name": "Test Patient 2",
            "age": 25,
            "chief_complaint": "minor cut",
            "bp_systolic": 120,
            "bp_diastolic": 80,
            "heart_rate": 75,
            "temperature": 98.6,
            "o2_saturation": 99,
            "respiratory_rate": 16,
            "pain_scale": 2,
            "bleeding": False,
            "breathing_difficulty": False,
            "trauma_indicator": False,
            "consciousness_level": "Alert",
            "gender": "Female"
        },
        {
            "name": "Test Patient 3",
            "age": 70,
            "chief_complaint": "shortness of breath",
            "bp_systolic": 85,
            "bp_diastolic": 55,
            "heart_rate": 45,
            "temperature": 97.5,
            "o2_saturation": 88,
            "respiratory_rate": 28,
            "pain_scale": 6,
            "bleeding": False,
            "breathing_difficulty": True,
            "trauma_indicator": False,
            "consciousness_level": "Confused",
            "gender": "Male"
        }
    ]

    print("Testing AI Triage Engine")
    print("=" * 50)

    for i, patient in enumerate(test_patients, 1):
        print(f"\nPatient {i}: {patient['name']}")
        print(f"Complaint: {patient['chief_complaint']}")
        print(f"Vitals: BP {patient['bp_systolic']}/{patient['bp_diastolic']}, HR {patient['heart_rate']}, O2 {patient['o2_saturation']}%")

        # Get AI prediction
        esi_level, confidence, reasoning = ai_triage_engine.predict_esi_level(patient)

        print(f"ESI Level: {esi_level}")
        print(f"Confidence: {confidence:.1%}")
        print("Reasoning:")
        for reason in reasoning:
            print(f"  - {reason}")

        # Calculate priority score
        priority_score = ai_triage_engine.calculate_priority_score(
            esi_level, 15, patient['age'], patient['pain_scale']
        )
        print(f"Priority Score: {priority_score}")
        print("-" * 30)

if __name__ == "__main__":
    test_ai_model()