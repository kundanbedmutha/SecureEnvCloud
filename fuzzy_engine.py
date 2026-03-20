"""
fuzzy_engine.py
---------------
Mamdani Fuzzy Inference System implemented in pure NumPy.
No scikit-fuzzy dependency — fully compatible with Python 3.12.

Inputs  : temperature (°C, 0–50), humidity (%, 0–100), aqi (0–300)
Output  : risk_score (0–100), risk_label (Safe/Advisory/Warning/Emergency)

Steps:
  1. Fuzzification   — trimf / trapmf membership functions
  2. Rule Evaluation — Mamdani min-inference on 15 IF-THEN rules
  3. Aggregation     — max aggregation of rule outputs
  4. Defuzzification — centroid method
"""

import numpy as np


# ── Universe of discourse ─────────────────────────────────────────
_T   = np.arange(0,   51, 0.5)   # temperature 0–50 °C
_H   = np.arange(0,  101, 0.5)   # humidity    0–100 %
_A   = np.arange(0,  301, 1.0)   # AQI         0–300
_R   = np.arange(0,  101, 0.5)   # risk score  0–100


# ── Membership function helpers ──────────────────────────────────
def _trimf(x, a, b, c):
    """Triangular membership function."""
    return np.maximum(0, np.minimum((x - a) / (b - a + 1e-10),
                                    (c - x) / (c - b + 1e-10)))


def _degree(universe, mf, value):
    """Return membership degree of a crisp value in a MF array."""
    idx = int(round((value - universe[0]) /
                    (universe[1] - universe[0])))
    idx = np.clip(idx, 0, len(mf) - 1)
    return float(mf[idx])


# ── Pre-compute membership function arrays ─────────────────────
# Temperature
_t_low       = _trimf(_T,  0,   0,  20)
_t_moderate  = _trimf(_T, 15,  22,  30)
_t_high      = _trimf(_T, 25,  32,  40)
_t_hazardous = _trimf(_T, 35,  43,  50)

# Humidity
_h_low       = _trimf(_H,  0,   0,  40)
_h_moderate  = _trimf(_H, 30,  50,  70)
_h_high      = _trimf(_H, 60,  80, 100)

# AQI
_a_good      = _trimf(_A,   0,   0,  50)
_a_moderate  = _trimf(_A,  40,  70, 100)
_a_unhealthy = _trimf(_A,  90, 145, 200)
_a_hazardous = _trimf(_A, 175, 237, 300)

# Risk (output)
_r_safe      = _trimf(_R,  0,   0,  30)
_r_advisory  = _trimf(_R, 20,  40,  60)
_r_warning   = _trimf(_R, 50,  65,  80)
_r_emergency = _trimf(_R, 70,  85, 100)


def _fuzzify_temperature(v):
    v = np.clip(v, 0, 50)
    return {
        "low":       _degree(_T, _t_low,       v),
        "moderate":  _degree(_T, _t_moderate,  v),
        "high":      _degree(_T, _t_high,      v),
        "hazardous": _degree(_T, _t_hazardous, v),
    }


def _fuzzify_humidity(v):
    v = np.clip(v, 0, 100)
    return {
        "low":      _degree(_H, _h_low,      v),
        "moderate": _degree(_H, _h_moderate, v),
        "high":     _degree(_H, _h_high,     v),
    }


def _fuzzify_aqi(v):
    v = np.clip(v, 0, 300)
    return {
        "good":      _degree(_A, _a_good,      v),
        "moderate":  _degree(_A, _a_moderate,  v),
        "unhealthy": _degree(_A, _a_unhealthy, v),
        "hazardous": _degree(_A, _a_hazardous, v),
    }


# ── Mamdani Inference ────────────────────────────────────────────
def compute_risk(temperature: float, humidity: float, aqi: float):
    """
    Run the Mamdani fuzzy inference for one sensor reading.

    Returns
    -------
    risk_score : float  (0–100)
    risk_label : str    (Safe / Advisory / Warning / Emergency)
    """
    t = _fuzzify_temperature(temperature)
    h = _fuzzify_humidity(humidity)
    a = _fuzzify_aqi(aqi)

    # 15 IF-THEN rules: each entry is (firing_strength, output_mf)
    rules = [
        # Safe
        (min(a["good"],      t["low"],       h["moderate"]), _r_safe),
        (min(a["good"],      t["moderate"],  h["low"]),      _r_safe),
        (min(a["good"],      t["low"],       h["low"]),      _r_safe),
        # Advisory
        (min(a["moderate"],  t["moderate"],  h["moderate"]), _r_advisory),
        (min(a["good"],      t["high"],      h["high"]),     _r_advisory),
        (min(a["moderate"],  t["low"],       h["high"]),     _r_advisory),
        (min(a["moderate"],  t["high"],      h["low"]),      _r_advisory),
        # Warning
        (min(a["unhealthy"], t["moderate"],  h["moderate"]), _r_warning),
        (min(a["unhealthy"], t["high"],      h["moderate"]), _r_warning),
        (min(a["moderate"],  t["hazardous"], h["high"]),     _r_warning),
        (min(a["unhealthy"], t["low"],       h["high"]),     _r_warning),
        (min(a["hazardous"], t["low"],       h["low"]),      _r_warning),
        # Emergency
        (min(a["hazardous"], t["hazardous"], h["high"]),     _r_emergency),
        (min(a["hazardous"], t["high"],      h["high"]),     _r_emergency),
        (min(a["hazardous"], t["moderate"],  h["moderate"]), _r_emergency),
        (min(a["unhealthy"], t["hazardous"], h["high"]),     _r_emergency),
    ]

    # Aggregate: clip each output MF at its firing strength, then take max
    aggregated = np.zeros_like(_R)
    for strength, mf in rules:
        aggregated = np.maximum(aggregated, np.minimum(strength, mf))

    # Defuzzify: centroid method
    total = np.sum(aggregated)
    if total < 1e-10:
        # Fallback if no rule fires
        risk_score = round((aqi / 300) * 60 + (temperature / 50) * 25 + (humidity / 100) * 15, 2)
    else:
        risk_score = round(float(np.sum(_R * aggregated) / total), 2)

    # Map to linguistic label
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
    """Return a hex colour for a given risk label."""
    return {
        "Safe":      "#2ecc71",
        "Advisory":  "#f1c40f",
        "Warning":   "#e67e22",
        "Emergency": "#e74c3c",
    }.get(risk_label, "#95a5a6")
