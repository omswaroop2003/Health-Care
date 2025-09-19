#!/usr/bin/env python3
"""
Final AI model performance test
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.ai_triage_simple import ai_triage_engine

def test_final_ai():
    """Test final AI model performance"""

    test_cases = [
        # Critical case
        {
            "name": "Critical Emergency",
            "age": 60,
            "chief_complaint": "cardiac arrest",
            "bp_systolic": 70,
            "bp_diastolic": 40,
            "heart_rate": 160,
            "temperature": 96.5,
            "o2_saturation": 80,
            "respiratory_rate": 35,
            "pain_scale": 10,
            "consciousness_level": "Unconscious",
            "expected": 1
        },
        # High risk
        {
            "name": "High Risk",
            "age": 55,
            "chief_complaint": "chest pain",
            "bp_systolic": 85,
            "bp_diastolic": 55,
            "heart_rate": 110,
            "o2_saturation": 90,
            "pain_scale": 8,
            "breathing_difficulty": True,
            "expected": 2
        },
        # Non-urgent
        {
            "name": "Non-urgent",
            "age": 22,
            "chief_complaint": "minor rash",
            "bp_systolic": 115,
            "bp_diastolic": 75,
            "heart_rate": 72,
            "o2_saturation": 99,
            "pain_scale": 1,
            "expected": 5
        }
    ]

    print("AI Model Final Performance Test")
    print("=" * 40)

    correct = 0
    total = len(test_cases)

    for case in test_cases:
        esi, confidence, reasoning = ai_triage_engine.predict_esi_level(case)

        print(f"\nCase: {case['name']}")
        print(f"Expected: ESI {case['expected']}")
        print(f"Predicted: ESI {esi}")
        print(f"Confidence: {confidence:.1%}")

        if esi == case['expected']:
            correct += 1
            print("Result: CORRECT")
        else:
            print("Result: INCORRECT")

    accuracy = (correct / total) * 100
    print(f"\nOverall Performance:")
    print(f"Accuracy: {correct}/{total} = {accuracy:.1f}%")

    # Check if AI model is being used (vs rule-based)
    test_patient = {
        "age": 30,
        "chief_complaint": "test",
        "bp_systolic": 120,
        "bp_diastolic": 80,
        "heart_rate": 80,
        "o2_saturation": 98,
        "pain_scale": 2
    }

    _, conf, reasoning = ai_triage_engine.predict_esi_level(test_patient)

    if any("AI ensemble" in r for r in reasoning):
        print("\nStatus: AI Model is ACTIVE")
        print(f"Model confidence: {conf:.1%}")
    else:
        print("\nStatus: Using rule-based fallback")
        print("AI model may not be loading correctly")

if __name__ == "__main__":
    test_final_ai()