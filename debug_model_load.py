#!/usr/bin/env python3
"""
Debug model loading paths from the AI service perspective
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Mimic the service directory structure
service_file_path = os.path.join(os.path.dirname(__file__), 'backend', 'app', 'services', 'ai_triage_simple.py')
print(f"Service file path: {service_file_path}")
print(f"Service directory: {os.path.dirname(service_file_path)}")

# Test paths from service perspective
possible_paths = [
    "ml_pipeline/models/triage_classifier.pkl",
    "../ml_pipeline/models/triage_classifier.pkl",
    "../../ml_pipeline/models/triage_classifier.pkl",
    os.path.join(os.path.dirname(service_file_path), "../../../ml_pipeline/models/triage_classifier.pkl"),
    os.path.join(os.path.dirname(service_file_path), "../../../../ml_pipeline/models/triage_classifier.pkl"),
    os.path.abspath(os.path.join(os.path.dirname(service_file_path), "../../../ml_pipeline/models/triage_classifier.pkl"))
]

print("\nTesting paths from service perspective:")
print("=" * 50)

for i, path in enumerate(possible_paths, 1):
    abs_path = os.path.abspath(path)
    exists = os.path.exists(path)
    print(f"{i}. Path: {path}")
    print(f"   Absolute: {abs_path}")
    print(f"   Exists: {exists}")
    if exists:
        try:
            size = os.path.getsize(path)
            print(f"   Size: {size} bytes")

            # Try to read first few bytes to check if it's a valid pickle file
            with open(path, 'rb') as f:
                first_bytes = f.read(10)
                print(f"   First bytes: {first_bytes}")
        except Exception as e:
            print(f"   Error reading: {e}")
    print()

# Also check the current working directory when the service is loaded
print(f"Current working directory: {os.getcwd()}")
print(f"Direct path check: {os.path.exists('ml_pipeline/models/triage_classifier.pkl')}")

if __name__ == "__main__":
    pass