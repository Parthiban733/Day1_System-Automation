import csv
import random

FILE_NAME = "HISTORY_DATA_DAY2.csv"
NUM_ROWS = 150

FIELDNAMES = [
    "Temprature", "Pressure", "Vibration",
    "RPM", "Current", "State"
]

def classify_state(tm, pr, vb, rp, cu):
    # Example operating limits; adjust for your machine.
    if (
        tm > 85 or 
        pr < 30 or pr > 80 or
        vb > 0.80 or
        rp < 100 or rp > 950 or
        cu > 18
    ):
        return "Error"
    return "Normal"

def generate_row():
    tm = random.randint(50, 95)
    pr = random.randint(20, 90)
    vb = round(random.uniform(0.0, 1.0), 4)
    rp = round(random.uniform(0.0, 1000.0), 2)
    cu = round(random.uniform(0.0, 20.0), 2)

    st = classify_state(tm, pr, vb, rp, cu)

    return {
        "Temprature": tm,
        "Pressure": pr,
        "Vibration": vb,
        "RPM": rp,
        "Current": cu,
        "State": st
    }

def validate_row(row):
    assert 50 <= row["Temprature"] <= 95
    assert 20 <= row["Pressure"] <= 90
    assert 0.0 <= row["Vibration"] <= 1.0
    assert 0.0 <= row["RPM"] <= 1000.0
    assert 0.0 <= row["Current"] <= 20.0
    assert row["State"] in ("Normal", "Error")

    # Confirm the label matches the defined rules.
    expected = classify_state(
        row["Temprature"],
        row["Pressure"],
        row["Vibration"],
        row["RPM"],
        row["Current"]
    )
    assert row["State"] == expected

rows = [generate_row() for _ in range(NUM_ROWS)]

for row in rows:
    validate_row(row)

with open(FILE_NAME, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)
