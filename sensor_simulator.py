"""
sensor_simulator.py
-------------------
Simulates an IoT environmental sensor device.

In a real deployment this would be a physical sensor (e.g. Raspberry Pi)
sending data to AWS IoT Core. Here we simulate it with Python, which is
standard practice in IoT research prototyping.

Sends one reading every 5 seconds to the local SQLite database.
Occasionally injects anomaly spikes to test the fuzzy alert system.
"""

import random
import time
from datetime import datetime
from database import init_db, insert_sensor_reading, insert_fuzzy_result, insert_alert
from fuzzy_engine import compute_risk

# ── Simulation configuration ────────────────────────────────
INTERVAL_SECONDS = 5      # how often to send a reading
ANOMALY_CHANCE   = 0.08   # 8% chance of injecting a dangerous spike


def generate_normal_reading():
    """Generate a typical environmental sensor reading."""
    return {
        "temperature": round(random.uniform(18.0, 35.0), 2),
        "humidity":    round(random.uniform(35.0, 75.0), 2),
        "aqi":         round(random.uniform(10.0, 120.0), 2),
    }


def generate_anomaly_reading():
    """
    Inject a dangerous spike reading.
    Used to test the fuzzy emergency alert pipeline.
    """
    spike_type = random.choice(["heat_wave", "pollution", "combined"])

    if spike_type == "heat_wave":
        return {
            "temperature": round(random.uniform(40.0, 50.0), 2),
            "humidity":    round(random.uniform(70.0, 95.0), 2),
            "aqi":         round(random.uniform(80.0, 140.0), 2),
        }
    elif spike_type == "pollution":
        return {
            "temperature": round(random.uniform(25.0, 35.0), 2),
            "humidity":    round(random.uniform(40.0, 60.0), 2),
            "aqi":         round(random.uniform(200.0, 300.0), 2),
        }
    else:  # combined worst case
        return {
            "temperature": round(random.uniform(38.0, 50.0), 2),
            "humidity":    round(random.uniform(75.0, 95.0), 2),
            "aqi":         round(random.uniform(220.0, 300.0), 2),
        }


def send_alert(timestamp, risk_label, risk_score, reading):
    """
    Log an alert to the database.
    In a real cloud deployment, this would trigger AWS SNS
    to send an email/SMS. Here it logs locally and prints to console.
    """
    message = (
        f"[{risk_label.upper()} ALERT] Environmental risk score: {risk_score}/100 | "
        f"Temp: {reading['temperature']}°C | "
        f"Humidity: {reading['humidity']}% | "
        f"AQI: {reading['aqi']}"
    )
    insert_alert(
        timestamp  = timestamp,
        risk_label = risk_label,
        risk_score = risk_score,
        temperature= reading['temperature'],
        humidity   = reading['humidity'],
        aqi        = reading['aqi'],
        message    = message
    )
    print(f"  🚨 ALERT TRIGGERED: {message}")


def run_simulator():
    """Main simulator loop — runs indefinitely until Ctrl+C."""
    print("=" * 60)
    print("  FuzzyEnvCloud — IoT Sensor Simulator")
    print("  Simulating environmental sensor readings...")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    # Initialize database tables on first run
    init_db()

    reading_count = 0

    while True:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Decide normal or anomaly reading
            if random.random() < ANOMALY_CHANCE:
                reading = generate_anomaly_reading()
                reading_type = "⚡ ANOMALY"
            else:
                reading = generate_normal_reading()
                reading_type = "📡 NORMAL "

            # Step 1: Store raw sensor reading (simulates IoT ingestion layer)
            reading_id = insert_sensor_reading(
                timestamp   = timestamp,
                temperature = reading['temperature'],
                humidity    = reading['humidity'],
                aqi         = reading['aqi'],
            )

            # Step 2: Run Fuzzy Mamdani Inference (core intelligence layer)
            risk_score, risk_label = compute_risk(
                temperature = reading['temperature'],
                humidity    = reading['humidity'],
                aqi         = reading['aqi'],
            )

            # Step 3: Store fuzzy result (simulates processed data layer)
            insert_fuzzy_result(
                reading_id  = reading_id,
                timestamp   = timestamp,
                temperature = reading['temperature'],
                humidity    = reading['humidity'],
                aqi         = reading['aqi'],
                risk_score  = risk_score,
                risk_label  = risk_label,
            )

            reading_count += 1

            # Console log
            print(
                f"[{timestamp}] {reading_type} | "
                f"Temp: {reading['temperature']:5.1f}°C | "
                f"Hum: {reading['humidity']:5.1f}% | "
                f"AQI: {reading['aqi']:6.1f} | "
                f"Risk: {risk_score:5.1f}/100 [{risk_label}]"
            )

            # Step 4: Trigger alert if Warning or Emergency
            if risk_label in ("Warning", "Emergency"):
                send_alert(timestamp, risk_label, risk_score, reading)

            time.sleep(INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print(f"\n[Simulator stopped] Total readings sent: {reading_count}")
            break
        except Exception as e:
            print(f"[Error] {e}")
            time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run_simulator()
