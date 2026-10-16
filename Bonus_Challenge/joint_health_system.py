"""
joint_health_system.py
----------------------
Robotic Arm Joint Health Monitoring System
23IF02 · System Automation Bonus Challenge

Implements the complete 5-stage health monitoring pipeline:
1. Deterministic Immediate Safety Stop
2. Spoofed-Sensor Attack Defense
3. Predictive Joint Wear Detection (ML)
4. Maintenance Log Free-Text Analysis
5. Final Decision Arbitration (SAFE, MONITOR, SCHEDULE_MAINTENANCE, EMERGENCY_STOP)
"""

import os
import re
import joblib
import pandas as pd

# Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "wear_model.pkl")
LOG_PATH = os.path.join(BASE_DIR, "maintenance_logs.txt")

# ---------------------------------------------------------------------------
# 1. IMMEDIATE SAFETY THRESHOLDS (Deterministic - Day 1 Rule Engine)
# ---------------------------------------------------------------------------
# These limits are absolute physical safety boundaries. If exceeded, the arm
# must stop instantly without waiting for any ML model or text analysis.
CRITICAL_THRESHOLDS = {
    "temperature_max": 95.0,  # deg C (risk of motor insulation failure / fire)
    "torque_max": 120.0,       # Nm (mechanical overload / risk of gear shear)
    "vibration_max": 8.0       # mm/s (severe resonance, loose mounts, broken teeth)
}

# Joint mapping used by the trained ML model
JOINT_MAP = {
    "shoulder": 0,
    "elbow": 1,
    "wrist": 2
}

# ---------------------------------------------------------------------------
# 2. SPOOFED SENSOR DEFENSE (Physics-based cross-validation)
# ---------------------------------------------------------------------------
def check_sensor_spoofing(joint_name, telemetry):
    """
    Detects if sensor readings have been spoofed to mask a physical problem.
    
    Attack scenario:
    An attacker or faulty node reports artificially low torque (e.g. < 15 Nm)
    to pretend the joint is lightly loaded, while temperature and vibration
    are dangerously elevated due to severe internal friction or mechanical binding.
    """
    torque = telemetry["torque"]
    temp = telemetry["temperature"]
    vib = telemetry["vibration"]

    # Check 1: Negative torque is physically invalid for this motor sensor
    if torque < 0:
        return True, f"Negative torque reading ({torque} Nm) detected on {joint_name}."

    # Check 2: Physical correlation anomaly
    # If a joint is dissipating severe heat (> 70 C) and shaking (> 3.0 mm/s),
    # it is physically impossible to draw almost zero torque (< 18 Nm) under operation.
    if temp >= 70.0 and vib >= 3.0 and torque < 18.0:
        return True, (
            f"Physical inconsistency on {joint_name}: high heat ({temp} C) and high vibration "
            f"({vib} mm/s) reported with abnormally low torque ({torque} Nm). Potential spoofing attack!"
        )

    return False, ""

# ---------------------------------------------------------------------------
# 3. IMMEDIATE SAFETY CHECK
# ---------------------------------------------------------------------------
def evaluate_immediate_safety(arm_data):
    """
    Checks if any single joint crosses dangerous physical thresholds.
    Returns (is_emergency, reason).
    Instant and deterministic — never waits for or depends on ML.
    """
    for joint in ["shoulder", "elbow", "wrist"]:
        if joint not in arm_data:
            continue
        
        telemetry = arm_data[joint]

        # Check immediate safety limits
        if telemetry["temperature"] >= CRITICAL_THRESHOLDS["temperature_max"]:
            return True, f"CRITICAL HAZARD: {joint.title()} temperature ({telemetry['temperature']} C) >= {CRITICAL_THRESHOLDS['temperature_max']} C limit."

        if telemetry["torque"] >= CRITICAL_THRESHOLDS["torque_max"]:
            return True, f"CRITICAL HAZARD: {joint.title()} torque ({telemetry['torque']} Nm) >= {CRITICAL_THRESHOLDS['torque_max']} Nm limit."

        if telemetry["vibration"] >= CRITICAL_THRESHOLDS["vibration_max"]:
            return True, f"CRITICAL HAZARD: {joint.title()} vibration ({telemetry['vibration']} mm/s) >= {CRITICAL_THRESHOLDS['vibration_max']} mm/s limit."

    return False, ""

# ---------------------------------------------------------------------------
# 4. MAINTENANCE LOG SCANNER (Free-text inspection signal)
# ---------------------------------------------------------------------------
WARNING_KEYWORDS = [
    "grind", "grinding", "noise", "squeak", "vibration", "hot",
    "burning", "leak", "seepage", "backlash", "jitter", "loose",
    "play", "clicking", "stiff", "friction"
]

def scan_maintenance_logs(arm_id, log_file_path=LOG_PATH):
    """
    Scans plain-text technician notes for mentions of the specified arm.
    Extracts relevant mechanical warnings while filtering routine notes.
    """
    if not os.path.exists(log_file_path):
        return False, "Log file not found"

    matched_warnings = []
    
    with open(log_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            # Check if this line is about the target arm
            if arm_id.lower() in line_str.lower():
                # Check for any warning keyword
                for kw in WARNING_KEYWORDS:
                    pattern = r"\b" + re.escape(kw) + r"\b"
                    if re.search(pattern, line_str, re.IGNORECASE):
                        matched_warnings.append(line_str)
                        break

    if matched_warnings:
        return True, matched_warnings
    return False, []

# ---------------------------------------------------------------------------
# 5. PREDICTIVE WEAR DETECTION (Machine Learning Model)
# ---------------------------------------------------------------------------
class WearPredictor:
    def __init__(self, model_file=MODEL_PATH):
        self.model = None
        if os.path.exists(model_file):
            self.model = joblib.load(model_file)
        else:
            print(f"[WARN] ML Model not found at {model_file}. Model-based wear detection unavailable.")

    def predict_arm(self, arm_data):
        """
        Evaluates each joint with the trained classifier.
        Returns (wear_detected, details_list, max_confidence).
        """
        if self.model is None:
            return False, ["Model not loaded"], 0.0

        wear_flags = []
        max_prob = 0.0

        for joint in ["shoulder", "elbow", "wrist"]:
            if joint not in arm_data:
                continue

            telemetry = arm_data[joint]
            joint_code = JOINT_MAP.get(joint, 0)
            
            # Prepare feature vector: [joint_code, torque_nm, temperature_c, vibration_mms]
            input_df = pd.DataFrame([{
                "joint_code": joint_code,
                "torque_nm": telemetry["torque"],
                "temperature_c": telemetry["temperature"],
                "vibration_mms": telemetry["vibration"]
            }])

            pred = self.model.predict(input_df)[0]
            prob = float(self.model.predict_proba(input_df)[0][1]) # Probability of wear

            if prob > max_prob:
                max_prob = prob

            if pred == 1 or prob >= 0.65:
                wear_flags.append({
                    "joint": joint,
                    "confidence": round(prob * 100, 1),
                    "telemetry": telemetry
                })

        return (len(wear_flags) > 0), wear_flags, round(float(max_prob), 2)

# ---------------------------------------------------------------------------
# 6. COMPLETE DECISION PIPELINE
# ---------------------------------------------------------------------------
def evaluate_arm_health(arm_data, predictor=None, log_file=LOG_PATH):
    """
    Produces ONE final decision per robotic arm:
    - SAFE
    - MONITOR
    - SCHEDULE_MAINTENANCE
    - EMERGENCY_STOP
    """
    arm_id = arm_data.get("arm_id", "Unknown-Arm")
    
    # -----------------------------------------------------------------------
    # STEP 1: Deterministic Immediate Safety Stop Check
    # -----------------------------------------------------------------------
    is_emergency, safety_reason = evaluate_immediate_safety(arm_data)
    if is_emergency:
        return {
            "arm_id": arm_id,
            "decision": "EMERGENCY_STOP",
            "reason": safety_reason,
            "details": {"stage": "Immediate Safety Stop"}
        }

    # -----------------------------------------------------------------------
    # STEP 2: Defend Against Spoofed Sensor Attack
    # -----------------------------------------------------------------------
    for joint in ["shoulder", "elbow", "wrist"]:
        if joint in arm_data:
            is_spoofed, spoof_reason = check_sensor_spoofing(joint, arm_data[joint])
            if is_spoofed:
                return {
                    "arm_id": arm_id,
                    "decision": "EMERGENCY_STOP",
                    "reason": f"SECURITY / SPOOF ATTACK DETECTED: {spoof_reason}",
                    "details": {"stage": "Sensor Spoof Defense"}
                }

    # -----------------------------------------------------------------------
    # STEP 3: Predictive ML Wear Detection
    # -----------------------------------------------------------------------
    if predictor is None:
        predictor = WearPredictor()

    has_wear, wear_details, max_prob = predictor.predict_arm(arm_data)

    # -----------------------------------------------------------------------
    # STEP 4: Technician Maintenance Notes Analysis
    # -----------------------------------------------------------------------
    has_log_warning, log_notes = scan_maintenance_logs(arm_id, log_file)

    # -----------------------------------------------------------------------
    # STEP 5: Final Decision Arbitration Logic
    # -----------------------------------------------------------------------
    # High wear confidence OR dual corroboration -> SCHEDULE_MAINTENANCE
    if (has_wear and has_log_warning) or (has_wear and max_prob >= 0.85):
        reason = "Corroborated wear: "
        if has_wear and has_log_warning:
            reason += f"ML predicted wear ({max_prob*100:.0f}%) AND technician notes flagged mechanical issue."
        else:
            reason += f"High-confidence ML wear alert ({max_prob*100:.0f}% probability)."
            
        return {
            "arm_id": arm_id,
            "decision": "SCHEDULE_MAINTENANCE",
            "reason": reason,
            "details": {
                "ml_wear": wear_details,
                "log_warnings": log_notes,
                "confidence": max_prob
            }
        }

    # Single signal alert -> MONITOR
    if has_wear or has_log_warning:
        if has_wear:
            reason = f"ML model detected early joint wear pattern (prob: {max_prob*100:.0f}%), no technician log warnings yet."
        else:
            reason = "Technician log reported inspection warning, but sensor telemetry is still within normal boundaries."

        return {
            "arm_id": arm_id,
            "decision": "MONITOR",
            "reason": reason,
            "details": {
                "ml_wear": wear_details,
                "log_warnings": log_notes,
                "confidence": max_prob
            }
        }

    # All signals clear -> SAFE
    return {
        "arm_id": arm_id,
        "decision": "SAFE",
        "reason": "All joint telemetry normal, predictive model clear, and no maintenance log warnings.",
        "details": {"status": "Nominal Operation"}
    }
