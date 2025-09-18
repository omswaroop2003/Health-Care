import subprocess
import os
import sys

print("="*50)
print("Emergency Triage System - Setup")
print("="*50)

# Core dependencies to install
dependencies = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "streamlit",
    "plotly",
    "scikit-learn",
    "pandas",
    "numpy",
    "pydantic",
    "python-multipart",
    "faker",
    "joblib",
    "httpx"
]

print("\nInstalling dependencies...")
for dep in dependencies:
    print(f"  Installing {dep}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--quiet"])
    except:
        print(f"  Warning: Could not install {dep}, may already be installed")

print("\nDependencies installed!")

# Create data directory
os.makedirs("data", exist_ok=True)
print("\nData directory created!")

print("\n" + "="*50)
print("Setup Complete!")
print("="*50)

print("\nTo start the system:")
print("1. Run backend: python -m uvicorn backend.app.main:app --reload")
print("2. Run frontend: streamlit run frontend/app.py")
print("\nOr use the provided batch files:")
print("   - run_backend.bat")
print("   - run_frontend.bat")