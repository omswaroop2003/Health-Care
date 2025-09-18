#!/usr/bin/env python3
"""
Test Your Patient - Interactive AI Triage Testing
Use this to test the AI system with your own patient data
"""

import requests
import json
import sys

def create_test_patient(patient_data):
    """Send patient data to AI triage system"""
    url = "http://localhost:8000/api/v1/patients/"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=patient_data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend server!")
        print("Make sure the backend is running on http://localhost:8000")
        return None

def get_ai_model_info():
    """Get AI model information"""
    url = "http://localhost:8000/api/v1/triage/ai-model/info"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def print_result(result):
    """Print the AI triage result"""
    if not result:
        return

    print("\n" + "="*50)
    print("AI TRIAGE RESULT")
    print("="*50)
    print(f"Patient ID: {result['id']}")
    print(f"Age: {result['age']} years old")
    print(f"Gender: {result['gender']}")
    print(f"Chief Complaint: {result['chief_complaint']}")
    print(f"\nVital Signs:")
    print(f"  Blood Pressure: {result['bp_systolic']}/{result['bp_diastolic']} mmHg")
    print(f"  Heart Rate: {result['heart_rate']} bpm")
    print(f"  Temperature: {result['temperature']}°C")
    print(f"  O2 Saturation: {result['o2_saturation']}%")
    print(f"  Respiratory Rate: {result['respiratory_rate']} breaths/min")
    print(f"  Pain Scale: {result['pain_scale']}/10")

    esi_names = {1: "RESUSCITATION", 2: "EMERGENT", 3: "URGENT", 4: "LESS URGENT", 5: "NON-URGENT"}
    esi_colors = {1: "🔴 CRITICAL", 2: "🟠 HIGH", 3: "🟡 MEDIUM", 4: "🟢 LOW", 5: "🔵 MINIMAL"}

    print(f"\n🤖 AI TRIAGE DECISION:")
    print(f"  ESI Level: {result['esi_level']} - {esi_names.get(result['esi_level'], 'UNKNOWN')}")
    print(f"  Priority Score: {result['priority_score']}")
    print(f"  Arrival Time: {result['arrival_time']}")

    print("\n" + "="*50)

# Pre-defined test cases
test_cases = {
    "1": {
        "name": "Critical Heart Attack",
        "data": {
            "age": 68,
            "gender": "Male",
            "chief_complaint": "severe chest pain with sweating and nausea",
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
    },
    "2": {
        "name": "Pediatric Emergency",
        "data": {
            "age": 3,
            "gender": "Female",
            "chief_complaint": "severe allergic reaction with difficulty breathing",
            "medical_history": {},
            "allergies": ["peanuts"],
            "current_medications": [],
            "bp_systolic": 70,
            "bp_diastolic": 45,
            "heart_rate": 160,
            "temperature": 37.8,
            "o2_saturation": 85,
            "respiratory_rate": 40,
            "pain_scale": 8,
            "consciousness_level": "Voice",
            "bleeding": False,
            "breathing_difficulty": True,
            "trauma_indicator": False
        }
    },
    "3": {
        "name": "Moderate Injury",
        "data": {
            "age": 35,
            "gender": "Male",
            "chief_complaint": "broken arm from fall",
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
    },
    "4": {
        "name": "Minor Cold",
        "data": {
            "age": 28,
            "gender": "Female",
            "chief_complaint": "sore throat and runny nose for 3 days",
            "medical_history": {},
            "allergies": [],
            "current_medications": [],
            "bp_systolic": 118,
            "bp_diastolic": 76,
            "heart_rate": 72,
            "temperature": 37.2,
            "o2_saturation": 99,
            "respiratory_rate": 16,
            "pain_scale": 2,
            "consciousness_level": "Alert",
            "bleeding": False,
            "breathing_difficulty": False,
            "trauma_indicator": False
        }
    }
}

def main():
    print("AI TRIAGE SYSTEM - PATIENT TESTER")
    print("="*50)

    # Check AI model status
    model_info = get_ai_model_info()
    if model_info:
        print(f"✅ AI Model Status: {model_info['status']}")
        print(f"🤖 Model Type: {model_info['model_type']}")
        print(f"📊 Features: {model_info['feature_count']}")
    else:
        print("❌ Cannot connect to AI model")
        return

    while True:
        print("\n" + "="*50)
        print("Choose a test option:")
        print("1. Critical Heart Attack (ESI 1-2 expected)")
        print("2. Pediatric Emergency (ESI 1-2 expected)")
        print("3. Moderate Injury (ESI 3-4 expected)")
        print("4. Minor Cold (ESI 4-5 expected)")
        print("5. Custom Patient (enter your own data)")
        print("6. Check Database")
        print("0. Exit")

        choice = input("\nEnter your choice (0-6): ").strip()

        if choice == "0":
            print("Goodbye!")
            break
        elif choice == "6":
            import subprocess
            subprocess.run([sys.executable, "simple_db_check.py"])
            continue
        elif choice == "5":
            print("\n📝 Enter custom patient data:")
            try:
                custom_patient = {
                    "age": int(input("Age: ")),
                    "gender": input("Gender (Male/Female): "),
                    "chief_complaint": input("Chief complaint: "),
                    "medical_history": {},
                    "allergies": [],
                    "current_medications": [],
                    "bp_systolic": int(input("Blood pressure systolic: ")),
                    "bp_diastolic": int(input("Blood pressure diastolic: ")),
                    "heart_rate": int(input("Heart rate: ")),
                    "temperature": float(input("Temperature (°C): ")),
                    "o2_saturation": int(input("Oxygen saturation (%): ")),
                    "respiratory_rate": int(input("Respiratory rate: ")),
                    "pain_scale": int(input("Pain scale (0-10): ")),
                    "consciousness_level": input("Consciousness (Alert/Voice/Pain/Unresponsive): "),
                    "bleeding": input("Bleeding? (y/n): ").lower().startswith('y'),
                    "breathing_difficulty": input("Breathing difficulty? (y/n): ").lower().startswith('y'),
                    "trauma_indicator": input("Trauma? (y/n): ").lower().startswith('y')
                }

                print(f"\n🔄 Testing custom patient...")
                result = create_test_patient(custom_patient)
                print_result(result)

            except (ValueError, KeyboardInterrupt):
                print("Invalid input or cancelled.")
                continue
        elif choice in test_cases:
            case = test_cases[choice]
            print(f"\n🔄 Testing: {case['name']}")
            result = create_test_patient(case['data'])
            print_result(result)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()