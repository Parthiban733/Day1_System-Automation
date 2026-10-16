# Day 1 & Day 2 System Automation + Bonus Challenge

This repository contains hands-on coursework and projects for **23IF02 · System Automation**:
- **DAY1**: Rule engine fundamentals and deterministic safety limits.
- **DAY2**: Telemetry dataset generation, predictive machine learning models (`RandomForestClassifier`), and model evaluation.
- **Combined_Day1&2**: Live machine monitoring terminal and dashboard.
- **Bonus_Challenge**: Robotic Arm Joint Health Monitoring System.

---

## Bonus Challenge: Robotic Arm Joint Health Monitoring System

An automated multi-signal health monitoring and safety system for a fleet of 6-axis robotic arms on an assembly line. It monitors joint torque, joint temperature, and vibration at the shoulder, elbow, and wrist joints.

### Features
1. **Immediate Safety Stop**: Deterministic $O(1)$ fail-safe stopping the arm immediately if temperature ($>95^\circ\text{C}$), torque ($>120\text{ Nm}$), or vibration ($>8\text{ mm/s}$) crosses dangerous limits (does not depend on ML).
2. **Predictive Wear Detection**: Machine learning model (`RandomForestClassifier`) trained on synthetic historical degradation data (`historical_wear_dataset.csv`, 360 records) to predict joint wear before failures occur.
3. **Maintenance Notes Analysis**: Natural language scanning of free-text technician inspection logs (`maintenance_logs.txt`) for mechanical warning keywords.
4. **Spoofed-Sensor Defense**: Physics-based cross-sensor correlation detecting spoofed low-torque injections that attempt to mask high heat and vibration.
5. **Multi-Signal Decision Matrix**: Generates one final decision per arm:
   - `SAFE`
   - `MONITOR`
   - `SCHEDULE_MAINTENANCE`
   - `EMERGENCY_STOP`

### How to Run

```bash
# 1. Navigate to the bonus challenge folder
cd Bonus_Challenge

# 2. (Optional) Re-generate dataset and retrain model
python generate_dataset.py
python train_wear_model.py

# 3. Run the complete demonstration showing all 4 outcomes + spoof defense
python run_demo.py
```

### Documentation
See [Bonus_Challenge/explanation.md](Bonus_Challenge/explanation.md) for the detailed half-page written explanation addressing:
- Safety threshold selection rationale.
- ML prediction and maintenance log combination logic.
- Spoofed-sensor defense mechanics, attack coverage, and limitations.
