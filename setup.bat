@echo off
echo ============================================
echo   FuzzyEnvCloud - Setup Script
echo ============================================
echo.

echo [1/3] Creating virtual environment...
python -m venv venv
echo Done.
echo.

echo [2/3] Activating virtual environment...
call venv\Scripts\activate
echo Done.
echo.

echo [3/3] Installing required libraries...
pip install -r requirements.txt
echo Done.
echo.

echo ============================================
echo   Setup Complete!
echo   Now run:  run.bat
echo ============================================
pause
