"""
train_wear_model.py
-------------------
Trains a predictive machine learning model (Random Forest Classifier)
to detect robotic arm joint wear based on historical sensor data.
"""

import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "historical_wear_dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "wear_model.pkl")

# Mapping joint strings to integers for simple, clean ML input
JOINT_MAP = {
    "shoulder": 0,
    "elbow": 1,
    "wrist": 2
}

def train():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset file not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"[INFO] Loaded dataset with {len(df)} rows.")

    # Encode joint_type
    df["joint_code"] = df["joint_type"].map(JOINT_MAP)

    features = ["joint_code", "torque_nm", "temperature_c", "vibration_mms"]
    X = df[features]
    y = df["wear_status"]

    # 80-20 Train-Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"[INFO] Training set size: {len(X_train)}, Test set size: {len(X_test)}")

    model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n[EVALUATION] Model Test Accuracy: {acc * 100:.2f}%")
    print("\nClassification Report:\n", classification_report(y_test, y_pred, target_names=["Normal", "Wear"]))

    # Save model
    joblib.dump(model, MODEL_PATH)
    print(f"[OK] Trained model successfully saved to '{MODEL_PATH}'")

if __name__ == "__main__":
    train()
