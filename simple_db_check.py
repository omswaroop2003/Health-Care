#!/usr/bin/env python3
"""Simple Database Inspector"""

import sqlite3
import pandas as pd
import json

# Connect to database
conn = sqlite3.connect("backend/emergency_triage.db")

print("DATABASE INSPECTOR - EMERGENCY TRIAGE SYSTEM")
print("=" * 60)

# Show patients
print("\nPATIENTS:")
try:
    patients_df = pd.read_sql_query("SELECT * FROM patients", conn)
    print(f"Total Patients: {len(patients_df)}")
    for idx, row in patients_df.iterrows():
        print(f"\nPatient {row['id']}: {row['age']}yr {row['gender']}")
        print(f"  Complaint: {row['chief_complaint']}")
        print(f"  Vitals: BP {row['bp_systolic']}/{row['bp_diastolic']}, HR {row['heart_rate']}, O2 {row['o2_saturation']}%")
        print(f"  Pain: {row['pain_scale']}/10, Conscious: {row['consciousness_level']}")
except Exception as e:
    print(f"Error: {e}")

# Show queue
print("\n" + "=" * 40)
print("TRIAGE QUEUE:")
try:
    queue_df = pd.read_sql_query("""
        SELECT q.patient_id, q.esi_level, q.priority_score, q.status, p.chief_complaint
        FROM queue_entries q
        JOIN patients p ON q.patient_id = p.id
        ORDER BY q.priority_score DESC
    """, conn)

    print(f"Queue Size: {len(queue_df)}")
    for idx, row in queue_df.iterrows():
        esi_names = {1: "CRITICAL", 2: "EMERGENT", 3: "URGENT", 4: "LESS-URGENT", 5: "NON-URGENT"}
        esi_name = esi_names.get(row['esi_level'], f"ESI-{row['esi_level']}")
        print(f"  {idx+1}. Patient {row['patient_id']} - {esi_name} (Score: {row['priority_score']})")
        print(f"      {row['chief_complaint']}")
except Exception as e:
    print(f"Error: {e}")

# Show AI assessments
print("\n" + "=" * 40)
print("AI ASSESSMENTS:")
try:
    assess_df = pd.read_sql_query("""
        SELECT t.patient_id, t.esi_level, t.ml_confidence, t.reason_codes, p.chief_complaint
        FROM triage_assessments t
        JOIN patients p ON t.patient_id = p.id
    """, conn)

    print(f"AI Assessments: {len(assess_df)}")
    for idx, row in assess_df.iterrows():
        reasons = json.loads(row['reason_codes']) if row['reason_codes'] else []
        print(f"\nAI Assessment for Patient {row['patient_id']}:")
        print(f"  AI Prediction: ESI Level {row['esi_level']}")
        print(f"  Confidence: {row['ml_confidence']:.3f}")
        print(f"  Reasons: {', '.join(reasons[:3])}...")  # Show first 3 reasons
        print(f"  Case: {row['chief_complaint']}")
except Exception as e:
    print(f"Error: {e}")

conn.close()
print("\n" + "=" * 60)
print("Database check complete!")