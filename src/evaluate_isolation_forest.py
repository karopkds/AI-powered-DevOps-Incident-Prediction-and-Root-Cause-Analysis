
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
)

ROOT = Path(__file__).resolve().parent.parent

MODEL_FILE = ROOT / "models/isolation_forest_v2.joblib"
TEST_FILE = ROOT / "data/processed/experiment_04_labeled.csv"
RESULT_FILE = ROOT / "data/processed/experiment_04_predictions.csv"

FEATURES = [
    "request_rate",
    "error_5xx_rate",
    "avg_latency_seconds",
]

# Load the previously trained model
model = joblib.load(MODEL_FILE)

# Load independent experiment data
df = pd.read_csv(TEST_FILE)

X_test = df[FEATURES].copy()
X_test = X_test.apply(pd.to_numeric, errors="coerce")
X_test = X_test.replace([np.inf, -np.inf], np.nan)

# Predict without retraining
df["anomaly_prediction"] = model.predict(X_test)
df["anomaly_score"] = model.decision_function(X_test)

df["is_anomaly"] = (
    df["anomaly_prediction"] == -1
).astype(int)

# Compare with recorded incident-state labels
y_true = df["incident_active"]
y_pred = df["is_anomaly"]

print("Experiment 3 — Independent Evaluation")
print("-----------------------------------")
print("Total observations:", len(df))
print("Actual incident-active observations:", y_true.sum())
print("Detected anomalies:", y_pred.sum())

print("\nConfusion Matrix:")
print(confusion_matrix(y_true, y_pred, labels=[0, 1]))

print("\nClassification Report:")
print(classification_report(
    y_true,
    y_pred,
    labels=[0, 1],
    target_names=["Normal", "Incident"],
    zero_division=0,
))

RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(RESULT_FILE, index=False)

print("\nPredictions saved to:", RESULT_FILE)
