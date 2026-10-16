"""
generate_dataset.py
-------------------
Generates a synthetic historical dataset for predictive joint wear detection
in a 6-axis robotic arm fleet.

Monitored joints:
- Shoulder (higher torque capacity)
- Elbow (medium torque capacity)
- Wrist (lower torque capacity)

Labels:
- 0: Normal (healthy joint)
- 1: Wear (bearing wear, gear degradation, lack of lubrication)
"""

import os
import csv
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "historical_wear_dataset.csv")
NUM_SAMPLES = 120

# Setting seed for reproducible synthetic data
random.seed(42)

FIELDNAMES = [
    "joint_type",
    "torque_nm",
    "temperature_c",
    "vibration_mms",
    "wear_status"
]

# Baseline normal operating parameters per joint
JOINT_CONFIGS = {
    "shoulder": {
        "normal_torque": (30.0, 65.0),
        "normal_temp": (38.0, 60.0),
        "normal_vib": (0.5, 2.0),
        "wear_torque": (70.0, 95.0),
        "wear_temp": (65.0, 85.0),
        "wear_vib": (2.8, 5.5),
    },
    "elbow": {
        "normal_torque": (20.0, 50.0),
        "normal_temp": (35.0, 55.0),
        "normal_vib": (0.4, 1.8),
        "wear_torque": (55.0, 80.0),
        "wear_temp": (60.0, 80.0),
        "wear_vib": (2.5, 5.0),
    },
    "wrist": {
        "normal_torque": (10.0, 32.0),
        "normal_temp": (30.0, 50.0),
        "normal_vib": (0.3, 1.5),
        "wear_torque": (36.0, 58.0),
        "wear_temp": (55.0, 75.0),
        "wear_vib": (2.2, 4.5),
    }
}

def generate_sample(joint_type, is_wear):
    cfg = JOINT_CONFIGS[joint_type]
    
    if is_wear:
        # Degraded joint exhibits higher torque due to friction,
        # higher temperature from heat dissipation, and elevated vibration.
        torque = round(random.uniform(*cfg["wear_torque"]) + random.gauss(0, 1.5), 2)
        temp = round(random.uniform(*cfg["wear_temp"]) + random.gauss(0, 1.2), 2)
        vib = round(random.uniform(*cfg["wear_vib"]) + random.gauss(0, 0.2), 2)
        status = 1
    else:
        # Healthy joint operating within normal specs
        torque = round(random.uniform(*cfg["normal_torque"]) + random.gauss(0, 1.5), 2)
        temp = round(random.uniform(*cfg["normal_temp"]) + random.gauss(0, 1.2), 2)
        vib = round(random.uniform(*cfg["normal_vib"]) + random.gauss(0, 0.2), 2)
        status = 0

    # Physical clamping to realistic positive values
    torque = max(5.0, torque)
    temp = max(25.0, temp)
    vib = max(0.1, vib)

    return {
        "joint_type": joint_type,
        "torque_nm": torque,
        "temperature_c": temp,
        "vibration_mms": vib,
        "wear_status": status
    }

def main():
    rows = []
    joints = ["shoulder", "elbow", "wrist"]
    
    # Generate balanced dataset of normal and worn states
    for _ in range(NUM_SAMPLES // 2):
        for j in joints:
            rows.append(generate_sample(j, is_wear=False))
            rows.append(generate_sample(j, is_wear=True))

    # Shuffle the dataset
    random.shuffle(rows)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Generated {len(rows)} historical records saved to '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    main()
