#!/usr/bin/env python3
"""
Comprehensive test of AI model performance and accuracy
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.ai_triage_simple import ai_triage_engine

def test_comprehensive_cases():
    """Test AI model with various ESI level scenarios"""

    test_cases = [
        # ESI Level 1 - Life threatening
        {
            "name": "Critical Patient",
            "age": 60,
            "chief_complaint": "cardiac arrest",
            "bp_systolic": 70,
            "bp_diastolic": 40,
            "heart_rate": 160,
            "temperature": 96.5,
            "o2_saturation": 80,
            "respiratory_rate": 35,
            "pain_scale": 10,
            "bleeding": False,
            "breathing_difficulty": True,
            "trauma_indicator": False,
            "consciousness_level": "Unconscious",
            "gender": "Male",
            "expected_esi": 1
        },

        # ESI Level 2 - High risk
        {
            "name": "High Risk Patient",
            "age": 55,
            "chief_complaint": "chest pain",
            "bp_systolic": 85,
            "bp_diastolic": 55,
            "heart_rate": 110,
            "temperature": 98.8,
            "o2_saturation": 90,
            "respiratory_rate": 24,
            "pain_scale": 8,
            "bleeding": False,
            "breathing_difficulty": True,
            "trauma_indicator": False,
            "consciousness_level": "Alert",
            "gender": "Female",
            "expected_esi": 2
        },

        # ESI Level 3 - Urgent
        {
            "name": "Urgent Patient",
            "age": 35,
            "chief_complaint": "abdominal pain",
            "bp_systolic": 140,
            "bp_diastolic": 90,
            "heart_rate": 95,
            "temperature": 99.2,
            "o2_saturation": 96,
            "respiratory_rate": 20,
            "pain_scale": 6,
            "bleeding": False,
            "breathing_difficulty": False,
            "trauma_indicator": True,
            "consciousness_level": "Alert",
            "gender": "Male",
            "expected_esi": 3
        },

        # ESI Level 4 - Less urgent
        {
            "name": "Less Urgent Patient",
            "age": 28,
            "chief_complaint": "fever and headache",
            "bp_systolic": 130,
            "bp_diastolic": 85,
            "heart_rate": 85,
            "temperature": 100.5,
            "o2_saturation": 98,
            "respiratory_rate": 18,
            "pain_scale": 4,
            "bleeding": False,
            "breathing_difficulty": False,
            "trauma_indicator": False,
            "consciousness_level": "Alert",
            "gender": "Female",
            "expected_esi": 4
        },

        # ESI Level 5 - Non-urgent
        {
            "name": "Non-urgent Patient",
            "age": 22,
            "chief_complaint": "minor rash",
            "bp_systolic": 115,
            "bp_diastolic": 75,
            "heart_rate": 72,
            "temperature": 98.6,
            "o2_saturation": 99,
            "respiratory_rate": 16,
            "pain_scale": 1,
            "bleeding": False,
            "breathing_difficulty": False,
            "trauma_indicator": False,
            "consciousness_level": "Alert",
            "gender": "Male",
            "expected_esi": 5
        }
    ]

    print("Comprehensive AI Model Testing")
    print("=" * 60)

    correct_predictions = 0
    total_predictions = len(test_cases)

    for case in test_cases:
        print(f"\nCase: {case['name']}")
        print(f"Expected ESI: {case['expected_esi']}")
        print(f"Complaint: {case['chief_complaint']}")

        # Get AI prediction
        esi_level, confidence, reasoning = ai_triage_engine.predict_esi_level(case)

        print(f"Predicted ESI: {esi_level}")
        print(f"Confidence: {confidence:.1%}")

        # Check accuracy
        is_correct = (esi_level == case['expected_esi'])
        if is_correct:
            correct_predictions += 1
            print("Result: CORRECT ✓")
        else:
            print(f"Result: INCORRECT (expected {case['expected_esi']}, got {esi_level})")

        print("AI Reasoning:")
        for reason in reasoning[:3]:  # Show first 3 reasons
            print(f"  - {reason}")

        print("-" * 40)

    # Calculate accuracy
    accuracy = (correct_predictions / total_predictions) * 100
    print(f"\nModel Performance Summary:")
    print(f"Correct predictions: {correct_predictions}/{total_predictions}")
    print(f"Accuracy: {accuracy:.1f}%")

    # Test edge cases
    print(f"\nTesting Edge Cases:")
    print("=" * 30)

    edge_cases = [
        {
            "name": "Elderly with multiple conditions",
            "age": 85,
            "chief_complaint": "fall with confusion",
            "bp_systolic": 160,
            "bp_diastolic": 95,
            "heart_rate": 55,
            "temperature": 97.0,
            "o2_saturation": 93,
            "respiratory_rate": 22,
            "pain_scale": 5,
            "bleeding": False,
            "breathing_difficulty": False,
            "trauma_indicator": True,
            "consciousness_level": "Confused",
            "gender": "Female"
        },
        {
            "name": "Pediatric emergency",
            "age": 3,
            "chief_complaint": "difficulty breathing",
            "bp_systolic": 90,
            "bp_diastolic": 55,
            "heart_rate": 140,
            "temperature": 102.5,
            "o2_saturation": 88,
            "respiratory_rate": 40,
            "pain_scale": 7,
            "bleeding": False,
            "breathing_difficulty": True,
            "trauma_indicator": False,
            "consciousness_level": "Alert",
            "gender": "Male"
        }
    ]

    for case in edge_cases:
        print(f"\nEdge Case: {case['name']} (Age: {case['age']})")
        esi_level, confidence, reasoning = ai_triage_engine.predict_esi_level(case)
        print(f"ESI Level: {esi_level}")
        print(f"Confidence: {confidence:.1%}")
        print(f"Key reasoning: {reasoning[0] if reasoning else 'No reasoning provided'}")

if __name__ == "__main__":
    test_comprehensive_cases()