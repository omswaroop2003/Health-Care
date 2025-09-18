@echo off
echo Starting Emergency Triage System Frontend...
echo.

cd frontend
streamlit run app.py --server.port 8501

pause