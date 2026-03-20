@echo off
echo ============================================
echo   FuzzyEnvCloud - Starting Application
echo ============================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting sensor simulator in background...
start "Sensor Simulator" python sensor_simulator.py

echo Waiting 3 seconds for simulator to start...
timeout /t 3 /nobreak > NUL

echo Starting Flask dashboard...
echo.
echo ============================================
echo   Open your browser at: http://localhost:5000
echo   Press Ctrl+C to stop
echo ============================================
echo.
python app.py
pause
