"""
app.py
------
Streamlit dashboard for FuzzyEnvCloud.
Includes:
  - Login system (role-based: admin vs viewer)
  - Live sensor readings charts (Temperature, Humidity, AQI, Risk Score)
  - Alerts log table
  - Summary statistics
  - Benchmark panel (admin only)
Run with:
    streamlit run app.py --server.port 8501
"""

import time
import random
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from database import init_db, get_latest_readings, get_latest_alerts, get_stats
from fuzzy_engine import get_risk_color

# ── Page config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="FuzzyEnvCloud Dashboard",
    page_icon="🌿",
    layout="wide",
)

# ── User store (role-based access) ───────────────────────────────
USERS = {
    "admin":  {"password": "admin123",  "role": "admin"},
    "viewer": {"password": "viewer123", "role": "viewer"},
}

# ── Initialize DB on startup ─────────────────────────────────────
init_db()

# ── Session state defaults ───────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""


# ── Login Page ───────────────────────────────────────────────────
def show_login():
    st.markdown(
        """
        <style>
        .login-box {
            max-width: 400px;
            margin: 80px auto;
            background: #1e1e2e;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        .login-title {
            color: #a6e3a1;
            font-size: 2rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 8px;
        }
        .login-sub {
            color: #cdd6f4;
            text-align: center;
            margin-bottom: 32px;
            font-size: 0.95rem;
        }
        </style>
        <div class='login-box'>
            <div class='login-title'>🌿 FuzzyEnvCloud</div>
            <div class='login-sub'>IoT Environmental Monitoring System</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 Login")
        username = st.text_input("Username", placeholder="admin or viewer")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        if st.button("Login", use_container_width=True, type="primary"):
            user = USERS.get(username)
            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = user["role"]
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")
        st.caption("Admin: `admin / admin123` | Viewer: `viewer / viewer123`")


# ── Helper: color badge ──────────────────────────────────────────
def badge(label: str) -> str:
    colors = {
        "Safe": "#2ecc71", "Advisory": "#f1c40f",
        "Warning": "#e67e22", "Emergency": "#e74c3c",
    }
    bg = colors.get(label, "#95a5a6")
    return f"<span style='background:{bg};color:#fff;padding:2px 10px;border-radius:20px;font-size:0.82rem'>{label}</span>"


# ── Benchmark simulation ─────────────────────────────────────────
def run_benchmark():
    loads = [10, 50, 100, 200, 500]
    results = {"loads": loads, "serverless": [], "vm_based": [], "cost": []}
    for load in loads:
        cold_start = max(0, (20 - load * 0.02))
        serverless = round(cold_start + random.uniform(18, 28) + load * 0.01, 1)
        vm = round(random.uniform(20, 30) + (load ** 1.3) * 0.08, 1)
        serverless_cost = round((load * 60 * 24 * 30) * 0.0000002, 4)
        vm_cost = 8.50
        results["serverless"].append(serverless)
        results["vm_based"].append(vm)
        results["cost"].append({
            "load": load,
            "serverless_cost": serverless_cost,
            "vm_cost": vm_cost,
            "saving_percent": round((1 - serverless_cost / vm_cost) * 100, 1),
        })
    return results


# ── Main Dashboard ───────────────────────────────────────────────
def show_dashboard():
    # Sidebar
    with st.sidebar:
        st.markdown(f"## 🌿 FuzzyEnvCloud")
        st.markdown(f"**User:** `{st.session_state.username}`")
        st.markdown(f"**Role:** `{st.session_state.role}`")
        st.divider()
        auto_refresh = st.toggle("🔄 Auto Refresh (5s)", value=True)
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.rerun()

    st.title("🌿 FuzzyEnvCloud — IoT Environmental Monitoring")
    st.caption("Live dashboard powered by Mamdani Fuzzy Inference System")

    # ── Fetch data ──────────────────────────────────────────────
    readings = get_latest_readings(limit=50)
    alerts   = get_latest_alerts(limit=10)
    stats    = get_stats()

    # ── Stats Cards ─────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    avgs = stats.get("averages", {})
    c1.metric("📊 Total Readings", stats.get("total_readings", 0))
    c2.metric("🌡 Avg Temperature", f"{round(avgs.get('avg_temp') or 0, 1)}°C")
    c3.metric("💧 Avg Humidity",    f"{round(avgs.get('avg_hum') or 0, 1)}%")
    c4.metric("🚨 Total Alerts",    stats.get("alert_count", 0))

    st.divider()

    if not readings:
        st.info("⏳ Waiting for sensor data... Make sure sensor_simulator.py is running.")
        if auto_refresh:
            time.sleep(5)
            st.rerun()
        return

    df = pd.DataFrame(readings)

    # ── Latest Reading Highlight ─────────────────────────────────
    latest = readings[0]
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.subheader("📡 Latest Reading")
        risk_color = get_risk_color(latest["risk_label"])
        st.markdown(
            f"""
            <div style='background:#1e1e2e;border-radius:12px;padding:20px;border-left:5px solid {risk_color}'>
                <div style='font-size:2.5rem;font-weight:700;color:{risk_color}'>{latest['risk_score']}<span style='font-size:1rem;color:#cdd6f4'>/100</span></div>
                <div style='color:#cdd6f4;font-size:1.1rem;margin-bottom:8px'>{badge(latest['risk_label'])}</div>
                <hr style='border-color:#313244'>
                <div style='color:#cdd6f4'>🌡 <b>{latest['temperature']}°C</b> &nbsp; 💧 <b>{latest['humidity']}%</b> &nbsp; 🏭 AQI <b>{latest['aqi']}</b></div>
                <div style='color:#6c7086;font-size:0.8rem;margin-top:8px'>{latest['timestamp']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_b:
        # Risk gauge chart
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest["risk_score"],
            title={"text": "Fuzzy Risk Score", "font": {"color": "#cdd6f4"}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar":  {"color": get_risk_color(latest["risk_label"])},
                "steps": [
                    {"range": [0,  30], "color": "#2ecc71"},
                    {"range": [30, 55], "color": "#f1c40f"},
                    {"range": [55, 75], "color": "#e67e22"},
                    {"range": [75,100], "color": "#e74c3c"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 3},
                    "thickness": 0.75,
                    "value": latest["risk_score"],
                },
            },
            number={"font": {"color": "#cdd6f4"}},
        ))
        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=250, margin=dict(t=10, b=10, l=30, r=30),
            font={"color": "#cdd6f4"},
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.divider()

    # ── Time-series charts ───────────────────────────────────────
    df_chart = df.iloc[::-1]  # chronological order

    tab1, tab2, tab3, tab4 = st.tabs(["🌡 Temperature", "💧 Humidity", "🏭 AQI", "⚠️ Risk Score"])

    def make_line(y_col, color, labels):
        fig = go.Figure(go.Scatter(
            x=df_chart["timestamp"], y=df_chart[y_col],
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=4),
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, color="#cdd6f4"),
            yaxis=dict(gridcolor="#313244", color="#cdd6f4"),
            height=280, margin=dict(t=10, b=10, l=10, r=10),
        )
        return fig

    with tab1:
        st.plotly_chart(make_line("temperature", "#e74c3c", "°C"), use_container_width=True)
    with tab2:
        st.plotly_chart(make_line("humidity", "#3498db", "%"), use_container_width=True)
    with tab3:
        st.plotly_chart(make_line("aqi", "#9b59b6", ""), use_container_width=True)
    with tab4:
        st.plotly_chart(make_line("risk_score", "#e67e22", "/100"), use_container_width=True)

    st.divider()

    # ── Alerts Table ─────────────────────────────────────────────
    st.subheader("🚨 Recent Alerts")
    if alerts:
        df_alerts = pd.DataFrame(alerts)[["timestamp", "risk_label", "risk_score", "temperature", "humidity", "aqi", "message"]]
        df_alerts.columns = ["Time", "Level", "Score", "Temp (°C)", "Humidity (%)", "AQI", "Message"]
        st.dataframe(df_alerts, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No alerts yet — environment looks safe!")

    # ── Benchmark panel (admin only) ─────────────────────────────
    if st.session_state.role == "admin":
        st.divider()
        st.subheader("📈 Serverless vs VM Benchmark (Admin Only)")
        if st.button("▶️ Run Benchmark Simulation"):
            with st.spinner("Simulating load scenarios..."):
                time.sleep(1)
                bm = run_benchmark()
            df_bm = pd.DataFrame({
                "Load (req/min)": bm["loads"],
                "Serverless (ms)": bm["serverless"],
                "VM-based (ms)":   bm["vm_based"],
            })
            fig_bm = go.Figure()
            fig_bm.add_trace(go.Scatter(x=df_bm["Load (req/min)"], y=df_bm["Serverless (ms)"], mode="lines+markers", name="Serverless", line=dict(color="#2ecc71")))
            fig_bm.add_trace(go.Scatter(x=df_bm["Load (req/min)"], y=df_bm["VM-based (ms)"],   mode="lines+markers", name="VM-Based",    line=dict(color="#e74c3c")))
            fig_bm.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(title="Load (req/min)", color="#cdd6f4"),
                yaxis=dict(title="Response Time (ms)", gridcolor="#313244", color="#cdd6f4"),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#cdd6f4")),
                height=300, margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig_bm, use_container_width=True)

            cost_data = pd.DataFrame(bm["cost"])
            cost_data.columns = ["Load", "Serverless Cost ($)", "VM Cost ($)", "Saving (%)"]
            st.dataframe(cost_data, use_container_width=True, hide_index=True)

    # ── Auto refresh ─────────────────────────────────────────────
    if auto_refresh:
        time.sleep(5)
        st.rerun()


# ── Entry point ──────────────────────────────────────────────────
if st.session_state.logged_in:
    show_dashboard()
else:
    show_login()