import random
import time

LOG_FILE = "day1_log.txt"


# STEP 1 — Generate sensor data for one machine
def generate_sensor_data():
    return {
        "temperature": random.randint(50, 95),
        "pressure": random.randint(20, 90),
        "vibration": round(random.uniform(0.0, 1.0), 2),
    }


# STEP 2 — Define automation rules
RULES = [
    {
        "name": "HIGH_TEMP",
        "priority": 1,
        "condition": lambda r: r["temperature"] > 80,
        "action": "STOP_MACHINE",
    },
    {
        "name": "HIGH_PRESSURE",
        "priority": 2,
        "condition": lambda r: r["pressure"] > 80,
        "action": "STOP_MACHINE",
    },
    {
        "name": "HIGH_VIBRATION",
        "priority": 3,
        "condition": lambda r: r["vibration"] > 0.9,
        "action": "STOP_MACHINE",
    },
    {
        "name": "LOW_PRESSURE",
        "priority": 4,
        "condition": lambda r: r["pressure"] < 25,
        "action": "STOP_MACHINE",
    },
    {
        "name": "LOW_VIBRATION",
        "priority": 5,
        "condition": lambda r: r["vibration"] < 0.2,
        "action": "STOP_MACHINE",
    },
    {
        "name": "LOW_TEMP",
        "priority": 6,
        "condition": lambda r: r["temperature"] < 50,
        "action": "STOP_MACHINE",
    },
]


# STEP 3 — Evaluate rules in priority order
def evaluate_rules(reading, rules):
    for rule in sorted(rules, key=lambda r: r["priority"]):
        if rule["condition"](reading):
            return rule["name"], rule["action"]

    return "NO_RULE_FIRED", "CONTINUE_NORMAL"


# STEP 4 — Take action
def take_action(action):
    actions = {
        "STOP_MACHINE": "Immediate attention required!",
        "START_MACHINE": "Machine started.",
        "CONTINUE_NORMAL": "Machine operating normally.",
    }
    return actions.get(action, f"Unknown action: {action}")


# STEP 5 — Log decisions
def log_decision(machine_name, reading, rule_name, action):
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(
            f"Machine: {machine_name} | "
            f"Reading: {reading} | "
            f"Rule: {rule_name} | "
            f"Action: {action}\n"
        )


# STEP 6 — Monitor five machines
def main():
    machines = [f"Machine_{i}" for i in range(1, 6)]
    attention_needed = []

    print("\n===== FACTORY MACHINE MONITOR =====\n")

    for machine in machines:
        reading = generate_sensor_data()
        rule_name, action = evaluate_rules(reading, RULES)
        outcome = take_action(action)

        print(f"{machine}:")
        print(f"  Sensors : {reading}")
        print(f"  Rule    : {rule_name}")
        print(f"  Status  : {outcome}\n")

        log_decision(machine, reading, rule_name, action)

        if action == "STOP_MACHINE":
            attention_needed.append((machine, rule_name, reading))

    print("=" * 40)
    print("MACHINES NEEDING IMMEDIATE ATTENTION")
    print("=" * 40)

    if attention_needed:
        for machine, rule_name, reading in attention_needed:
            print(f"{machine} -> {rule_name}")
            print(f"  Sensor readings: {reading}")
    else:
        print("No machines triggered an attention rule.")

    print(f"\nTotal machines monitored: {len(machines)}")
    print(f"Machines needing attention: {len(attention_needed)}")


if __name__ == "__main__":
    main()