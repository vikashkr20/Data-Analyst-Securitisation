@echo off
echo ============================================================
echo   Securitisation Risk Arena — Quick Launch
echo   Project Code: 483553A ^| Candidate: Manish Kumar
echo ============================================================
echo.

REM Install dependencies
echo [1/4] Installing dependencies...
pip install -r requirements.txt -q
echo     Done.

REM Generate Excel workbooks
echo [2/4] Generating Excel validation workbooks...
python generate_excel_validations.py
echo     Done.

REM Run unit tests
echo [3/4] Running unit tests...
pip install pytest pytest-cov -q
pytest tests/ -v --tb=short
echo     Done.

REM Launch Streamlit app
echo [4/4] Launching Securitisation Risk Arena...
echo     App URL: http://localhost:8501
echo     Press Ctrl+C to stop.
echo.
streamlit run simulation_app.py

pause
