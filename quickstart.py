"""
Quick Start Script for Emergency Triage System
Run this to quickly test if the system is working
"""

import os
import sys

print("="*60)
print("EMERGENCY TRIAGE SYSTEM - QUICK START")
print("="*60)

# Check if core packages are installed
packages_to_check = ["fastapi", "streamlit", "pandas", "sklearn"]
missing_packages = []

for package in packages_to_check:
    try:
        __import__(package)
        print(f"[OK] {package} is installed")
    except ImportError:
        print(f"[MISSING] {package} is not installed")
        missing_packages.append(package)

if missing_packages:
    print("\n" + "="*60)
    print("INSTALLATION REQUIRED")
    print("="*60)
    print(f"\nPlease install missing packages:")
    print(f"pip install {' '.join(missing_packages)}")
    print("\nOr run: python setup.py")
else:
    print("\n" + "="*60)
    print("ALL DEPENDENCIES INSTALLED!")
    print("="*60)

    print("\nTo start the Emergency Triage System:")
    print("\n1. BACKEND SERVER:")
    print("   Open a terminal and run:")
    print("   cd backend")
    print("   python -m uvicorn app.main:app --reload")

    print("\n2. FRONTEND DASHBOARD:")
    print("   Open another terminal and run:")
    print("   cd frontend")
    print("   streamlit run app.py")

    print("\n3. ACCESS THE SYSTEM:")
    print("   Open your browser to: http://localhost:8501")

    print("\n" + "="*60)
    print("DEMO SCENARIOS AVAILABLE:")
    print("="*60)
    print("1. Mass Casualty Event - 50 patients")
    print("2. Pediatric Emergency - Critical response")
    print("3. Overcrowded ER - Optimization demo")

print("\n" + "="*60)