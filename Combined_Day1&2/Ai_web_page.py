"""system System Automation: Day 1 rule engine + Day 2 trained ML model.

Run from this folder:
    streamlit run final_live_monitor.py

IMPORTANT: The default sensor source is SIMULATED telemetry. Replace
read_sensor_data() with your real sensor/PLC/OPC-UA/MQTT reader before
using this with physical equipment. This dashboard does not stop machinery.
"""
from pathlib import Path
from datetime import datetime
import random
import csv
import warnings

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
MODEL_PATH = PROJECT_ROOT / "DAY2" / "telemetry_model.pkl"
HISTORY_PATH = ROOT / "live_monitor_history.csv"
FEATURES = ["temperature", "pressure", "vibration", "rpm", "current"]
MACHINES = [f"Machine_{i}" for i in range(1, 6)]

st.set_page_config(page_title="system Live Machine Monitor", page_icon="⚙️", layout="wide")

@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found at {MODEL_PATH}. Keep DAY2/telemetry_model.pkl next to this script."
        )
    # The bundled model was saved with scikit-learn 1.4.2. Install that version
    # from requirements.txt for the most reproducible model loading.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return joblib.load(MODEL_PATH)


def read_sensor_data(machine_name: str) -> dict:
    """Generate one simulated live reading in the approximate training-data range.

    Replace this function with your hardware data acquisition code. Return all
    five numeric keys in FEATURES, using the same units/ranges as training data.
    """
    return {
        "temperature": round(random.uniform(54.0, 98.0), 2),  # deg C
        "pressure": round(random.uniform(1.4, 6.5), 2),      # training-data units
        "vibration": round(random.uniform(1.2, 6.5), 2),     # training-data units
        "rpm": int(random.uniform(1350, 2250)),
        "current": round(random.uniform(7.5, 25.0), 2),      # training-data units
    }


# Day 1 priority rule engine adapted to Day 2's feature scales.
# These are example thresholds, not certified machine safety limits.
RULES = [
    (1, "HIGH_TEMP", lambda x: x["temperature"] > 80),
    (2, "LOW_PRESSURE", lambda x: x["pressure"] < 3.0),
    (3, "HIGH_VIBRATION", lambda x: x["vibration"] > 5.0),
    (4, "MOTOR_OVERLOAD", lambda x: x["current"] > 18.0),
    (5, "RPM_OUT_OF_RANGE", lambda x: x["rpm"] < 1300 or x["rpm"] > 2300),
]


def evaluate_rules(reading):
    for _, name, condition in sorted(RULES, key=lambda r: r[0]):
        if condition(reading):
            return name
    return "NO_RULE_FIRED"


def classify_reading(model, reading):
    row = pd.DataFrame([[reading[f] for f in FEATURES]], columns=FEATURES)
    prediction = str(model.predict(row)[0])
    rule = evaluate_rules(reading)
    if rule != "NO_RULE_FIRED":
        action = "STOP_MACHINE / ATTENTION REQUIRED"
        status = "ALERT"
    elif prediction != "NORMAL":
        action = "INSPECT MACHINE"
        status = "WARNING"
    else:
        action = "CONTINUE NORMAL"
        status = "NORMAL"
    confidence = None
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(row)[0]
        confidence = float(np.max(probabilities)) * 100
    return prediction, rule, action, status, confidence


def append_history(rows):
    if not rows:
        return
    frame = pd.DataFrame(rows)
    frame.to_csv(HISTORY_PATH, mode="a", header=not HISTORY_PATH.exists(), index=False)


st.title("⚙️ system — Live Machine Monitoring")
st.caption("Day 1: priority-based rule engine  •  Day 2: trained Random Forest model")
st.warning("DEMO MODE: readings are simulated. This dashboard only reports alerts; it does not control or stop real machinery.")

try:
    model = load_model()
except Exception as exc:
    st.error(f"Could not load the trained model: {exc}")
    st.stop()

with st.sidebar:
    st.header("Monitoring settings")
    live = st.toggle("Run live simulation", value=True)
    refresh_seconds = st.slider("Refresh interval (seconds)", min_value=1, max_value=10, value=2)
    st.caption("For real hardware, replace read_sensor_data() in the script and validate all thresholds with your supervisor.")

if live:
    st_autorefresh(interval=refresh_seconds * 1000, key="system_live_refresh")

if "monitor_rows" not in st.session_state:
    st.session_state.monitor_rows = []

# Generate a new set on initial load and on each auto-refresh while live is enabled.
if live or not st.session_state.monitor_rows:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    new_rows = []
    for machine in MACHINES:
        reading = read_sensor_data(machine)
        prediction, rule, action, status, confidence = classify_reading(model, reading)
        new_rows.append({
            "timestamp": now,
            "machine": machine,
            **reading,
            "ml_prediction": prediction,
            "rule_triggered": rule,
            "status": status,
            "recommended_action": action,
            "model_confidence_pct": round(confidence, 2) if confidence is not None else None,
        })
    st.session_state.monitor_rows = (new_rows + st.session_state.monitor_rows)[:500]
    try:
        append_history(new_rows)
    except Exception as exc:
        st.warning(f"Could not write history CSV: {exc}")

history = pd.DataFrame(st.session_state.monitor_rows)
latest = history.drop_duplicates(subset=["machine"], keep="first").copy()
alerts = int((latest["status"] == "ALERT").sum())
warnings_count = int((latest["status"] == "WARNING").sum())
normal = int((latest["status"] == "NORMAL").sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Machines monitored", len(latest))
c2.metric("Rule alerts", alerts)
c3.metric("ML warnings", warnings_count)
c4.metric("Normal", normal)

st.subheader("Current machine status")
def highlight_status(row):
    if row["status"] == "ALERT":
        return ["background-color: #ffe0e0"] * len(row)
    if row["status"] == "WARNING":
        return ["background-color: #fff0cc"] * len(row)
    return ["background-color: #e3f5e8"] * len(row)

show_cols = ["machine", "temperature", "pressure", "vibration", "rpm", "current", "ml_prediction", "model_confidence_pct", "rule_triggered", "status", "recommended_action", "timestamp"]
st.dataframe(latest[show_cols].style.apply(highlight_status, axis=1), use_container_width=True, hide_index=True)

left, right = st.columns(2)
with left:
    st.subheader("Latest sensor readings")
    sensor_choice = st.selectbox("Choose sensor", ["temperature", "pressure", "vibration", "rpm", "current"])
    chart_data = latest.set_index("machine")[[sensor_choice]]
    st.bar_chart(chart_data)
with right:
    st.subheader("ML prediction counts — latest cycle")
    st.bar_chart(latest["ml_prediction"].value_counts().rename_axis("prediction").to_frame("machines"))

st.subheader("Recent monitoring history")
st.dataframe(history[show_cols].head(50), use_container_width=True, hide_index=True)

csv_bytes = history.to_csv(index=False).encode("utf-8")
st.download_button("Download session history (CSV)", data=csv_bytes, file_name="system_live_monitor_history.csv", mime="text/csv")
if st.button("Clear displayed session history"):
    st.session_state.monitor_rows = []
    st.rerun()

with st.expander("How the combined system works"):
    st.markdown("""
    1. **Day 1 rule engine:** checks each machine reading against priority rules.
    2. **Day 2 trained model:** the bundled `telemetry_model.pkl` predicts `NORMAL`, `OVERHEATING`, `HIGH_VIBRATION`, `LOW_PRESSURE`, or `MOTOR_OVERLOAD`.
    3. **Combined result:** a rule trigger produces an alert; otherwise, a non-normal model prediction produces a warning; only a normal prediction with no rule trigger is shown as normal.
    4. **Logging:** each cycle is appended to `live_monitor_history.csv`.

    The thresholds in this demo are illustrative. Confirm sensor units and safety limits for the actual machine before using real telemetry.
    """)
