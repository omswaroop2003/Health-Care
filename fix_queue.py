#!/usr/bin/env python3
"""Fix queue entries with null estimated_treatment_time"""

import sqlite3

# Connect to database
conn = sqlite3.connect("backend/emergency_triage.db")
cursor = conn.cursor()

# Update existing queue entries with null estimated_treatment_time
print("Fixing queue entries...")

# Set estimated treatment time based on ESI level
cursor.execute("""
UPDATE queue_entries
SET estimated_treatment_time = CASE
    WHEN esi_level = 1 THEN 0
    WHEN esi_level = 2 THEN 10
    WHEN esi_level = 3 THEN 30
    WHEN esi_level = 4 THEN 60
    WHEN esi_level = 5 THEN 120
    ELSE 60
END
WHERE estimated_treatment_time IS NULL
""")

affected = cursor.rowcount
conn.commit()
conn.close()

print(f"Updated {affected} queue entries")
print("Queue fixed!")