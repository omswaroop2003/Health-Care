#!/usr/bin/env python3
"""Simple Patient Tester"""

import requests
import json

def test_patient(patient_data, case_name):
    """Test a patient case"""
    print(f"\nTesting: {case_name}")
    print("="*40)

    url = "http://localhost:8000/api/v1/patients/"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=patient_data)
        if response.status_code == 200:
            result = response.json()

            print(f"Patient: {result['age']}yr {result['gender']}")
            print(f"Complaint: {result['chief_complaint']}")
            print(f"Vitals: BP {result['bp_systolic']}/{result['bp_diastolic']}, HR {result['heart_rate']}, O2 {result['o2_saturation']}%")
            print(f"Pain: {result['pain_scale']}/10")

            esi_names = {1: "RESUSCITATION", 2: "EMERGENT", 3: "URGENT", 4: "LESS URGENT", 5: "NON-URGENT"}
            print(f"\nAI DECISION: ESI Level {result['esi_level']} - {esi_names.get(result['esi_level'])}")
            print(f"Priority Score: {result['priority_score']}")

            return result
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None

# Test cases
print("AI TRIAGE SYSTEM - QUICK TESTS")
print("="*50)

# Critical case
critical_patient = {
    "age": 68,
    "gender": "Male",
    "chief_complaint": "severe chest pain with sweating",
    "medical_history": {},
    "allergies": [],
    "current_medications": [],
    "bp_systolic": 80,
    "bp_diastolic": 50,
    "heart_rate": 145,
    "temperature": 37.1,
    "o2_saturation": 87,
    "respiratory_rate": 32,
    "pain_scale": 10,
    "consciousness_level": "Alert",
    "bleeding": False,
    "breathing_difficulty": True,
    "trauma_indicator": False
}

test_patient(critical_patient, "Critical Heart Attack")

# Moderate case
moderate_patient = {
    "age": 35,
    "gender": "Female",
    "chief_complaint": "broken wrist from fall",
    "medical_history": {},
    "allergies": [],
    "current_medications": [],
    "bp_systolic": 125,
    "bp_diastolic": 82,
    "heart_rate": 88,
    "temperature": 36.8,
    "o2_saturation": 98,
    "respiratory_rate": 18,
    "pain_scale": 6,
    "consciousness_level": "Alert",
    "bleeding": False,
    "breathing_difficulty": False,
    "trauma_indicator": True
}

test_patient(moderate_patient, "Moderate Injury")

# Minor case
minor_patient = {
    "age": 25,
    "gender": "Male",
    "chief_complaint": "sore throat and mild headache",
    "medical_history": {},
    "allergies": [],
    "current_medications": [],
    "bp_systolic": 120,
    "bp_diastolic": 78,
    "heart_rate": 75,
    "temperature": 37.0,
    "o2_saturation": 99,
    "respiratory_rate": 16,
    "pain_scale": 2,
    "consciousness_level": "Alert",
    "bleeding": False,
    "breathing_difficulty": False,
    "trauma_indicator": False
}

test_patient(minor_patient, "Minor Illness")

print("\n" + "="*50)
print("Testing complete! Check database with:")
print("python simple_db_check.py")