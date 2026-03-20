"""
app.py
------
Flask web dashboard for FuzzyEnvCloud.
Now includes:
  - Login system (Gap 2: Security)
  - Role-based access control: admin vs viewer
  - Session management

Routes:
  GET/POST /login      → login page
  GET      /logout     → logout
  GET      /           → main dashboard (requires login)
  GET      /api/data   → latest readings as JSON
  GET      /api/alerts → latest alerts as JSON
  GET      /api/stats  → summary statistics as JSON
  POST     /api/benchmark → run benchmark (admin only)
"""

from flask import (Flask, render_template, jsonify,
                   request, redirect, url_for, session)
from functools import wraps
from database import init_db, get_latest_readings, get_latest_alerts, get_stats
from fuzzy_engine import get_risk_color
import time, random

app = Flask(__name__)
app.secret_key = "fuzzyenvcloud_secret_2024"   # needed for sessions

# ── User store (simulates IAM users / role-based access) ──────
# In a real AWS deployment these would be IAM roles + Cognito
USERS = {
    "admin":  {"password": "admin123",  "role": "admin"},
    "viewer": {"password": "viewer123", "role": "viewer"},
}


# ── Auth decorators ────────────────────────────────────────────
def login_required(f):
    """Redirect to login if user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Return 403 if user is not admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


# ── Auth routes ────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = USERS.get(username)
        if user and user["password"] == password:
            session["username"] = username
            session["role"]     = user["role"]
            return redirect(url_for("dashboard"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ──────────────────────────────────────────────────
@app.route("/")
@login_required
def dashboard():
    return render_template(
        "index.html",
        username=session["username"],
        role=session["role"]
    )


# ── API routes ─────────────────────────────────────────────────
@app.route("/api/data")
@login_required
def api_data():
    readings = get_latest_readings(limit=50)
    for r in readings:
        r["color"] = get_risk_color(r["risk_label"])
    readings.reverse()
    return jsonify(readings)


@app.route("/api/alerts")
@login_required
def api_alerts():
    alerts = get_latest_alerts(limit=10)
    for a in alerts:
        a["color"] = get_risk_color(a["risk_label"])
    return jsonify(alerts)


@app.route("/api/stats")
@login_required
def api_stats():
    stats = get_stats()
    latest = get_latest_readings(limit=1)
    if latest:
        stats["latest"] = latest[0]
        stats["latest"]["color"] = get_risk_color(latest[0]["risk_label"])
    else:
        stats["latest"] = None
    return jsonify(stats)


# ── Benchmark API (admin only) ─────────────────────────────────
@app.route("/api/benchmark")
@login_required
@admin_required
def api_benchmark():
    """
    Gap 1 — Cost vs Scalability proof.
    Simulates response time comparison between:
      - Serverless (event-driven, our architecture)
      - Always-on VM (traditional architecture)
    Returns JSON results for the dashboard benchmark panel.
    """
    results = run_benchmark()
    return jsonify(results)


def run_benchmark():
    """
    Simulate the performance difference between serverless
    and always-on VM architectures under different load levels.

    In a real deployment you would measure actual AWS Lambda vs EC2
    response times. Here we simulate the known characteristics:
      - Serverless: scales instantly, zero idle cost, slight cold-start
      - VM-based:   fixed cost always, degrades under high load
    """
    loads = [10, 50, 100, 200, 500]   # requests per minute
    results = {"loads": loads, "serverless": [], "vm_based": [], "cost": []}

    for load in loads:
        # Serverless response time (ms)
        # Stays low under any load due to auto-scaling
        # Small cold-start penalty at low loads
        cold_start  = max(0, (20 - load * 0.02))
        serverless  = round(cold_start + random.uniform(18, 28) + load * 0.01, 1)

        # VM-based response time (ms)
        # Good at low load, degrades significantly under high load
        vm = round(random.uniform(20, 30) + (load ** 1.3) * 0.08, 1)

        # Simulated monthly cost (USD)
        # Serverless: pay per request (~$0.0000002 per request)
        # VM (t2.micro): fixed $8.50/month regardless of load
        serverless_cost = round((load * 60 * 24 * 30) * 0.0000002, 4)
        vm_cost         = 8.50

        results["serverless"].append(serverless)
        results["vm_based"].append(vm)
        results["cost"].append({
            "load":             load,
            "serverless_cost":  serverless_cost,
            "vm_cost":          vm_cost,
            "saving_percent":   round((1 - serverless_cost / vm_cost) * 100, 1)
        })

    return results


if __name__ == "__main__":
    init_db()
    print("=" * 60)
    print("  FuzzyEnvCloud Dashboard — With Security + Benchmarking")
    print("  Open your browser at: http://localhost:5000")
    print("  Login: admin / admin123  (full access)")
    print("  Login: viewer / viewer123 (read-only)")
    print("=" * 60)
    app.run(debug=False, host="0.0.0.0", port=5000)