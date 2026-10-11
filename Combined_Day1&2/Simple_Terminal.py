import os
import time
import random
import joblib
import pandas as pd

from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_PATH = os.path.join(BASE_DIR, "..", "day2", "day2_sample.csv")
MODEL_PATH = os.path.join(BASE_DIR, "..", "day2", "telemetry_model.pkl")
HISTORY_PATH = os.path.join(BASE_DIR, "live_monitor_history.csv")

# Match the actual CSV column names
FEATURES = [
    "temperature",
    "pressure",
    "vibration",
    "current",
    "rpm"
]

TARGET = "state"

MACHINES = [
    "Machine-01",
    "Machine-02",
    "Machine-03",
    "Machine-04",
    "Machine-05"
]

# --------------------------------------------------
# 2. LOAD AND VALIDATE DATA
# --------------------------------------------------

if not os.path.isfile(CSV_PATH):
    raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip().str.lower()

required_columns = FEATURES + [TARGET]
missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns: {missing_columns}. "
        f"Available columns: {df.columns.tolist()}"
    )

df[FEATURES] = df[FEATURES].apply(
    pd.to_numeric, errors="coerce"
)
df[TARGET] = df[TARGET].astype("string").str.strip().str.upper()

df = df.dropna(subset=required_columns)

if df.empty:
    raise ValueError("No valid rows found in the CSV.")

if df[TARGET].nunique() < 2:
    raise ValueError("Training requires at least two state classes.")

if df[TARGET].value_counts().min() < 2:
    raise ValueError(
        "Each state needs at least two rows for stratified splitting."
    )

print("Dataset loaded:", CSV_PATH)
print("Rows:", len(df))
print("\nState distribution:")
print(df[TARGET].value_counts())

# --------------------------------------------------
# 3. TRAIN AND EVALUATE MODEL
# --------------------------------------------------

X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

model = RandomForestClassifier(
    n_estimators=300,
    class_weight="balanced",
    random_state=42
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print(f"\nHeld-out test accuracy: {accuracy * 100:.2f}%")
print("\nClassification report:")
print(classification_report(
    y_test,
    predictions,
    zero_division=0
))

# Save the trained model using all available data.
# The test score above was calculated before this final fit.
model.fit(X, y)
joblib.dump(model, MODEL_PATH)

print("Model saved:", MODEL_PATH)
print("Model features:", FEATURES)

# --------------------------------------------------
# 4. SIMULATE SENSOR DATA
# --------------------------------------------------

def generate_sensor_data():
    return {
        "temperature": round(random.uniform(25, 100), 2),
        "pressure": round(random.uniform(1, 7), 2),
        "vibration": round(random.uniform(1, 10), 2),
        "current": round(random.uniform(1, 30), 2),
        "rpm": random.randint(1400, 2200)
    }

# --------------------------------------------------
# 5. RULE-BASED AUTOMATION
# Illustrative thresholds; calibrate to your machine.
# --------------------------------------------------

def evaluate_rules(data):
    if data["temperature"] > 85:
        return "HIGH_TEMP", "INSPECT_TEMPERATURE"

    elif data["pressure"] < 3.0:
        return "LOW_PRESSURE", "CHECK_PRESSURE"

    elif data["vibration"] > 6.0:
        return "HIGH_VIBRATION", "INSPECT_VIBRATION"

    elif data["current"] > 18.0:
        return "MOTOR_OVERLOAD", "CHECK_MOTOR_LOAD"

    return "NO_RULE_FIRED", "CONTINUE_NORMAL"

# --------------------------------------------------
# 6. SAVE MONITORING HISTORY
# --------------------------------------------------

def save_history(record):
    history_df = pd.DataFrame([record])

    history_df.to_csv(
        HISTORY_PATH,
        mode="a",
        header=not os.path.exists(HISTORY_PATH),
        index=False
    )

# --------------------------------------------------
# 7. LIVE MONITORING
# --------------------------------------------------

def live_monitor():
    cycle = 0

    try:
        while True:
            cycle += 1

            print("\n" + "=" * 65)
            print(f"LIVE MONITORING - CYCLE {cycle}")
            print("=" * 65)

            for machine in MACHINES:
                data = generate_sensor_data()

                input_data = pd.DataFrame(
                    [data],
                    columns=FEATURES
                )

                prediction = str(
                    model.predict(input_data)[0]
                ).strip().upper()

                rule, action = evaluate_rules(data)

                # Any non-normal ML prediction or triggered
                # rule creates a warning.
                status = (
                    "NORMAL"
                    if prediction == "NORMAL"
                    and rule == "NO_RULE_FIRED"
                    else "WARNING"
                )

                timestamp = datetime.now().isoformat(
                    timespec="seconds"
                )

                print(f"\nMachine: {machine}")
                print(f"Time: {timestamp}")

                for feature in FEATURES:
                    print(f"{feature.title()}: {data[feature]}")

                print(f"ML Prediction: {prediction}")
                print(f"Rule Triggered: {rule}")
                print(f"Recommended Action: {action}")
                print(f"Machine Status: {status}")

                if status == "WARNING":
                    print("!!! MAINTENANCE ALERT !!!")

                record = {
                    "timestamp": timestamp,
                    "machine": machine,
                    **data,
                    "ml_prediction": prediction,
                    "rule_triggered": rule,
                    "recommended_action": action,
                    "machine_status": status
                }

                save_history(record)

            print("\nNext cycle starts in 10 seconds")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
        print("History saved to:", HISTORY_PATH)


# --------------------------------------------------
# 8. START
# --------------------------------------------------

if __name__ == "__main__":
    live_monitor()