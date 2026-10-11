import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def train_model():
    file_path = (
        r"C:\Users\pl\OneDrive\mmm\Day1_System-Automation\DAY2\day2_sample.csv"
    )
    df = pd.read_csv(file_path)

    # --- DIAGNOSTIC PRINT ---
    # This will print the exact column names to your terminal so you can verify them
    print("Columns found in your CSV file:", df.columns.tolist())

    # OPTIONAL CLEANUP: Strips hidden white spaces from column names just in case
    df.columns = df.columns.str.strip()

    # Change "temprature" to "temperature" below if the print statement shows it has an 'e'
    X = df[["temperature", "pressure", "vibration", "rpm", "current"]]
    y = df["state"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)

    save_path = r"C:\Users\pl\OneDrive\mmm\Day1_System-Automation\DAY2\telemetry_model.pkl"
    joblib.dump(model, save_path)
    print(f"Model successfully saved to: {save_path}")

    return model


train_model()
