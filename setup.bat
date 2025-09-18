@echo off
echo Setting up Emergency Triage System...
echo.

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Creating data directory...
mkdir data 2>nul

echo.
echo Generating training data...
cd ml_pipeline\training
python data_generator.py

echo.
echo Training ML model...
python train_model.py

cd ..\..

echo.
echo Setup complete!
echo.
echo To start the system:
echo 1. Run 'run_backend.bat' to start the API server
echo 2. Run 'run_frontend.bat' to start the dashboard
echo.

pause