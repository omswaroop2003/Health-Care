#!/usr/bin/env python3
"""
Test model file path resolution
"""

import os

def test_model_paths():
    """Test which model path is accessible"""

    # Current directory
    print(f"Current directory: {os.getcwd()}")

    # From the backend directory perspective
    base_paths = [
        "ml_pipeline/models/triage_classifier.pkl",
        "../ml_pipeline/models/triage_classifier.pkl",
        "../../ml_pipeline/models/triage_classifier.pkl",
        os.path.join(os.path.dirname(__file__), "ml_pipeline/models/triage_classifier.pkl"),
        os.path.join(os.path.dirname(__file__), "../ml_pipeline/models/triage_classifier.pkl"),
        os.path.join(os.path.dirname(__file__), "../../ml_pipeline/models/triage_classifier.pkl")
    ]

    for path in base_paths:
        abs_path = os.path.abspath(path)
        exists = os.path.exists(path)
        print(f"Path: {path}")
        print(f"  Absolute: {abs_path}")
        print(f"  Exists: {exists}")
        if exists:
            print(f"  Size: {os.path.getsize(path)} bytes")
        print()

if __name__ == "__main__":
    test_model_paths()