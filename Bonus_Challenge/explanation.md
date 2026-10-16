# Robotic Arm Joint Health Monitoring System
## Bonus Challenge — Written Explanation (23IF02 · System Automation)

---

### 1. Selection of Safety Thresholds for Immediate-Stop Check
The immediate safety-stop check is deterministic and operates independently of any machine learning model or natural language log scanner. It acts as an instant, hard fail-safe ($O(1)$ rule engine) using the following physical limits:

* **Maximum Temperature ($95.0^\circ\text{C}$):**
  Industrial robot servo motors generally utilize Class F or Class H winding insulation, with maximum casing operating temperatures recommended below $80^\circ\text{C}\text{--}85^\circ\text{C}$. Operating at or above $95^\circ\text{C}$ causes rapid thermal degradation of bearing lubrication grease, demagnetization risks in permanent-magnet motors, and acute hazards of motor coil burnout or electrical fire.
* **Maximum Torque ($120.0\text{ Nm}$):**
  For standard 6-axis assembly line arms (specifically shoulder and elbow joints), continuous operational torque remains well within $30\text{--}70\text{ Nm}$. Crossing $120\text{ Nm}$ represents a dangerous mechanical overload, emergency obstruction, or tool collision. Tripping an immediate stop prevents harmonic drive gear shearing, bent motor shafts, or mounting frame damage.
* **Maximum Vibration ($8.0\text{ mm/s RMS}$):**
  According to ISO 10816 standards for industrial machinery vibration severity, vibration velocities above $4.5\text{ mm/s}$ indicate degraded operation, while levels exceeding $7.0\text{--}8.0\text{ mm/s}$ represent the "Zone D (Danger)" boundary. Such extreme vibration threatens structural integrity (e.g., loose structural anchor bolts, cracked gear teeth, or damaged raceways) and requires instantaneous cessation of motion.

---

### 2. Multi-Signal Arbitration: Combining ML Predictions and Maintenance Logs
To prevent false alarms while maintaining high sensitivity to gradual joint wear, the system employs a priority-based multi-signal arbitration pipeline:

```
[ Sensor Telemetry ] --> [ Deterministic Safety Check ] --> EMERGENCY_STOP (Hard threshold breach)
                                    | (Pass)
                                    v
                         [ Spoof Defense Check ]    --> EMERGENCY_STOP (Sensor spoof detected)
                                    | (Pass)
                                    v
               +--------------------+--------------------+
               |                                         |
               v                                         v
     [ ML Wear Model ]                         [ Free-Text Log Scanner ]
  Predicts wear prob (0-1)                    Flags technician warnings
               |                                         |
               +--------------------+--------------------+
                                    |
                                    v
                        [ Decision Combination ]
   - Dual Corroboration / Very High ML (>=85%)  --> SCHEDULE_MAINTENANCE
   - Single Signal Alert (ML only OR Log only) --> MONITOR
   - Nominal Telemetry & Clean Logs            --> SAFE
```

1. **`EMERGENCY_STOP`:** Highest priority. Triggered immediately if hard physical safety boundaries are crossed or sensor spoofing is detected.
2. **`SCHEDULE_MAINTENANCE`:** Triggered when both independent signals agree—the ML model identifies anomalous torque/temperature/vibration trends indicating wear, and the technician's free-text inspection log flags a mechanical defect (e.g., grinding sound, grease seepage, backlash). It also triggers if the ML model predicts wear with very high certainty ($\ge 85\%$).
3. **`MONITOR`:** Triggered when only a single signal raises an alert. For example, if the ML model notices early-stage wear while technician logs are clean, or if a technician logged a suspicious noise during a shift but sensor numbers remain within acceptable margins. This prevents unnecessary downtime while flagging the arm for increased surveillance.
4. **`SAFE`:** All sensors are within normal bands, the ML model predicts healthy operation, and maintenance logs report no issues.

---

### 3. Spoofed-Sensor Defense: Mechanism, Capabilities, and Limitations

#### How the Defense Works
The defense leverages physical cross-sensor correlation and conservation of energy. In electric motor joints, severe mechanical binding, worn gear teeth, or bearing breakdown generates elevated heat dissipation ($P_{\text{loss}} \propto I^2 R + \text{friction}$) and elevated vibration harmonics. An attacker attempting to mask this failure might tamper with or spoof the torque sensor stream to report a low, normal torque value (e.g., $< 18\text{ Nm}$). 

The system cross-validates torque against temperature and vibration:
$$\text{If } T_{\text{joint}} \ge 70.0^\circ\text{C} \quad \text{AND} \quad V_{\text{joint}} \ge 3.0\text{ mm/s} \quad \text{AND} \quad \tau_{\text{joint}} < 18.0\text{ Nm} \implies \textbf{SPOOF DETECTED}$$

#### What It Would Catch
* **Torque Masking Attacks:** Attacks where an adversary or corrupted sensor node feeds low/zero torque values to make a heavily strained or jammed joint appear idle or lightly loaded.
* **Negative / Out-of-Range Spoofs:** Injections reporting impossible negative torque readings ($\tau < 0$).
* **Sensor Disconnection / Zero-Drop Under Load:** A sensor failure or malicious drop to zero while the joint is actively under high thermal and vibrational stress.

#### What It Wouldn't Catch
* **Full-Vector Coordinated Spoofing:** If an attacker compromises the communication bus or PLC and simultaneously spoofs all three streams (torque, temperature, and vibration) to report consistent "healthy" values (e.g., $40\text{ Nm}$, $45^\circ\text{C}$, $0.8\text{ mm/s}$), this physical cross-check alone cannot detect the deception without bus-level message authentication codes (MACs) or cryptographic signatures.
* **Subtle In-Band Falsification:** Small bias injections (e.g., shaving $5\text{ Nm}$ off a reading when temperature is only $48^\circ\text{C}$ and vibration is $1.0\text{ mm/s}$) that remain inside plausible physical covariance envelopes.
