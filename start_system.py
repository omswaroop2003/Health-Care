"""
Emergency Triage System - System Starter
This script checks dependencies and starts the appropriate version
"""

import subprocess
import sys
import os
import time

def check_imports():
    """Check if all required packages are available"""
    required_packages = {
        'fastapi': 'fastapi',
        'streamlit': 'streamlit',
        'pandas': 'pandas',
        'sklearn': 'scikit-learn',
        'plotly': 'plotly',
        'sqlalchemy': 'sqlalchemy'
    }

    missing = []
    available = []

    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            available.append(package_name)
        except ImportError:
            missing.append(package_name)

    return available, missing

def start_backend():
    """Start the FastAPI backend"""
    print("Starting FastAPI Backend Server...")
    os.chdir("backend")
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    return subprocess.Popen(cmd)

def start_frontend():
    """Start the Streamlit frontend"""
    print("Starting Streamlit Dashboard...")
    os.chdir("frontend")
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"]
    return subprocess.Popen(cmd)

def start_standalone_demo():
    """Start the standalone demo"""
    print("Starting Standalone Demo...")
    subprocess.run([sys.executable, "demo_standalone.py"])

def main():
    print("="*60)
    print("EMERGENCY TRIAGE SYSTEM - STARTUP")
    print("="*60)

    # Check dependencies
    available, missing = check_imports()

    print(f"\nChecking dependencies...")
    for pkg in available:
        print(f"  [OK] {pkg}")

    if missing:
        print(f"\nMissing packages:")
        for pkg in missing:
            print(f"  [MISSING] {pkg}")

        print(f"\nOption 1: Install missing packages")
        print(f"  pip install {' '.join(missing)}")
        print(f"\nOption 2: Run standalone demo (no dependencies required)")

        choice = input("\nWould you like to run the standalone demo? (y/n): ").lower()
        if choice in ['y', 'yes']:
            start_standalone_demo()
        else:
            print("Please install missing packages and try again.")
        return

    # All packages available
    print(f"\n[OK] All dependencies satisfied!")

    print(f"\nChoose startup option:")
    print(f"1. Full System (Backend + Frontend)")
    print(f"2. Backend Only")
    print(f"3. Frontend Only")
    print(f"4. Standalone Demo")
    print(f"0. Exit")

    choice = input("\nEnter choice (0-4): ")

    if choice == "1":
        print("\nStarting full system...")
        backend_proc = start_backend()
        time.sleep(3)  # Give backend time to start
        frontend_proc = start_frontend()

        print(f"\nSystem started!")
        print(f"Backend API: http://localhost:8000")
        print(f"Frontend Dashboard: http://localhost:8501")
        print(f"\nPress Ctrl+C to stop both services")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            backend_proc.terminate()
            frontend_proc.terminate()

    elif choice == "2":
        backend_proc = start_backend()
        print(f"\nBackend started at http://localhost:8000")
        try:
            backend_proc.wait()
        except KeyboardInterrupt:
            backend_proc.terminate()

    elif choice == "3":
        frontend_proc = start_frontend()
        print(f"\nFrontend started at http://localhost:8501")
        try:
            frontend_proc.wait()
        except KeyboardInterrupt:
            frontend_proc.terminate()

    elif choice == "4":
        start_standalone_demo()

    elif choice == "0":
        print("Goodbye!")

    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()