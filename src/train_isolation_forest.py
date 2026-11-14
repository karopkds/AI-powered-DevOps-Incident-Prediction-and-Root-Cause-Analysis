
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent.parent

TRAIN_FILE = ROOT / "data/processed/normal_training_data.csv"
TEST_FILE = ROOT / "data/processed/experiment_02_labeled.csv"

MODEL_FILE = ROOT / "models/isolation_forest_v2.joblib"
RESULT_FILE = ROOT / "data/processed/isolation_forest_v2_results.csv"

FEATURES = [
    "request_rate",
    "error_5xx_rate",
    "avg_latency_seconds",
]

train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)

def prepare_features(df):
    X = df[FEATURES].copy()
    X = X.apply(pd.to_numeric, errors="coerce")
    return X.replace([np.inf, -np.inf], np.nan)

X_train = prepare_features(train_df)
X_test = prepare_features(test_df)

pipeline = Pipeline([
    ("imputer", SimpleImputer(
        strategy="constant",
        fill_value=0.0
    )),
    ("model", IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42
    )),
])

pipeline.fit(X_train)

test_df["anomaly_prediction"] = pipeline.predict(X_test)
test_df["anomaly_score"] = pipeline.decision_function(X_test)
test_df["is_anomaly"] = (
    test_df["anomaly_prediction"] == -1
).astype(int)

MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)

joblib.dump(pipeline, MODEL_FILE)
test_df.to_csv(RESULT_FILE, index=False)

print("Isolation Forest V2 training completed!")
print("Training observations:", len(train_df))
print("Testing observations:", len(test_df))
print("Detected anomalies:", test_df["is_anomaly"].sum())

print("\nIncident vs Anomaly:")
print(pd.crosstab(
    test_df["incident_active"],
    test_df["is_anomaly"]
))

print("\nAnomaly score statistics:")
print(test_df["anomaly_score"].describe())

print("\nModel saved:", MODEL_FILE)
print("Results saved:", RESULT_FILE)
