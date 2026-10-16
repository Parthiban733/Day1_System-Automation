"""
run_demo.py
------------
Executes the Robotic Arm Joint Health Monitoring System across a fleet
of arms on an assembly line. Demonstrates all four required decisions:
1. SAFE
2. MONITOR
3. SCHEDULE_MAINTENANCE
4. EMERGENCY_STOP (Immediate Safety Threshold)
Plus an explicit test of the Spoofed Sensor Defense!
"""

from joint_health_system import evaluate_arm_health, WearPredictor

def run_demonstration():
    print("=" * 80)
    print("      ROBOTIC ARM JOINT HEALTH MONITORING SYSTEM - DEMONSTRATION")
    print("        Course: 23IF02 · System Automation Bonus Challenge")
    print("=" * 80)

    # Initialize predictive ML model
    predictor = WearPredictor()

    # Define test fleet scenarios to demonstrate each outcome
    fleet = [
        {
            # Case 1: All sensors within normal limits, routine inspection clean
            # Expected outcome: SAFE
            "arm_id": "Arm-01",
            "shoulder": {"torque": 42.0, "temperature": 45.0, "vibration": 0.8},
            "elbow":    {"torque": 31.0, "temperature": 41.0, "vibration": 0.7},
            "wrist":    {"torque": 18.0, "temperature": 36.0, "vibration": 0.5},
        },
        {
            # Case 2: Sensors nominal, but technician noted grinding noise in log
            # Expected outcome: MONITOR (single signal alert)
            "arm_id": "Arm-02",
            "shoulder": {"torque": 46.0, "temperature": 49.0, "vibration": 1.1},
            "elbow":    {"torque": 34.0, "temperature": 43.0, "vibration": 0.8},
            "wrist":    {"torque": 19.0, "temperature": 37.0, "vibration": 0.6},
        },
        {
            # Case 3: Wrist joint shows wear symptoms (T=44Nm, Temp=64C, Vib=3.4)
            # AND technician log noted excessive backlash & mechanical jitter
            # Expected outcome: SCHEDULE_MAINTENANCE (corroborated dual signals)
            "arm_id": "Arm-03",
            "shoulder": {"torque": 48.0, "temperature": 52.0, "vibration": 1.2},
            "elbow":    {"torque": 36.0, "temperature": 46.0, "vibration": 1.0},
            "wrist":    {"torque": 44.0, "temperature": 64.0, "vibration": 3.4},
        },
        {
            # Case 4: Shoulder temperature spikes to 98.5 C (> 95.0 C critical safety limit)
            # Expected outcome: EMERGENCY_STOP (deterministic immediate safety stop)
            "arm_id": "Arm-04",
            "shoulder": {"torque": 75.0, "temperature": 98.5, "vibration": 3.1},
            "elbow":    {"torque": 35.0, "temperature": 45.0, "vibration": 0.9},
            "wrist":    {"torque": 20.0, "temperature": 39.0, "vibration": 0.6},
        },
        {
            # Case 5: Spoofed sensor attack test
            # Elbow has high temp (78 C) and high vibration (4.2 mm/s),
            # but adversary injected fake low torque (9.5 Nm) to mask severe binding!
            # Expected outcome: EMERGENCY_STOP (spoof defense triggered)
            "arm_id": "Arm-05",
            "shoulder": {"torque": 45.0, "temperature": 50.0, "vibration": 1.0},
            "elbow":    {"torque": 9.5,  "temperature": 78.0, "vibration": 4.2},
            "wrist":    {"torque": 18.0, "temperature": 40.0, "vibration": 0.6},
        }
    ]

    for arm_data in fleet:
        arm_id = arm_data["arm_id"]
        result = evaluate_arm_health(arm_data, predictor=predictor)

        print(f"\n--- EVALUATING {arm_id} ---")
        print(f"Telemetry Summary:")
        for joint in ["shoulder", "elbow", "wrist"]:
            t = arm_data[joint]
            print(f"  * {joint.title():8s}: Torque={t['torque']:5.1f} Nm | Temp={t['temperature']:5.1f} C | Vib={t['vibration']:4.1f} mm/s")

        print(f"\n>>> FINAL DECISION: [{result['decision']}]")
        print(f"    Reason        : {result['reason']}")
        if "details" in result:
            print(f"    Details       : {result['details']}")
        print("-" * 80)

if __name__ == "__main__":
    run_demonstration()
