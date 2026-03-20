"""
database.py
-----------
Handles all SQLite database operations.
This simulates what AWS DynamoDB would do in a real cloud deployment.
"""

import sqlite3
import os

DB_PATH = "fuzzyenv.db"


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like access to rows
    return conn


def init_db():
    """
    Create the database tables if they don't exist.
    Called once at startup.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1: raw sensor readings (simulates IoT data ingestion)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            temperature REAL    NOT NULL,
            humidity    REAL    NOT NULL,
            aqi         REAL    NOT NULL
        )
    """)

    # Table 2: fuzzy risk scores (simulates processed/enriched data)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fuzzy_results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            reading_id  INTEGER NOT NULL,
            timestamp   TEXT    NOT NULL,
            temperature REAL    NOT NULL,
            humidity    REAL    NOT NULL,
            aqi         REAL    NOT NULL,
            risk_score  REAL    NOT NULL,
            risk_label  TEXT    NOT NULL,
            alert_sent  INTEGER DEFAULT 0,
            FOREIGN KEY (reading_id) REFERENCES sensor_readings(id)
        )
    """)

    # Table 3: alerts log (simulates AWS SNS alert history)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            risk_label  TEXT    NOT NULL,
            risk_score  REAL    NOT NULL,
            temperature REAL    NOT NULL,
            humidity    REAL    NOT NULL,
            aqi         REAL    NOT NULL,
            message     TEXT    NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")


def insert_sensor_reading(timestamp, temperature, humidity, aqi):
    """Insert a new raw sensor reading."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sensor_readings (timestamp, temperature, humidity, aqi)
        VALUES (?, ?, ?, ?)
    """, (timestamp, temperature, humidity, aqi))
    reading_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reading_id


def insert_fuzzy_result(reading_id, timestamp, temperature, humidity, aqi,
                         risk_score, risk_label):
    """Insert the fuzzy inference result for a sensor reading."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO fuzzy_results
            (reading_id, timestamp, temperature, humidity, aqi, risk_score, risk_label)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (reading_id, timestamp, temperature, humidity, aqi, risk_score, risk_label))
    conn.commit()
    conn.close()


def insert_alert(timestamp, risk_label, risk_score, temperature, humidity, aqi, message):
    """Log an alert event."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alerts (timestamp, risk_label, risk_score, temperature, humidity, aqi, message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, risk_label, risk_score, temperature, humidity, aqi, message))
    conn.commit()
    conn.close()


def get_latest_readings(limit=50):
    """Fetch the most recent fuzzy results for the dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM fuzzy_results
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_latest_alerts(limit=10):
    """Fetch the most recent alerts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM alerts
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_stats():
    """Get summary statistics for the dashboard header cards."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM fuzzy_results")
    total = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT risk_label, COUNT(*) as count
        FROM fuzzy_results
        GROUP BY risk_label
    """)
    label_counts = {row["risk_label"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) as total FROM alerts")
    alert_count = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT AVG(temperature) as avg_temp,
               AVG(humidity)    as avg_hum,
               AVG(aqi)         as avg_aqi,
               AVG(risk_score)  as avg_risk
        FROM fuzzy_results
    """)
    avgs = dict(cursor.fetchone())

    conn.close()
    return {
        "total_readings": total,
        "label_counts":   label_counts,
        "alert_count":    alert_count,
        "averages":       avgs,
    }
