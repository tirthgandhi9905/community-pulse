@echo off
echo ===================================================
echo   Community Pulse - Local Setup and Run Script
echo ===================================================
echo.

:: Check if virtual environment folder exists
if not exist venv (
    echo Creating virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error: Python is not installed or not in PATH.
        pause
        exit /b %errorlevel%
    )
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing/Updating dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo Starting Streamlit App...
echo.
streamlit run app.py

pause
