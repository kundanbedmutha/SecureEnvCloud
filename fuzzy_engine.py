"""
fuzzy_engine.py
---------------
Implements the Mamdani Fuzzy Inference System (FIS).

This is the core academic contribution of the project.

Inputs  : temperature (°C), humidity (%), aqi (0–300)
Output  : risk_score  (0–100)  →  risk_label (Safe / Advisory / Warning / Emergency)

How Mamdani FIS works:
  Step 1 - Fuzzification   : convert crisp sensor values to membership degrees
  Step 2 - Rule Evaluation : fire IF-THEN rules, compute weighted outputs
  Step 3 - Defuzzification : centroid method → single crisp risk score
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


def build_fuzzy_system():
    """
    Build and return the Mamdani fuzzy control system.
    Called once at startup — reused for every sensor reading.
    """

    # ── Universe of discourse (input ranges) ──────────────────
    temperature_range = np.arange(0,   51,  1)   # 0°C to 50°C
    humidity_range    = np.arange(0,  101,  1)   # 0% to 100%
    aqi_range         = np.arange(0,  301,  1)   # AQI 0 to 300
    risk_range        = np.arange(0,  101,  1)   # Risk Score 0 to 100

    # ── Fuzzy variables ────────────────────────────────────────
    temperature = ctrl.Antecedent(temperature_range, 'temperature')
    humidity    = ctrl.Antecedent(humidity_range,    'humidity')
    aqi         = ctrl.Antecedent(aqi_range,         'aqi')
    risk        = ctrl.Consequent(risk_range,        'risk')

    # ── Membership functions: Temperature ─────────────────────
    # Low: 0–20°C  Moderate: 15–30°C  High: 25–40°C  Hazardous: 35–50°C
    temperature['low']      = fuzz.trimf(temperature_range, [0,   0,  20])
    temperature['moderate'] = fuzz.trimf(temperature_range, [15, 22,  30])
    temperature['high']     = fuzz.trimf(temperature_range, [25, 32,  40])
    temperature['hazardous']= fuzz.trimf(temperature_range, [35, 43,  50])

    # ── Membership functions: Humidity ─────────────────────────
    # Low: 0–40%  Moderate: 30–70%  High: 60–100%
    humidity['low']      = fuzz.trimf(humidity_range, [0,   0,  40])
    humidity['moderate'] = fuzz.trimf(humidity_range, [30, 50,  70])
    humidity['high']     = fuzz.trimf(humidity_range, [60, 80, 100])

    # ── Membership functions: AQI ──────────────────────────────
    # Good:0–50  Moderate:40–100  Unhealthy:90–200  Hazardous:175–300
    aqi['good']      = fuzz.trimf(aqi_range, [0,    0,   50])
    aqi['moderate']  = fuzz.trimf(aqi_range, [40,  70,  100])
    aqi['unhealthy'] = fuzz.trimf(aqi_range, [90, 145,  200])
    aqi['hazardous'] = fuzz.trimf(aqi_range, [175, 237, 300])

    # ── Membership functions: Risk Score (output) ──────────────
    risk['safe']      = fuzz.trimf(risk_range, [0,   0,  30])
    risk['advisory']  = fuzz.trimf(risk_range, [20, 40,  60])
    risk['warning']   = fuzz.trimf(risk_range, [50, 65,  80])
    risk['emergency'] = fuzz.trimf(risk_range, [70, 85, 100])

    # ── Fuzzy Rule Base (IF-THEN rules) ───────────────────────
    # These are the linguistic rules that define system behavior
    rules = [
        # Safe conditions
        ctrl.Rule(aqi['good']      & temperature['low']       & humidity['moderate'], risk['safe']),
        ctrl.Rule(aqi['good']      & temperature['moderate']  & humidity['low'],      risk['safe']),
        ctrl.Rule(aqi['good']      & temperature['low']       & humidity['low'],      risk['safe']),

        # Advisory conditions
        ctrl.Rule(aqi['moderate']  & temperature['moderate']  & humidity['moderate'], risk['advisory']),
        ctrl.Rule(aqi['good']      & temperature['high']      & humidity['high'],     risk['advisory']),
        ctrl.Rule(aqi['moderate']  & temperature['low']       & humidity['high'],     risk['advisory']),
        ctrl.Rule(aqi['moderate']  & temperature['high']      & humidity['low'],      risk['advisory']),

        # Warning conditions
        ctrl.Rule(aqi['unhealthy'] & temperature['moderate']  & humidity['moderate'], risk['warning']),
        ctrl.Rule(aqi['unhealthy'] & temperature['high']      & humidity['moderate'], risk['warning']),
        ctrl.Rule(aqi['moderate']  & temperature['hazardous'] & humidity['high'],     risk['warning']),
        ctrl.Rule(aqi['unhealthy'] & temperature['low']       & humidity['high'],     risk['warning']),

        # Emergency conditions
        ctrl.Rule(aqi['hazardous'] & temperature['hazardous'] & humidity['high'],     risk['emergency']),
        ctrl.Rule(aqi['hazardous'] & temperature['high']      & humidity['high'],     risk['emergency']),
        ctrl.Rule(aqi['hazardous'] & temperature['moderate']  & humidity['moderate'], risk['emergency']),
        ctrl.Rule(aqi['hazardous'] & temperature['low']       & humidity['low'],      risk['warning']),
        ctrl.Rule(aqi['unhealthy'] & temperature['hazardous'] & humidity['high'],     risk['emergency']),
    ]

    # ── Build and return the control system ───────────────────
    risk_ctrl   = ctrl.ControlSystem(rules)
    risk_sim    = ctrl.ControlSystemSimulation(risk_ctrl)

    return risk_sim


# Build the system once at import time
_fuzzy_sim = build_fuzzy_system()


def compute_risk(temperature: float, humidity: float, aqi: float):
    """
    Run the Mamdani fuzzy inference for one sensor reading.

    Parameters
    ----------
    temperature : float  (°C,  0–50)
    humidity    : float  (%,   0–100)
    aqi         : float  (AQI, 0–300)

    Returns
    -------
    risk_score  : float  (0–100, continuous)
    risk_label  : str    (Safe / Advisory / Warning / Emergency)
    """
    # Clamp inputs to valid ranges to prevent edge-case crashes
    temperature = float(np.clip(temperature, 0,   50))
    humidity    = float(np.clip(humidity,    0,  100))
    aqi         = float(np.clip(aqi,         0,  300))

    try:
        _fuzzy_sim.input['temperature'] = temperature
        _fuzzy_sim.input['humidity']    = humidity
        _fuzzy_sim.input['aqi']         = aqi
        _fuzzy_sim.compute()
        risk_score = round(float(_fuzzy_sim.output['risk']), 2)
    except Exception:
        # Fallback: weighted average if fuzzy system hits an edge case
        risk_score = round((aqi / 300) * 60 + (temperature / 50) * 25 + (humidity / 100) * 15, 2)

    # Map score to linguistic label
    if risk_score <= 30:
        risk_label = "Safe"
    elif risk_score <= 55:
        risk_label = "Advisory"
    elif risk_score <= 75:
        risk_label = "Warning"
    else:
        risk_label = "Emergency"

    return risk_score, risk_label


def get_risk_color(risk_label: str) -> str:
    """Return a hex color for a given risk label (used by dashboard)."""
    return {
        "Safe":      "#2ecc71",
        "Advisory":  "#f1c40f",
        "Warning":   "#e67e22",
        "Emergency": "#e74c3c",
    }.get(risk_label, "#95a5a6")
