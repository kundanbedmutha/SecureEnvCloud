# FuzzyEnvCloud
### A Serverless-Style, Fuzzy Mamdani IoT Environmental Monitoring System
**Semester Project — Local Simulation Version**

---

## What This Project Does

Simulates a cloud-based IoT environmental monitoring system entirely on your
local machine. A Python script acts as an IoT sensor, sending temperature,
humidity, and AQI readings every 5 seconds. A Mamdani Fuzzy Inference System
scores each reading (0–100) and classifies it as Safe / Advisory / Warning /
Emergency. A live Flask web dashboard shows everything in real time.

---

## Project Structure

```
FuzzyEnvCloud/
├── setup.bat              ← Run this FIRST (creates venv + installs libraries)
├── run.bat                ← Run this to START the project
├── requirements.txt       ← Python library list
│
├── database.py            ← SQLite database (simulates AWS DynamoDB)
├── fuzzy_engine.py        ← Mamdani Fuzzy Inference System (core AI)
├── sensor_simulator.py    ← IoT sensor simulation (sends data every 5s)
├── app.py                 ← Flask web dashboard server
│
└── templates/
    └── index.html         ← Live dashboard webpage
```

---

## HOW TO RUN (Step by Step)

### Step 1 — First Time Setup
Double-click `setup.bat`
This will:
- Create a Python virtual environment (venv)
- Install all required libraries (flask, scikit-fuzzy, numpy, plotly)
Wait for it to finish. You will see "Setup Complete!"

### Step 2 — Run the Project
Double-click `run.bat`
This will:
- Activate the virtual environment
- Start the sensor simulator in the background
- Start the Flask dashboard

### Step 3 — Open the Dashboard
Open your browser and go to:
    http://localhost:5000

You will see the live dashboard updating every 5 seconds!

### Step 4 — Stop the Project
Close the two black command prompt windows that opened.

---

## What You Will See on the Dashboard

- Live temperature, humidity, and AQI graphs
- Fuzzy Risk Score gauge (0–100) updating in real time
- Color-coded risk badge: Safe (green) / Advisory (yellow) / Warning (orange) / Emergency (red)
- Alerts log table showing all Warning and Emergency events
- Membership function reference table

---

## The Fuzzy Mamdani System Explained

### Inputs
| Variable    | Range    | Linguistic Values                          |
|-------------|----------|--------------------------------------------|
| Temperature | 0–50°C   | Low, Moderate, High, Hazardous             |
| Humidity    | 0–100%   | Low, Moderate, High                        |
| AQI         | 0–300    | Good, Moderate, Unhealthy, Hazardous       |

### Output
| Variable    | Range   | Linguistic Values                           |
|-------------|---------|---------------------------------------------|
| Risk Score  | 0–100   | Safe, Advisory, Warning, Emergency          |

### Alert Levels
| Score  | Label     | Color  |
|--------|-----------|--------|
| 0–30   | Safe      | Green  |
| 31–55  | Advisory  | Yellow |
| 56–75  | Warning   | Orange |
| 76–100 | Emergency | Red    |

---

## For Your Research Paper

You can truthfully write:
- "The system implements a Mamdani Fuzzy Inference System with 15 IF-THEN rules"
- "Sensor data is stored in a structured database (simulating AWS DynamoDB)"
- "The system generates graduated alerts at four risk levels"
- "A real-time web dashboard visualizes sensor readings and fuzzy risk scores"
- "The architecture is designed to be cloud-deployable on AWS Lambda + DynamoDB"

---

## Troubleshooting

**setup.bat fails?**
Make sure Python is installed and "Add Python to PATH" was ticked during install.
Open CMD and run: python --version

**Dashboard shows no data?**
Make sure sensor_simulator is running (there should be a CMD window showing readings).
Wait 10 seconds and refresh the browser.

**Port 5000 in use?**
Open app.py and change port=5000 to port=5001, then go to http://localhost:5001
