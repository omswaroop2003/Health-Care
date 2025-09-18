#!/usr/bin/env python3
"""
Database Inspector for Emergency Triage System
Run this to check what data is stored in the database
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime

# Connect to the database
db_path = "backend/emergency_triage.db"
conn = sqlite3.connect(db_path)

print("DATABASE INSPECTOR - EMERGENCY TRIAGE SYSTEM")
print("=" * 60)

# Show all tables
print("\nAvailable Tables:")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\n" + "=" * 60)

# Show patients data
print("\nPATIENTS DATA:")
try:
    patients_df = pd.read_sql_query("SELECT * FROM patients", conn)
    if not patients_df.empty:
        print(f"Total Patients: {len(patients_df)}")
        print("\nPatient Records:")
        for idx, row in patients_df.iterrows():
            print(f"\nPatient #{row['id']}:")
            print(f"  Age: {row['age']} | Gender: {row['gender']}")
            print(f"  Chief Complaint: {row['chief_complaint']}")
            print(f"  Vitals: BP {row['bp_systolic']}/{row['bp_diastolic']}, HR {row['heart_rate']}, O2 {row['o2_saturation']}%")
            print(f"  Pain Scale: {row['pain_scale']}/10")
            print(f"  Conscious: {row['consciousness_level']}")
            print(f"  Arrived: {row['arrival_time']}")
    else:
        print("No patients found in database")
except Exception as e:
    print(f"Error reading patients: {e}")

# Show queue data
print("\n" + "=" * 60)
print("\n📋 TRIAGE QUEUE:")
try:
    queue_df = pd.read_sql_query("""
        SELECT q.*, p.chief_complaint, p.age
        FROM queue_entries q
        JOIN patients p ON q.patient_id = p.id
        ORDER BY q.priority_score DESC
    """, conn)

    if not queue_df.empty:
        print(f"Queue Length: {len(queue_df)}")
        print("\nQueue Status:")
        for idx, row in queue_df.iterrows():
            esi_colors = {1: "🔴 CRITICAL", 2: "🟠 EMERGENT", 3: "🟡 URGENT", 4: "🟢 LESS URGENT", 5: "🔵 NON-URGENT"}
            esi_display = esi_colors.get(row['esi_level'], f"ESI {row['esi_level']}")
            print(f"  {idx+1}. Patient #{row['patient_id']} - {esi_display}")
            print(f"      Priority Score: {row['priority_score']} | Status: {row['status']}")
            print(f"      Chief Complaint: {row['chief_complaint']}")
    else:
        print("No patients in queue")
except Exception as e:
    print(f"Error reading queue: {e}")

# Show triage assessments
print("\n" + "=" * 60)
print("\n🤖 AI TRIAGE ASSESSMENTS:")
try:
    assessments_df = pd.read_sql_query("""
        SELECT t.*, p.chief_complaint
        FROM triage_assessments t
        JOIN patients p ON t.patient_id = p.id
        ORDER BY t.assessment_time DESC
    """, conn)

    if not assessments_df.empty:
        print(f"Total Assessments: {len(assessments_df)}")
        print("\nAI Assessments:")
        for idx, row in assessments_df.iterrows():
            reasons = json.loads(row['reason_codes']) if row['reason_codes'] else []
            print(f"\n🤖 Assessment #{row['id']}:")
            print(f"  Patient: #{row['patient_id']} - {row['chief_complaint']}")
            print(f"  AI Prediction: ESI Level {row['esi_level']}")
            print(f"  ML Confidence: {row['ml_confidence']:.3f}")
            print(f"  Priority Score: {row['priority_score']}")
            print(f"  AI Reasons: {', '.join(reasons)}")
            print(f"  Critical: {'Yes' if row['vital_signs_critical'] else 'No'}")
            print(f"  Time: {row['assessment_time']}")
    else:
        print("No AI assessments found")
except Exception as e:
    print(f"Error reading assessments: {e}")

# Show alerts
print("\n" + "=" * 60)
print("\n🚨 ACTIVE ALERTS:")
try:
    alerts_df = pd.read_sql_query("""
        SELECT a.*, p.chief_complaint
        FROM alerts a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.acknowledged = 0
        ORDER BY a.created_at DESC
    """, conn)

    if not alerts_df.empty:
        print(f"Active Alerts: {len(alerts_df)}")
        for idx, row in alerts_df.iterrows():
            severity_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            icon = severity_icons.get(row['severity'], "⚠️")
            print(f"\n{icon} Alert #{row['id']}:")
            print(f"  Patient: #{row['patient_id']} - {row['chief_complaint']}")
            print(f"  Type: {row['alert_type']}")
            print(f"  Severity: {row['severity']}")
            print(f"  Message: {row['message']}")
            print(f"  Created: {row['created_at']}")
    else:
        print("No active alerts")
except Exception as e:
    print(f"Error reading alerts: {e}")

conn.close()
print("\n" + "=" * 60)
print("✅ Database inspection complete!")
print("\n💡 To test with your own inputs, use the test_your_patient.py script")